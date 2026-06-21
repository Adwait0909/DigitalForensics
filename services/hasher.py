"""
Hashing service.
Computes SHA-256 and MD5 of uploaded files.
"""

import hashlib
import logging
from flask import current_app

logger = logging.getLogger(__name__)
CHUNK = 8192  # bytes


def _compute_local(file_path: str) -> dict:
    """Pure-Python concurrent-ish hashing (reads file once)."""
    sha256 = hashlib.sha256()
    md5    = hashlib.md5()
    try:
        with open(file_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK), b""):
                sha256.update(chunk)
                md5.update(chunk)
        return {"sha256": sha256.hexdigest(), "md5": md5.hexdigest(), "source": "local"}
    except OSError as exc:
        logger.error("Hashing failed for %s: %s", file_path, exc)
        raise


def compute_hashes(file_path: str) -> dict:
    """
    Returns {"sha256": ..., "md5": ..., "source": ...}.
    Uses local Python hashing only.
    """
    return _compute_local(file_path)


def verify_integrity(file_path: str, stored_sha256: str, stored_md5: str) -> dict:
    """
    Recomputes hashes and compares with stored values.
    Returns a dict with status and current hash values.
    """
    current = compute_hashes(file_path)
    sha_match = current["sha256"] == stored_sha256
    md5_match = current["md5"]    == stored_md5
    status = "Verified" if (sha_match and md5_match) else "Tampered"
    return {
        "status":          status,
        "sha256_match":    sha_match,
        "md5_match":       md5_match,
        "current_sha256":  current["sha256"],
        "current_md5":     current["md5"],
        "stored_sha256":   stored_sha256,
        "stored_md5":      stored_md5,
    }
