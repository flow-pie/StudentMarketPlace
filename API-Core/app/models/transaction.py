import enum
from datetime import datetime, timezone
from decimal import Decimal
from ..extensions import db


class Status(enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"
    FAILED = "Failed"


class PaymentMethod(enum.Enum):
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    MPESA = "Mpesa"
    PAYPAL = "PayPal"
    BANK_TRANSFER = "Bank Transfer"
    CRYPTO = "Cryptocurrency"


class Transaction(db.Model):
    __tablename__ = 'transactions'

    transaction_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey('items.item_id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    seller_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    status = db.Column(
        db.Enum(Status),
        default=Status.PENDING,
        nullable=False,
        index=True
    )
    payment_method = db.Column(
        db.Enum(PaymentMethod),
        nullable=False
    )
    payment_reference = db.Column(db.String(100))  # For payment processor reference
    completed_at = db.Column(db.DateTime)  # When transaction was completed
    notes = db.Column(db.Text)  # For any additional transaction notes

    # Relationships
    item = db.relationship('Item', backref='transactions')
    buyer = db.relationship(
        'User',
        foreign_keys=[buyer_id],
        backref='purchases'
    )
    seller = db.relationship(
        'User',
        foreign_keys=[seller_id],
        backref='sales'
    )

    __table_args__ = (
        db.Index('idx_transaction_buyer_status', 'buyer_id', 'status'),
        db.Index('idx_transaction_seller_status', 'seller_id', 'status'),
        db.CheckConstraint('amount > 0', name='check_positive_amount'),
    )

    def complete(self):
        """Mark transaction as completed"""
        if self.status == Status.PENDING:
            self.status = Status.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
            return True
        return False

    def cancel(self, reason=None):
        """Cancel the transaction"""
        if self.status == Status.PENDING:
            self.status = Status.CANCELLED
            if reason:
                self.notes = f"Cancelled: {reason}"
            return True
        return False