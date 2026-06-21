"""Reports generation route."""

import os
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, current_app, send_from_directory,
)
from models import db
from models.case import Case
from models.audit import Report
from services.report_service import generate_case_report
from services.audit_service import log_action, add_custody_record
from utils import login_required, get_current_user, roles_required

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/generate/<int:case_id>", methods=["POST"])
@login_required
@roles_required("Administrator", "Investigator", "Analyst")
def generate(case_id):
    user = get_current_user()
    case = Case.query.get_or_404(case_id)

    evidence_list   = case.evidence.order_by("uploaded_at").all()
    custody_records = case.custody_log.order_by("timestamp").all()

    try:
        filename, filepath = generate_case_report(
            case, evidence_list, custody_records,
            current_app.config["REPORTS_FOLDER"],
        )
    except Exception as exc:
        flash(f"Report generation failed: {exc}", "danger")
        return redirect(url_for("cases.view_case", case_id=case_id))

    report = Report(
        case_id=case_id,
        generated_by=user.id,
        filename=filename,
        file_path=filepath,
    )
    db.session.add(report)
    db.session.commit()

    log_action("REPORT_GENERATED", user_id=user.id, resource="cases",
               resource_id=case_id, details=f"PDF: {filename}")
    add_custody_record(case_id, user.id, "Report Generated",
                       notes=f"PDF report generated: {filename}")

    flash(f"Report {filename} generated successfully.", "success")
    return redirect(url_for("reports.download_report", report_id=report.id))


@reports_bp.route("/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = Report.query.get_or_404(report_id)
    reports_folder = current_app.config["REPORTS_FOLDER"]
    return send_from_directory(
        reports_folder, report.filename, as_attachment=True,
        download_name=report.filename,
    )
