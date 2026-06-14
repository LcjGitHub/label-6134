import csv
import io
import re
from datetime import date, datetime

from flask import Blueprint, jsonify, request, make_response

from db import get_db, row_to_gift, generate_verification_code

gifts_bp = Blueprint("gifts", __name__)


@gifts_bp.route("/api/gifts", methods=["GET"])
def list_gifts():
    conn = get_db()
    try:
        item_name = request.args.get("item_name", "").strip()
        is_taken_param = request.args.get("is_taken")

        query = """
            SELECT g.*, c.name AS category_name
            FROM gifts g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE 1=1
        """
        params = []

        if item_name:
            query += " AND g.item_name LIKE ?"
            params.append(f"%{item_name}%")

        if is_taken_param is not None and is_taken_param != "":
            try:
                is_taken_val = int(is_taken_param)
                query += " AND g.is_taken = ?"
                params.append(is_taken_val)
            except (TypeError, ValueError):
                pass

        query += " ORDER BY g.gift_date DESC, g.id DESC"

        rows = conn.execute(query, params).fetchall()
        return jsonify([row_to_gift(r) for r in rows])
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/<int:gift_id>", methods=["GET"])
def get_gift(gift_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT g.*, c.name AS category_name
            FROM gifts g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.id = ?
            """,
            (gift_id,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(row_to_gift(row))
    finally:
        conn.close()


@gifts_bp.route("/api/gifts", methods=["POST"])
def create_gift():
    data = request.get_json(silent=True) or {}
    item_name = (data.get("item_name") or "").strip()
    if not item_name:
        return jsonify({"error": "物品名不能为空"}), 400

    gift_date = (data.get("gift_date") or date.today().isoformat()).strip()
    description = (data.get("description") or "").strip()
    recipient_nickname = (data.get("recipient_nickname") or "").strip()
    is_taken = 1 if data.get("is_taken") else 0
    donor_nickname = (data.get("donor_nickname") or "").strip()
    donor_phone = (data.get("donor_phone") or "").strip()
    location = (data.get("location") or "").strip()

    if not donor_phone:
        return jsonify({"error": "联系电话不能为空"}), 400
    if not re.match(r"^\d{11}$", donor_phone):
        return jsonify({"error": "联系电话必须为11位数字"}), 400

    category_id = data.get("category_id")
    if category_id is not None:
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            category_id = None

    conn = get_db()
    try:
        if category_id is not None:
            cat_exists = conn.execute(
                "SELECT id FROM categories WHERE id = ?", (category_id,)
            ).fetchone()
            if cat_exists is None:
                category_id = None

        verification_code = None if is_taken else generate_verification_code()

        cursor = conn.execute(
            """
            INSERT INTO gifts
                (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location, verification_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location, verification_code),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT g.*, c.name AS category_name
            FROM gifts g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(row_to_gift(row)), 201
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/<int:gift_id>", methods=["PUT"])
def update_gift(gift_id: int):
    data = request.get_json(silent=True) or {}
    item_name = (data.get("item_name") or "").strip()
    if not item_name:
        return jsonify({"error": "物品名不能为空"}), 400

    gift_date = (data.get("gift_date") or date.today().isoformat()).strip()
    description = (data.get("description") or "").strip()
    recipient_nickname = (data.get("recipient_nickname") or "").strip()
    is_taken = 1 if data.get("is_taken") else 0
    donor_nickname = (data.get("donor_nickname") or "").strip()
    donor_phone = (data.get("donor_phone") or "").strip()
    location = (data.get("location") or "").strip()

    if not donor_phone:
        return jsonify({"error": "联系电话不能为空"}), 400
    if not re.match(r"^\d{11}$", donor_phone):
        return jsonify({"error": "联系电话必须为11位数字"}), 400

    category_id = data.get("category_id")
    if category_id is not None:
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            category_id = None

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM gifts WHERE id = ?", (gift_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        if category_id is not None:
            cat_exists = conn.execute(
                "SELECT id FROM categories WHERE id = ?", (category_id,)
            ).fetchone()
            if cat_exists is None:
                category_id = None

        existing_code_row = conn.execute(
            "SELECT verification_code, is_taken FROM gifts WHERE id = ?",
            (gift_id,),
        ).fetchone()
        old_is_taken = bool(existing_code_row["is_taken"])
        old_code = existing_code_row["verification_code"]

        new_verification_code = old_code
        if not is_taken and not old_code:
            new_verification_code = generate_verification_code()
        elif is_taken:
            new_verification_code = None

        conn.execute(
            """
            UPDATE gifts SET
                item_name = ?,
                description = ?,
                gift_date = ?,
                recipient_nickname = ?,
                is_taken = ?,
                category_id = ?,
                donor_nickname = ?,
                donor_phone = ?,
                location = ?,
                verification_code = ?
            WHERE id = ?
            """,
            (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location, new_verification_code, gift_id),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT g.*, c.name AS category_name
            FROM gifts g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.id = ?
            """,
            (gift_id,),
        ).fetchone()
        return jsonify(row_to_gift(row))
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/export", methods=["GET"])
def export_gifts():
    conn = get_db()
    try:
        item_name = request.args.get("item_name", "").strip()
        is_taken_param = request.args.get("is_taken")

        query = """
            SELECT g.*, c.name AS category_name
            FROM gifts g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE 1=1
        """
        params = []

        if item_name:
            query += " AND g.item_name LIKE ?"
            params.append(f"%{item_name}%")

        if is_taken_param is not None and is_taken_param != "":
            try:
                is_taken_val = int(is_taken_param)
                query += " AND g.is_taken = ?"
                params.append(is_taken_val)
            except (TypeError, ValueError):
                pass

        query += " ORDER BY g.gift_date DESC, g.id DESC"

        rows = conn.execute(query, params).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["物品名", "描述", "赠送日期", "接收方昵称", "是否已取走"])

        for row in rows:
            writer.writerow([
                row["item_name"],
                row["description"],
                row["gift_date"],
                row["recipient_nickname"],
                "已取走" if bool(row["is_taken"]) else "待取走",
            ])

        output.seek(0)
        content = "\ufeff" + output.getvalue()
        output.close()

        filename = f"gift_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = make_response(content.encode("utf-8-sig"))
        response.headers["Content-Type"] = "text/csv; charset=utf-8-sig"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/<int:gift_id>/mark-taken", methods=["PUT"])
def mark_gift_taken(gift_id: int):
    data = request.get_json(silent=True) or {}
    verification_code = (data.get("verification_code") or "").strip()

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, is_taken, verification_code FROM gifts WHERE id = ?",
            (gift_id,),
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        if bool(existing["is_taken"]):
            return jsonify({"error": "该物品已标记为取走，无需重复操作"}), 400

        if not verification_code:
            return jsonify({"error": "请输入验证码"}), 400

        if existing["verification_code"] != verification_code:
            return jsonify({"error": "验证码错误，请重新输入"}), 400

        conn.execute(
            "UPDATE gifts SET is_taken = 1, verification_code = NULL WHERE id = ?",
            (gift_id,),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT g.*, c.name AS category_name
            FROM gifts g
            LEFT JOIN categories c ON g.category_id = c.id
            WHERE g.id = ?
            """,
            (gift_id,),
        ).fetchone()
        return jsonify(row_to_gift(row))
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/<int:gift_id>/verification-code", methods=["GET"])
def get_verification_code(gift_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, is_taken, verification_code FROM gifts WHERE id = ?",
            (gift_id,),
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        if bool(existing["is_taken"]):
            return jsonify({"error": "该物品已取走，无验证码"}), 400

        if not existing["verification_code"]:
            code = generate_verification_code()
            conn.execute(
                "UPDATE gifts SET verification_code = ? WHERE id = ?",
                (code, gift_id),
            )
            conn.commit()
        else:
            code = existing["verification_code"]

        return jsonify({"verification_code": code})
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/<int:gift_id>/verification-code", methods=["PUT"])
def regenerate_verification_code(gift_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, is_taken FROM gifts WHERE id = ?", (gift_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        if bool(existing["is_taken"]):
            return jsonify({"error": "该物品已取走，无法生成验证码"}), 400

        code = generate_verification_code()
        conn.execute(
            "UPDATE gifts SET verification_code = ? WHERE id = ?",
            (code, gift_id),
        )
        conn.commit()

        return jsonify({"verification_code": code})
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/<int:gift_id>", methods=["DELETE"])
def delete_gift(gift_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM gifts WHERE id = ?", (gift_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        conn.execute("DELETE FROM gifts WHERE id = ?", (gift_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@gifts_bp.route("/api/gifts/summary", methods=["GET"])
def get_gift_summary():
    conn = get_db()
    try:
        total_count = conn.execute("SELECT COUNT(*) FROM gifts").fetchone()[0]
        taken_count = conn.execute(
            "SELECT COUNT(*) FROM gifts WHERE is_taken = 1"
        ).fetchone()[0]
        pending_count = total_count - taken_count

        return jsonify({
            "total_count": total_count,
            "taken_count": taken_count,
            "pending_count": pending_count,
        })
    finally:
        conn.close()
