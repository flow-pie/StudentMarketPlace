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

from app import create_app, configure_logging
from app.extensions import db
from app.config import Config

# colored console output
init(autoreset=True)

logger = logging.getLogger(__name__)

app = create_app()
log_file_path = configure_logging(app)
logger.info(f"Logging system initialized. Log file {log_file_path}")


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
            logger.info(
                color_print("success",
                            f"Database connection: successfully connected to {'PostgreSQL' if 'postgres' in app.config['SQLALCHEMY_DATABASE_URI'] else 'MySQL'}"
                            ))
            if Config.ENV == 'development':
                logger.info("Running in development mode")
                # db.drop_all()  # Uncomment if  you want to drop all
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