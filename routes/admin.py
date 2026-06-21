"""Admin panel – user management."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.user import User
from models.role import Role
from services.audit_service import log_action
from utils import login_required, get_current_user, roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users")
@login_required
@roles_required("Administrator")
def users():
    user  = get_current_user()
    users = User.query.order_by(User.created_at.desc()).all()
    roles = Role.query.all()
    return render_template("admin/users.html", user=user, users=users, roles=roles)


@admin_bp.route("/users/<int:uid>/toggle", methods=["POST"])
@login_required
@roles_required("Administrator")
def toggle_user(uid):
    current = get_current_user()
    target  = User.query.get_or_404(uid)
    if target.id == current.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.users"))
    target.is_active = not target.is_active
    db.session.commit()
    state = "activated" if target.is_active else "deactivated"
    log_action(f"USER_{state.upper()}", user_id=current.id,
               resource="users", resource_id=uid)
    flash(f"User {target.username} {state}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:uid>/role", methods=["POST"])
@login_required
@roles_required("Administrator")
def change_role(uid):
    current   = get_current_user()
    target    = User.query.get_or_404(uid)
    role_name = request.form.get("role")
    role      = Role.query.filter_by(name=role_name).first()
    if not role:
        flash("Invalid role.", "danger")
        return redirect(url_for("admin.users"))
    old_role      = target.role.name
    target.role_id = role.id
    db.session.commit()
    log_action("USER_ROLE_CHANGED", user_id=current.id, resource="users",
               resource_id=uid, details=f"{old_role} → {role_name}")
    flash(f"Role updated: {target.username} is now {role_name}.", "success")
    return redirect(url_for("admin.users"))
