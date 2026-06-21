"""Evidence model – stores metadata and hash values for uploaded files."""

from datetime import datetime
from models import db


class Evidence(db.Model):
    __tablename__ = "evidence"

    id            = db.Column(db.Integer, primary_key=True)
    evidence_id   = db.Column(db.String(50), unique=True, nullable=False, index=True)
    case_id       = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False, index=True)
    filename      = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_size     = db.Column(db.BigInteger, nullable=False)
    file_type     = db.Column(db.String(50))
    file_path     = db.Column(db.String(500), nullable=False)
    description   = db.Column(db.Text)

    # ── Hashes ────────────────────────────────────────────────────────────
    sha256_hash   = db.Column(db.String(64), nullable=False, index=True)
    md5_hash      = db.Column(db.String(32), nullable=False)

    # ── Status ────────────────────────────────────────────────────────────
    integrity_status = db.Column(
        db.Enum("Unverified", "Verified", "Tampered"),
        default="Unverified",
    )
    last_verified_at = db.Column(db.DateTime, nullable=True)

    uploaded_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationship
    custody_log = db.relationship("ChainOfCustody", backref="evidence", lazy="dynamic",
                                   foreign_keys="ChainOfCustody.evidence_id")

    def to_dict(self):
        return {
            "id":               self.id,
            "evidence_id":      self.evidence_id,
            "case_id":          self.case_id,
            "filename":         self.filename,
            "original_name":    self.original_name,
            "file_size":        self.file_size,
            "file_type":        self.file_type,
            "description":      self.description,
            "sha256_hash":      self.sha256_hash,
            "md5_hash":         self.md5_hash,
            "integrity_status": self.integrity_status,
            "uploaded_by":      self.uploaded_by,
            "uploaded_at":      self.uploaded_at.isoformat(),
        }

    def __repr__(self):
        return f"<Evidence {self.evidence_id}>"
