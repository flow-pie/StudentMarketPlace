from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_jwt_extended import  current_user, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from ...extensions import db
from ...models import Item
from ...schemas.item import ItemCreateSchema, ItemSchema
from ...schemas.message import MessageCreateSchema
from ...services.item import ItemService
from ...services.message import MessageService

msg_bp = Blueprint('msg_crud', __name__)
message_schema = MessageCreateSchema()


@msg_bp.route('', methods=['POST'])
@jwt_required()
def send_message():
    errors = message_schema.validate(request.json)
    if errors:
        return jsonify({"error": errors}), 400

    try:
        message = MessageService.create_message(
            sender_id=current_user.user_id,
            message_data=request.json
        )

        return jsonify({
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "timestamp": message.sent_at.isoformat()
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500