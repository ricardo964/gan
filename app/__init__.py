"""Aplicación web MDGA (Vista + Controlador del patrón MVC, Hito 2 sección 4)."""
import os

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()


def create_app(config: dict | None = None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "mysql+pymysql://mdga:mdga_pass@localhost:3306/mdga?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024      # archivos de ingesta
    app.config["JSON_SORT_KEYS"] = False
    app.config.update(config or {})
    db.init_app(app)

    from .controllers import datos, inicio, ingesta, optimizacion, reglas, resultados

    for module in (inicio, datos, ingesta, reglas, optimizacion, resultados):
        app.register_blueprint(module.bp)

    @app.get("/health")
    def health():
        try:
            n = db.session.execute(text("SELECT COUNT(*) FROM franjas")).scalar()
            return jsonify(status="ok", db="ok", franjas=n)
        except Exception as e:  # noqa: BLE001
            return jsonify(status="error", db=str(e)), 503

    if not app.config.get("TESTING"):
        with app.app_context():
            try:
                from .services.optimizer import mark_interrupted

                mark_interrupted()
            except Exception:  # noqa: BLE001 - la BD puede no estar lista aún
                db.session.rollback()

    return app
