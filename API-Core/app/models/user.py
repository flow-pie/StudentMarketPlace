from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.ext.hybrid import hybrid_property

from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class UserInstitution(Enum):
    POLYTECHNIC = 'Polytechnic'
    UNIVERSITY = 'University'
    COLLEGE = 'College'
    OTHER = 'Other'


class AccountStatus(Enum):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    BANNED = 'Banned'
    SUSPENDED = 'Suspended'
    UNVERIFIED = 'Unverified'  #for email verification


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    institution = db.Column(db.Enum(UserInstitution))
    student_id = db.Column(db.String(20), unique=True)
    profile_picture = db.Column(db.String(255))
    account_status = db.Column(db.Enum(AccountStatus), default=AccountStatus.UNVERIFIED, nullable=False)
    registered_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_number = db.Column(db.String(20))

    # Relationships
    items = db.relationship('Item', back_populates='seller')
    transactions_as_buyer = db.relationship('Transaction', foreign_keys='Transaction.buyer_id', back_populates='buyer',
                                            lazy='dynamic')
    transactions_as_seller = db.relationship('Transaction', foreign_keys='Transaction.seller_id', back_populates='seller',
                                             lazy='dynamic')

    __table_args__ = (
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_status', 'account_status'),
    )

    #takes keyword arguments
    def __init__(self, **kwargs):
        password = kwargs.pop('password', None)  # remove 'password' if exists
        super(User, self).__init__(**kwargs)
        if password:
            self.set_password(password)

    @hybrid_property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    #hash plain password
    def set_password(self, password):
        """Create hashed password."""
        self.password_hash = generate_password_hash(password)

    #return true if password match eg during login
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)

    #combine first name and last name
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    #marks account status active if user verifies email
    def activate_account(self):
        self.account_status = AccountStatus.ACTIVE
        self.email_verified = True