import logging
from pathlib import Path
from flask import jsonify
from werkzeug.exceptions import HTTPException
from logging.handlers import RotatingFileHandler


class APIError(Exception):
    """Base API Error Class"""

    def __init__(self, message, code, status_code=500):
        super().__init__()
        self.message = message
        self.code = code
        self.status_code = status_code


class ValidationError(APIError):
    """Validation Error (400-level)"""

    def __init__(self, message, code="VALIDATION_ERROR"):
        super().__init__(message, code, 400)


class RedactingFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""

    def filter(self, record):
        sensitive_keys = ['password', 'token', 'authorization', 'secret']
        msg = str(record.msg)
        for key in sensitive_keys:
            if key.lower() in msg.lower():
                record.msg = msg.replace(key, '***')
        return True


def configure_logging(app):
    """Centralized logging configuration"""
    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()

    # Create logs directory if it doesn't exist
    log_dir = Path(app.root_path) / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Set up log file path
    log_file = log_dir / 'app_errors.log'

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure file handler
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RedactingFilter())

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RedactingFilter())

    # Apply to root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

    # Configure Flask's app logger
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

    # Configure werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(console_handler)


def register_error_handlers(app):
    """Register error handlers for the application"""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Convert APIError instances to proper JSON responses"""
        app.logger.error(f"API Error [{error.code}]: {error.message}")
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
    def handle_unexpected_error(e):
        """Handle all unexpected exceptions"""
        app.logger.exception("Unhandled exception occurred")
        return jsonify({
            'error': 'SERVER_ERROR',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_SERVER_ERROR'
        }), 500