from flask import request, current_app
from flask_smorest import Blueprint
from http import HTTPStatus

from flask_jwt_extended import jwt_required

from ...errors import APIError
from ...schemas.report import ReportSchema, ReportStatusSchema
from ...decorators.auth import admin_required
from ...services.report import create_report, get_all_reports, update_report_status

report_bp = Blueprint('Admin reports', __name__)
report_schema = ReportSchema()

@report_bp.route('/reports', methods=['POST'])
@jwt_required()
@report_bp.doc(security=[{"BearerAuth": []}])
@report_bp.arguments(ReportSchema)
@report_bp.response(201, ReportSchema)
def report_content(data):
    """
    Create a new report.

    Parameters:
    - data: dict → report details validated by ReportSchema.
    """
    try:
        report = create_report(data)
        return report_schema.dump(report), HTTPStatus.CREATED
    except ValueError as e:
        raise APIError(
            message=str(e),
            code="INVALID_INPUT",
            status_code=HTTPStatus.BAD_REQUEST
        )

@report_bp.route('/reports', methods=['GET'])
@admin_required
@report_bp.doc(security=[{"BearerAuth": []}])
@report_bp.response(200, None)
def get_reports():
    """
    Retrieve all reports (admin only).
    """
    try:
        reports = get_all_reports()
        return report_schema.dump(reports, many=True), HTTPStatus.OK
    except Exception:
        raise APIError(
            message="Failed to retrieve reports",
            code="REPORT_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@report_bp.route('/reports/<int:report_id>', methods=['PATCH'])
@admin_required
@report_bp.doc(security=[{"BearerAuth": []}])
@report_bp.arguments(ReportStatusSchema)  # This schema should only validate {'status': str}
@report_bp.response(200, ReportSchema)
def resolve_report(data, report_id):
    """
    Update the status of a specific report.

    Parameters:
    - report_id: int → the unique report ID.
    - data: dict → {'status': str} with the new status.
    """
    try:
        report = update_report_status(report_id, data['status'])
        if not report:
            raise APIError(
                message="Invalid status provided",
                code="INVALID_STATUS",
                status_code=HTTPStatus.BAD_REQUEST
            )
        return report_schema.dump(report), HTTPStatus.OK
    except ValueError as e:
        raise APIError(
            message=str(e),
            code="INVALID_INPUT",
            status_code=HTTPStatus.BAD_REQUEST
        )