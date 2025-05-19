from flask import request

from flask import Blueprint, jsonify

from ...decorators.auth import admin_required
from ...extensions import db
from ...models import User

admin_bp = Blueprint('admin', __name__)
@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.all()
    return jsonify([user.to_admin_dict() for user in users]), 200

@admin_bp.route('/users/<int:user_id>/ban', methods=['PATCH'])
@admin_required
def toogle_ban(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if data.get('banned'):
        user.ban_user(reason=data.get('reason'))
    else:
        user.unban_user()

    db.session.commit()
    return jsonify(user.to_admin_dict()), 200