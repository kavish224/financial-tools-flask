import logging
from flask import jsonify
from app.routes.health import health_bp
from app.routes.update import update_bp, bhavupdate_bp
from app.routes.analytics import analytics_bp
logger = logging.getLogger(__name__)
def register_routes(app):
    try:
        app.register_blueprint(health_bp, url_prefix='/v1')
        app.register_blueprint(update_bp, url_prefix='/v1')
        app.register_blueprint(bhavupdate_bp, url_prefix='/v1')
        app.register_blueprint(analytics_bp, url_prefix='/v1')
        logger.info("All routes registered successfully")
        register_error_handlers(app)
    except Exception as e:
        logger.error(f"Error registering routes: {str(e)}")
        raise

def register_error_handlers(app):
    """
    Register global error handlers for the application.
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {error}")
        return jsonify({
            "error": "Bad Request",
            "message": "The request could not be understood by the server",
            "status_code": 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        logger.warning(f"Unauthorized access: {error}")
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication required",
            "status_code": 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        logger.warning(f"Forbidden access: {error}")
        return jsonify({
            "error": "Forbidden",
            "message": "Access denied",
            "status_code": 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        logger.info(f"Route not found: {error}")
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource could not be found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        logger.warning(f"Method not allowed: {error}")
        return jsonify({
            "error": "Method Not Allowed",
            "message": "The method is not allowed for the requested URL",
            "status_code": 405
        }), 405
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        logger.warning(f"Rate limit exceeded: {error}")
        return jsonify({
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later",
            "status_code": 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": 500
        }), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        logger.error(f"Bad gateway: {error}")
        return jsonify({
            "error": "Bad Gateway",
            "message": "Invalid response from upstream server",
            "status_code": 502
        }), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        logger.error(f"Service unavailable: {error}")
        return jsonify({
            "error": "Service Unavailable",
            "message": "The service is temporarily unavailable",
            "status_code": 503
        }), 503
    
    @app.errorhandler(504)
    def gateway_timeout(error):
        logger.error(f"Gateway timeout: {error}")
        return jsonify({
            "error": "Gateway Timeout",
            "message": "The server did not receive a timely response",
            "status_code": 504
        }), 504
    
    # Handle any other exceptions
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        # Don't return detailed error info in production
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": 500
        }), 500

def get_registered_routes(app):
    """
    Get all registered routes for debugging/documentation purposes.
    """
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': rule.rule
        })
    return routes

