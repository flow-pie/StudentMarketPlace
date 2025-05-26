from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_jwt_extended import  current_user, jwt_required
from sqlalchemy.exc import SQLAlchemyError, DatabaseError

from ... import logger
from ...errors import APIError, ValidationError
from ...extensions import db
from ...models import Item, User, ItemCategory
from ...schemas.item import ItemCreateSchema, ItemSchema, ItemFilterSchema, PaginatedItemSchema
from ...models import Item
from ...schemas.item import ItemCreateSchema, ItemSchema, ItemUpdateSchema
from ...services.item import ItemService

items_crud_bp = Blueprint('items_crud', __name__, url_prefix='/api/items')
schema = ItemCreateSchema()


@items_crud_bp.route('', methods=['POST'])
@jwt_required()
def create_item():
    errors = schema.validate(request.json)
    if errors:
        raise APIError(
            message="Validation failed: " + "; ".join(
                f"{field}: {', '.join(messages)}"
                for field, messages in errors.items()
            ),
            code = "VALIDATION_ERROR",
            status_code = HTTPStatus.BAD_REQUEST.value
        )
    try:
        item = ItemService.create_item(
            user_id=current_user.user_id,
            item_data=request.json
        )
        return jsonify({
            "success": True,
            "data": {
                "item_id": item.item_id,
                "title": item.title,
                "status": item.status.value
            },
            "message": "Listing created successfully"
        }), HTTPStatus.CREATED.value

    except ValueError as e:
         raise APIError(
             message= "Invalid input data provided",
             code = "INVALID_INPUT",
             status_code = HTTPStatus.BAD_REQUEST.value
         )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise APIError(
            message= "Database operation failed",
            code = "DATABASE_ERROR",
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


#get all items
@items_crud_bp.route('', methods=['GET'])
def get_all_item():
    try:
        items =  Item.query.order_by(Item.created_at.desc()).all()
        return ItemSchema(many=True).dump(items), HTTPStatus.OK.value
    except DatabaseError:
        raise APIError(
            message="Failed to retrieve items",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )
#get an item by id
@items_crud_bp.route('/<int:item_id>', methods=['GET'])
def get_item_by_id(item_id):
    item = Item.query.get(item_id)

    if not item:
        app.logger.error(f"Item not found - ID: {item_id}")
        raise APIError(
            message="Item not found",
            code="ITEM_NOT_FOUND",
            status_code=404
        )

    try:
        return jsonify(ItemSchema().dump(item)), HTTPStatus.OK.value
    except DatabaseError :
        raise APIError(
            message="Database operation failed",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@items_crud_bp.route('/params', methods=['GET'])
def get_items():
    try:
        filters = ItemFilterSchema().load(request.args)
        result = ItemService.get_filtered_items(filters)

        return PaginatedItemSchema().dump({
            'items': result.items,
            'total': result.total,
            'page': result.page,
            'per_page': result.per_page
        })

    except ValidationError as ve:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "details": ve.messages
        }), 400

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "Could not retrieve items"
        }), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "error": "SERVER_ERROR",
            "message": "An unexpected error occurred"
        }), 500

@items_crud_bp.route('paginated', methods=['GET'])
def get_page_items():
    try:
        # Parse query params
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')

        # Get paginated results
        result = ItemService.get_paginated_items(
            page=page,
            per_page=per_page,
            category=category
        )

        return PaginatedItemSchema().dump(result), 200

    except KeyError:  # Invalid category
        raise APIError(
            message="Invalid category",
            code="INVALID_CATEGORY",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except Exception:
        raise APIError(
            message="Failed to retrieve items",
            code="SERVER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@items_crud_bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    try:
        ItemService.delete_item(item_id)
        return jsonify({"success": True, "message": f"Item {item_id} deleted successfully."}), HTTPStatus.NO_CONTENT
    except ValueError as e:
        raise APIError(
            message="Item not found",
            code="ITEM_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND.value
        )
    except Exception as e:
        raise APIError(
            message="Failed to delete item",
            code="SERVER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )

@items_crud_bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    errors = ItemUpdateSchema().validate(request.json)
    if errors:
        raise APIError(
            message="Validation failed: " + "; ".join(
                f"{field}: {', '.join(messages)}"
                for field, messages in errors.items()
            ),
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST.value
        )

    try:
        item = ItemService.update_item(
            item_data={
                "item_id": item_id,
                "user_id": current_user.user_id,
                **request.json
            }
        )
        return {
            "success": True,
            "data": ItemSchema().dump(item),
            "message": "Listing updated successfully"
        }, HTTPStatus.OK.value
    except PermissionError as e:
        raise APIError(
            message=str(e),
            code="PERMISSION_DENIED",
            status_code=HTTPStatus.FORBIDDEN.value
        )
    except ValueError as e:
        raise APIError(
            message=str(e),
            code="INVALID_INPUT",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Database operation failed",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )