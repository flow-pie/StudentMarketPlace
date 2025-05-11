# Extensions init: db, jwt, cors
from flask_cors import CORS
from flask_jwt_extended import JWTManager
#db
from flask_sqlalchemy import SQLAlchemy
db= SQLAlchemy() #new sqlAlchemy object
cors= CORS()
jwt = JWTManager()