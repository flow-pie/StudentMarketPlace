from marshmallow import Schema, fields, validate
from ..models import ItemCategory, ItemCondition, ItemStatus
from marshmallow_enum import EnumField
from enum import Enum

class ItemCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=True)
    price = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    category = fields.Enum(ItemCategory, by_value=True, required=False)
    condition = fields.Enum(ItemCondition, by_value=True, required=False)

class ItemSchema(Schema):
    item_id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    price = fields.Decimal(as_string=True)
    category = EnumField(ItemCategory, by_value=True)
    condition = EnumField(ItemCondition, by_value=True)
    status = EnumField(ItemStatus, by_value=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    seller_id = fields.Int()

class ItemUpdateSchema(Schema):
    title = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False)
    price = fields.Decimal(required=False, places=2, validate=validate.Range(min=0))
    category = fields.Enum(ItemCategory, by_value=True, required=False)
    condition = fields.Enum(ItemCondition, by_value=True, required=False)
    status = fields.Enum(ItemStatus, by_value=True, required=False)
