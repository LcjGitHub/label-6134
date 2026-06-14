from datetime import datetime

from flask import Blueprint, jsonify, request

from db import (
    get_db,
    row_to_reservation,
    add_flow_history,
    RESERVATION_STATUS_PENDING,
    RESERVATION_STATUS_CONFIRMED,
    RESERVATION_STATUS_CANCELLED,
)

reservations_bp = Blueprint("reservations", __name__)


@reservations_bp.route("/api/reservations", methods=["GET"])
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


@reservations_bp.route("/api/reservations/<int:resv_id>", methods=["GET"])
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


@reservations_bp.route("/api/reservations", methods=["POST"])
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


@reservations_bp.route("/api/reservations/<int:resv_id>/cancel", methods=["PUT"])
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
        resv_row = conn.execute(
            """
            SELECT r.gift_id, r.reserver_nickname, g.item_name AS gift_item_name
            FROM reservations r
            LEFT JOIN gifts g ON r.gift_id = g.id
            WHERE r.id = ?
            """,
            (resv_id,),
        ).fetchone()
        if resv_row and resv_row["gift_id"]:
            add_flow_history(
                conn,
                resv_row["gift_id"],
                "cancel_reservation",
                resv_row["reserver_nickname"] or "未知",
                f"取消物品「{resv_row['gift_item_name'] or '未知'}」的预约",
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
