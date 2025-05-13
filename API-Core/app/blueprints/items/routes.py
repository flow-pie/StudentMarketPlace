from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from ...extensions import db
from ...models import Item
from ...schemas.item import ItemCreateSchema, ItemSchema
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
            user_id=current_user.id,
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
