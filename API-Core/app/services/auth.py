from flask import jsonify
from flask_jwt_extended import create_access_token
from jinja2.runtime import identity

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
        return access_token