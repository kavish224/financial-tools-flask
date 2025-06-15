from flask import Blueprint,request, jsonify
from app.services.near_sma import update_sma_results, get_stocks_near_sma, backfill_sma_results
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)

def validate_sma_parameters(data):
    """Validate SMA parameters and return parsed values"""
    try:
        sma_period = int(data.get("sma_period", 50))
        threshold_pct = float(data.get("threshold_pct", 2.0))
        
        if sma_period <= 0 or sma_period > 500:
            raise ValueError("SMA period must be between 1 and 500")
        if threshold_pct < 0 or threshold_pct > 100:
            raise ValueError("Threshold percentage must be between 0 and 100")
            
        return sma_period, threshold_pct
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid parameters: {str(e)}")

@analytics_bp.route("/analytics/sma-nearby", methods=["POST"])
def sma_nearby():
    """Get stocks near SMA without storing in database"""
    request_id = f"sma_nearby_{int(time.time())}"
    logger.info(f"SMA nearby request started - Request ID: {request_id}")
    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "request_id": request_id
            }), 400
        data = request.get_json() or {}
        sma_period, threshold_pct = validate_sma_parameters(data)
        start_time = time.time()
        results = get_stocks_near_sma(sma_period, threshold_pct)
        processing_time = round(time.time() - start_time, 3)
        logger.info(f"SMA nearby completed - Request ID: {request_id}, " f"Results: {len(results)}, Time: {processing_time}s")
        return jsonify({
            "data": results,
            "count": len(results),
            "parameters": {
                "sma_period": sma_period,
                "threshold_pct": threshold_pct
            },
            "metadata": {
                "request_id": request_id,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 200
    except ValueError as e:
        logger.warning(f"SMA nearby validation error - Request ID: {request_id}: {str(e)}")
        return jsonify({
            "error": str(e),
            "request_id": request_id
        }), 400
    except Exception as e:
        logger.error(f"SMA nearby error - Request ID: {request_id}: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": "Failed to process SMA nearby request",
            "request_id": request_id
        }), 500
@analytics_bp.route("/analytics/smadb", methods=["POST"])
def update_sma_database():
    """Calculate and store SMA results in database"""
    request_id = f"sma_update_{int(time.time())}"
    logger.info(f"SMA database update started - Request ID: {request_id}")
    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "request_id": request_id
            }), 400
        data = request.get_json() or {}
        sma_period, threshold_pct = validate_sma_parameters(data)
        start_time = time.time()
        count = update_sma_results(sma_period, threshold_pct)
        processing_time = round(time.time() - start_time, 3)
        logger.info(f"SMA database update completed - Request ID: {request_id}, " f"Records: {count}, Time: {processing_time}s")
        return jsonify({
            "message": "SMA results calculated and stored in the database successfully",
            "records_updated": count,
            "parameters": {
                "sma_period": sma_period,
                "threshold_pct": threshold_pct
            },
            "metadata": {
                "request_id": request_id,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 200
    except ValueError as e:
        logger.warning(f"SMA database update validation error - Request ID: {request_id}: {str(e)}")
        return jsonify({
            "error": str(e),
            "request_id": request_id
        }), 400
    except Exception as e:
        logger.error(f"SMA database update error - Request ID: {request_id}: {str(e)}")
        return jsonify({
            "error": "Internal server error", 
            "message": "Failed to update SMA database",
            "request_id": request_id
        }), 500
    
@analytics_bp.route("/analytics/smadb/backfill", methods=["POST"])
def backfill_sma_database():
    """Backfill SMA results for the past N days"""
    request_id = f"sma_backfill_{int(time.time())}"
    logger.info(f"SMA backfill started - Request ID: {request_id}")
    try:
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "request_id": request_id
            }), 400
        data = request.get_json() or {}
        sma_period, threshold_pct = validate_sma_parameters(data)
        try:
            days = int(data.get("days", 7))
            if days <= 0 or days > 8:
                raise ValueError("Number of days must be between 1 and 8")
        except (TypeError, ValueError):
            return jsonify({
                "error": "Number of days must be a valid integer between 1 and 8",
                "request_id": request_id
            }), 400
        start_time = time.time()
        backfill_sma_results(sma_period, threshold_pct, days)
        processing_time = round(time.time() - start_time, 3)
        logger.info(f"SMA backfill completed - Request ID: {request_id}, "
                   f"Days: {days}, Time: {processing_time}s")
        return jsonify({
            "message": f"SMA results backfilled for the past {days} day(s) successfully",
            "parameters": {
                "sma_period": sma_period,
                "threshold_pct": threshold_pct,
                "days": days
            },
            "metadata": {
                "request_id": request_id,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 200
    except ValueError as e:
        logger.warning(f"SMA backfill validation error - Request ID: {request_id}: {str(e)}")
        return jsonify({
            "error": str(e),
            "request_id": request_id
        }), 400
    except Exception as e:
        logger.error(f"SMA backfill error - Request ID: {request_id}: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": "Failed to backfill SMA database", 
            "request_id": request_id
        }), 500