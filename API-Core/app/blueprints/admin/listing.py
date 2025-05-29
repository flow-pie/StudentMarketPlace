from flask import Blueprint, request
from http import HTTPStatus

from markupsafe import escape
from sqlalchemy.exc import SQLAlchemyError

from ...errors import APIError
from ...decorators.auth import admin_required
from ...extensions import db
from ...models import Item, ItemStatus, ItemCondition

admin_listings_bp = Blueprint('admin_listing', __name__)


@admin_listings_bp.route('/listings', methods=['GET'])
@admin_required
def get_all_listing():
    try:
        items = Item.query.all()
        return [item.to_dict() for item in items], HTTPStatus.OK.value
    except Exception as e:
        raise APIError(
            message="Failed to retrieve listings",
            code="LISTINGS_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@admin_listings_bp.route('/listings/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_listing(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            raise APIError(
                message="Item not found",
                code="ITEM_NOT_FOUND",
                status_code=HTTPStatus.NOT_FOUND.value
            )

        db.session.delete(item)
        db.session.commit()

        return {
            "message": f"Listing {escape(str(item_id))} deleted successfully"
        }, HTTPStatus.OK.value

    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Failed to delete listing",
            code="LISTING_DELETION_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@admin_listings_bp.route('/listings/<int:item_id>', methods=['PATCH'])
@admin_required
def update_listing(item_id):
    try:
        data = request.get_json() or {}
        item = Item.query.get(item_id)

        if not item:
            raise APIError(
                message="Item not found",
                code="ITEM_NOT_FOUND",
                status_code=HTTPStatus.NOT_FOUND.value
            )

        if 'status' in data:
            try:
                item.status = ItemStatus(data['status'])
            except ValueError:
                raise APIError(
                    message="Invalid status value",
                    code="INVALID_STATUS",
                    status_code=HTTPStatus.BAD_REQUEST.value
                )

        if 'condition' in data:
            try:
                item.condition = ItemCondition(data['condition'])
            except ValueError:
                raise APIError(
                    message="Invalid condition value",
                    code="INVALID_CONDITION",
                    status_code=HTTPStatus.BAD_REQUEST.value
                )

        if 'description' in data:
            item.description = data['description']

        db.session.commit()
        return item.to_dict(), HTTPStatus.OK.value

    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Failed to update listing",
            code="LISTING_UPDATE_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )