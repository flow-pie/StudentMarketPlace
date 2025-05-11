from datetime import datetime, timezone
from ..extensions import db


class Favourite(db.Model):
    __tablename__ = 'favourites'  # Explicit table name (plural)

    favourite_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = db.relationship('Users', backref='favourites')
    item = db.relationship('Items', backref='favorited_by')

    # Composite unique constraint to prevent duplicate favorites
    __table_args__ = (
        db.UniqueConstraint('user_id', 'item_id', name='_user_item_uc'),
    )