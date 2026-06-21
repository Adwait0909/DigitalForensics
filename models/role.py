"""Role model – Administrator | Investigator | Analyst | Auditor."""

from models import db


class Role(db.Model):
    __tablename__ = "roles"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"
