from ..extensions import db
from ..models import Message, Conversation

class MessageService:
    @staticmethod
    def create_message(sender_id, message_data):
        conversation_id = message_data.get('conversation_id')
        content = message_data.get('content')

        #Validate conversation already exists
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        #Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        return message