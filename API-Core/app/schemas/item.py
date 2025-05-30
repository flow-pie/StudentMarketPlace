from flask_smorest.fields import Upload
from marshmallow import Schema, fields, validate, ValidationError, validates
from marshmallow_enum import EnumField
from enum import Enum
import bleach
import re
from ..models import ItemCategory, ItemCondition, ItemStatus
from ..models.user import UserInstitution


# ---- Security Helpers ----
def sanitize_html(value):
    """Strip all HTML tags and special characters"""
    if not value:
        return value
    cleaned = bleach.clean(str(value), tags=[], attributes={}, strip=True)
    if cleaned != value:
        raise ValidationError("HTML tags or unsafe characters detected")
    return cleaned


def validate_safe_text(value):
    """Ensure text contains only allowed characters"""
    if not re.match(r'^[\w\s\-.,!?@\'"()/:;]+$', str(value)):
        raise ValidationError("Contains invalid characters")
    return value


class SecureSchema(Schema):
    """Base schema with automatic security validation"""

    def on_bind_field(self, field_name, field_obj):
        if isinstance(field_obj, fields.Str):
            # Get existing validators
            existing_validators = []
            if hasattr(field_obj, 'validate'):
                if callable(field_obj.validate):
                    existing_validators = [field_obj.validate]
                elif isinstance(field_obj.validate, (list, tuple)):
                    existing_validators = list(field_obj.validate)
            field_obj.validate = existing_validators + [sanitize_html, validate_safe_text]

class ItemUpdateSchema(SecureSchema):
    title = fields.Str(
        required=False,
        validate=[
            validate.Length(min=2, max=100),
            validate.Regexp(r'^[\w\s\-.,!?@\'"]+$')
        ]
    )
    description = fields.Str(
        required=False,
        validate=validate.Length(max=2000)
    )
    price = fields.Decimal(
        required=False,
        places=2,
        validate=validate.Range(min=0.01, max=99999.99)
    )
    category = EnumField(ItemCategory, by_value=True, required=False)
    condition = EnumField(ItemCondition, by_value=True, required=False)
    status = EnumField(ItemStatus, by_value=True, required=False)


class ItemSchema(SecureSchema):
    item_id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    status = fields.Str()
    created_at = fields.Str()
    updated_at = fields.Str()
    seller_id = fields.Int(dump_only=True)
    price = fields.Decimal(places=2)
    category = fields.Str(attribute="category.value")
    condition = fields.Str(attribute="condition.value")

    @validates('price')
    def validate_price(self, value):
        if value <= 0:
            raise ValidationError("Price must be greater than zero")
        if abs(value.as_tuple().exponent) > 2:
            raise ValidationError("Price must have maximum 2 decimal places")

class ItemFilterSchema(SecureSchema):
    category = EnumField(
        ItemCategory,
        by_value=False,
        required=False
    )
    school = EnumField(
        UserInstitution,
        by_value=True,
        required=False
    )
    min_price = fields.Decimal(
        required=False,
        places=2,
        validate=validate.Range(min=0),
        metadata={"strict": True}
    )
    max_price = fields.Decimal(
        required=False,
        places=2,
        validate=validate.Range(min=0),
        metadata={"strict": True}
    )
    page = fields.Int(
        load_default=1,
        validate=validate.Range(min=1, max=100)
    )
    per_page = fields.Int(
        validate=validate.Range(max=50),
        load_default=20
    )
    keyword = fields.Str(
        required=False,
        validate=[
            validate.Length(max=100),
            validate.Regexp(r'^[\w\s\-.,!?@\'"]+$')
        ]
    )


class PaginatedItemSchema(SecureSchema):
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


class ItemCreateSchema(SecureSchema):
    title = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=100),
            validate.Regexp(r'^[\w\s\-.,!?@\'"]+$')
        ]
    )
    description = fields.Str(
        required=True,
        validate=validate.Length(max=2000)
    )
    price = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0.01, max=99999.99)
    )
    category = EnumField(ItemCategory, by_value=True, required=True)
    condition = EnumField(ItemCondition, by_value=True, required=True)


class ImageResponseSchema(Schema):
    image_id = fields.Int()
    item_id = fields.Int()
    image_url = fields.Str()
    is_primary = fields.Bool()


class ImageSchema(Schema):
    image = Upload(required=True)


class ItemPaginationSchema(Schema):
    category = fields.String(
        required=False,
        validate=validate.OneOf([c.value for c in ItemCategory]),
    )
    page = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        required=False,
        validate=validate.Range(min=1, max=100),
    )


class ItemQuerySchema(Schema):
    category = fields.String(
        required=False,
        validate=validate.OneOf([c.value for c in ItemCategory]),
        metadata={'enum': [c.value for c in ItemCategory]}
    )

    school = fields.String(
        required=False,
        validate=validate.OneOf([c.value for c in UserInstitution]),
        metadata={'enum': [c.value for c in UserInstitution]}
    )
    min_price = fields.Float(required=False, validate=validate.Range(min=0))
    max_price = fields.Float(required=False, validate=validate.Range(min=0))

    condition = fields.String(
        required=False,
        validate=validate.OneOf([c.value for c in ItemCondition]),
        metadata={'enum': [c.value for c in ItemCondition]}
    )

    status = fields.String(
        required=False,
        validate=validate.OneOf([s.value for s in ItemStatus]),
        metadata={'enum': [s.value for s in ItemStatus]}
    )

    sort_by = fields.String(
        required=False,
        validate=validate.OneOf(['price', 'created_at']),
        metadata={'enum': ['price', 'created_at']}
    )

    sort_order = fields.String(
        required=False,
        validate=validate.OneOf(['asc', 'desc']),
        metadata={'enum': ['asc', 'desc']}
    )

    page = fields.Integer(
        required=False,
        validate=validate.Range(min=1)
    )
    per_page = fields.Integer(
        required=False,
        validate=validate.Range(min=1, max=100)
    )
