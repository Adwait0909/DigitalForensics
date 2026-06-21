"""Dashboard – overview statistics and recent activity."""

from flask import Blueprint, render_template
from models.case import Case
from models.evidence import Evidence
from models.audit import AuditLog, ChainOfCustody
from utils import login_required, get_current_user

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    user = get_current_user()

    # ── Case stats ────────────────────────────────────────────────────────
    total_cases  = Case.query.count()
    active_cases = Case.query.filter_by(status="Active").count()
    closed_cases = Case.query.filter_by(status="Closed").count()

    # ── Evidence stats ────────────────────────────────────────────────────
    total_evidence    = Evidence.query.count()
    verified_evidence = Evidence.query.filter_by(integrity_status="Verified").count()
    tampered_evidence = Evidence.query.filter_by(integrity_status="Tampered").count()

    # ── Recent activity (last 10 audit entries) ────────────────────────────
    recent_activity = (
        AuditLog.query
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )

    # ── Recent custody records ─────────────────────────────────────────────
    recent_custody = (
        ChainOfCustody.query
        .order_by(ChainOfCustody.timestamp.desc())
        .limit(8)
        .all()
    )

    # ── Recent cases ──────────────────────────────────────────────────────
    recent_cases = (
        Case.query
        .order_by(Case.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        user=user,
        total_cases=total_cases,
        active_cases=active_cases,
        closed_cases=closed_cases,
        total_evidence=total_evidence,
        verified_evidence=verified_evidence,
        tampered_evidence=tampered_evidence,
        recent_activity=recent_activity,
        recent_custody=recent_custody,
        recent_cases=recent_cases,
    )
