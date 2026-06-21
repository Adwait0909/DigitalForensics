"""Case management routes – CRUD for investigation cases."""

from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app,
)
from models import db
from models.case import Case
from models.user import User
from services.audit_service import log_action, add_custody_record
from utils import login_required, get_current_user, generate_case_number, roles_required

cases_bp = Blueprint("cases", __name__)


@cases_bp.route("/")
@login_required
def list_cases():
    user = get_current_user()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    # ── Filters ───────────────────────────────────────────────────────────
    status_filter   = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    search_query    = request.args.get("q", "").strip()

    query = Case.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(
            Case.title.ilike(like) | Case.case_number.ilike(like)
        )

    cases = query.order_by(Case.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    investigators = User.query.filter(User.is_active == True).all()

    return render_template(
        "cases/list.html",
        user=user,
        cases=cases,
        investigators=investigators,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_query=search_query,
    )


@cases_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("Administrator", "Investigator")
def create_case():
    user = get_current_user()

    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority    = request.form.get("priority", "Medium")
        assigned_to = request.form.get("assigned_to") or None

        if not title:
            flash("Case title is required.", "danger")
            return redirect(url_for("cases.create_case"))

        new_case = Case(
            case_number=generate_case_number(),
            title=title,
            description=description,
            priority=priority,
            status="Active",
            created_by=user.id,
            assigned_to=int(assigned_to) if assigned_to else None,
        )
        db.session.add(new_case)
        db.session.commit()

        log_action("CASE_CREATED", user_id=user.id, resource="cases",
                   resource_id=new_case.id, details=f"Case {new_case.case_number} created")
        add_custody_record(new_case.id, user.id, "Case Created",
                           notes=f"Case '{title}' opened by {user.username}")

        flash(f"Case {new_case.case_number} created successfully.", "success")
        return redirect(url_for("cases.view_case", case_id=new_case.id))

    investigators = User.query.filter(User.is_active == True).all()
    return render_template("cases/create.html", user=user, investigators=investigators)


@cases_bp.route("/<int:case_id>")
@login_required
def view_case(case_id):
    user = get_current_user()
    case = Case.query.get_or_404(case_id)

    log_action("CASE_VIEWED", user_id=user.id, resource="cases", resource_id=case_id)

    evidence_list  = case.evidence.order_by("uploaded_at").all()
    custody_records = (
        case.custody_log
        .order_by("timestamp")
        .all()
    )

    return render_template(
        "cases/detail.html",
        user=user,
        case=case,
        evidence_list=evidence_list,
        custody_records=custody_records,
    )


@cases_bp.route("/<int:case_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("Administrator", "Investigator")
def edit_case(case_id):
    user = get_current_user()
    case = Case.query.get_or_404(case_id)

    if request.method == "POST":
        old_status  = case.status
        case.title       = request.form.get("title", case.title).strip()
        case.description = request.form.get("description", "").strip()
        case.priority    = request.form.get("priority", case.priority)
        case.status      = request.form.get("status", case.status)
        assigned_to      = request.form.get("assigned_to") or None
        case.assigned_to = int(assigned_to) if assigned_to else None

        if case.status == "Closed" and old_status != "Closed":
            case.closed_at = datetime.utcnow()

        db.session.commit()

        log_action("CASE_UPDATED", user_id=user.id, resource="cases",
                   resource_id=case_id, details=f"Case {case.case_number} updated")
        add_custody_record(case_id, user.id, "Case Updated",
                           notes=f"Status: {old_status} → {case.status}")

        flash("Case updated successfully.", "success")
        return redirect(url_for("cases.view_case", case_id=case_id))

    investigators = User.query.filter(User.is_active == True).all()
    return render_template("cases/edit.html", user=user, case=case, investigators=investigators)


@cases_bp.route("/<int:case_id>/close", methods=["POST"])
@login_required
@roles_required("Administrator", "Investigator")
def close_case(case_id):
    user = get_current_user()
    case = Case.query.get_or_404(case_id)
    case.status    = "Closed"
    case.closed_at = datetime.utcnow()
    db.session.commit()

    add_custody_record(case_id, user.id, "Case Closed",
                       notes=f"Closed by {user.username}")
    log_action("CASE_CLOSED", user_id=user.id, resource="cases", resource_id=case_id)
    flash("Case closed.", "info")
    return redirect(url_for("cases.view_case", case_id=case_id))
