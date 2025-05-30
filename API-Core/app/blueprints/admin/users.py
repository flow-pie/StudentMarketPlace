from flask import request
from http import HTTPStatus
from flask_smorest import Blueprint


from sqlalchemy.exc import SQLAlchemyError

from ...errors import APIError
from ...decorators.auth import admin_required
from ...extensions import db
from ...models import User
import logging

from ...schemas.auth import UserBanSchema

logger = logging.getLogger(__name__)

admin_bp = Blueprint('User Management', __name__)

@admin_bp.route('/users', methods=['GET'])
@admin_required
@admin_bp.doc(security=[{"BearerAuth": []}])
@admin_bp.response(200, schema=None)

def list_users():
    """Returns a list of all users. """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)

        # Only fetch paginated items
        users = [user.to_admin_dict() for user in pagination.items]

        return {
            'users': users,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        }, HTTPStatus.OK

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving users: {str(e)}", exc_info=True)
        raise APIError(
            message="Database error while retrieving users",
            code="DB_ERROR_USER_RETRIEVAL",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving users: {str(e)}", exc_info=True)
        raise APIError(
            message="Unexpected failure retrieving users",
            code="USER_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@admin_bp.route('/users/<int:user_id>/ban', methods=['PATCH'])
@admin_required
@admin_bp.doc(security=[{"BearerAuth": []}])
@admin_bp.arguments(UserBanSchema)
@admin_bp.response(200, schema=None)
def toggle_ban(data, user_id):
    """Toggles whether a user is banned.

    Parameters:
    - user_id: int → the user’s unique ID in the database.
    - data: dict → {'banned': bool, 'reason': str (if banning)}
    """
    try:
        user = db.session.get(User, user_id)
        if not user:
            raise APIError("User not found", code="USER_NOT_FOUND", status_code=HTTPStatus.NOT_FOUND)

        if data['banned']:
            if not data.get('reason'):
                raise APIError("Ban reason required", code="MISSING_REASON", status_code=HTTPStatus.BAD_REQUEST)
            user.ban_user(reason=data['reason'])
        else:
            user.unban_user()

        db.session.commit()
        return user.to_admin_dict(), HTTPStatus.OK

    except ValueError as e:
        db.session.rollback()
        raise APIError(str(e), code="INVALID_OPERATION", status_code=HTTPStatus.BAD_REQUEST)
    except SQLAlchemyError as e:
        db.session.rollback()
        raise APIError("Database error", code="DB_ERROR", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        db.session.rollback()
        raise APIError("Unexpected error", code="USER_UPDATE_FAILED", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
