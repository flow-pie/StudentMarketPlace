from datetime import datetime, timezone
from ..extensions import db


class ItemImage(db.Model):
    __tablename__ = 'item_images'  # Explicit table name (plural)

    image_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id', ondelete='CASCADE'), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    order = db.Column(db.Integer, default=0)  # For sorting images

    # Relationship
    item = db.relationship('Item', backref=db.backref('images', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('idx_item_image_order', 'item_id', 'order'),  # For ordered display
        db.UniqueConstraint('item_id', 'is_primary', name='uq_item_primary_image'),  # Only one primary per item
    )