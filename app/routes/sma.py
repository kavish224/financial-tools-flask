# app/routes/sma.py
from flask import Blueprint, jsonify
from app.services.sma_crossing import calculate_sma_crossings

sma_bp = Blueprint("sma", __name__)

@sma_bp.route('/sma_crossings', methods=['GET'])
def sma_crossings_endpoint():
    """
    Endpoint to calculate SMA50 crossings for all stocks.
    """
    try:
        results = calculate_sma_crossings()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
