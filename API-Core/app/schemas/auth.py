from flask_bcrypt import generate_password_hash
from marshmallow import Schema, fields, validate, validates, ValidationError, validates_schema
from sqlalchemy.testing.pickleable import User
import bleach
import re
from datetime import datetime

# ---- Security Constants ----
PASSWORD_MIN_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # 5 minutes in seconds


class SecureAuthSchema(Schema):
    """Base schema with common security validations"""

    def on_bind_field(self, field_name, field_obj):
        if isinstance(field_obj, fields.Str):
            field_obj.validate.extend([
                self._sanitize_html,
                self._validate_safe_chars
            ])

    @staticmethod
    def _sanitize_html(value):
        """Strip all HTML/JavaScript tags"""
        if value and bleach.clean(value) != value:
            raise ValidationError("Contains disallowed HTML/JavaScript")
        return value

    @staticmethod
    def _validate_safe_chars(value):
        """Prevent injection attempts"""
        if value and not re.match(r'^[\w\s\-@.+!?#$%&*+=^`|~()\/]+$', value):
            raise ValidationError("Contains potentially dangerous characters")
        return value


class RegistrationSchema(SecureAuthSchema):
    first_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50),
            validate.Regexp(r'^[a-zA-Z\s\-]+$', error="Only letters, spaces and hyphens allowed")
        ]
    )
    last_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50),
            validate.Regexp(r'^[a-zA-Z\s\-]+$', error="Only letters, spaces and hyphens allowed")
        ]
    )
    email = fields.Email(
        required=True,
        validate=[
            validate.Email(),
            validate.Length(max=254),
            validate.Regexp(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        ]
    )
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=PASSWORD_MIN_LENGTH),
            validate.Regexp(r'(?=.*\d)', error="Must contain at least one digit"),
            validate.Regexp(r'(?=.*[a-z])', error="Must contain at least one lowercase letter"),
            validate.Regexp(r'(?=.*[A-Z])', error="Must contain at least one uppercase letter"),
            validate.Regexp(r'(?=.*[!@#$%^&*])', error="Must contain at least one special character"),
            validate.Regexp(r'^[\w!@#$%^&*]+$', error="Contains invalid characters")
        ],
        load_only=True
    )
    confirm_password = fields.String(
        required=True,
        load_only=True
    )
    institution = fields.Str(
        validate=validate.Length(max=100)
    )
    student_id = fields.Str(
        validate=[
            validate.Length(max=20),
            validate.Regexp(r'^[a-zA-Z0-9\-]+$')
        ]
    )

    @validates('email')
    def validate_email(self, email):
        """Check for existing email with case-insensitive comparison"""
        if User.query.filter(User.email.ilike(email)).first():
            raise ValidationError('Email already registered')

    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError("Passwords do not match", "confirm_password")

    def load(self, data, **kwargs):
        """Automatically hash password on load"""
        result = super().load(data, **kwargs)
        if 'password' in result:
            result['password_hash'] = generate_password_hash(result.pop('password'))
            result.pop('confirm_password', None)
        return result


class LoginSchema(SecureAuthSchema):
    email = fields.Email(
        required=True,
        validate=[
            validate.Email(),
            validate.Length(max=254)
        ]
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        load_only=True
    )

    @validates_schema
    def check_account_lockout(self, data, **kwargs):
        """Prevent brute force attacks"""
        user = User.query.filter_by(email=data.get('email')).first()

        if user and user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            time_since_last_attempt = (datetime.utcnow() - user.last_failed_login).total_seconds()
            if time_since_last_attempt < LOCKOUT_TIME:
                remaining_time = int(LOCKOUT_TIME - time_since_last_attempt)
                raise ValidationError(
                    f"Account temporarily locked. Try again in {remaining_time} seconds",
                    "email"
                )
