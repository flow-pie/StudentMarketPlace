from datetime import datetime, timezone
from flask import Blueprint
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError

from ...errors import APIError
from ...decorators.auth import admin_required
from ...models import User, Item, ItemStatus, Message
from ...models.report import Report

admin_stat_bp = Blueprint('stats', __name__)

@admin_stat_bp.route("/stats", methods=["GET"])
@admin_required
def get_admin_stats():
    """Returns aggregated platform statistics for the admin dashboard."""
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        stats = {
            # User stats
            "total_users": get_count_safely(User.query),
            "active_users": get_count_safely(User.query.filter_by(account_status='Active')),

            # Report stats
            "total_reports": get_count_safely(Report.query),
            "reports_today": get_count_safely(Report.query.filter(Report.created_at >= today_start)),
            "open_reports": get_count_safely(Report.query.filter_by(status='Open')),

            # Item stats
            "total_items": get_count_safely(Item.query),
            "available_items": get_count_safely(Item.query.filter_by(status=ItemStatus.AVAILABLE)),
            "items_today": get_count_safely(Item.query.filter(Item.created_at >= today_start)),

            # Message stats
            "total_messages": get_count_safely(Message.query),
            "messages_today": get_count_safely(Message.query.filter(Message.sent_at >= today_start)),
            "unread_messages": get_count_safely(Message.query.filter_by(is_read=False)),
        }

        return stats, HTTPStatus.OK.value

    except SQLAlchemyError as err:
        raise APIError(
            message="Failed to retrieve statistics",
            code="STATS_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )
    except Exception as err:
        raise APIError(
            message="An unexpected error occurred",
            code="SERVER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )

def get_count_safely(query):
    """Safely executes count() on a query with error handling"""
    try:
        return query.count()
    except Exception:
        return 0