from flask import Blueprint, request
from http import HTTPStatus

from sqlalchemy.exc import SQLAlchemyError

from ...errors import APIError
from ...decorators.auth import admin_required
from ...extensions import db
from ...models import User
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
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
def toggle_ban(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            raise APIError(
                message="User not found",
                code="USER_NOT_FOUND",
                status_code=HTTPStatus.NOT_FOUND.value
            )

        data = request.get_json()
        if not data or 'banned' not in data:
            raise APIError(
                message="Missing 'banned' status in request",
                code="MISSING_STATUS",
                status_code=HTTPStatus.BAD_REQUEST.value
            )

        if data.get('banned'):
            if not data.get('reason'):
                raise APIError(
                    message="Ban reason is required",
                    code="MISSING_REASON",
                    status_code=HTTPStatus.BAD_REQUEST.value
                )
            user.ban_user(reason=data.get('reason'))
        else:
            user.unban_user()

        db.session.commit()
        return user.to_admin_dict(), HTTPStatus.OK.value

    except ValueError as e:
        db.session.rollback()
        raise APIError(
            message=str(e),
            code="INVALID_OPERATION",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except Exception as e:
        db.session.rollback()
        raise APIError(
            message="Failed to update user status",
            code="USER_UPDATE_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )