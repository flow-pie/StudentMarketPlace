from flask import Blueprint, request, jsonify
from ...schemas.report import ReportSchema
from ...decorators.auth import admin_required, jwt_required
from ...services.report import create_report, get_all_reports, update_report_status

report_bp = Blueprint('report', __name__, url_prefix='/reports')

@report_bp.route('/', methods=['POST'])
@jwt_required
def report_content():
    data = request.get_json()
    schema = ReportSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    report = create_report(data)
    return schema.dump(report), 201

@report_bp.route('/admin/', methods=['GET'])
@admin_required
def get_reports():
    reports = get_all_reports()
    return ReportSchema(many=True).dump(reports), 200

@report_bp.route('/admin/<int:report_id>', methods=['PATCH'])
@admin_required
def resolve_report(report_id):
    data = request.get_json()
    status = data.get("status")
    if not status:
        return {"error": "Missing 'status' in body"}, 400

    report = update_report_status(report_id, status)
    if not report:
        return {"error": "Invalid status"}, 400

    return ReportSchema().dump(report), 200
