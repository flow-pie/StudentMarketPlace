from dotenv import load_dotenv
from flask import Flask, jsonify
import os
from datetime import timedelta
import logging
from werkzeug.exceptions import HTTPException

from .config import Config
from .errors import APIError, configure_logging, register_error_handlers
from .extensions import db
from .models.user import TokenBlockList

# Configure logging before app creation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config=None):
    """Application factory with enhanced configuration and error handling"""
    app = Flask(__name__)

    # Load environment variables FIRST
    load_dotenv()

    # Configure application settings
    configure_app(app, config)

    # Configure logging FIRST before any other operations
    configure_logging(app)
    logger = logging.getLogger(__name__)
    logger.info("Initializing application...")

    # Initialize extensions
    initialize_extensions(app)

    # Register error handlers (before blueprints)
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    # Configure teardown context
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    logger.info("Application initialized successfully")
    return app


def configure_app(app, config=None):
    """Centralized configuration management"""
    # Load from Config class
    app.config.from_object(Config)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'MYSQL_URL',
        os.getenv('SQLITE_URL', 'sqlite:///default.db')
    )

    # JWT Configuration
    app.config.update({
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'JWT_ERROR_MESSAGE_KEY': 'message',
        'PROPAGATE_EXCEPTIONS': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'ENV': os.getenv('FLASK_ENV', 'development'),
    })

    if not app.config['JWT_SECRET_KEY']:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment variables")

    # Apply any additional config
    if config:
        app.config.update(config)


def initialize_extensions(app):
    """Initialize Flask extensions with proper error handling"""
    from .extensions import db, jwt, cors, migrate

    try:
        # CRITICAL: Note the order
        db.init_app(app)
        migrate.init_app(app, db)
        cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

        jwt.init_app(app)
        configure_jwt_callbacks(jwt)

    except Exception as e:
        logging.getLogger(__name__).critical(
            f"Extension initialization failed: {str(e)}",
            exc_info=True
        )
        raise


def configure_jwt_callbacks(jwt):
    """Standardized JWT error handling"""
    from .models import User

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        try:
            identity = jwt_data["sub"]
            if user := User.query.get(identity):
                return user
            raise APIError("User not found", "USER_NOT_FOUND", 404)
        except Exception as e:
            raise APIError("Authentication failed", "AUTH_FAILURE", 401)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        raise APIError("Token expired", "TOKEN_EXPIRED", 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        raise APIError(f"Invalid token: {reason}", "TOKEN_INVALID", 422)

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        raise APIError("Authorization required", "UNAUTHORIZED", 401)

    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token = db.session.query(TokenBlockList).filter_by(jti=jti).first()
        if token:
            raise APIError("Token revoked", "TOKEN_REVOKED", 401)
        return False


def register_blueprints(app):
    """Register blueprints with conflict checking"""
    from .blueprints import (
        auth_bp, items_bp, items_crud_bp,
        images_crud_bp, msg_bp, admin_bp,
        admin_listings_bp, report_bp, admin_stat_bp
    )

    blueprints = [
        (auth_bp, '/api/auth'),
        (items_bp, '/api/items'),
        (items_crud_bp, '/api/items'),
        (images_crud_bp, '/api/images'),
        (msg_bp, '/api/messages'),
        (admin_bp, '/api/admin/users'),
        (admin_listings_bp, '/api/admin/listings'),
        (report_bp, '/api/admin/reports'),
        (admin_stat_bp, '/api/admin/stats')
    ]

    for blueprint, url_prefix in blueprints:
        try:
            app.register_blueprint(blueprint, url_prefix=url_prefix)
        except ValueError as e:
            logging.getLogger(__name__).error(
                f"Blueprint registration failed: {str(e)}"
            )
            raise

    logging.getLogger(__name__).info(f"Registered {len(blueprints)} blueprints")


def register_error_handlers(app):
    """Consolidated error handling"""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        app.logger.error(f"API Error [{error.code}]: {error.message}")
        response = jsonify({
            'error': error.code,
            'message': error.message,
            'status': error.status_code
        })
        response.status_code = error.status_code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        raise APIError(e.description, e.name.replace(' ', '_').upper(), e.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        logger.critical("Unexpected error", exc_info=True)
        raise APIError("Internal server error", "SERVER_ERROR", 500)