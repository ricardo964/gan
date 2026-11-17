import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "mysql+pymysql://mdga:mdga_pass@localhost:3306/mdga?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    db.init_app(app)

    @app.get("/health")
    def health():
        try:
            n = db.session.execute(text("SELECT COUNT(*) FROM franjas")).scalar()
            return jsonify(status="ok", db="ok", franjas=n)
        except Exception as e:  # noqa: BLE001
            return jsonify(status="error", db=str(e)), 503

    return app
