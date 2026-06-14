from flask import Blueprint, jsonify, request

from db import get_db, row_to_location

locations_bp = Blueprint("locations", __name__, url_prefix="/api/locations")


@locations_bp.route("", methods=["GET"])
def list_locations():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM locations ORDER BY sort_order, id"
        ).fetchall()
        return jsonify([row_to_location(r) for r in rows])
    finally:
        conn.close()


@locations_bp.route("/<int:loc_id>", methods=["GET"])
def get_location(loc_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM locations WHERE id = ?", (loc_id,)).fetchone()
        if row is None:
            return jsonify({"error": "地点不存在"}), 404
        return jsonify(row_to_location(row))
    finally:
        conn.close()


@locations_bp.route("", methods=["POST"])
def create_location():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "地点名称不能为空"}), 400
    sort_order = int(data.get("sort_order", 0) or 0)

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM locations WHERE name = ?", (name,)
        ).fetchone()
        if existing is not None:
            return jsonify({"error": "地点名称已存在"}), 400

        cursor = conn.execute(
            "INSERT INTO locations (name, sort_order) VALUES (?, ?)",
            (name, sort_order),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM locations WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return jsonify(row_to_location(row)), 201
    finally:
        conn.close()


@locations_bp.route("/<int:loc_id>", methods=["PUT"])
def update_location(loc_id: int):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "地点名称不能为空"}), 400
    sort_order = int(data.get("sort_order", 0) or 0)

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM locations WHERE id = ?", (loc_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "地点不存在"}), 404

        duplicate = conn.execute(
            "SELECT id FROM locations WHERE name = ? AND id != ?",
            (name, loc_id),
        ).fetchone()
        if duplicate is not None:
            return jsonify({"error": "地点名称已存在"}), 400

        conn.execute(
            "UPDATE locations SET name = ?, sort_order = ? WHERE id = ?",
            (name, sort_order, loc_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM locations WHERE id = ?", (loc_id,)
        ).fetchone()
        return jsonify(row_to_location(row))
    finally:
        conn.close()


@locations_bp.route("/<int:loc_id>", methods=["DELETE"])
def delete_location(loc_id: int):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM locations WHERE id = ?", (loc_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "地点不存在"}), 404

        conn.execute("DELETE FROM locations WHERE id = ?", (loc_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()
