from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime
import bleach
import re

class SecureMessageSchema(Schema):
    """Base schema with common security validations"""
    def on_bind_field(self, field_name, field_obj):
        if isinstance(field_obj, fields.Str):
            # Initialize validate list if it doesn't exist
            if not hasattr(field_obj, 'validate') or field_obj.validate is None:
                field_obj.validate = []
            field_obj.validate.extend([
                self._sanitize_html,
                self._validate_safe_chars
            ])

    @staticmethod
    def _sanitize_html(value):
        """Strip all HTML/JavaScript tags"""
        if value and bleach.clean(value) != value:
            raise ValidationError("Message contains disallowed HTML/JavaScript")
        return value

    @staticmethod
    def _validate_safe_chars(value):
        """Prevent injection attempts while allowing basic punctuation"""
        if value and not re.match(r'^[\w\s\-.,!?@\'"():;]+$', value):
            raise ValidationError("Message contains potentially dangerous characters")
        return value

class MessageCreateSchema(SecureMessageSchema):
    item_id = fields.Int(
        required=True,
        validate=[
            validate.Range(min=1)
        ]
    )
    content = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=1000)
        ]
    )


class MessagingSchema(SecureMessageSchema):
    message_id = fields.Int(dump_only=True)
    conversation_id = fields.Int(dump_only=True)
    sender_id = fields.Int(dump_only=True)
    receiver_id = fields.Int(dump_only=True)
    content = fields.Str(dump_only=True)
    sent_at = fields.Str(dump_only=True)

    # Rate limiting metadata (for client-side handling)
    can_reply = fields.Bool(dump_only=True)
    next_message_allowed_at = fields.DateTime(dump_only=True)

class MessageUpdateSchema(SecureMessageSchema):
    content = fields.Str(
        required=False,
        validate=[
            validate.Length(min=1, max=1000),
            validate.Regexp(r'^[\w\s\-.,!?@\'"():;\n]+$')
        ]
    )
    is_read = fields.Bool(required=False)

class MessageFilterSchema(SecureMessageSchema):
    conversation_id = fields.Int(
        required=False,
        validate=validate.Range(min=1)
    )
    since = fields.DateTime(required=False)
    until = fields.DateTime(required=False)
    limit = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100)
    )