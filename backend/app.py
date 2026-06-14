"""社区旧物赠送流转记录 - Flask 后端."""

import csv
import io
import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, jsonify, request, Response, make_response
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "gift.db"

RESERVATION_STATUS_PENDING = "pending"
RESERVATION_STATUS_CONFIRMED = "confirmed"
RESERVATION_STATUS_CANCELLED = "cancelled"

app = Flask(__name__)
CORS(app)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_category(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "sort_order": row["sort_order"],
    }


def row_to_gift(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "item_name": row["item_name"],
        "description": row["description"],
        "gift_date": row["gift_date"],
        "recipient_nickname": row["recipient_nickname"],
        "is_taken": bool(row["is_taken"]),
        "category_id": row["category_id"],
        "category_name": row["category_name"],
        "donor_nickname": row["donor_nickname"],
        "donor_phone": row["donor_phone"],
        "location": row["location"],
    }


def row_to_reservation(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "gift_id": row["gift_id"],
        "gift_item_name": row["gift_item_name"],
        "reserver_nickname": row["reserver_nickname"],
        "reserve_time": row["reserve_time"],
        "status": row["status"],
    }


def row_to_note(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "gift_id": row["gift_id"],
        "content": row["content"],
        "created_at": row["created_at"],
    }


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                gift_date TEXT NOT NULL,
                recipient_nickname TEXT NOT NULL DEFAULT '',
                is_taken INTEGER NOT NULL DEFAULT 0,
                category_id INTEGER DEFAULT NULL,
                donor_nickname TEXT NOT NULL DEFAULT '',
                donor_phone TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id INTEGER NOT NULL,
                reserver_nickname TEXT NOT NULL,
                reserve_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gift_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
            )
            """
        )

        cur = conn.execute("PRAGMA table_info(gifts)")
        existing_cols = {row["name"] for row in cur.fetchall()}
        if "donor_nickname" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN donor_nickname TEXT NOT NULL DEFAULT ''")
        if "donor_phone" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN donor_phone TEXT NOT NULL DEFAULT ''")
            donor_infos = [
                ("儿童绘本一套", "爱心妈妈李女士", "13800138001"),
                ("电热水壶", "201室张先生", "13800138002"),
                ("折叠晾衣架", "阳光大姐王阿姨", "13800138003"),
                ("冬季厚棉被", "退休教师陈奶奶", "13800138004"),
                ("闲置键盘", "IT工程师老刘", "13800138005"),
            ]
            for item_name, nickname, phone in donor_infos:
                conn.execute(
                    "UPDATE gifts SET donor_nickname = ?, donor_phone = ? WHERE item_name = ? AND (donor_nickname = '' OR donor_phone = '')",
                    (nickname, phone, item_name),
                )
            conn.commit()

        if "location" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN location TEXT NOT NULL DEFAULT ''")
            location_infos = [
                ("儿童绘本一套", "物业前台"),
                ("电热水壶", "菜鸟驿站"),
                ("折叠晾衣架", "楼道口"),
                ("冬季厚棉被", "物业前台"),
                ("闲置键盘", "菜鸟驿站"),
            ]
            for item_name, loc in location_infos:
                conn.execute(
                    "UPDATE gifts SET location = ? WHERE item_name = ? AND location = ''",
                    (loc, item_name),
                )
            conn.commit()

        cat_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if cat_count == 0:
            seed_categories = [
                ("图书文具", 1),
                ("家居用品", 2),
                ("服饰衣物", 3),
                ("数码电子", 4),
                ("母婴玩具", 5),
            ]
            conn.executemany(
                "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
                seed_categories,
            )
            conn.commit()

        cat_rows = conn.execute(
            "SELECT id, name FROM categories ORDER BY sort_order, id"
        ).fetchall()
        cat_map = {r["name"]: r["id"] for r in cat_rows}

        gift_count = conn.execute("SELECT COUNT(*) FROM gifts").fetchone()[0]
        if gift_count == 0:
            seed_gifts = [
                ("儿童绘本一套", "3-6 岁适用，共 12 本，品相良好", "2026-03-01", "小明妈妈", 1, cat_map.get("图书文具"), "爱心妈妈李女士", "13800138001", "物业前台"),
                ("电热水壶", "1.5L，使用约 1 年，功能正常", "2026-03-05", "邻居阿华", 0, cat_map.get("家居用品"), "201室张先生", "13800138002", "菜鸟驿站"),
                ("折叠晾衣架", "可收纳，适合小户型阳台", "2026-03-08", "302 室小李", 1, cat_map.get("家居用品"), "阳光大姐王阿姨", "13800138003", "楼道口"),
                ("冬季厚棉被", "8 斤重，已清洗晾晒", "2026-03-10", "社区志愿者", 0, cat_map.get("家居用品"), "退休教师陈奶奶", "13800138004", "物业前台"),
                ("闲置键盘", "机械键盘青轴，部分键帽有磨损", "2026-03-12", "程序员小王", 0, cat_map.get("数码电子"), "IT工程师老刘", "13800138005", "菜鸟驿站"),
            ]
            conn.executemany(
                """
                INSERT INTO gifts
                    (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                seed_gifts,
            )
            conn.commit()

        gift_rows = conn.execute("SELECT id, item_name FROM gifts ORDER BY id").fetchall()
        gift_map = {r["item_name"]: r["id"] for r in gift_rows}

        resv_count = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
        if resv_count == 0:
            seed_reservations = [
                (gift_map.get("电热水壶"), "张阿姨", "2026-03-06 10:30:00", RESERVATION_STATUS_PENDING),
                (gift_map.get("冬季厚棉被"), "501室王姐", "2026-03-11 14:20:00", RESERVATION_STATUS_CONFIRMED),
                (gift_map.get("闲置键盘"), "学生小李", "2026-03-13 09:15:00", RESERVATION_STATUS_CANCELLED),
                (gift_map.get("折叠晾衣架"), "社区赵叔", "2026-03-09 15:00:00", RESERVATION_STATUS_PENDING),
            ]
            conn.executemany(
                """
                INSERT INTO reservations
                    (gift_id, reserver_nickname, reserve_time, status)
                VALUES (?, ?, ?, ?)
                """,
                seed_reservations,
            )

        note_count = conn.execute("SELECT COUNT(*) FROM gift_notes").fetchone()[0]
        if note_count == 0:
            seed_notes = [
                (gift_map.get("儿童绘本一套"), "物品已清洗消毒，可放心使用", "2026-03-01 09:00:00"),
                (gift_map.get("儿童绘本一套"), "接收人已确认取走，孩子很喜欢", "2026-03-02 14:30:00"),
                (gift_map.get("电热水壶"), "底座稍有磨损，但不影响使用", "2026-03-05 11:00:00"),
                (gift_map.get("折叠晾衣架"), "已预约社区赵叔本周末上门领取", "2026-03-08 16:00:00"),
                (gift_map.get("折叠晾衣架"), "赵叔已取走，表示感谢", "2026-03-10 10:00:00"),
                (gift_map.get("冬季厚棉被"), "棉被已重新晾晒，保暖性好", "2026-03-10 08:30:00"),
                (gift_map.get("闲置键盘"), "赠送人说明可免费维修更换键帽", "2026-03-12 15:00:00"),
            ]
            conn.executemany(
                """
                INSERT INTO gift_notes
                    (gift_id, content, created_at)
                VALUES (?, ?, ?)
                """,
                seed_notes,
            )
        conn.commit()
    finally:
        conn.close()


# ----------------------------- Categories API -----------------------------

@app.route("/api/categories", methods=["GET"])
def list_categories():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY sort_order, id"
        ).fetchall()
        return jsonify([row_to_category(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/categories/<int:cat_id>", methods=["GET"])
def get_category(cat_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
        if row is None:
            return jsonify({"error": "类别不存在"}), 404
        return jsonify(row_to_category(row))
    finally:
        conn.close()


@app.route("/api/categories", methods=["POST"])
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "类别名称不能为空"}), 400
    sort_order = int(data.get("sort_order", 0) or 0)

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM categories WHERE name = ?", (name,)
        ).fetchone()
        if existing is not None:
            return jsonify({"error": "类别名称已存在"}), 400

        cursor = conn.execute(
            "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
            (name, sort_order),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return jsonify(row_to_category(row)), 201
    finally:
        conn.close()


@app.route("/api/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id: int):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "类别名称不能为空"}), 400
    sort_order = int(data.get("sort_order", 0) or 0)

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM categories WHERE id = ?", (cat_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "类别不存在"}), 404

        duplicate = conn.execute(
            "SELECT id FROM categories WHERE name = ? AND id != ?",
            (name, cat_id),
        ).fetchone()
        if duplicate is not None:
            return jsonify({"error": "类别名称已存在"}), 400

        conn.execute(
            "UPDATE categories SET name = ?, sort_order = ? WHERE id = ?",
            (name, sort_order, cat_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?", (cat_id,)
        ).fetchone()
        return jsonify(row_to_category(row))
    finally:
        conn.close()


@app.route("/api/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM categories WHERE id = ?", (cat_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "类别不存在"}), 404

        used_count = conn.execute(
            "SELECT COUNT(*) FROM gifts WHERE category_id = ?", (cat_id,)
        ).fetchone()[0]
        if used_count > 0:
            return jsonify({"error": f"该类别下还有 {used_count} 条赠送记录，无法删除"}), 400

        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


# ----------------------------- Gifts API -----------------------------

@app.route("/api/gifts", methods=["GET"])
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


@app.route("/api/gifts/<int:gift_id>", methods=["GET"])
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


@app.route("/api/gifts", methods=["POST"])
def create_gift():
    import re

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

        cursor = conn.execute(
            """
            INSERT INTO gifts
                (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location),
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


@app.route("/api/gifts/<int:gift_id>", methods=["PUT"])
def update_gift(gift_id: int):
    import re

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
                location = ?
            WHERE id = ?
            """,
            (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location, gift_id),
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


@app.route("/api/gifts/export", methods=["GET"])
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
        content = output.getvalue()
        output.close()

        filename = f"gift_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = make_response(content)
        response.headers["Content-Type"] = "text/csv; charset=utf-8-sig"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    finally:
        conn.close()


@app.route("/api/gifts/<int:gift_id>/mark-taken", methods=["PUT"])
def mark_gift_taken(gift_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, is_taken FROM gifts WHERE id = ?", (gift_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        if bool(existing["is_taken"]):
            return jsonify({"error": "该物品已标记为取走，无需重复操作"}), 400

        conn.execute(
            "UPDATE gifts SET is_taken = 1 WHERE id = ?",
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


@app.route("/api/gifts/<int:gift_id>", methods=["DELETE"])
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


@app.route("/api/gifts/summary", methods=["GET"])
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


# ----------------------------- Reservations API -----------------------------

@app.route("/api/reservations", methods=["GET"])
def list_reservations():
    status = request.args.get("status")
    conn = get_db()
    try:
        base_sql = """
            SELECT r.*, g.item_name AS gift_item_name
            FROM reservations r
            LEFT JOIN gifts g ON r.gift_id = g.id
        """
        params: tuple = ()
        if status:
            valid_statuses = {
                RESERVATION_STATUS_PENDING,
                RESERVATION_STATUS_CONFIRMED,
                RESERVATION_STATUS_CANCELLED,
            }
            if status not in valid_statuses:
                return jsonify({"error": "无效的预约状态"}), 400
            base_sql += " WHERE r.status = ?"
            params = (status,)
        base_sql += " ORDER BY r.reserve_time DESC, r.id DESC"
        rows = conn.execute(base_sql, params).fetchall()
        return jsonify([row_to_reservation(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/reservations/<int:resv_id>", methods=["GET"])
def get_reservation(resv_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT r.*, g.item_name AS gift_item_name
            FROM reservations r
            LEFT JOIN gifts g ON r.gift_id = g.id
            WHERE r.id = ?
            """,
            (resv_id,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "预约记录不存在"}), 404
        return jsonify(row_to_reservation(row))
    finally:
        conn.close()


@app.route("/api/reservations", methods=["POST"])
def create_reservation():
    data = request.get_json(silent=True) or {}
    gift_id = data.get("gift_id")
    reserver_nickname = (data.get("reserver_nickname") or "").strip()

    if gift_id is None:
        return jsonify({"error": "请选择预约物品"}), 400
    try:
        gift_id = int(gift_id)
    except (TypeError, ValueError):
        return jsonify({"error": "无效的物品编号"}), 400

    if not reserver_nickname:
        return jsonify({"error": "预约人昵称不能为空"}), 400

    reserve_time = (
        data.get("reserve_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ).strip()
    status = (data.get("status") or RESERVATION_STATUS_PENDING).strip()

    valid_statuses = {
        RESERVATION_STATUS_PENDING,
        RESERVATION_STATUS_CONFIRMED,
        RESERVATION_STATUS_CANCELLED,
    }
    if status not in valid_statuses:
        status = RESERVATION_STATUS_PENDING

    conn = get_db()
    try:
        gift_exists = conn.execute("SELECT id FROM gifts WHERE id = ?", (gift_id,)).fetchone()
        if gift_exists is None:
            return jsonify({"error": "预约物品不存在"}), 400

        cursor = conn.execute(
            """
            INSERT INTO reservations
                (gift_id, reserver_nickname, reserve_time, status)
            VALUES (?, ?, ?, ?)
            """,
            (gift_id, reserver_nickname, reserve_time, status),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT r.*, g.item_name AS gift_item_name
            FROM reservations r
            LEFT JOIN gifts g ON r.gift_id = g.id
            WHERE r.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(row_to_reservation(row)), 201
    finally:
        conn.close()


@app.route("/api/reservations/<int:resv_id>/cancel", methods=["PUT"])
def cancel_reservation(resv_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, status FROM reservations WHERE id = ?", (resv_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "预约记录不存在"}), 404

        if existing["status"] == RESERVATION_STATUS_CANCELLED:
            return jsonify({"error": "该预约已取消，无需重复操作"}), 400

        conn.execute(
            "UPDATE reservations SET status = ? WHERE id = ?",
            (RESERVATION_STATUS_CANCELLED, resv_id),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT r.*, g.item_name AS gift_item_name
            FROM reservations r
            LEFT JOIN gifts g ON r.gift_id = g.id
            WHERE r.id = ?
            """,
            (resv_id,),
        ).fetchone()
        return jsonify(row_to_reservation(row))
    finally:
        conn.close()


@app.route("/api/stats/gifts", methods=["GET"])
def get_gift_stats():
    conn = get_db()
    try:
        total_count = conn.execute("SELECT COUNT(*) FROM gifts").fetchone()[0]
        taken_count = conn.execute(
            "SELECT COUNT(*) FROM gifts WHERE is_taken = 1"
        ).fetchone()[0]
        pending_count = total_count - taken_count

        monthly_rows = conn.execute(
            """
            SELECT
                strftime('%Y-%m', gift_date) AS month,
                COUNT(*) AS count
            FROM gifts
            GROUP BY month
            ORDER BY month DESC
            """
        ).fetchall()

        monthly_stats = [
            {"month": row["month"], "count": row["count"]}
            for row in monthly_rows
        ]

        return jsonify({
            "total_count": total_count,
            "taken_count": taken_count,
            "pending_count": pending_count,
            "monthly_stats": monthly_stats,
        })
    finally:
        conn.close()


# ----------------------------- Gift Notes API -----------------------------

@app.route("/api/gifts/<int:gift_id>/notes", methods=["GET"])
def list_gift_notes(gift_id: int):
    conn = get_db()
    try:
        gift_exists = conn.execute("SELECT id FROM gifts WHERE id = ?", (gift_id,)).fetchone()
        if gift_exists is None:
            return jsonify({"error": "赠送记录不存在"}), 404
        rows = conn.execute(
            "SELECT * FROM gift_notes WHERE gift_id = ? ORDER BY created_at DESC, id DESC",
            (gift_id,),
        ).fetchall()
        return jsonify([row_to_note(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/gifts/<int:gift_id>/notes", methods=["POST"])
def create_gift_note(gift_id: int):
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "备注内容不能为空"}), 400

    conn = get_db()
    try:
        gift_exists = conn.execute("SELECT id FROM gifts WHERE id = ?", (gift_id,)).fetchone()
        if gift_exists is None:
            return jsonify({"error": "赠送记录不存在"}), 404

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            "INSERT INTO gift_notes (gift_id, content, created_at) VALUES (?, ?, ?)",
            (gift_id, content, created_at),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM gift_notes WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return jsonify(row_to_note(row)), 201
    finally:
        conn.close()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=6000, debug=True)
