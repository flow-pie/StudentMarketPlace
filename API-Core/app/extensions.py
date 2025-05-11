# Extensions init: db, jwt, cors
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
#db
from flask_sqlalchemy import SQLAlchemy
db= SQLAlchemy() #new sqlAlchemy object
migrate = Migrate()
cors= CORS()
jwt = JWTManager()

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db) #to initialize migrations with app and db