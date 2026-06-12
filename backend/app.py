"""社区旧物赠送流转记录 - Flask 后端."""

import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "gift.db"

app = Flask(__name__)
CORS(app)


def get_db() -> sqlite3.Connection:
    """获取 SQLite 连接，并启用 Row 工厂便于字典访问."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    """将 SQLite Row 转为 API 响应字典."""
    return {
        "id": row["id"],
        "item_name": row["item_name"],
        "description": row["description"],
        "gift_date": row["gift_date"],
        "recipient_nickname": row["recipient_nickname"],
        "is_taken": bool(row["is_taken"]),
    }


def init_db() -> None:
    """初始化数据库表结构并写入 seed 数据."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                gift_date TEXT NOT NULL,
                recipient_nickname TEXT NOT NULL DEFAULT '',
                is_taken INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM gifts").fetchone()[0]
        if count == 0:
            seed_rows = [
                ("儿童绘本一套", "3-6 岁适用，共 12 本，品相良好", "2026-03-01", "小明妈妈", 1),
                ("电热水壶", "1.5L，使用约 1 年，功能正常", "2026-03-05", "邻居阿华", 0),
                ("折叠晾衣架", "可收纳，适合小户型阳台", "2026-03-08", "302 室小李", 1),
                ("冬季厚棉被", "8 斤重，已清洗晾晒", "2026-03-10", "社区志愿者", 0),
                ("闲置键盘", "机械键盘青轴，部分键帽有磨损", "2026-03-12", "程序员小王", 0),
            ]
            conn.executemany(
                """
                INSERT INTO gifts
                    (item_name, description, gift_date, recipient_nickname, is_taken)
                VALUES (?, ?, ?, ?, ?)
                """,
                seed_rows,
            )
        conn.commit()
    finally:
        conn.close()


@app.route("/api/gifts", methods=["GET"])
def list_gifts():
    """获取全部赠送记录."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM gifts ORDER BY gift_date DESC, id DESC"
        ).fetchall()
        return jsonify([row_to_dict(r) for r in rows])
    finally:
        conn.close()


@app.route("/api/gifts/<int:gift_id>", methods=["GET"])
def get_gift(gift_id: int):
    """获取单条赠送记录."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM gifts WHERE id = ?", (gift_id,)).fetchone()
        if row is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(row_to_dict(row))
    finally:
        conn.close()


@app.route("/api/gifts", methods=["POST"])
def create_gift():
    """新建赠送记录."""
    data = request.get_json(silent=True) or {}
    item_name = (data.get("item_name") or "").strip()
    if not item_name:
        return jsonify({"error": "物品名不能为空"}), 400

    gift_date = (data.get("gift_date") or date.today().isoformat()).strip()
    description = (data.get("description") or "").strip()
    recipient_nickname = (data.get("recipient_nickname") or "").strip()
    is_taken = 1 if data.get("is_taken") else 0

    conn = get_db()
    try:
        cursor = conn.execute(
            """
            INSERT INTO gifts
                (item_name, description, gift_date, recipient_nickname, is_taken)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_name, description, gift_date, recipient_nickname, is_taken),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM gifts WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return jsonify(row_to_dict(row)), 201
    finally:
        conn.close()


@app.route("/api/gifts/<int:gift_id>", methods=["PUT"])
def update_gift(gift_id: int):
    """更新赠送记录."""
    data = request.get_json(silent=True) or {}
    item_name = (data.get("item_name") or "").strip()
    if not item_name:
        return jsonify({"error": "物品名不能为空"}), 400

    gift_date = (data.get("gift_date") or date.today().isoformat()).strip()
    description = (data.get("description") or "").strip()
    recipient_nickname = (data.get("recipient_nickname") or "").strip()
    is_taken = 1 if data.get("is_taken") else 0

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM gifts WHERE id = ?", (gift_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "记录不存在"}), 404

        conn.execute(
            """
            UPDATE gifts SET
                item_name = ?,
                description = ?,
                gift_date = ?,
                recipient_nickname = ?,
                is_taken = ?
            WHERE id = ?
            """,
            (item_name, description, gift_date, recipient_nickname, is_taken, gift_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM gifts WHERE id = ?", (gift_id,)).fetchone()
        return jsonify(row_to_dict(row))
    finally:
        conn.close()


@app.route("/api/gifts/<int:gift_id>", methods=["DELETE"])
def delete_gift(gift_id: int):
    """删除赠送记录."""
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


@app.route("/api/health", methods=["GET"])
def health():
    """健康检查."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=6000, debug=True)
