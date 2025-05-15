from marshmallow import Schema, fields, validate
from ..models import ItemCategory, ItemCondition, ItemStatus
from marshmallow_enum import EnumField

from ..models.user import UserInstitution


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
    category = fields.Function(lambda obj: (
        obj.category.name if isinstance(obj.category, ItemCategory)
        else ItemCategory(int(obj.category)).name if obj.category
        else None
    ))

    condition = fields.Function(lambda obj: (
        obj.condition.value if isinstance(obj.condition, ItemCondition)
        else obj.condition if obj.condition
        else None
    ))

    status = fields.Function(lambda obj: (
        obj.status.value if isinstance(obj.status, ItemStatus)
        else obj.status
    ))
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    seller_id = fields.Int()


class ItemFilterSchema(Schema):
    category = fields.Str(validate=validate.OneOf([c.name for c in ItemCategory]))
    school = fields.Str(validate=validate.OneOf([s.value for s in UserInstitution]))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))
    page = fields.Int(load_default=1)
    per_page = fields.Int(validate=validate.Range(max=50), load_default=20)
    keyword = fields.Str()


class PaginatedItemSchema(Schema):
    class Meta:
        ordered = True

    items = fields.List(fields.Nested(ItemSchema))
    page = fields.Integer()
    per_page = fields.Integer()
    total = fields.Integer()
    categories = fields.Dict(
        keys=fields.String(),
        values=fields.Integer(),
        metadata={"description": "Count of items per category"}
    )