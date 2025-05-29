from http import HTTPStatus
from flask import Blueprint, jsonify, request
from flask_jwt_extended import  current_user, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from ...errors import APIError
from ...extensions import db
from ...models import Item
from ...schemas.item import ItemCreateSchema, ItemSchema
from ...schemas.message import MessageCreateSchema, MessageSchema
from ...services.item import ItemService
from ...services.message import MessageService

msg_bp = Blueprint('msg_crud', __name__)
message_schema = MessageCreateSchema()
message_output_schema = MessageSchema(many=True)


@msg_bp.route('', methods=['POST'])
@jwt_required()
def send_message():
    try:
        errors = message_schema.validate(request.json)
        if errors:
            error_messages = [f"{field}: {', '.join(messages)}"
                              for field, messages in errors.items()]
            raise APIError(
                message="Validation errors: " + "; ".join(error_messages),
                code="VALIDATION_ERROR",
                status_code=HTTPStatus.BAD_REQUEST.value
            )
        message = MessageService.create_message(
            sender_id=current_user.user_id,
            message_data=request.json
        )

        return {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "timestamp": message.sent_at.isoformat()
        }, HTTPStatus.CREATED.value

    except ValueError as err:
        raise APIError(
            message="Invalid message data",
            code="INVALID_INPUT",
            status_code=HTTPStatus.BAD_REQUEST.value
        )

    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Failed to save message",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )
    #
    # except Exception as err:
    #     db.session.rollback()
    #     raise APIError(
    #         message="Message sending failed",
    #         code="MESSAGE_FAILURE",
    #         status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
    #     )

@msg_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_inbox(user_id):
    try:
        if user_id != current_user.user_id:
            raise APIError(
                message="Unauthorized access",
                code="PERMISSION_DENIED",
                status_code=HTTPStatus.FORBIDDEN.value
            )
        messages = MessageService.get_inbox_messages(user_id)
        return message_output_schema.dump(messages), HTTPStatus.OK.value

    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Failed to retrieve messages",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )

    except Exception as err:
        raise APIError(
            message="Failed to load messages",
            code="SERVER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )