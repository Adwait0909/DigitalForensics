"""Audit log viewer."""

from flask import Blueprint, render_template, request, current_app
from models.audit import AuditLog
from utils import login_required, get_current_user, roles_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/")
@login_required
@roles_required("Administrator", "Auditor")
def index():
    user     = get_current_user()
    page     = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    q        = request.args.get("q", "").strip()
    status_f = request.args.get("status", "")

    query = AuditLog.query
    if q:
        like  = f"%{q}%"
        query = query.filter(
            AuditLog.action.ilike(like) | AuditLog.details.ilike(like)
        )
    if status_f:
        query = query.filter_by(status=status_f)

    logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template("audit/index.html", user=user, logs=logs,
                           q=q, status_f=status_f)
