# app/routes/analytics.py
from flask import Blueprint, jsonify
from app.services.sma_crossing import calculate_golden_cross

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/golden-cross', methods=['GET'])
def golden_cross_endpoint():
    """
    Endpoint to calculate Golden Cross and Death Cross events for all stocks.
    """
    try:
        results = calculate_golden_cross()
        if not results:
            return jsonify({"message": "No crossing events found."}), 404
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
