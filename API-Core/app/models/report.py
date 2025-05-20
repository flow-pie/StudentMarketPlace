from datetime import datetime
from enum import Enum
from app.extensions import db

class ReportStatus(Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # e.g., 'item', 'message'
    content_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship("User", backref="reports")
