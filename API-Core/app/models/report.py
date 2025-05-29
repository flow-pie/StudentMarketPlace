from datetime import datetime
from enum import Enum
from ..extensions import db

class ReportStatus(Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)

    reporter_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    content_type = db.Column(db.String(255))
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.message_id"), nullable=True)

    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship("User", backref="reports")
    item = db.relationship("Item", backref="reports")
    message = db.relationship("Message", backref="reports")
