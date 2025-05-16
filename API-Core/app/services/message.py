from sqlalchemy import distinct

from ..extensions import db
from ..models import Message, Conversation, Item
from ..models.conversation import ConversationParticipant


class MessageService:
    @staticmethod
    def create_message(sender_id, message_data):
        item_id = message_data['item_id']
        content = message_data['content']

        # Get item and validate
        item = Item.query.get(item_id)
        if not item:
            raise ValueError("Item not found")

        if item.seller_id == sender_id:
            raise ValueError("Cannot message yourself")

        conversation = Conversation.query.filter(
            (Conversation.item_id == item_id) &
            (Conversation.sender_id == sender_id)
        ).first()

        if not conversation:
            conversation = Conversation(
                sender_id=sender_id,
                item_id=item_id
            )
            db.session.add(conversation)
            db.session.flush()

            conversation.participants = [
                ConversationParticipant(user_id=sender_id),
                ConversationParticipant(user_id=item.seller_id)
            ]

        message = Message(
            conversation_id=conversation.conversation_id,
            sender_id=sender_id,
            receiver_id=item.seller_id,  # Receiver is always item owner
            content=content
        )
        db.session.add(message)
        db.session.commit()
        return message