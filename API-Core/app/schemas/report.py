from datetime import datetime

from marshmallow import Schema, fields, validate
from marshmallow import validates_schema, ValidationError

class ReportSchema(Schema):
    id = fields.Int(dump_only=True)
    reporter_id = fields.Int(required=True)
    content_type = fields.Str(required=True, validate=validate.OneOf(["item", "message"]))
    content_id = fields.Int(required=True)
    reason = fields.Str(required=True)
    status = fields.Str(dump_only=True)

    @validates_schema
    def check_content_reference(self, data, **kwargs):
        if 'content_type' not in data or 'content_id' not in data:
            raise ValidationError("content_type and content_id are required")


class ReportStatusSchema(Schema):
    status = fields.Str(required=True)
