import email
from sqlalchemy.exc import IntegrityError
from flask import jsonify
from flask import Blueprint, request, jsonify
from werkzeug.routing import ValidationError

from ... import TokenBlockList
from ...models import user
from ...schemas.auth import RegistrationSchema
from ...models.user import User, AccountStatus
from ...extensions import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta, timezone, datetime
from ...schemas.auth import LoginSchema
from ...services.auth import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    if user.account_status != AccountStatus.ACTIVE:
        return jsonify({"error": "Account not active"}), 403

    if user.account_status == AccountStatus.BANNED:
        return jsonify({"error": "Your account has been banned."}), 403

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    # unpacking tokens
    access_token, refresh_token=AuthService.generate_token(user)
    return jsonify(
        {
            "message": "Login successful",
            "tokens":{
                "access_token" : access_token,
                "refresh_token" : refresh_token
            },
            "user": {
                "id": user.user_id,
                "email": user.email,
                'name': user.get_full_name()
            }
        }
    ), 200


# app/blueprints/auth/routes.py
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validate required fields
        required = ['email', 'password', 'first_name', 'last_name']
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400

        # Create user
        user = User(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Registration successful",
            "user": {
                "id": user.user_id,
                "email": user.email
            }
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Email already registered"}), 400


    except Exception as e:
        # Print full traceback to terminal or logs
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return jsonify({"access_token": new_access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)
def logout():
    jwt = get_jwt()
    jti = jwt['jti']
    token_type = jwt['type']

    token_block =TokenBlockList(jti=jti)
    token_block.save()

    return jsonify({"message": f"{token_type} token revoked successfully"}), 200
