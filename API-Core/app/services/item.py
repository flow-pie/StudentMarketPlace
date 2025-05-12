from ..models import Item, ItemStatus
from ..extensions import db

class ItemService:
    @staticmethod
    def create_item(user_id, item_data):
        new_item = Item(
            seller_id=user_id,
            title=item_data["title"],
            description=item_data["description"],
            price=item_data["price"],
            category=item_data["category"],
            condition=item_data["condition"],
            status=ItemStatus.AVAILABLE  # Default status
        )
        db.session.add(new_item)
        db.session.commit()
        return new_item