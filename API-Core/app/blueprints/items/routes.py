from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_jwt_extended import  current_user, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from ...extensions import db
from ...models import Item, User, ItemCategory
from ...schemas.item import ItemCreateSchema, ItemSchema, ItemFilterSchema, PaginatedItemSchema
from ...services.item import ItemService

items_crud_bp = Blueprint('items_crud', __name__, url_prefix='/api/items')
schema = ItemCreateSchema()


@items_crud_bp.route('', methods=['POST'])
@jwt_required()
def create_item():
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"success": False, "errors": errors}), HTTPStatus.BAD_REQUEST.value

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
        return jsonify({"success": False, "error": str(e)}), HTTPStatus.BAD_REQUEST.value
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "Database operation failed"}), HTTPStatus.INTERNAL_SERVER_ERROR.value


#get all items
@items_crud_bp.route('', methods=['GET'])
def get_all_item():
    items =  Item.query.order_by(Item.created_at.desc()).all()
    return jsonify(ItemSchema(many=True).dump(items)), HTTPStatus.OK.value

#get an item by id
@items_crud_bp.route('/<int:item_id>', methods=['GET'])
def get_item_by_id(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(ItemSchema().dump(item)), HTTPStatus.OK.value



@items_crud_bp.route('/params', methods=['GET'])
def get_items():
    try:
        filters = ItemFilterSchema().load(request.args)
        result = ItemService.get_filtered_items(filters)

        return jsonify({
            'items': [item.to_dict() for item in result.items],
            'total': result.total,
            'page': result.page,
            'per_page': result.per_page
        })

    except ValueError as e:
        return jsonify({
            "error": "invalid_filter",
            "message": str(e)
        }), HTTPStatus.BAD_REQUEST.value
    except Exception as e:
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred"
        }), HTTPStatus.INTERNAL_SERVER_ERROR.value


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
        return jsonify({"error": "Invalid category"}), 400