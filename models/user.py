"""User model with bcrypt password hashing."""

from datetime import datetime
from models import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email      = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name  = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id    = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cases_created  = db.relationship("Case",     backref="creator",   lazy="dynamic",
                                     foreign_keys="Case.created_by")
    evidence_uploaded = db.relationship("Evidence", backref="uploader", lazy="dynamic",
                                         foreign_keys="Evidence.uploaded_by")
    custody_records   = db.relationship("ChainOfCustody", backref="actor", lazy="dynamic")
    audit_logs        = db.relationship("AuditLog",        backref="user",  lazy="dynamic")

    # ── Password helpers ──────────────────────────────────────────────────
    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id":        self.id,
            "username":  self.username,
            "email":     self.email,
            "full_name": self.full_name,
            "role":      self.role.name if self.role else None,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"
