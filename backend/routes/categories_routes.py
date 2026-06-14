from flask import Blueprint, jsonify, request

from db import get_db, row_to_category

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.route("", methods=["GET"])
def list_categories():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY sort_order, id"
        ).fetchall()
        return jsonify([row_to_category(r) for r in rows])
    finally:
        conn.close()


@categories_bp.route("/<int:cat_id>", methods=["GET"])
def get_category(cat_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
        if row is None:
            return jsonify({"error": "类别不存在"}), 404
        return jsonify(row_to_category(row))
    finally:
        conn.close()


@categories_bp.route("", methods=["POST"])
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


@categories_bp.route("/<int:cat_id>", methods=["PUT"])
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


@categories_bp.route("/<int:cat_id>", methods=["DELETE"])
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
