"""Enhanced item service with caching and performance optimizations."""

from typing import List, Dict, Any, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from flask import current_app

from ..models import Item, ItemStatus, ItemCategory, ItemCondition, User
from ..extensions import db
from ..middleware.caching import cached, invalidate_cache_pattern
from ..models.user import UserInstitution


class EnhancedItemService:
    """Enhanced item service with caching and optimizations."""

    @staticmethod
    @cached(timeout=300, key_prefix="popular_items")
    def get_popular_items(limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular items with caching."""
        try:
            items = (Item.query
                    .options(joinedload(Item.seller))
                    .filter_by(status=ItemStatus.AVAILABLE)
                    .order_by(Item.created_at.desc())
                    .limit(limit)
                    .all())

            return [item.to_dict() for item in items]
        except Exception as e:
            current_app.logger.error(f"Error fetching popular items: {e}")
            return []

    @staticmethod
    @cached(timeout=600, key_prefix="category_stats")
    def get_category_statistics() -> Dict[str, int]:
        """Get item count by category with caching."""
        try:
            stats = (db.session.query(
                        Item.category,
                        func.count(Item.item_id).label('count')
                    )
                    .filter_by(status=ItemStatus.AVAILABLE)
                    .group_by(Item.category)
                    .all())

            return {
                category.name if category else "Uncategorized": count
                for category, count in stats
            }
        except Exception as e:
            current_app.logger.error(f"Error fetching category stats: {e}")
            return {}

    @staticmethod
    def get_optimized_filtered_items(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized filtered items query with eager loading."""
        try:
            # Build base query with optimized joins
            query = (Item.query
                    .options(
                        joinedload(Item.seller),
                        joinedload(Item.images)
                    ))

            if filters.get('category'):
                query = query.filter(Item.category == filters['category'])

            if filters.get('school'):
                query = query.join(Item.seller).filter(
                    User.institution == filters['school']
                )

            if filters.get('min_price'):
                query = query.filter(Item.price >= filters['min_price'])

            if filters.get('max_price'):
                query = query.filter(Item.price <= filters['max_price'])

            if filters.get('condition'):
                query = query.filter(Item.condition == filters['condition'])

            if filters.get('status'):
                query = query.filter(Item.status == filters['status'])

            if filters.get('keyword'):
                keyword = f"%{filters['keyword']}%"
                query = query.filter(
                    or_(
                        Item.title.ilike(keyword),
                        Item.description.ilike(keyword)
                    )
                )

            # Apply sorting
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = filters.get('sort_order', 'desc')

            if sort_by in ['price', 'created_at'] and sort_order in ['asc', 'desc']:
                column = getattr(Item, sort_by)
                if sort_order == 'desc':
                    column = column.desc()
                query = query.order_by(column)

            # Pagination
            page = filters.get('page', 1)
            per_page = min(filters.get('per_page', 20), 100)  # Limit max per_page

            paginated = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            return {
                'items': [item.to_dict() for item in paginated.items],
                'total': paginated.total,
                'page': paginated.page,
                'per_page': paginated.per_page,
                'pages': paginated.pages
            }

        except Exception as e:
            current_app.logger.error(f"Error in optimized filtered items: {e}")
            raise

    @staticmethod
    def invalidate_item_caches(item_id: Optional[int] = None):
        """Invalidate relevant caches when items change."""
        patterns = [
            "popular_items:*",
            "category_stats:*",
            "filtered_items:*"
        ]

        for pattern in patterns:
            invalidate_cache_pattern(pattern)
        
        current_app.logger.info(f"Invalidated item caches for item_id: {item_id}")