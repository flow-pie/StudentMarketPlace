# create_app() with factory pattern

from dotenv import load_dotenv
from flask import Flask
import os
from .extensions import db, jwt, cors, migrate, init_jwt
from .blueprints.auth.routes import auth_bp

def create_app():
    from . import models
    load_dotenv()

    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('NEON_POSTGRES_URL')
    #app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYSQL_URL') #msql DBMS
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

    # with app.app_context(): #not needed when using flask migrate
    #     db.create_all()

    return app