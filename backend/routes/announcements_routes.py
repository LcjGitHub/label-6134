from datetime import datetime

from flask import Blueprint, jsonify, request

from db import get_db, row_to_announcement

announcements_bp = Blueprint("announcements", __name__)


@announcements_bp.route("/api/announcements", methods=["GET"])
def list_announcements():
    conn = get_db()
    try:
        title = request.args.get("title", "").strip()
        is_pinned_param = request.args.get("is_pinned")

        query = "SELECT * FROM announcements WHERE 1=1"
        params = []

        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")

        if is_pinned_param is not None and is_pinned_param != "":
            try:
                is_pinned_val = int(is_pinned_param)
                query += " AND is_pinned = ?"
                params.append(is_pinned_val)
            except (TypeError, ValueError):
                pass

        query += " ORDER BY is_pinned DESC, publish_time DESC, id DESC"

        rows = conn.execute(query, params).fetchall()
        return jsonify([row_to_announcement(r) for r in rows])
    finally:
        conn.close()


@announcements_bp.route("/api/announcements/<int:announcement_id>", methods=["GET"])
def get_announcement(announcement_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM announcements WHERE id = ?",
            (announcement_id,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "公告不存在"}), 404
        return jsonify(row_to_announcement(row))
    finally:
        conn.close()


@announcements_bp.route("/api/announcements", methods=["POST"])
def create_announcement():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "标题不能为空"}), 400

    content = (data.get("content") or "").strip()
    publisher_nickname = (data.get("publisher_nickname") or "").strip()
    publish_time = (data.get("publish_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()
    is_pinned = 1 if data.get("is_pinned") else 0

    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO announcements
                (title, content, publisher_nickname, publish_time, is_pinned)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, content, publisher_nickname, publish_time, is_pinned),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM announcements WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(row_to_announcement(row)), 201
    finally:
        conn.close()


@announcements_bp.route("/api/announcements/<int:announcement_id>", methods=["PUT"])
def update_announcement(announcement_id: int):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "标题不能为空"}), 400

    content = (data.get("content") or "").strip()
    publisher_nickname = (data.get("publisher_nickname") or "").strip()
    publish_time = (data.get("publish_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()
    is_pinned = 1 if data.get("is_pinned") else 0

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM announcements WHERE id = ?", (announcement_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "公告不存在"}), 404

        conn.execute(
            """
            UPDATE announcements SET
                title = ?,
                content = ?,
                publisher_nickname = ?,
                publish_time = ?,
                is_pinned = ?
            WHERE id = ?
            """,
            (title, content, publisher_nickname, publish_time, is_pinned, announcement_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM announcements WHERE id = ?",
            (announcement_id,),
        ).fetchone()
        return jsonify(row_to_announcement(row))
    finally:
        conn.close()


@announcements_bp.route("/api/announcements/<int:announcement_id>/toggle-pin", methods=["PUT"])
def toggle_pin_announcement(announcement_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, is_pinned FROM announcements WHERE id = ?", (announcement_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "公告不存在"}), 404

        new_pinned = 0 if bool(existing["is_pinned"]) else 1
        conn.execute(
            "UPDATE announcements SET is_pinned = ? WHERE id = ?",
            (new_pinned, announcement_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM announcements WHERE id = ?",
            (announcement_id,),
        ).fetchone()
        return jsonify(row_to_announcement(row))
    finally:
        conn.close()


@announcements_bp.route("/api/announcements/<int:announcement_id>", methods=["DELETE"])
def delete_announcement(announcement_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM announcements WHERE id = ?", (announcement_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "公告不存在"}), 404

        conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()
