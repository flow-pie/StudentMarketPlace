from marshmallow import Schema, fields, validate

class ReportSchema(Schema):
    id = fields.Int(dump_only=True)
    reporter_id = fields.Int(required=True)
    content_type = fields.Str(required=True, validate=validate.OneOf(["item", "message"]))
    content_id = fields.Int(required=True)
    reason = fields.Str(required=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
