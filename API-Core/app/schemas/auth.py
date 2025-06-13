from http import HTTPStatus

from flask_bcrypt import generate_password_hash
from marshmallow import (
    Schema, fields, validate, validates, ValidationError,
    validates_schema, pre_load, EXCLUDE
)
import bleach
import re
from datetime import datetime

from .. import db, APIError
from ..models import User
from ..models.user import UserInstitution

# --- Security Constants ---
PASSWORD_MIN_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # seconds (5 minutes)


class SecureAuthSchema(Schema):
    """
    Base schema with input sanitization.
    """

    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields
        ordered = True

    @pre_load
    def sanitize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                if "<" in value or ">" in value:
                    raise ValidationError(f"{key} contains invalid characters")
        return data

    @staticmethod
    def _sanitize_html(value):
        """Reject HTML/JS tags."""
        if value and bleach.clean(value) != value:
            raise ValidationError("Contains disallowed HTML/JavaScript")
        return value

    @staticmethod
    def _validate_safe_chars(value):
        """Allow only safe characters."""
        if value and not re.match(r'^[\w\s\-@.+!?#$%&*+=^`|~()\/]+$', value):
            raise ValidationError("Contains potentially dangerous characters")
        return value


class RegistrationSchema(SecureAuthSchema):
    first_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50),
            validate.Regexp(r'^[a-zA-Z\s\-]+$', error="Only letters, spaces and hyphens allowed")
        ],
        data_key="firstName"  # Map to JSON's firstName
    )
    last_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50),
            validate.Regexp(r'^[a-zA-Z\s\-]+$', error="Only letters, spaces and hyphens allowed")
        ],
        data_key="lastName"
    )
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, error="Must be at least 8 characters"),
            validate.Regexp(r'(?=.*\d)', error="Must contain a digit"),
            validate.Regexp(r'(?=.*[a-z])', error="Must contain lowercase"),
            validate.Regexp(r'(?=.*[A-Z])', error="Must contain uppercase"),
            validate.Regexp(r'(?=.*[\W_])', error="Must contain a special character (!@#$%^&* etc.)")
        ],
        load_only=True
    )
    institution = fields.Str(
        required=False,
        validate=[
            validate.Length(max=100),
            validate.OneOf([e.value for e in UserInstitution], error="Invalid institution")
        ],
        data_key="institution"
    )
    student_id = fields.Str(
        required=False,
        validate=[
            validate.Length(max=20),
            validate.Regexp(r'^[a-zA-Z0-9\-]+$')
        ],
        data_key="studentId"
    )

class LoginSchema(SecureAuthSchema):
    """
    Schema for user login.
    """

    email = fields.Email(
        required=True,
        validate=validate.Length(max=254)
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=1)
    )

    @validates_schema
    def check_account_lockout(self, data, **kwargs):
        user = User.query.filter_by(email=data['email']).first()
        if user:
            if user.last_failed_login:
                elapsed = (datetime.utcnow() - user.last_failed_login).total_seconds()
                if elapsed >= LOCKOUT_TIME:
                    user.failed_login_attempts = 0
                    user.last_failed_login = None
                    db.session.commit()

            attempts = user.failed_login_attempts or 0
            if attempts >= MAX_LOGIN_ATTEMPTS:
                if user.last_failed_login:
                    elapsed = (datetime.utcnow() - user.last_failed_login).total_seconds()
                    if elapsed < LOCKOUT_TIME:
                        remaining = int(LOCKOUT_TIME - elapsed)
                        raise APIError(
                            message=f"Account locked. Try again in {remaining} seconds",
                            code="ACCOUNT_LOCKED",
                            status_code=HTTPStatus.TOO_MANY_REQUESTS
                        )


class TokenSchema(Schema):
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)


class UserResponseSchema(Schema):
    id = fields.Integer(attribute="user_id", required=True)
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    institution = fields.Str(required=True)
    student_id = fields.Str(required=True)


class LoginResponseSchema(Schema):
    message = fields.Str(required=True)
    tokens = fields.Nested(TokenSchema, required=True)
    user = fields.Nested(UserResponseSchema, required=True)


class MessageSchema(Schema):
    message = fields.String()


class UserBanSchema(Schema):
    banned = fields.Boolean(required=True)
    reason = fields.Str()