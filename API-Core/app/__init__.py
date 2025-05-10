# create_app() with factory pattern

#apply cors when initializing the app
from flask import Flask, request, jsonify
from  .extensions import  cors
#TODO!! import db, jwt, etc

def create_app():
    app = Flask(__name__)

    #cors setup
    #global access
    cors.init_app(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}}, supports_credentials=True)

    #TODO!! db, jwt init etc will go here

    return app

