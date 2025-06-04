from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from http import HTTPStatus

from ...errors import APIError
from ...extensions import db
from ...schemas.auth import MessageSchema
from ...schemas.message import MessageCreateSchema, MessagingSchema
from ...services.message import MessageService

msg_bp = Blueprint('Messaging System', __name__, description="Message-related operations")

message_schema = MessageCreateSchema()
message_output_schema = MessagingSchema(many=True)
message_field_schema = MessageSchema()


@msg_bp.route('', methods=['POST'])
@msg_bp.doc(
    description="Send a message to another user. Requires authentication.",
    tags=["Messaging System"]
)

@msg_bp.arguments(MessageCreateSchema)
@msg_bp.response(201, message_schema)
@jwt_required()
@msg_bp.doc(security=[{"BearerAuth": []}])
def send_message(data):
    """
    Send a message.

    Request body:
    - receiver_id (int): ID of the user receiving the message.
    - content (str): Message content.

    Returns:
    - message_id (int)
    - conversation_id (int)
    - sender_id (int)
    - receiver_id (int)
    - content (str)
    - timestamp (ISO8601 string)
    """
    try:
        message = MessageService.create_message(
            sender_id=current_user.user_id,
            message_data=data
        )
        return {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "timestamp": message.sent_at.isoformat()
        }, HTTPStatus.CREATED

    except ValueError as e:
        error_msg = str(e)
        code = "INVALID_INPUT"

        if "not found" in error_msg.lower():
            code = "ITEM_NOT_FOUND"
        elif "content" in error_msg.lower():
            code = "INVALID_MESSAGE_CONTENT"

        raise APIError(
            message=error_msg,
            code=code,
            status_code=HTTPStatus.BAD_REQUEST
        )

    except PermissionError as e:
        raise APIError(
            message=str(e),
            code="PERMISSION_DENIED",
            status_code=HTTPStatus.FORBIDDEN
        )

    except SQLAlchemyError:
        db.session.rollback()
        raise APIError(
            message="Failed to save message",
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@msg_bp.route('/<int:user_id>', methods=['GET'])
@msg_bp.doc(
    description="Retrieve all inbox messages for a user. Requires authentication.",
    params={
        "user_id": {
            "description": "ID of the user whose inbox is requested",
            "type": "integer"
        }
    },
    tags=["Messaging System"]
)

@msg_bp.response(200, message_output_schema)
@jwt_required()
@msg_bp.doc(
    security=[{"BearerAuth": []}],
    description="Retrieve all inbox messages for a user. Requires authentication.",
    params={
        "user_id": {
            "description": "ID of the user whose inbox is requested",
            "type": "integer"
        }
    },
    tags=["Messaging System"]


)
def get_inbox(user_id):
    """
       Get inbox messages.

       Path parameter:
       - user_id (int): ID of the user whose inbox is requested.

       Returns:
       - List of message objects.
       """
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