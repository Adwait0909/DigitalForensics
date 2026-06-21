"""
Audit logging and Chain-of-Custody service.
Every significant action is recorded for forensic accountability.
"""

import logging
from flask import request
from models import db
from models.audit import AuditLog, ChainOfCustody

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    user_id: int | None = None,
    resource: str | None = None,
    resource_id: str | None = None,
    details: str | None = None,
    status: str = "success",
):
    """Write one row to audit_logs."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=_get_ip(),
            user_agent=request.headers.get("User-Agent", "")[:300],
            status=status,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
        db.session.rollback()


def add_custody_record(
    case_id: int,
    user_id: int,
    action: str,
    evidence_id: int | None = None,
    notes: str | None = None,
):
    """Write one row to chain_of_custody."""
    try:
        record = ChainOfCustody(
            case_id=case_id,
            evidence_id=evidence_id,
            user_id=user_id,
            action=action,
            notes=notes,
            ip_address=_get_ip(),
        )
        db.session.add(record)
        db.session.commit()
    except Exception as exc:
        logger.error("Failed to write custody record: %s", exc)
        db.session.rollback()


def _get_ip() -> str:
    """Extract the real client IP."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"
