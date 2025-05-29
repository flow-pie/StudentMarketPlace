from datetime import datetime, UTC
from enum import Enum
from ..extensions import db


class ItemCategory(str, Enum):
    ELECTRONICS = "ELECTRONICS"
    BOOKS = "BOOKS"
    CLOTHING = "CLOTHING"
    FURNITURE = "FURNITURE"
    OTHER = "OTHER"

class ItemCondition(str, Enum):
    NEW = "New"
    LIKE_NEW = "Like New"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class ItemStatus(str, Enum):
    AVAILABLE = "Available"
    PENDING = "Pending"
    SOLD = "Sold"


class Item(db.Model):
    __tablename__ = 'items'

    item_id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.Enum(ItemCategory))
    condition = db.Column(db.Enum(ItemCondition))
    status = db.Column(db.Enum(ItemStatus), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))

    seller = db.relationship('User', back_populates='items')

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "price": float(self.price),
            "category": self.category.name if self.category else None,
            "condition": self.condition.value if self.condition else None,
            "status": self.status.value,
            "school": self.seller.institution.value if self.seller and self.seller.institution else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }