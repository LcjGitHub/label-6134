from flask import Blueprint, jsonify

from db import get_db

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/api/stats/gifts", methods=["GET"])
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
