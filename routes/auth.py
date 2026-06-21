"""Authentication routes – login, register, logout."""

from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, make_response,
)
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
)
from models import db
from models.user import User
from models.role import Role
from services.audit_service import log_action
from utils import get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.is_active and user.check_password(password):
            token = create_access_token(identity=str(user.id))
            user.last_login = datetime.utcnow()
            db.session.commit()

            log_action("USER_LOGIN", user_id=user.id, resource="auth",
                       resource_id=user.id, details=f"Login from {request.remote_addr}")

            resp = make_response(redirect(url_for("dashboard.index")))
            set_access_cookies(resp, token)
            flash(f"Welcome back, {user.full_name}!", "success")
            return resp
        else:
            log_action("FAILED_LOGIN", resource="auth",
                       details=f"Failed login for username: {username}", status="failure")
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username  = request.form.get("username", "").strip()
        email     = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password  = request.form.get("password", "")
        role_name = request.form.get("role", "Investigator")

        # ── Validation ────────────────────────────────────────────────────
        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html")

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role.query.filter_by(name="Investigator").first()

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role_id=role.id,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        log_action("USER_REGISTERED", resource="users", resource_id=new_user.id,
                   details=f"New user registered: {username}")
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    roles = Role.query.all()
    return render_template("auth/register.html", roles=roles)


@auth_bp.route("/logout")
def logout():
    user = get_current_user()
    if user:
        log_action("USER_LOGOUT", user_id=user.id, resource="auth", resource_id=user.id)
    resp = make_response(redirect(url_for("auth.login")))
    unset_jwt_cookies(resp)
    flash("You have been logged out.", "info")
    return resp
