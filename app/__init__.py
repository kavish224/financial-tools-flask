from flask import Flask
from app.extensions import db, migrate
from app.routes import register_routes
from config import Config
from flask_cors import CORS
def create_app():
    app = Flask(__name__)

    # Apply configuration to the Flask app
    app.config.from_object(Config)
    CORS(app)
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register routes
    register_routes(app)

    return app
