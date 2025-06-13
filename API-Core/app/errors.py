import logging
from http import HTTPStatus
from pathlib import Path
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException, UnprocessableEntity
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
        super().__init__(message, code, HTTPStatus.BAD_REQUEST.value)


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
    """
    Centralized logging configuration WITHOUT double‐attaching the same handler.
    We create file + console handlers and attach them ONLY to app.logger and werkzeug,
    but we do NOT call logging.basicConfig(...), so the root logger stays clean.
    """
    log_dir = Path(app.root_path) / "logs"
    log_dir.mkdir(exist_ok=True)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # RotatingFileHandler
    log_file = log_dir / "app_errors.log"
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    #Clear any existing handlers from app.logger (to avoid leaks when code reloads)
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

    # 7) Do the same for werkzeug’s logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(console_handler)
    werkzeug_logger.setLevel(logging.INFO)

    return log_file



def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Return JSON for any raised APIError."""
        response = jsonify({
            "error": error.code,
            "message": error.message,
            "status": error.status_code
        })
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Return JSON for any raised ValidationError."""
        response = jsonify({
            "error": error.code,
            "message": error.message,
            "status": error.status_code
        })
        response.status_code = error.status_code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """
        Return JSON for any Werkzeug HTTPException.
        If e.data['messages'] exists (Webargs validation), return those details.
        Otherwise return e.description.
        """
        current_app.logger.error(f"HTTP Error {e.code}: {e.description}")

        if isinstance(e, UnprocessableEntity) and hasattr(e, "data"):
            messages = e.data.get("messages")
            if messages:
                return (
                    jsonify({
                        "error": "VALIDATION_ERROR",
                        "message": messages,
                        "status": e.code
                    }),
                    e.code
                )

        return (
            jsonify({
                "error": e.name.replace(" ", "_").upper(),
                "message": e.description,
                "status": e.code
            }),
            e.code
        )

    @app.errorhandler(ValueError)
    def handle_enum_value_error(err):
        text = str(err)
        if "is not a valid" in text and "ItemCategory" in text:
            return jsonify({
                "error": "VALIDATION_ERROR",
                "message": {"category": [text]},
                "status": 422
            }), 422

        raise err

    @app.errorhandler(AttributeError)
    def handle_attribute_error(e):
        # Check if it's the specific marshmallow_enum error
        if "'super' object has no attribute 'fail'" in str(e):
            return jsonify({
                "success": False,
                "message": "Invalid enum value provided",
                "code": "INVALID_ENUM_VALUE",
                "details": "Please check the category and condition values"
            }), 400
        raise e

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        """
        Handle:
          - marshmallow_enum AttributeError that mentions " is not a valid "
          - any other uncaught exception
        """
        msg = str(err)
        if isinstance(err, AttributeError) and " is not a valid " in msg:
            current_app.logger.error(f"Enum validation failed: {msg}", exc_info=True)
            return (
                jsonify({
                    "error": "VALIDATION_ERROR",
                    "message": msg,
                    "status": HTTPStatus.BAD_REQUEST.value
                }),
                HTTPStatus.BAD_REQUEST.value
            )

        current_app.logger.exception("Unhandled exception occurred")
        return (
            jsonify({
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "status": HTTPStatus.INTERNAL_SERVER_ERROR.value
            }),
            HTTPStatus.INTERNAL_SERVER_ERROR.value
        )
