from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify
from http import HTTPStatus

from ..errors import APIError


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as err:
            raise APIError(
                message="Invalid or expired token",
                code="AUTH_REQUIRED",
                status_code=HTTPStatus.UNAUTHORIZED
            )
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin', False):
                raise APIError(
                    message="Admin privileges required",
                    code="ADMIN_REQUIRED",
                    status_code=HTTPStatus.FORBIDDEN
                )
            return fn(*args, **kwargs)
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                message="Invalid or expired token",
                code="ADMIN_AUTH_REQUIRED",
                status_code=HTTPStatus.UNAUTHORIZED
            )
    return wrapper