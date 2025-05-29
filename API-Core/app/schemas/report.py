from marshmallow import Schema, fields, validate
from marshmallow import validates_schema, ValidationError

class ReportSchema(Schema):
    id = fields.Int(dump_only=True)
    reporter_id = fields.Int(required=True)
    content_type = fields.Str(required=True, validate=validate.OneOf(["item", "message"]))
    item_id = fields.Int()
    message_id = fields.Int()
    reason = fields.Str(required=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    @validates_schema
    def check_content_reference(self, data, **kwargs):
        if data['content_type'] == 'item' and 'item_id' not in data:
            raise ValidationError('item_id is required when content_type is "item"')
        if data['content_type'] == 'message' and 'message_id' not in data:
            raise ValidationError('message_id is required when content_type is "message"')
