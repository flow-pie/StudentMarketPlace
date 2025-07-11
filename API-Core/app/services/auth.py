from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from jinja2.runtime import identity

import random
import string
from datetime import datetime, timedelta
from flask import current_app
from ..extensions import db
from ..models.user import User
from flask_mail import Message
from ..extensions import mail

class AuthService:
    @staticmethod
    def generate_token(user):
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                'name': user.get_full_name(),
                'email': user.email,
                'is_admin': user.is_admin
            }
        )
        refresh_token = create_refresh_token(
            identity=str(user.user_id),
            additional_claims={
                'name': user.get_full_name(),
                'email': user.email,
                'is_admin': user.is_admin
            }
        )

        return access_token, refresh_token

    @staticmethod
    def generate_otp(length=4):
        digits = string.digits
        return ''.join(random.choice(digits) for _ in range(length))

    @staticmethod
    def generate_and_send_otp(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("Email not registered")

        otp = AuthService.generate_otp()
        user.otp_code = otp
        user.otp_expiration = datetime.utcnow() + timedelta(minutes=10) 
        db.session.commit()

        msg = Message(
            subject="Your Password Reset OTP",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email],
            body=f"Your OTP for password reset is: {otp}. It is valid for 10 minutes."
        )
        mail.send(msg)

    @staticmethod
    def verify_otp_and_reset_password(email, otp, new_password):
        """Verify OTP and reset password if valid."""
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("Email not registered")

        if not user.otp_code or not user.otp_expiration:
            raise ValueError("No OTP requested")

        if datetime.utcnow() > user.otp_expiration:
            raise ValueError("OTP expired")

        if user.otp_code != otp:
            raise ValueError("Invalid OTP")

        user.set_password(new_password)
        
        user.otp_code = None
        user.otp_expiration = None
        db.session.commit()
