from http import HTTPStatus

from dotenv import load_dotenv
from flask import Flask, jsonify
import os
from datetime import timedelta
import logging
from werkzeug.exceptions import HTTPException, NotFound
from .config import Config
from .errors import APIError, configure_logging, register_error_handlers, ValidationError
from .extensions import db, api
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

    # Swagger Config
    app.config['API_TITLE'] = 'Student Marketplace API documentation with endpoints '
    app.config['API_DESCRIPTION'] = 'Marketplace API documentation with endpoints for items, users, auth, etc.'
    app.config['API_VERSION'] = 'v1'
    app.config['OPENAPI_VERSION'] = '3.0.3'
    app.config['OPENAPI_URL_PREFIX'] = '/'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = '/'
    app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

    api.init_app(app)
    api.spec.components.security_scheme(
        "BearerAuth",
        {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
    )

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
        'SUPABASE_CONN')

    # Optimized connection pooling settings for Supabase
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 1,  # Max connections per worker
        'max_overflow': 0,  # No additional connections beyond pool_size
        'pool_timeout': 10,  # Wait time for connection (seconds)
        'pool_recycle': 300,  # Recycle connections every 5 minutes (300s)
        'pool_pre_ping': True,  # Check connection health before use
        'pool_use_lifo': True  # Use Last-In-First-Out queue for better connection reuse
    }

    # JWT Configuration
    app.config.update({
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'JWT_ERROR_MESSAGE_KEY': 'message',
        'PROPAGATE_EXCEPTIONS': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'ENV': os.getenv('FLASK_ENV', 'production'),
        'SQLALCHEMY_ENGINE_OPTIONS': app.config['SQLALCHEMY_ENGINE_OPTIONS']  #useful for supabase
    })

    if not app.config['JWT_SECRET_KEY']:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment variables")

    # Apply any additional config
    if config:
        app.config.update(config)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
        if hasattr(db, 'engine') and db.engine:
            db.engine.dispose()


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
        return jsonify({
            "message": "Token has expired",
            "code": "TOKEN_EXPIRED",
            "status_code": HTTPStatus.UNAUTHORIZED.value
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify(
            {"message": "Invalid token", "code": "TOKEN_INVALID", "status_code": HTTPStatus.UNAUTHORIZED}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify(
            {"message": "Authorization required", "code": "UNAUTHORIZED", "status_code": HTTPStatus.UNAUTHORIZED}), 401

    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token = db.session.query(TokenBlockList).filter_by(jti=jti).first()
        if token:
            return jsonify({"message": "Token revoked", "code": "TOKEN_REVOKED", "status_code": 401})
        return False


def register_blueprints(app):
    """Register blueprints with conflict checking"""
    from .blueprints.auth.routes import auth_bp
    from .blueprints.items.routes import items_crud_bp
    # from .blueprints.routes import items_bp
    from .blueprints.item_images.images import images_crud_bp
    from .blueprints.admin.listing import admin_listings_bp
    from .blueprints.admin.view import report_bp
    from .blueprints.messages.routes import msg_bp
    from .blueprints.admin.users import admin_bp
    from .blueprints.admin.stats import admin_stat_bp

    blueprints = [
        (auth_bp, '/api/auth'),
        # (items_bp, '/api/admin'),
        (items_crud_bp, '/api/items'),
        (images_crud_bp, '/api/items'),
        (msg_bp, '/api/messages'),
        (admin_bp, '/api/admin'),
        (admin_listings_bp, '/api/admin'),
        (report_bp, '/api/admin'),
        (admin_stat_bp, '/api/admin')
    ]

    for blueprint, url_prefix in blueprints:
        try:
            api.register_blueprint(blueprint, url_prefix=url_prefix)
        except ValueError as e:
            logging.getLogger(__name__).error(
                f"Blueprint registration failed: {str(e)}"
            )
            raise

    logging.getLogger(__name__).info(f"Registered {len(blueprints)} blueprints")

    @app.errorhandler(Exception)
    def handle_all_errors(e):
        # Convert exceptions to JSON
        if isinstance(e, APIError):
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response

        if isinstance(e, HTTPException):
            response = jsonify({
                "error": e.name.replace(" ", "_").upper(),
                "message": e.description,
                "status": e.code
            })
            response.status_code = e.code
            return response

        # Fallback for unexpected errors
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({
            "error": "SERVER_ERROR",
            "message": "Internal server error",
            "status": 500
        }), 500

    @app.errorhandler(APIError)
    def handle_api_error(error):
        app.logger.error(f"API Error [{error.code}]: {error.message} : {str(error)}")
        response = jsonify({
            'error': error.code,
            'message': error.message,
            'status': error.status_code
        })
        response.status_code = error.status_code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle Werkzeug HTTP exceptions"""
        app.logger.error(f"HTTP Error {e.code}: {e.description}")
        return jsonify({
            'error': e.code,
            'message': e.description,
            'code': e.name.replace(' ', '_').upper()
        }), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.critical("Unexpected error", exc_info=True)

        # Check if it's a validation error first
        if isinstance(err, ValidationError):
            return jsonify({
                "error": "Validation Error",
                "messages": err.messages
            }), 400

        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }), 500
