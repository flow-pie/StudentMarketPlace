from marshmallow import Schema, fields, validate, ValidationError
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

# ---- Item Schemas ----
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
        validate=[
            validate.Range(min=0.01, max=99999.99),
            validate.Regexp(r'^\d{1,5}(\.\d{1,2})?$')
        ]
    )
    category = EnumField(ItemCategory, by_value=True, required=False)
    condition = EnumField(ItemCondition, by_value=True, required=False)


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
        validate=[
            validate.Range(min=0.01, max=99999.99),
            validate.Regexp(r'^\d{1,5}(\.\d{1,2})?$')
        ]
    )
    category = EnumField(ItemCategory, by_value=True, required=False)
    condition = EnumField(ItemCondition, by_value=True, required=False)
    status = EnumField(ItemStatus, by_value=True, required=False)


class ItemSchema(SecureSchema):
    item_id = fields.Int(dump_only=True)
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
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(allow_none=True, dump_only=True)
    seller_id = fields.Int(dump_only=True)


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