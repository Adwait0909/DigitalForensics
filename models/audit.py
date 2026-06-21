"""ChainOfCustody and AuditLog models."""

from datetime import datetime
from models import db


class ChainOfCustody(db.Model):
    __tablename__ = "chain_of_custody"

    id          = db.Column(db.Integer, primary_key=True)
    case_id     = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False, index=True)
    evidence_id = db.Column(db.Integer, db.ForeignKey("evidence.id"), nullable=True, index=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"),     nullable=False)
    action      = db.Column(db.String(100), nullable=False)
    notes       = db.Column(db.Text)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address  = db.Column(db.String(45))

    def to_dict(self):
        return {
            "id":          self.id,
            "case_id":     self.case_id,
            "evidence_id": self.evidence_id,
            "user_id":     self.user_id,
            "action":      self.action,
            "notes":       self.notes,
            "timestamp":   self.timestamp.isoformat(),
            "ip_address":  self.ip_address,
        }

    def __repr__(self):
        return f"<CoC {self.action} @ {self.timestamp}>"


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action      = db.Column(db.String(200), nullable=False)
    resource    = db.Column(db.String(100))   # e.g. "evidence", "case"
    resource_id = db.Column(db.String(100))   # ID of the affected resource
    details     = db.Column(db.Text)
    ip_address  = db.Column(db.String(45))
    user_agent  = db.Column(db.String(300))
    status      = db.Column(db.Enum("success", "failure", "warning"), default="success")
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "action":      self.action,
            "resource":    self.resource,
            "resource_id": self.resource_id,
            "details":     self.details,
            "ip_address":  self.ip_address,
            "status":      self.status,
            "timestamp":   self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f"<AuditLog {self.action} @ {self.timestamp}>"


class Report(db.Model):
    __tablename__ = "reports"

    id          = db.Column(db.Integer, primary_key=True)
    case_id     = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename    = db.Column(db.String(255))
    file_path   = db.Column(db.String(500))
    report_type = db.Column(db.String(50), default="Full")
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    case      = db.relationship("Case", backref="reports")
    generator = db.relationship("User", backref="reports")

    def __repr__(self):
        return f"<Report case={self.case_id}>"
