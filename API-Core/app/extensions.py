# app/extensions.py

import os
import logging
from datetime import timedelta
from flask import jsonify, request
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# ——— Set up shared extensions ———
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()

# Configure a dedicated logger for JWT events
jwt_logger = logging.getLogger('jwt')
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
jwt_logger.addHandler(handler)
jwt_logger.setLevel(logging.DEBUG)


def init_app(app):
    """Initialize database, migrations and CORS extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


def init_jwt(app):
    """Configure JWT, register all identity loaders and error handlers."""
    # ——— Core JWT settings ———
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_DECODE_LEEWAY'] = 10

    # ——— Optional security tweaks ———
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_CSRF_CHECK_FORM'] = False

    #Exceptions bubble up for detailed logging ———
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'detail'

    # Initialize the JWTManager
    jwt.init_app(app)
    jwt_logger.debug(f"JWT Secret Key: {'set' if app.config['JWT_SECRET_KEY'] else 'missing'}")

    from .models import User  # avoid circular import

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """
        Get the identity used in the 'sub' claim.
        Parameters:
          - user: a User model instance
        Returns:
          - user.user_id (int)
        """
        try:
            return str(user.user_id)
        except AttributeError as e:
            jwt_logger.error(f"user_identity_lookup failed: {e}")
            return None

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """
        Load a User from the database using the 'sub' claim.
        """
        user_id = jwt_data.get('sub')
        if not user_id:
            jwt_logger.error("Missing 'sub' claim in JWT")
            return None

        jwt_logger.debug(f"Looking up user ID: {user_id}")
        user = User.query.get(user_id)
        if not user:
            jwt_logger.error(f"User not found: ID {user_id}")
            return None
        if user.account_status != 'Active':
            jwt_logger.warning(f"Inactive account: ID {user_id}")
            return None

        return user

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        """Handle malformed or tampered tokens."""
        jwt_logger.error(f"Invalid token: {reason} | Raw: {request.headers.get('Authorization','')}")
        return jsonify({
            "detail": "Token validation failed",
            "category": "authentication",
            "code": "token_invalid"
        }), 422

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        """Handle requests with no token present."""
        jwt_logger.warning(f"Authorization missing: {reason}")
        return jsonify({
            "detail": "Authorization required",
            "category": "authentication",
            "code": "authorization_missing"
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired tokens."""
        jwt_logger.info(f"Expired token used: {jwt_payload}")
        return jsonify({
            "detail": "Token has expired",
            "category": "authentication",
            "code": "token_expired"
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked tokens."""
        jwt_logger.warning(f"Revoked token attempt: {jwt_payload}")
        return jsonify({
            "detail": "Token has been revoked",
            "category": "authentication",
            "code": "token_revoked"
        }), 401
