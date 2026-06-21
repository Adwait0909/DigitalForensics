"""
Utility helpers: JWT decorators, file validation, ID generation.
"""

import os
import uuid
import string
import random
import logging
from functools import wraps
from datetime import datetime

from flask import request, redirect, url_for, flash, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.user import User

logger = logging.getLogger(__name__)

ALLOWED_CHARS = string.ascii_uppercase + string.digits


# ── Auth helpers ───────────────────────────────────────────────────────────

def get_current_user() -> User | None:
    """Return the currently logged-in User object or None."""
    try:
        verify_jwt_in_request(locations=["cookies"])
        user_id = get_jwt_identity()
        return User.query.get(int(user_id))
    except Exception:
        return None


def login_required(f):
    """Redirect to login if no valid JWT cookie is present."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_active:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def roles_required(*roles):
    """Allow access only for users with one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Please log in.", "warning")
                return redirect(url_for("auth.login"))
            if user.role.name not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── File helpers ───────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def safe_filename(filename: str) -> str:
    """Sanitise original filename and prepend a UUID to avoid collisions."""
    from werkzeug.utils import secure_filename
    base = secure_filename(filename)
    uid  = uuid.uuid4().hex[:8]
    return f"{uid}_{base}"


def human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ── ID generators ─────────────────────────────────────────────────────────

def generate_case_number() -> str:
    """e.g.  CASE-2024-XK7R"""
    year = datetime.utcnow().year
    suffix = "".join(random.choices(ALLOWED_CHARS, k=4))
    return f"CASE-{year}-{suffix}"


def generate_evidence_id() -> str:
    """e.g.  EV-A3F9B1C2"""
    suffix = "".join(random.choices(ALLOWED_CHARS + string.digits, k=8))
    return f"EV-{suffix}"
