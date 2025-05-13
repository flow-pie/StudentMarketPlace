import email
from sqlalchemy.exc import IntegrityError
from flask import jsonify
from flask import Blueprint, request, jsonify
from werkzeug.routing import ValidationError
from ...schemas.auth import RegistrationSchema
from ...models.user import User, AccountStatus
from ...extensions import db
from flask_jwt_extended import create_access_token
from datetime import timedelta, timezone, datetime
from ...schemas.auth import LoginSchema

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

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    # Create JWT token
    access_token = create_access_token(
        identity=str(user.user_id),
        additional_claims={
            'name' : user.get_full_name(),
            'email': user.email,
            'is_admin': user.is_admin
        }
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.user_id,
            "email": user.email,
            'name': user.get_full_name()
        }
    })

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