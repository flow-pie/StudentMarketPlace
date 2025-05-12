from marshmallow import Schema, fields, validate
from ..models import ItemCategory, ItemCondition

class ItemCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=True)
    price = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    category = fields.Enum(ItemCategory, by_value=True, required=True)
    condition = fields.Enum(ItemCondition, by_value=True, required=True)

