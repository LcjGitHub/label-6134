"""社区旧物赠送流转记录 - Flask 后端."""

from flask import Flask, jsonify
from flask_cors import CORS

from db import init_db
from routes import categories_bp, gifts_bp, reservations_bp, notes_bp, stats_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(categories_bp)
app.register_blueprint(gifts_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(stats_bp)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=6000, debug=True)
