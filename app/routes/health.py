from flask import Blueprint, jsonify
import psutil
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "service": "stock-analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed health check with system metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database connection check (you'll need to implement this)
        # db_status = check_database_connection()
        
        health_data = {
            "status": "healthy",
            "service": "stock-analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                }
            },
            "services": {
                "database": "healthy",  # You can implement actual DB check
                "api": "healthy"
            }
        }
        
        # Determine overall health
        if cpu_percent > 90 or memory.percent > 90:
            health_data["status"] = "degraded"
            health_data["warnings"] = []
            if cpu_percent > 90:
                health_data["warnings"].append("High CPU usage")
            if memory.percent > 90:
                health_data["warnings"].append("High memory usage")
        
        status_code = 200 if health_data["status"] == "healthy" else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "stock-analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Health check failed"
        }), 503