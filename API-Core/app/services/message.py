from sqlalchemy import distinct

from ..extensions import db
from ..models import Message, Conversation, Item
from ..models.conversation import ConversationParticipant


class MessageService:
    @staticmethod
    def create_message(sender_id, message_data):
        item_id = message_data['item_id']
        content = message_data['content']

        if not content or len(content) > 1000:
            raise ValueError("Message content must be 1-1000 characters")

        item = Item.query.get(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")

        if item.seller_id == sender_id:
            raise PermissionError("Cannot message yourself about your own item")

        conversation = Conversation.query.filter(
            Conversation.item_id == item_id,
            Conversation.sender_id == sender_id
        ).first()

        if not conversation:
            conversation = Conversation(
                sender_id=sender_id,
                item_id=item_id
            )
            db.session.add(conversation)
            db.session.flush()  # Get conversation ID without committing

            # Add participants
            db.session.add_all([
                ConversationParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=sender_id
                ),
                ConversationParticipant(
                    conversation_id=conversation.conversation_id,
                    user_id=item.seller_id
                )
            ])

        # Create message
        message = Message(
            conversation_id=conversation.conversation_id,
            sender_id=sender_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        return message

    @staticmethod
    def get_inbox_messages(user_id):
        # Fetch messages where the user is a participant in the conversation
        messages = Message.query.join(
            Conversation, Message.conversation_id == Conversation.conversation_id
        ).join(
            ConversationParticipant, Conversation.conversation_id == ConversationParticipant.conversation_id
        ).filter(
            ConversationParticipant.user_id == user_id
        ).order_by(Message.sent_at.desc()).all()

        return messages
