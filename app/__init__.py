import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, g
from app.extensions import db, migrate, cache, register_db_event_listeners
from app.routes import register_routes
from config import Config
from flask_cors import CORS
import time
from datetime import datetime

def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    setup_logging(app)
    initialize_extensions(app)
    register_middlewares(app)
    register_routes(app)
    register_app_routes(app)
    register_shutdown_handlers(app)
    logger = logging.getLogger(__name__)
    logger.info(f"Flask app created successfully in {app.config.get('ENV', 'unknown')} mode")
    return app

def setup_logging(app):
    """
    Setup production-ready logging configuration.
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    if not os.path.exists('logs'):
        os.makedirs('logs')

    file_handler = RotatingFileHandler(
        'logs/stock_analytics.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
    ))
    file_handler.setLevel(log_level)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(log_level)
    logging.basicConfig(
        level=log_level,
        handlers=[file_handler, console_handler],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    if app.logger.hasHandlers():
        app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

def initialize_extensions(app):
    """
    Initialize Flask extensions.
    """
    logger = logging.getLogger(__name__)
    
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        register_db_event_listeners(app)
        logger.info("Database initialized successfully")
        cache.init_app(app)
        logger.info("Cache initialized successfully")
        CORS(app, 
             origins=app.config.get('CORS_ORIGINS', ['*']),
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             supports_credentials=True)
        logger.info("CORS initialized successfully")
 
    except Exception as e:
        logger.error(f"Error initializing extensions: {str(e)}")
        raise

def register_middlewares(app):
    """
    Register application middlewares.
    """
    @app.before_request
    def before_request():
        """Execute before each request."""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}_{id(request)}"
        
        app.logger.info(f"Request started - ID: {g.request_id}, "
                       f"Method: {request.method}, Path: {request.path}")
    
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        if hasattr(g, 'start_time'):
            duration = round((time.time() - g.start_time) * 1000, 2)
            app.logger.info(f"Request completed - ID: {getattr(g, 'request_id', 'unknown')}, "
                           f"Status: {response.status_code}, Duration: {duration}ms")
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    @app.teardown_appcontext
    def teardown_db(error):
        """Close database connections after each request."""
        if error:
            app.logger.error(f"Request teardown error: {str(error)}")

def register_app_routes(app):
    """
    Register additional application routes.
    """
    @app.route('/', methods=['GET'])
    def home():
        """Root endpoint providing basic service information."""
        return jsonify({
            "service": "stock-analytics",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "health": "/v1/health",
                "detailed_health": "/v1/health/detailed",
                "analytics": "/v1/analytics/*",
                "updates": "/v1/update_all_symbols"
            }
        })
    
    @app.route('/favicon.ico')
    def favicon():
        """Handle favicon requests."""
        return '', 204

def register_shutdown_handlers(app):
    """
    Register cleanup handlers for graceful shutdown.
    """
    import atexit
    import signal
    
    def cleanup():
        """Cleanup function for graceful shutdown."""
        logger = logging.getLogger(__name__)
        logger.info("Application shutting down...")
        
        try:
            db.session.remove()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")
        
        try:
            cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
        
        logger.info("Application shutdown complete")
    
    atexit.register(cleanup)
    
    def signal_handler(signum, frame):
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        cleanup()
        exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)