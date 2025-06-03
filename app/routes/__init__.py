from flask import Blueprint
from app.routes.health import health_bp
from app.routes.update import update_bp
from app.routes.update import bhavupdate_bp
from app.routes.analytics import analytics_bp
def register_routes(app):
    app.register_blueprint(health_bp, url_prefix='/v1')
    app.register_blueprint(update_bp, url_prefix='/v1')
    app.register_blueprint(bhavupdate_bp, url_prefix='/v1')
    app.register_blueprint(analytics_bp, url_prefix='/v1')

