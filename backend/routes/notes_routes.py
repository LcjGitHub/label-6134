from datetime import datetime

from flask import Blueprint, jsonify, request

from db import get_db, row_to_note

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/api/gifts/<int:gift_id>/notes", methods=["GET"])
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


@notes_bp.route("/api/gifts/<int:gift_id>/notes", methods=["POST"])
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
