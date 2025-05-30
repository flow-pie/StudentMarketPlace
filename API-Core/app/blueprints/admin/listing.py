from flask import request
from flask_smorest import Blueprint
from http import HTTPStatus

from markupsafe import escape
from sqlalchemy.exc import SQLAlchemyError

from ...errors import APIError
from ...decorators.auth import admin_required
from ...extensions import db
from ...models import Item, ItemStatus, ItemCondition
from ...schemas.item import ItemSchema, ItemUpdateSchema

admin_listings_bp = Blueprint(
    'admin listings',
    __name__,
    description="Admin: manage all item listings, including viewing, updating, and deleting"
)

@admin_listings_bp.route('/listings', methods=['GET'])
@admin_required
@admin_listings_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Get all listings",
    description="Retrieve a list of all item listings in the system. Admin access required."
)
@admin_listings_bp.response(200, ItemSchema(many=True), description="List of all items")
@admin_listings_bp.response(500, description="Internal server error while retrieving listings")
def get_all_listing():
    """
    Get all listings.

    Returns:
        200 OK: List of all item objects.
        500 Internal Server Error: If retrieval fails.
    """
    try:
        items = Item.query.all()
        return [item.to_dict() for item in items], HTTPStatus.OK.value
    except Exception:
        raise APIError(
            message="Failed to retrieve listings",
            code="LISTINGS_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@admin_listings_bp.route('/listings/<int:item_id>', methods=['DELETE'])
@admin_required
@admin_listings_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Delete a specific listing",
    description="Delete an item listing by its unique ID. Admin access required.",
    params={
        "item_id": {
            "description": "Unique ID of the item to delete",
            "in": "path",
            "type": "integer",
            "required": True
        }
    }
)
@admin_listings_bp.response(200, description="Deletion confirmation")
@admin_listings_bp.response(404, description="Item not found")
@admin_listings_bp.response(500, description="Internal server error during deletion")
def delete_listing(item_id):
    """
    Delete a listing.

    Parameters:
        item_id (int): ID of the item to delete.

    Returns:
        200 OK: Confirmation message.
        404 Not Found: If item does not exist.
        500 Internal Server Error: If deletion fails.
    """
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
@admin_listings_bp.doc(
    summary="Update a specific listing",
    description="Update details of an item listing (status, condition, description, price). **JSON body required.**",
    security=[{"BearerAuth": []}]
)
@admin_listings_bp.arguments(ItemUpdateSchema, location="json")
@admin_listings_bp.response(200, ItemSchema)
def update_listing(data, item_id):
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

        if 'price' in data:
            item.price = data['price']

        db.session.commit()
        return item, HTTPStatus.OK.value

    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Failed to update listing",
            code="LISTING_UPDATE_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )