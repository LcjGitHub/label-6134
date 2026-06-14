from flask import Blueprint, jsonify

from db import get_db, row_to_flow_history

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/gifts/<int:gift_id>/flow-history", methods=["GET"])
def get_flow_history(gift_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM gifts WHERE id = ?", (gift_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        rows = conn.execute(
            "SELECT * FROM gift_flow_history WHERE gift_id = ? ORDER BY operated_at DESC, id DESC",
            (gift_id,),
        ).fetchall()
        return jsonify([row_to_flow_history(r) for r in rows])
    finally:
        conn.close()
