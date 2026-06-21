"""Evidence management routes – upload, view, verify, download."""

import os
import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_from_directory, abort,
)
from werkzeug.utils import secure_filename
from models import db
from models.case import Case
from models.evidence import Evidence
from services.hasher import compute_hashes, verify_integrity
from services.audit_service import log_action, add_custody_record
from utils import (
    login_required, get_current_user,
    allowed_file, safe_filename, generate_evidence_id,
    roles_required,
)

evidence_bp = Blueprint("evidence", __name__)
logger = logging.getLogger(__name__)


@evidence_bp.route("/")
@login_required
def list_evidence():
    user     = get_current_user()
    page     = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    q         = request.args.get("q", "").strip()
    status_f  = request.args.get("status", "")
    type_f    = request.args.get("file_type", "")
    case_f    = request.args.get("case_id", "")

    query = Evidence.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            Evidence.original_name.ilike(like)
            | Evidence.evidence_id.ilike(like)
            | Evidence.sha256_hash.ilike(like)
        )
    if status_f:
        query = query.filter_by(integrity_status=status_f)
    if type_f:
        query = query.filter_by(file_type=type_f)
    if case_f:
        query = query.filter_by(case_id=int(case_f))

    evidence = query.order_by(Evidence.uploaded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    cases = Case.query.order_by(Case.case_number).all()
    return render_template("evidence/list.html", user=user, evidence=evidence,
                           cases=cases, q=q, status_f=status_f,
                           type_f=type_f, case_f=case_f)


@evidence_bp.route("/upload", methods=["GET", "POST"])
@login_required
@roles_required("Administrator", "Investigator")
def upload():
    user   = get_current_user()
    cases  = Case.query.filter_by(status="Active").order_by(Case.case_number).all()

    if request.method == "POST":
        file        = request.files.get("file")
        case_id     = request.form.get("case_id")
        description = request.form.get("description", "").strip()

        # ── Validation ────────────────────────────────────────────────────
        if not file or file.filename == "":
            flash("No file selected.", "danger")
            return redirect(url_for("evidence.upload"))
        if not case_id:
            flash("Please select a case.", "danger")
            return redirect(url_for("evidence.upload"))
        if not allowed_file(file.filename):
            flash("File type not allowed.", "danger")
            return redirect(url_for("evidence.upload"))

        case = Case.query.get(int(case_id))
        if not case:
            abort(404)

        # ── Save file ─────────────────────────────────────────────────────
        orig_name  = secure_filename(file.filename)
        saved_name = safe_filename(orig_name)
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)
        save_path  = os.path.join(upload_dir, saved_name)
        file.save(save_path)

        file_size = os.path.getsize(save_path)
        ext       = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else "unknown"

        # ── Compute hashes ────────────────────────────────────────────────
        try:
            hashes = compute_hashes(save_path)
        except Exception as exc:
            logger.error("Hashing failed: %s", exc)
            os.remove(save_path)
            flash("Failed to compute file hashes. Upload aborted.", "danger")
            return redirect(url_for("evidence.upload"))

        # ── Persist to DB ─────────────────────────────────────────────────
        ev = Evidence(
            evidence_id=generate_evidence_id(),
            case_id=int(case_id),
            filename=saved_name,
            original_name=orig_name,
            file_size=file_size,
            file_type=ext,
            file_path=save_path,
            description=description,
            sha256_hash=hashes["sha256"],
            md5_hash=hashes["md5"],
            integrity_status="Unverified",
            uploaded_by=user.id,
        )
        db.session.add(ev)
        db.session.commit()

        log_action("EVIDENCE_UPLOADED", user_id=user.id, resource="evidence",
                   resource_id=ev.id,
                   details=f"{orig_name} → {ev.evidence_id} (SHA256: {hashes['sha256'][:16]}…)")
        add_custody_record(int(case_id), user.id, "Evidence Uploaded",
                           evidence_id=ev.id,
                           notes=f"File: {orig_name} | Size: {file_size} bytes")

        flash(f"Evidence {ev.evidence_id} uploaded and hashed successfully.", "success")
        return redirect(url_for("evidence.detail", evidence_id=ev.id))

    return render_template("evidence/upload.html", user=user, cases=cases)


@evidence_bp.route("/<int:evidence_id>")
@login_required
def detail(evidence_id):
    user = get_current_user()
    ev   = Evidence.query.get_or_404(evidence_id)

    log_action("EVIDENCE_VIEWED", user_id=user.id, resource="evidence",
               resource_id=evidence_id)
    add_custody_record(ev.case_id, user.id, "Evidence Viewed",
                       evidence_id=evidence_id,
                       notes=f"Viewed by {user.username}")

    custody = (
        ev.custody_log
        .order_by("timestamp")
        .all()
    )

    return render_template("evidence/detail.html", user=user, ev=ev, custody=custody)


@evidence_bp.route("/<int:evidence_id>/verify", methods=["POST"])
@login_required
def verify(evidence_id):
    user = get_current_user()
    ev   = Evidence.query.get_or_404(evidence_id)

    if not os.path.exists(ev.file_path):
        flash("Original file not found on disk. Cannot verify.", "danger")
        return redirect(url_for("evidence.detail", evidence_id=evidence_id))

    result = verify_integrity(ev.file_path, ev.sha256_hash, ev.md5_hash)

    from datetime import datetime
    ev.integrity_status  = result["status"]
    ev.last_verified_at  = datetime.utcnow()
    db.session.commit()

    note = (
        f"Verification result: {result['status']} | "
        f"SHA256 match: {result['sha256_match']} | "
        f"MD5 match: {result['md5_match']}"
    )
    log_action("EVIDENCE_VERIFIED", user_id=user.id, resource="evidence",
               resource_id=evidence_id, details=note,
               status="success" if result["status"] == "Verified" else "warning")
    add_custody_record(ev.case_id, user.id,
                       f"Integrity {result['status']}",
                       evidence_id=evidence_id, notes=note)

    badge = "success" if result["status"] == "Verified" else "danger"
    flash(f"Integrity check complete: {result['status']}", badge)
    return redirect(url_for("evidence.detail", evidence_id=evidence_id))


@evidence_bp.route("/<int:evidence_id>/download")
@login_required
def download(evidence_id):
    user = get_current_user()
    ev   = Evidence.query.get_or_404(evidence_id)

    log_action("EVIDENCE_DOWNLOADED", user_id=user.id, resource="evidence",
               resource_id=evidence_id, details=f"Downloaded: {ev.original_name}")
    add_custody_record(ev.case_id, user.id, "Evidence Downloaded",
                       evidence_id=evidence_id,
                       notes=f"Downloaded by {user.username}")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir, ev.filename, as_attachment=True,
        download_name=ev.original_name,
    )
