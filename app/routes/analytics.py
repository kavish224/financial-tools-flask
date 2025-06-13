from flask import Blueprint,request, jsonify
from app.services.near_sma import update_sma_results, get_stocks_near_sma, backfill_sma_results
import logging
logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)
@analytics_bp.route("/analytics/sma-nearby", methods=["POST"])
def sma_nearby():
    """Get stocks near SMA without storing in database"""
    try:
        data = request.get_json() or {}
        sma_period = int(data.get("sma_period", 50))
        threshold_pct = float(data.get("threshold_pct", 2.0))
        if sma_period <= 0:
            return jsonify({"error": "SMA period must be positive"}), 400
        if threshold_pct < 0:
            return jsonify({"error": "Threshold percentage must be non-negative"}), 400
        results = get_stocks_near_sma(sma_period, threshold_pct)
        return jsonify({
            "data": results,
            "count": len(results),
            "parameters": {
                "sma_period": sma_period,
                "threshold_pct": threshold_pct
            }
        })
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in sma_nearby: {str(e)}")
        return jsonify({"error": str(e)}), 500
@analytics_bp.route("/analytics/smadb", methods=["POST"])
def update_sma_database():
    """Calculate and store SMA results in database"""
    try:
        data = request.get_json() or {}
        sma_period = int(data.get("sma_period", 50))
        threshold_pct = float(data.get("threshold_pct", 2.0))
        if sma_period <= 0:
            return jsonify({"error": "SMA period must be positive"}), 400
        if threshold_pct < 0:
            return jsonify({"error": "Threshold percentage must be non-negative"}), 400
        count = update_sma_results(sma_period, threshold_pct)
        
        return jsonify({
            "message": "SMA results calculated and stored in the database successfully.",
            "records_updated": count,
            "parameters": {
                "sma_period": sma_period,
                "threshold_pct": threshold_pct
            }
        })
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in update_sma_database: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@analytics_bp.route("/analytics/smadb/backfill", methods=["POST"])
def backfill_sma_database():
    """Backfill SMA results for the past N days"""
    try:
        data = request.get_json() or {}
        sma_period = int(data.get("sma_period", 50))
        threshold_pct = float(data.get("threshold_pct", 2.0))
        days = int(data.get("days", 7))

        if sma_period <= 0:
            return jsonify({"error": "SMA period must be positive"}), 400
        if threshold_pct < 0:
            return jsonify({"error": "Threshold percentage must be non-negative"}), 400
        if days <= 0:
            return jsonify({"error": "Number of days must be positive"}), 400

        backfill_sma_results(sma_period, threshold_pct, days)

        return jsonify({
            "message": f"SMA results backfilled for the past {days} day(s) successfully.",
            "parameters": {
                "sma_period": sma_period,
                "threshold_pct": threshold_pct,
                "days": days
            }
        })

    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in backfill_sma_database: {str(e)}")
        return jsonify({"error": str(e)}), 500
