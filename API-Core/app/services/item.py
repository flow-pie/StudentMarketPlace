from ..models import Item, ItemStatus, ItemCategory, ItemCondition
from ..extensions import db

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