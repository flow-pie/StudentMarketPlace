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
        db.Index('idx_item_image_order', 'item_id', 'order'),
        db.UniqueConstraint(
            'item_id',
            name='uq_item_primary_image',
            is_primary='is_primary IS TRUE' )
        )

    @staticmethod
    def get_next_order(item_id):
        last_image = ItemImage.query.filter_by(item_id=item_id) \
            .order_by(ItemImage.order.desc()).first()
        return (last_image.order + 1) if last_image else 1

    def set_as_primary(self):
        # Clear existing primary
        ItemImage.query.filter_by(item_id=self.item_id, is_primary=True) \
            .update({'is_primary': False})
        self.is_primary = True

    def to_dict(self):
        return {
            "image_id": self.image_id,
            "url": self.image_url,
            "is_primary": self.is_primary,
            "order": self.order,
            "created_at": self.created_at.isoformat()
        }