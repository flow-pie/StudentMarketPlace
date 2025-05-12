# Extensions init: db, jwt, cors configs
import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv

#db
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db= SQLAlchemy() #new sqlAlchemy object
migrate = Migrate()
cors= CORS()
jwt = JWTManager()

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db) #to initialize migrations with app and db

def init_jwt(app):
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Flask Secret Key
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # JWT Secret Key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    jwt.init_app(app)

    from .models import User#importing here to avoid circular import err

    #add user identity loader
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return user_id

    #adding claims to tokens
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = User.query.get(identity)
        return {
            'is_admin': user.is_admin,
            'email': user.email,
            'status': user.account_status.value
        }

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.get(identity)
