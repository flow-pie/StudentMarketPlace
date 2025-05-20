from dotenv import load_dotenv
from flask import Flask, jsonify
import os
from datetime import timedelta
import logging
from werkzeug.exceptions import HTTPException

from .blueprints.admin.stats import admin_stat_bp
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """Application factory with enhanced configuration and error handling"""
    # Initialize Flask app
    app = Flask(__name__)

    #initialize configuration file
    app.config.from_object(Config)
    Config.init_app(app)

    # Load environment variables
    load_dotenv()

    # Configure application
    configure_app(app, config)

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Configure error handlers
    register_error_handlers(app)

    return app


def configure_app(app, config=None):
    """Configure application settings"""
    # Default configuration
    app.config.update({
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_ERROR_MESSAGE_KEY': 'message',
        'PROPAGATE_EXCEPTIONS': True,
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
    })

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYSQL_URL', os.getenv('SQLITE_URL'))

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    if not app.config['JWT_SECRET_KEY']:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment variables")

    # Override with passed config
    if config:
        app.config.update(config)

    logger.info("Application configuration loaded successfully")


def initialize_extensions(app):
    """Initialize Flask extensions with proper error handling"""
    from .extensions import db, jwt, cors, migrate

    try:
        # Initialize database
        db.init_app(app)

        # Configure CORS
        cors.init_app(
            app,
            resources={r"/api/*": {"origins": "*"}},
            supports_credentials=True
        )

        # Initialize migrations
        migrate.init_app(app, db)

        # Initialize JWT
        jwt.init_app(app)
        configure_jwt_callbacks(jwt)

        logger.info("Extensions initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize extensions: {str(e)}")
        raise


def configure_jwt_callbacks(jwt):
    """Configure JWT callbacks with enhanced error handling"""
    from .models import User

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        try:
            identity = jwt_data["sub"]
            user = User.query.get(identity)
            if not user:
                logger.warning(f"User not found for JWT identity: {identity}")
            return user
        except Exception as e:
            logger.error(f"User lookup failed: {str(e)}")
            return None

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning(f"Expired token attempt: {jwt_payload}")
        return jsonify({
            'message': 'Token has expired',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        logger.error(f"Invalid token: {reason}")
        return jsonify({
            'message': 'Token validation failed',
            'error': 'token_invalid',
            'reason': str(reason)
        }), 422

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        logger.warning(f"Unauthorized request: {error}")
        return jsonify({
            'message': 'Missing or invalid authorization',
            'error': 'authorization_required'
        }), 401


def register_blueprints(app):
    """Register application blueprints with proper URL prefixes"""
    from .blueprints.auth.routes import auth_bp
    from .blueprints.items.routes import items_crud_bp
    from .blueprints.routes import items_bp
    from .blueprints.item_images.images import  images_crud_bp
    from .blueprints.admin.listing import admin_listings_bp
    from .blueprints.admin.view import report_bp
    from .blueprints import images_crud_bp, msg_bp
    from .blueprints.admin.users import admin_bp

    blueprints = [
        (auth_bp, '/api/auth'),
        (items_bp, '/api/admin'),
        (items_crud_bp, '/api/items'),
        (images_crud_bp, '/api/item'),
        (msg_bp, '/api/messages'),
        (admin_bp, '/api/admin'),
        (admin_listings_bp, '/api/admin'),
        (report_bp, '/api/admin'),
        (admin_stat_bp, '/api/admin')
    ]

    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)

    logger.info(f"Registered {len(blueprints)} blueprints")


def register_error_handlers(app):
    """Register global error handlers"""

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        logger.error(f"HTTP Error {e.code}: {e.description}")
        return jsonify({
            'message': e.description,
            'error': e.name.lower().replace(' ', '_')
        }), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'message': 'An unexpected error occurred',
            'error': 'server_error'
        }), 500

    logger.info("Error handlers registered")


def create_cli_app():
    """Create application instance for CLI commands"""
    app = create_app()
    return app