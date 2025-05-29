# API-Core/app/extensions.py
import os
import logging
from datetime import timedelta
from flask import jsonify, request
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError as MarshmallowValidationError
from .errors import ValidationError, APIError

# ——— Set up shared extensions ———
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
ma = Marshmallow()


def handle_ma_validation_error(e):
    """Convert marshmallow validation errors to our APIError format"""
    error_messages = []
    for field, errors in e.messages.items():
        if isinstance(errors, list):
            error_messages.append(f"{field}: {', '.join(errors)}")
        elif isinstance(errors, dict):
            for subfield, suberrors in errors.items():
                error_messages.append(f"{field}.{subfield}: {', '.join(suberrors)}")

    raise ValidationError(
        message="Validation failed: " + "; ".join(error_messages),
        code="VALIDATION_ERROR"
    )


# Configure Marshmallow to use our error handler
ma.SQLAlchemyAutoSchema.OPTIONS_CLASS.include_relationships = True
ma.SQLAlchemyAutoSchema.OPTIONS_CLASS.include_fk = True
ma.handle_error = handle_ma_validation_error


def init_app(app):
    """Initialize database, migrations and CORS extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


def init_jwt(app):
    """Configure JWT with standardized error responses and logging."""
    # ——— Core JWT settings ———
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_DECODE_LEEWAY'] = 10

    # ——— Optional security tweaks ———
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_CSRF_CHECK_FORM'] = False

    # Exceptions bubble up for detailed logging
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'

    # Initialize the JWTManager
    jwt.init_app(app)
    app.logger.debug(f"JWT Secret Key: {'set' if app.config['JWT_SECRET_KEY'] else 'missing'}")

    from .models import User  # avoid circular import

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Get the identity used in the 'sub' claim."""
        try:
            return str(user.user_id)
        except AttributeError as e:
            app.logger.error(f"user_identity_lookup failed: {e}")
            raise APIError(
                message="User identity lookup failed",
                code="AUTHENTICATION_ERROR",
                status_code=401
            )

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Load a User from the database using the 'sub' claim."""
        user_id = jwt_data.get('sub')
        if not user_id:
            app.logger.error("Missing 'sub' claim in JWT")
            raise APIError(
                message="Invalid token claims",
                code="TOKEN_INVALID",
                status_code=422
            )

        app.logger.debug(f"Looking up user ID: {user_id}")
        user = User.query.get(user_id)
        if not user:
            app.logger.error(f"User not found: ID {user_id}")
            raise APIError(
                message="User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        if user.account_status != 'Active':
            app.logger.warning(f"Inactive account: ID {user_id}")
            raise APIError(
                message="Account is not active",
                code="ACCOUNT_INACTIVE",
                status_code=403
            )

        return user

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        """Handle malformed or tampered tokens."""
        app.logger.error(f"Invalid token: {reason} | Raw: {request.headers.get('Authorization', '')}")
        raise APIError(
            message="Token validation failed",
            code="TOKEN_INVALID",
            status_code=422
        )

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        """Handle requests with no token present."""
        app.logger.warning(f"Authorization missing: {reason}")
        raise APIError(
            message="Authorization required",
            code="AUTHORIZATION_MISSING",
            status_code=401
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired tokens."""
        app.logger.info(f"Expired token used: {jwt_payload}")
        raise APIError(
            message="Token has expired",
            code="TOKEN_EXPIRED",
            status_code=401
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked tokens."""
        app.logger.warning(f"Revoked token attempt: {jwt_payload}")
        raise APIError(
            message="Token has been revoked",
            code="TOKEN_REVOKED",
            status_code=401
        )
