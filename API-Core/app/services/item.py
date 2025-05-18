from sqlalchemy import func

from ..models import Item, ItemStatus, ItemCategory, ItemCondition, User
from ..extensions import db
from ..models.user import UserInstitution

class ItemService:
    @staticmethod
    def create_item(user_id, item_data):
        category_enum = ItemCategory(item_data["category"])  # int -> enum
        condition_enum = ItemCondition(item_data["condition"])  # str -> enum

        new_item = Item(
            seller_id=user_id,
            title=item_data["title"],
            description=item_data["description"],
            price=item_data["price"],
            category= category_enum,
            condition= condition_enum,
            status=ItemStatus.AVAILABLE  # Default status
        )
        db.session.add(new_item)
        db.session.commit()
        return new_item

    @staticmethod
    def get_all_items(self):
        return Item.query.all()

    @staticmethod
    def get_item_by_id(self, item_id):
        return Item.query.get_or_404(item_id)

    @staticmethod
    def get_filtered_items(filters):
        query = Item.query.join(User)

        # Category filter (convert string to enum value)
        if 'category' in filters:
            category = ItemCategory[filters['category'].upper()].value
            query = query.filter(Item.category == category)

        # School filter (convert string to enum value)
        if 'school' in filters:
            school = UserInstitution(filters['school']).value
            query = query.filter(User.institution == school)

        # Price range filter
        if 'min_price' in filters:
            query = query.filter(Item.price >= float(filters['min_price']))
        if 'max_price' in filters:
            query = query.filter(Item.price <= float(filters['max_price']))

        return query.paginate(
            page=int(filters.get('page', 1)),
            per_page=int(filters.get('per_page', 20)),
            error_out=False
        )

    @staticmethod
    def get_paginated_items(page=1, per_page=20, category=None):
        query = Item.query

        # Filter by category if specified
        if category:
            query = query.filter(Item.category == ItemCategory[category.upper()])

        # Get category counts (for sidebar/filter UI)
        category_counts = dict(
            db.session.query(
                Item.category,
                func.count(Item.item_id)
            ).group_by(Item.category).all()
        )

        # Paginate results
        pagination = query.order_by(Item.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            "items": pagination.items,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "categories": {
                category.name if category else "Uncategorized": count
                for category, count in category_counts.items()
            }
        }

    def update_item(item_data):
        # Get item by ID from the data
        item = Item.query.get_or_404(item_data["item_id"])  # FIXED

        # Verify correct ownership field
        if item.seller_id != item_data["user_id"]:  # Changed user_id to seller_id
            raise PermissionError('User does not have permission to update this item')

        # Update only provided fields
        if "title" in item_data:
            item.title = item_data["title"]
        if "description" in item_data:
            item.description = item_data["description"]
        if "price" in item_data:
            item.price = item_data["price"]
        if "category" in item_data:
            item.category = ItemCategory(item_data["category"])
        if "condition" in item_data:
            item.condition = ItemCondition(item_data["condition"])
        if "status" in item_data:
            item.status = ItemStatus(item_data["status"])

        db.session.commit()
        return item

    @staticmethod
    def delete_item(item_id):
        item = Item.query.get(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        try:
            db.session.delete(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e