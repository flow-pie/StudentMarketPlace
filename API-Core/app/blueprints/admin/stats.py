from datetime import timezone, datetime

from flask import jsonify, Blueprint

from ...decorators.auth import admin_required
from ...models import User, Item, ItemStatus, Message
from ...models.report import Report

admin_stat_bp = Blueprint('stats', __name__)

@admin_stat_bp.route("/stats", methods=["GET"])
@admin_required
def get_admin_stats():
    """Returns aggregated platform statistics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    stats = {
        # User stats
        "total_users": User.query.count(),

        # Report stats
        "total_reports": Report.query.count(),
        "reports_today": Report.query.filter(Report.created_at >= today_start).count(),

        # Item stats
        "total_items": Item.query.count(),
        "available_items": Item.query.filter_by(status=ItemStatus.AVAILABLE).count(),
        "items_today": Item.query.filter(Item.created_at >= today_start).count(),

        # Message stats
        "total_messages": Message.query.count(),
        "messages_today": Message.query.filter(Message.sent_at >= today_start).count(),
        "unread_messages": Message.query.filter_by(is_read=False).count(),
    }

    return jsonify(stats), 200
