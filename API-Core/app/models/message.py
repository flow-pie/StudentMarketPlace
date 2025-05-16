from datetime import datetime, timezone
from ..extensions import db


class Message(db.Model):
    __tablename__ = 'messages'

    message_id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey('conversations.conversation_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),  # Timezone-aware timestamp
        nullable=False
    )
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime)  # Track when message was read

    # Relationships with backrefs
    conversation = db.relationship(
        'Conversation',
        backref=db.backref('messages', lazy='dynamic', cascade='all, delete-orphan')
    )
    sender = db.relationship(
        'User',
        foreign_keys=[sender_id],
        backref=db.backref('sent_messages', lazy='dynamic')
    )
    receiver = db.relationship(
        'User',
        foreign_keys=[receiver_id],
        backref=db.backref('received_messages', lazy='dynamic')
    )

    __table_args__ = (
        db.Index('idx_message_conversation_time', 'conversation_id', 'sent_at'),  # Optimize message history queries
    )

    def mark_as_read(self):
        """Helper method to mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc)