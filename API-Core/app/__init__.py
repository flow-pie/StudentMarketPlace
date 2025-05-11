# create_app() with factory pattern

from dotenv import load_dotenv
from flask import Flask
import os
from .extensions import db, jwt, cors

def create_app():
    load_dotenv()

    app = Flask(__name__)
    #app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('MYSQL_URL') #msql DBMS
    app.config['SQLALCHEMY_DATABASE_URI'] =  os.getenv('SQLITE_URL')  #uncomment this if you prefer sqlite DBMS
    print("[CREATE_APP] Connection to database successful")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)#initializinf the app
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()

    return app