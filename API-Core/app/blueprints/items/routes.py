from http import HTTPStatus
from flask import jsonify, request, current_app
from flask_smorest import Blueprint
from flask_jwt_extended import  current_user, jwt_required
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from ...errors import APIError, ValidationError
from ...extensions import db
from ...models import Item, User, ItemCategory
from ...schemas.item import ItemCreateSchema, ItemSchema, ItemFilterSchema, PaginatedItemSchema, ItemQuerySchema, \
    ItemPaginationSchema
from ...models import Item
from ...schemas.item import ItemCreateSchema, ItemSchema, ItemUpdateSchema
from ...services.item import ItemService
import logging

logger = logging.getLogger(__name__)

items_crud_bp = Blueprint('Items', 'items', url_prefix='/api/items', description='Operations on items')
schema = ItemCreateSchema()


@items_crud_bp.route('', methods=['POST'])
@items_crud_bp.doc(
    description="Create a new item. Requires authentication.",
    tags=["Items"],
    security=[{"BearerAuth": []}]
)
@items_crud_bp.arguments(ItemCreateSchema)
@items_crud_bp.response(201, ItemSchema)
@jwt_required()
def create_item(data):
    """
    Create a new item.

    Request body:
    - title (str)
    - description (str)
    - category (str, optional)

    Returns:
    - item_id (int)
    - title (str)
    - description (str)
    - category (str)
    - created_at (datetime)
    """
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        current_app.logger.error(f"Validation failed: {err.messages}")
        return jsonify({"errors": err.messages}), 400
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

    except ValueError as err:
         raise APIError(
             message= "Invalid input data provided",
             code = "INVALID_INPUT",
             status_code = HTTPStatus.BAD_REQUEST.value
         )
    except SQLAlchemyError as err:
        db.session.rollback()
        raise APIError(
            message= "Database operation failed",
            code = "DATABASE_ERROR",
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        )
    except Exception as err:
        logger.error(f"Unexpected error: {str(err)}")
        return jsonify({
            "error": "SERVER_ERROR",
            "message": "An unexpected error occurred"
        }), 500


#get all items
@items_crud_bp.route('', methods=['GET'])
@items_crud_bp.doc(
    description="Get all items without filters (paginated).",
    tags=["Items"]
)
@items_crud_bp.response(200, ItemSchema(many=True))
def get_all_items():
    """
    Retrieve all items, paginated.

    Query Parameters:
    - page: int, page number (default 1)
    - per_page: int, items per page (default 20)

    Returns:
    - List of item objects.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        pagination = Item.query.order_by(Item.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        items = pagination.items
        return ItemSchema(many=True).dump(items), HTTPStatus.OK.value
    except DatabaseError:
        return {
            "success": False,
            "error": "DATABASE_ERROR",
            "message": "Failed to retrieve items"
        }, HTTPStatus.INTERNAL_SERVER_ERROR.value
    except Exception as e:
        return {
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": str(e)
        }, HTTPStatus.INTERNAL_SERVER_ERROR.value

#get an item by id
@items_crud_bp.route('/<int:item_id>', methods=['GET'])
@items_crud_bp.doc(
    description="Get an item by its ID.",
    tags=["Items"],
    security=[{"BearerAuth": []}]
)
@items_crud_bp.response(200, ItemSchema)
def get_item_by_id(item_id):
    """
    Get item details.

    Path params:
    - item_id (int): ID of the item.

    Returns:
    - Item object.
    """
    item = Item.query.get(item_id)

    if not item:
        logger.error(f"Item not found - ID: {item_id}")
        raise APIError(
            message="Item not found",
            code="ITEM_NOT_FOUND",
            status_code=404
        )

    try:
        return item, HTTPStatus.OK.value
    except DatabaseError :
        raise APIError(
            message="Database operation failed",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@items_crud_bp.route('/params', methods=['GET'])
@items_crud_bp.doc(
    description="Get items filtered by query params: category, school, min_price, max_price, keyword, condition, status, page, per_page, sort_by, sort_order.",
    tags=["Items"]
)
@items_crud_bp.arguments(ItemQuerySchema, location='query')  # Ensure schema has all fields!
@items_crud_bp.response(200, PaginatedItemSchema)
def get_filtered_items(args):
    """
    Retrieve items with advanced filters.

    Query params (validated by ItemQuerySchema):
    - category (str)
    - school (str)
    - min_price (float)
    - max_price (float)
    - keyword (str)
    - condition (str)
    - status (str)
    - sort_by (str: 'price', 'created_at')
    - sort_order (str: 'asc', 'desc')
    - page (int)
    - per_page (int)

    Returns:
    {
      items: [...],
      total: <int>,
      page: <int>,
      per_page: <int>
    }
    """
    try:
        # Pass all validated args directly as filters
        filters = args

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
        logger.exception("Database error")
        return jsonify({
            "error": "DATABASE_ERROR",
            "message": "Could not retrieve items"
        }), 500

    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({
            "error": "SERVER_ERROR",
            "message": "An unexpected error occurred"
        }), 500


@items_crud_bp.route('/paginated', methods=['GET'])
@items_crud_bp.doc(
    description="Get paginated items with optional category filter.",
    tags=["Items"],
)
@items_crud_bp.arguments(ItemPaginationSchema, location='query')
@items_crud_bp.response(200, PaginatedItemSchema)
def get_paginated_items(args):
    """
    Retrieve paginated items.

    Query params:
    - category (str, optional)
    - page (int, optional)
    - per_page (int, optional)

    Returns:
    - Paginated list of items.
    """
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
@items_crud_bp.doc(
    description="Delete an item by its ID. Requires authentication.",
    tags=["Items"],
    security=[{"BearerAuth": []}]
)
@items_crud_bp.response(204)
@jwt_required()
def delete_item(item_id):
    """
    Delete an item.

    Path params:
    - item_id (int): ID of the item.

    Returns:
    - No content (204).
    """
    try:
        item = Item.query.get(item_id)
        if item.seller_id != current_user.user_id:
            raise APIError("Unauthorized", "PERMISSION_DENIED", HTTPStatus.FORBIDDEN.value)

        ItemService.delete_item(item_id)
        return jsonify({"success": True, "message": f"Item {item_id} deleted successfully."}), HTTPStatus.NO_CONTENT
    except ValueError as err:
        raise APIError(
            message="Item not found",
            code="ITEM_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND.value
        )
    except Exception as err:
        if item.seller_id != current_user.user_id:
            raise APIError("Unauthorized", "PERMISSION_DENIED", HTTPStatus.FORBIDDEN.value)

        raise APIError(
            message="Failed to delete item",
            code="SERVER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )

@items_crud_bp.route('/<int:item_id>', methods=['PUT'])
@items_crud_bp.doc(
    description="Update an existing item. Requires authentication.",
    tags=["Items"],
    security=[{"BearerAuth": []}]
)
@items_crud_bp.arguments(ItemUpdateSchema)
@items_crud_bp.response(200, None)
@jwt_required()
def update_item(data, item_id):
    """
    Update an item.

    Path params:
    - item_id (int): ID of the item.

    Request body:
    - title (str, optional)
    - description (str, optional)
    - category (str, optional)
    - status (str, optional)

    Returns:
    - Updated item object.
    """
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