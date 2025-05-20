from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.decorators.auth import admin_required
from app.extensions import db
from app.models import User, Item, ItemStatus, ItemCondition

admin_listings_bp = Blueprint('admin_listing', __name__)

@admin_listings_bp.route('/listings', methods=['GET'])
@admin_required
def get_all_listing():
    items = Item.query.all()
    return jsonify([i.to_dict() for i in items]), 200

@admin_listings_bp.route('/listings/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_listing(item_id):
    item = Item.query.get_or_404(item_id, description='Item not found')
    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': f'Listing {item_id} deleted'}), 200

@admin_listings_bp.route('/listings/<int:item_id>', methods=['PATCH'])
@admin_required
def update_listing(item_id):
    data = request.get_json() or {}
    item = Item.query.get_or_404(item_id, description='Item not found')

    if 'status' in data:
        try:
            item.status = ItemStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status value'}), 404
    if 'condition' in data:
        try:
            item.condition = ItemCondition(data['condition'])
        except ValueError:
            return jsonify({'error': 'Invalid condition value'}), 404
    if 'description' in data:
        item.description = data['description']

    db.session.commit()
    return jsonify(item.to_dict()), 200
