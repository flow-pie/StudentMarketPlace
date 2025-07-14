"""
Monitoring and health check middleware.
"""
import logging
import time
import psutil
import os
from flask import jsonify, current_app, g
from sqlalchemy import text
from ..extensions import db

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health check utilities for monitoring."""

    @staticmethod
    def check_database():
        """Check database connectivity."""
        try:
            start_time = time.perf_counter()
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            response_time = time.perf_counter() - start_time
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': "An internal error has occurred!",
                'response_time_ms': -1
            }

    @staticmethod
    def check_system_resources():
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available // (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free // (1024 * 1024 * 1024)
            }
        except Exception as e:
            logger.error(f"System resource check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': "An internal error has occurred!"}

    @staticmethod
    def get_application_metrics():
        """Get application-specific metrics."""
        try:
            # Get basic app info
            metrics = {
                'app_name': current_app.config.get('APP_NAME', 'StudentMarketplace'),
                'version': current_app.config.get('VERSION', '1.0.0'),
                'environment': current_app.config.get('FLASK_ENV', 'production'),
                'uptime_seconds': time.time() - current_app.config.get('START_TIME', time.time()),
                'request_metrics': RequestMetrics.get_global_stats()
            }

            # Add cache stats if available
            if hasattr(current_app, 'cache_manager'):
                metrics['cache_stats'] = current_app.cache_manager.get_stats()

            return metrics
        except Exception as e:
            logger.error(f"Application metrics check failed: {str(e)}")
            return {'error': "An internal error has occurred!"}


class RequestMetrics:
    """Track request metrics."""

    _instance = None

    def __init__(self):
        self.request_count = 0
        self.response_times = []
        self.error_count = 0
        self.status_codes = {}

    @classmethod
    def get_global_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = RequestMetrics()
        return cls._instance

    @classmethod
    def get_global_stats(cls):
        """Get global request statistics."""
        return cls.get_global_instance().get_stats()

    def record_request(self, response_time, status_code):
        """Record request metrics."""
        self.request_count += 1
        self.response_times.append(response_time)

        # Track status code distribution
        status_category = f"{status_code // 100}xx"
        self.status_codes[status_category] = self.status_codes.get(status_category, 0) + 1

        if status_code >= 400:
            self.error_count += 1

        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    def get_stats(self):
        """Get request statistics."""
        if not self.response_times:
            return {
                'request_count': self.request_count,
                'error_count': self.error_count,
                'status_codes': self.status_codes,
                'error_rate': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0
            }

        avg_response_time = sum(self.response_times) / len(self.response_times)
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0

        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'status_codes': self.status_codes,
            'error_rate': round(error_rate, 2),
            'avg_response_time': round(avg_response_time, 3),
            'min_response_time': round(min(self.response_times), 3),
            'max_response_time': round(max(self.response_times), 3),
            'p95_response_time': round(
                sorted(self.response_times)[int(len(self.response_times) * 0.95)],
                3
            )
        }


def init_monitoring(app):
    """Initialize monitoring middleware."""
    # Record start time
    app.config['START_TIME'] = time.time()

    # Initialize request metrics
    RequestMetrics.get_global_instance()

    @app.before_request
    def before_request():
        """Record request start time."""
        g.start_time = time.perf_counter()

    @app.after_request
    def after_request(response):
        """Record request metrics."""
        if hasattr(g, 'start_time'):
            response_time = time.perf_counter() - g.start_time
            RequestMetrics.get_global_instance().record_request(
                response_time,
                response.status_code
            )

        # Add monitoring headers
        response.headers['X-Response-Time'] = f"{response_time:.4f}s"
        response.headers['X-Request-Count'] = RequestMetrics.get_global_instance().request_count
        return response