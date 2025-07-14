from flask import jsonify, current_app
from flask_smorest import Blueprint
from http import HTTPStatus
import time
import logging
import psutil
from ...extensions import db
from ...middleware.monitoring import HealthChecker

logger = logging.getLogger(__name__)

# Create health blueprint
health_bp = Blueprint(
    'System Health',
    'health',
    url_prefix='/api/health',
    description='Health views endpoints'
)


@health_bp.route('/health', methods=['GET'])
@health_bp.doc(
    description="Comprehensive health check of application components",
    tags=["System Health"]
)
@health_bp.response(200, description="System is healthy")
@health_bp.response(503, description="System is unhealthy")
def health_check():
    """
    Check overall system health including database and resources

    Returns:
    - status: Overall health status
    - checks: Detailed component statuses
    """
    try:
        db_health = HealthChecker.check_database()
        system_health = HealthChecker.check_system_resources()

        overall_status = 'healthy'
        if db_health['status'] != 'healthy' or system_health['status'] != 'healthy':
            overall_status = 'unhealthy'

        response = {
            'status': overall_status,
            'timestamp': time.time(),
            'checks': {
                'database': db_health,
                'system': system_health
            }
        }

        status_code = HTTPStatus.OK if overall_status == 'healthy' else HTTPStatus.SERVICE_UNAVAILABLE
        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': "An internal error has occurred!",
            'timestamp': time.time()
        }), HTTPStatus.SERVICE_UNAVAILABLE


@health_bp.route('/ready', methods=['GET'])
@health_bp.doc(
    description="Readiness check for service discovery",
    tags=["System Health"]
)
@health_bp.response(200, description="Service is ready")
@health_bp.response(503, description="Service is not ready")
def readiness_check():
    """
    Kubernetes-ready endpoint for service readiness

    Returns:
    - status: Current readiness status
    """
    try:
        db_health = HealthChecker.check_database()
        if db_health['status'] == 'healthy':
            return jsonify({
                'status': 'ready',
                'timestamp': time.time()
            }), HTTPStatus.OK
        else:
            return jsonify({
                'status': 'not_ready',
                'reason': 'database_unavailable',
                'timestamp': time.time()
            }), HTTPStatus.SERVICE_UNAVAILABLE

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not_ready',
            'error': "An internal error has occurred!",
            'timestamp': time.time()
        }), HTTPStatus.SERVICE_UNAVAILABLE


@health_bp.route('/live', methods=['GET'])
@health_bp.doc(
    description="Liveness check for process views",
    tags=["System Health"]
)
@health_bp.response(200, description="Service is alive")
def liveness_check():
    """
    Kubernetes liveness probe endpoint

    Returns:
    - status: Always returns 'alive' if reachable
    """
    return jsonify({
        'status': 'alive',
        'timestamp': time.time()
    }), HTTPStatus.OK


@health_bp.route('/metrics', methods=['GET'])
@health_bp.doc(
    description="Application performance metrics",
    tags=["System Health"]
)
@health_bp.response(200, description="Metrics data")
@health_bp.response(500, description="Metrics collection error")
def metrics_endpoint():
    """
    Get detailed application performance metrics

    Returns:
    - application: App-specific metrics
    - system: Resource utilization metrics
    """
    try:
        metrics = HealthChecker.get_application_metrics()
        system_health = HealthChecker.check_system_resources()

        response = {
            'application': metrics,
            'system': system_health,
            'timestamp': time.time()
        }

        return jsonify(response), HTTPStatus.OK

    except Exception as e:
        logger.error(f"Metrics endpoint failed: {str(e)}")
        return jsonify({
            'error': "An internal error has occurred!",
            'timestamp': time.time()
        }), HTTPStatus.INTERNAL_SERVER_ERROR
