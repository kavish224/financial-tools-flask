from flask import Blueprint,request, jsonify
from app.models import db, HistoricalData1D
from app.services.near_sma import get_stocks_near_sma
analytics_bp = Blueprint("analytics", __name__)
@analytics_bp.route("/analytics/sma-nearby", methods=["POST"])
def sma_nearby():
    try:
        data = request.get_json()
        sma_period = int(data.get("sma_period", 50))
        threshold_pct = float(data.get("threshold_pct", 2.0))
        results = get_stocks_near_sma(sma_period,threshold_pct)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
