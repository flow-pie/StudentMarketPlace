#!/usr/bin/env python
"""Main application entry point with robust logging configuration"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

from colorama import Fore, Style, init
from sqlalchemy.exc import OperationalError
import pymysql
from app import create_app
from app.extensions import db
from app.config import Config

# Initialize colorama for colored console output
init(autoreset=True)


def configure_logging():
    """Configure comprehensive logging system with file rotation"""
    # Create logs directory relative to this file's location
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / 'app_errors.log'

    # Clear any existing log handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation (5MB per file, keep 3 backups)
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure Flask's logger
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.handlers.clear()
    flask_logger.addHandler(file_handler)
    flask_logger.addHandler(console_handler)

    return str(log_file.absolute())


# Configure logging before anything else
log_file_path = configure_logging()
logger = logging.getLogger(__name__)
logger.info(f"Logging system initialized. Log file: {log_file_path}")

app = create_app()


def color_print(level, message):
    """Print colored messages to console based on level"""
    colors = {
        'error': Fore.RED,
        'warning': Fore.YELLOW,
        'success': Fore.GREEN,
        'info': Fore.CYAN
    }
    symbols = {
        'error': '[!]',
        'warning': '[~]',
        'success': '[✓]',
        'info': '[i]'
    }
    print(f"{colors[level]}{symbols[level]} {message}{Style.RESET_ALL}",
          file=sys.stderr if level == 'error' else sys.stdout)


def initialize_database():
    """Initialize database with comprehensive error handling"""
    try:
        with app.app_context():
            logger.info(f"Database connection: {app.config['SQLALCHEMY_DATABASE_URI']}")

            if Config.ENV == 'development':
                logger.info("Running in development mode")
                # db.drop_all()  # Uncomment if needed
                # db.create_all()

            db.metadata.create_all(bind=db.engine, checkfirst=True)
            color_print('success', "Database tables verified/created")
            return True

    except OperationalError as e:
        if isinstance(e.orig, pymysql.err.OperationalError):
            if e.orig.args[0] == 2003:  # Connection refused
                error_msg = "MySQL connection refused"
                color_print('error', error_msg)
                logger.error(error_msg, exc_info=True)
                color_print('warning', "Troubleshooting:")
                color_print('warning', "1. Is MySQL service running?")
                color_print('warning', "2. Check connection details in .env file")
                color_print('warning',
                            f"3. Verify host is reachable: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1].split('/')[0]}")
            elif e.orig.args[0] == 1045:  # Access denied
                error_msg = "Invalid MySQL credentials"
                color_print('error', error_msg)
                logger.error(error_msg)
        else:
            error_msg = f"Database error: {str(e)}"
            color_print('error', error_msg)
            logger.error(error_msg, exc_info=True)
        return False

    except Exception as e:
        error_msg = f"Unexpected database error: {str(e)}"
        color_print('error', error_msg)
        logger.exception(error_msg)
        return False


if __name__ == '__main__':
    logger.info(f"Starting application (ENV={Config.ENV})")
    logger.info(f"Host: {app.config.get('HOST', '0.0.0.0')}")
    logger.info(f"Port: {app.config.get('PORT', 5000)}")

    if initialize_database():
        try:
            color_print('success', "Application starting...")
            app.run(
                debug=Config.ENV == 'development',
                host=app.config.get('HOST', '0.0.0.0'),
                port=app.config.get('PORT', 5000)
            )
        except Exception as e:
            logger.critical(f"Application crash: {str(e)}", exc_info=True)
            color_print('error', f"Application failed: {str(e)}")
            sys.exit(1)
    else:
        logger.critical("Application aborted due to database issues")
        color_print('error', "Cannot start due to database problems")
        sys.exit(1)
