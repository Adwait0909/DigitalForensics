"""
Digital Forensics Evidence Management System (DFEMS)
Main application entry point.
"""

import os
import logging
from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from models import db, bcrypt
from routes.auth import auth_bp
from routes.cases import cases_bp
from routes.evidence import evidence_bp
from routes.dashboard import dashboard_bp
from routes.reports import reports_bp
from routes.audit import audit_bp
from routes.admin import admin_bp

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)

    # ── Blueprints ────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(cases_bp,     url_prefix="/cases")
    app.register_blueprint(evidence_bp,  url_prefix="/evidence")
    app.register_blueprint(reports_bp,   url_prefix="/reports")
    app.register_blueprint(audit_bp,     url_prefix="/audit")
    app.register_blueprint(admin_bp,     url_prefix="/admin")

    # ── Root redirect ─────────────────────────────────────────────────────
    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # ── DB init ───────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_roles(app)

    logger.info("DFEMS application started.")
    return app


def _seed_roles(app):
    """Insert default roles and admin user if the DB is empty."""
    from models.role import Role
    from models.user import User

    roles = ["Administrator", "Investigator", "Analyst", "Auditor"]
    for name in roles:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()

    if not User.query.filter_by(username="admin").first():
        admin_role = Role.query.filter_by(name="Administrator").first()
        admin = User(
            username="admin",
            email="admin@dfems.local",
            full_name="System Administrator",
            role_id=admin_role.id,
            is_active=True,
        )
        admin.set_password("Admin@1234")
        db.session.add(admin)
        db.session.commit()
        logger.info("Default admin user created  (admin / Admin@1234).")


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=5000)
