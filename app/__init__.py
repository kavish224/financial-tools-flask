from flask import Flask
from app.extensions import db, migrate
from app.routes import register_routes
from config import Config
from flask_cors import CORS
from flask_apscheduler import APScheduler
from app.services.near_sma import update_sma_results
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
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(
        id="daily_sma_job",
        func=lambda: update_sma_results(50, 2.0),
        trigger="cron",
        hour=18,
        minute=00
    )
    return app
