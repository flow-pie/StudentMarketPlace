from ..models import User, Item, Message
from ..models.report import Report, ReportStatus
from ..extensions import db

def create_report(data):
    reporter_id = data.get("reporter_id")
    content_type = data.get("content_type")
    reason = data.get("reason")

    if reporter_id is None:
        raise ValueError("Missing 'reporter_id' in data.")

    if not User.query.get(reporter_id):
        raise ValueError(f"Invalid reporter_id: user with id {reporter_id} does not exist.")

    if content_type == "item":
        item_id = data.get("item_id")
        if item_id is None:
            raise ValueError("Missing 'item_id' for item report.")
        if not Item.query.get(item_id):
            raise ValueError(f"Item with id {item_id} does not exist.")
        data["item_id"] = item_id  # map to DB field

    elif content_type == "message":
        message_id = data.get("message_id")
        if message_id is None:
            raise ValueError("Missing 'message_id' for message report.")
        if not Message.query.get(message_id):
            raise ValueError(f"Message with id {message_id} does not exist.")
        data["message_id"] = message_id  # map to DB field

    else:
        raise ValueError(f"Invalid content_type: {content_type}")

    try:
        report = Report(**data)
        db.session.add(report)
        db.session.commit()
        return report

    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Failed to create report: {e}")


def get_all_reports():
    return Report.query.order_by(Report.created_at.desc()).all()

def update_report_status(report_id, new_status):
    report = Report.query.get_or_404(report_id)
    try:
        report.status = ReportStatus(new_status)
    except ValueError:
        return None
    db.session.commit()
    return report
