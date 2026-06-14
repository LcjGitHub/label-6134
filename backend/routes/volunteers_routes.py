import re
from datetime import date

from flask import Blueprint, jsonify, request

from db import get_db, row_to_volunteer

volunteers_bp = Blueprint("volunteers", __name__)


@volunteers_bp.route("/api/volunteers", methods=["GET"])
def list_volunteers():
    conn = get_db()
    try:
        name = request.args.get("name", "").strip()
        is_active_param = request.args.get("is_active")

        query = """
            SELECT * FROM volunteers WHERE 1=1
        """
        params = []

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")

        if is_active_param is not None and is_active_param != "":
            try:
                is_active_val = int(is_active_param)
                query += " AND is_active = ?"
                params.append(is_active_val)
            except (TypeError, ValueError):
                pass

        query += " ORDER BY register_date DESC, id DESC"

        rows = conn.execute(query, params).fetchall()
        return jsonify([row_to_volunteer(r) for r in rows])
    finally:
        conn.close()


@volunteers_bp.route("/api/volunteers/<int:volunteer_id>", methods=["GET"])
def get_volunteer(volunteer_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM volunteers WHERE id = ?",
            (volunteer_id,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "志愿者不存在"}), 404
        return jsonify(row_to_volunteer(row))
    finally:
        conn.close()


@volunteers_bp.route("/api/volunteers", methods=["POST"])
def create_volunteer():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "姓名不能为空"}), 400

    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "联系电话不能为空"}), 400
    if not re.match(r"^\d{11}$", phone):
        return jsonify({"error": "联系电话必须为11位数字"}), 400

    service_time = (data.get("service_time") or "").strip()
    skill_category = (data.get("skill_category") or "").strip()
    register_date = (data.get("register_date") or date.today().isoformat()).strip()
    is_active = 1 if data.get("is_active") else 0

    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO volunteers
                (name, phone, service_time, skill_category, register_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, phone, service_time, skill_category, register_date, is_active),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM volunteers WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(row_to_volunteer(row)), 201
    finally:
        conn.close()


@volunteers_bp.route("/api/volunteers/<int:volunteer_id>", methods=["PUT"])
def update_volunteer(volunteer_id: int):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "姓名不能为空"}), 400

    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "联系电话不能为空"}), 400
    if not re.match(r"^\d{11}$", phone):
        return jsonify({"error": "联系电话必须为11位数字"}), 400

    service_time = (data.get("service_time") or "").strip()
    skill_category = (data.get("skill_category") or "").strip()
    register_date = (data.get("register_date") or date.today().isoformat()).strip()
    is_active = 1 if data.get("is_active") else 0

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM volunteers WHERE id = ?", (volunteer_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "志愿者不存在"}), 404

        conn.execute(
            """
            UPDATE volunteers SET
                name = ?,
                phone = ?,
                service_time = ?,
                skill_category = ?,
                register_date = ?,
                is_active = ?
            WHERE id = ?
            """,
            (name, phone, service_time, skill_category, register_date, is_active, volunteer_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM volunteers WHERE id = ?",
            (volunteer_id,),
        ).fetchone()
        return jsonify(row_to_volunteer(row))
    finally:
        conn.close()


@volunteers_bp.route("/api/volunteers/<int:volunteer_id>", methods=["DELETE"])
def delete_volunteer(volunteer_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM volunteers WHERE id = ?", (volunteer_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "志愿者不存在"}), 404

        conn.execute("DELETE FROM volunteers WHERE id = ?", (volunteer_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()
