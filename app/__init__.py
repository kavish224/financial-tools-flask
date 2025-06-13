from flask import Flask, jsonify
from app.extensions import db, migrate, cache
from app.routes import register_routes
from config import Config
from flask_cors import CORS
import logging
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    CORS(app)
    
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    register_routes(app)
    @app.route('/', methods=['GET'])
    def home():
        print("App started and home route registered")
        return jsonify({"service": "stock-analytics"})
    
    return app
