from datetime import datetime, timezone
from ..extensions import db


class Conversation(db.Model):
    __tablename__ = 'conversations'

    conversation_id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='conversations_initiated')
    item = db.relationship('Item', backref='conversations')

    # participants through a secondary relationship if needed
    participants = db.relationship(
        'User',
        secondary='conversation_participants',
        backref='conversations_participated'
    )

    __table_args__ = (
        db.Index('idx_conversation_item_sender', 'item_id', 'sender_id'),
    )