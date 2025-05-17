from marshmallow import Schema, fields, validate

class MessageCreateSchema(Schema):
    conversation_id = fields.Int(required=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=10000))
