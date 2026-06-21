"""Case model – investigation case container."""

from datetime import datetime
from models import db


class Case(db.Model):
    __tablename__ = "cases"

    id          = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority    = db.Column(db.Enum("Critical", "High", "Medium", "Low"),
                            nullable=False, default="Medium")
    status      = db.Column(db.Enum("Active", "Closed", "Archived", "Pending"),
                            nullable=False, default="Active")
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at   = db.Column(db.DateTime, nullable=True)

    # Relationships
    evidence      = db.relationship("Evidence",       backref="case", lazy="dynamic",
                                    cascade="all, delete-orphan")
    custody_log   = db.relationship("ChainOfCustody", backref="case", lazy="dynamic")
    assignee      = db.relationship("User", foreign_keys=[assigned_to])

    def to_dict(self):
        return {
            "id":          self.id,
            "case_number": self.case_number,
            "title":       self.title,
            "description": self.description,
            "priority":    self.priority,
            "status":      self.status,
            "created_by":  self.created_by,
            "assigned_to": self.assigned_to,
            "created_at":  self.created_at.isoformat(),
            "updated_at":  self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Case {self.case_number}>"
