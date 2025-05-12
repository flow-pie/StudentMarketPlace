# create_app() with factory pattern

from dotenv import load_dotenv
from flask import Flask, jsonify
import os

from .blueprints.items.routes import items_bp
from .extensions import db, jwt, cors, migrate, init_jwt
from .blueprints.auth.routes import auth_bp
from flask_jwt_extended.exceptions import JWTExtendedException

def create_app():
    from . import models
    load_dotenv()

    app = Flask(__name__)

    #app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('NEON_POSTGRES_URL')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYSQL_URL') #msql DBMS
    #app.config['SQLALCHEMY_DATABASE_URI'] =  os.getenv('SQLITE_URL')  #uncomment this if you prefer sqlite DBMS



    print("INFO [CREATE_APP] Connection to database successful")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    #initialize extensions
    db.init_app(app)
    #--setup cors for frontend communication
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    #--perform db migration using app migrate obj
    migrate.init_app(app, db)
    #--jwt
    jwt.init_app(app)

    #initialize jwt
    init_jwt(app)

    #register auth services
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(items_bp, url_prefix='/api/items')

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Missing or invalid token'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Expired token'}), 401

    return app