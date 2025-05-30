# Routes related to items
from flask import jsonify
from flask_smorest import Blueprint
from flask_jwt_extended import current_user
from ..decorators.auth import jwt_required, admin_required

items_bp = Blueprint('testing routes', __name__)


# protected
@items_bp.route('/me', methods=['GET'])
@jwt_required
def protected_items():
    return jsonify(message=f"Hello {current_user.email}!"), 200


@items_bp.route('/items', methods=['GET'])
@admin_required
def admin_only():
    return jsonify(message="Top secret admins data")


@items_bp.route('/public', methods=['GET'])
def public_route():
    return jsonify({"message": "Public access allowed"}), 200
