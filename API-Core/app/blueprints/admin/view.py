from flask import Blueprint, request
from http import HTTPStatus

from flask_jwt_extended import jwt_required

from ...errors import APIError
from ...schemas.report import ReportSchema
from ...decorators.auth import admin_required
from ...services.report import create_report, get_all_reports, update_report_status

report_bp = Blueprint('report', __name__)
report_schema = ReportSchema()

@report_bp.route('/reports', methods=['POST'])
@jwt_required()
def report_content():
    try:
        data = request.get_json()
        errors = report_schema.validate(data)
        if errors:
            raise APIError(
                message="Invalid report data",
                code="VALIDATION_ERROR",
                status_code=HTTPStatus.BAD_REQUEST.value
            )

        report = create_report(data)
        return report_schema.dump(report), HTTPStatus.CREATED.value

    except ValueError as e:
        raise APIError(
            message=str(e),
            code="INVALID_INPUT",
            status_code=HTTPStatus.BAD_REQUEST.value
        )

@report_bp.route('/reports', methods=['GET'])
@admin_required
def get_reports():
    try:
        reports = get_all_reports()
        return report_schema.dump(reports, many=True), HTTPStatus.OK.value
    except Exception as err:
        raise APIError(
            message="Failed to retrieve reports",
            code="REPORT_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )

@report_bp.route('/reports/<int:report_id>', methods=['PATCH'])
@admin_required
def resolve_report(report_id):
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            raise APIError(
                message="Missing 'status' in request body",
                code="MISSING_STATUS",
                status_code=HTTPStatus.BAD_REQUEST.value
            )

        report = update_report_status(report_id, data['status'])
        if not report:
            raise APIError(
                message="Invalid status provided",
                code="INVALID_STATUS",
                status_code=HTTPStatus.BAD_REQUEST.value
            )

        return report_schema.dump(report), HTTPStatus.OK.value

    except ValueError as e:
        raise APIError(
            message=str(e),
            code="INVALID_INPUT",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except Exception as e:
        raise APIError(
            message="Failed to update report status",
            code="REPORT_UPDATE_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )