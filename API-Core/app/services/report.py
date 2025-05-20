from app.models.report import Report, ReportStatus
from app.extensions import db

def create_report(data):
    report = Report(**data)
    db.session.add(report)
    db.session.commit()
    return report

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
