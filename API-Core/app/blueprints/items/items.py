from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from ...schemas.item import ItemCreateSchema
from ...services.item import ItemService


items_bp = Blueprint('items', __name__)
schema = ItemCreateSchema()


@items_bp.route('/', methods=['POST'])
@jwt_required()
def create_item():
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        item = ItemService.create_item(
            user_id=current_user.id,
            item_data=request.json
        )
        return jsonify({
            "item_id": item.item_id,
            "title": item.title,
            "status": item.status.value,
            "message": "Listing created successfully"
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400