from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import limiter
from flask import request, current_app
from flask_smorest import Blueprint, abort
from flask_bcrypt import generate_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from werkzeug.routing import ValidationError

from ...errors import APIError
from ...extensions import db
from ...models.user import TokenBlockList, User, UserInstitution
from ...models.user import AccountStatus
from ...schemas.auth import LoginSchema, RegistrationSchema, LoginResponseSchema, UserResponseSchema, TokenSchema, \
    MessageSchema
from ...services.auth import AuthService
from flask_limiter import Limiter

auth_bp = Blueprint('Authentication', __name__,
                    description="Authentication endpoints including login, register, refresh, and logout")

limiter = Limiter(key_func=get_remote_address)


@auth_bp.route('/forgot-password', methods=['POST'])
@auth_bp.arguments(ForgotPasswordRequestSchema)
@auth_bp.response(HTTPStatus.OK, MessageSchema, description="Sends OTP to user's email for password reset")
def forgot_password(data):
    """
    Forgot password endpoint.

    Accepts email, generates OTP, and sends it to the user's email.
    """
    try:
        AuthService.generate_and_send_otp(data['email'])
        return {"message": "OTP sent to your email"}, HTTPStatus.OK
    except ValueError as e:
        abort(HTTPStatus.BAD_REQUEST, message=str(e))
    except Exception as e:
        current_app.logger.error(f"Forgot password error: {str(e)}", exc_info=True)
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to send OTP")

@auth_bp.route('/reset-password', methods=['POST'])
@auth_bp.arguments(ResetPasswordRequestSchema)
@auth_bp.response(HTTPStatus.OK, ResetPasswordResponseSchema, description="Resets password using OTP")
def reset_password(data):
    """
    Reset password endpoint.

    Accepts email, OTP, and new password. Verifies OTP and resets password.
    """
    try:
        AuthService.verify_otp_and_reset_password(data['email'], data['otp'], data['new_password'])
        return {"message": "Password reset successful"}, HTTPStatus.OK
    except ValueError as e:
        abort(HTTPStatus.BAD_REQUEST, message=str(e))
    except Exception as e:
        current_app.logger.error(f"Reset password error: {str(e)}", exc_info=True)
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to reset password")

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
@auth_bp.arguments(RegistrationSchema)
@auth_bp.response(HTTPStatus.CREATED, UserResponseSchema, description="Registers a new user and returns their details")
def register(data):
    """
    User registration endpoint.

    Accepts user details (email, password, name, institution, student ID),
    creates a new user in the system, returns created user.
    Rate limited to 10 requests per minute.
    """
    try:
        schema = RegistrationSchema()
        data = schema.load(request.json)

        user = User(
            email=data['email'].lower(),
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            institution=UserInstitution(data['institution'].capitalize()),
            student_id=data['student_id']
        )

        db.session.add(user)
        db.session.commit()

        return user, HTTPStatus.CREATED.value

    except ValidationError as err:
        error_messages = err.normalized_messages()
        raise APIError(
            message=error_messages,
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except IntegrityError as err:
        db.session.rollback()
        raise APIError(
            message={"email/student id": ["Email or student id already registered"]},
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except Exception as err:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(err)}", exc_info=True)
        if 'registered' in str(err).lower():
            raise APIError(
                message={"email": ["Email already registered"]},
                code="VALIDATION_ERROR",
                status_code=HTTPStatus.BAD_REQUEST.value
            )
        else:
            raise APIError(
                message="Registration failed",
                code="REGISTRATION_FAILED",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
            )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@auth_bp.response(
    HTTPStatus.OK,
    TokenSchema,
    description="Generates a new access token using a valid refresh token",
    examples={
        "application/json": {
            "access_token": "newly_generated_access_token"
        }
    }
)
@auth_bp.doc(security=[{'bearerAuth': []}])
def refresh_access_token():
    """
    Access token refresh endpoint.

    Requires a valid refresh token in Authorization header.

    (use postman to test this endpoint)
    """
    try:
        identity = get_jwt_identity()
        new_access_token = create_access_token(identity=identity)
        return {"access_token": new_access_token}, HTTPStatus.OK.value
    except Exception as err:
        raise APIError(
            message="Token refresh failed",
            code="REFRESH_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@auth_bp.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)
@auth_bp.response(
    HTTPStatus.OK,
    MessageSchema,
    description="Revokes the current JWT token (access or refresh)",
    examples={
        "application/json": {
            "message": "access token revoked successfully"
        }
    }
)
@auth_bp.doc(security=[{'bearerAuth': []}])
def logout():
    """
    User logout endpoint.

    Revokes the current JWT token.
    Requires Authorization header.

    (use postman to test this endpoint)

    """
    try:
        jwt = get_jwt()
        jti = jwt['jti']
        token_type = jwt['type']

        token_block = TokenBlockList(jti=jti)
        token_block.save()

        return {
            "message": f"{token_type} token revoked successfully"
        }, HTTPStatus.OK.value
    except Exception as err:
        raise APIError(
            message="Logout failed",
            code="LOGOUT_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )