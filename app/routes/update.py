# app/routes/update.py
from flask import Blueprint, request, jsonify
import logging
import threading
from app.services.background import update_all_symbols
from app.services.bhavcopy_update import process_bhavcopy

update_bp = Blueprint('update', __name__)
bhavupdate_bp = Blueprint('bhavupdate', __name__)

def update_all_symbols_in_background():
    """
    Run the update_all_symbols function in a separate thread.
    """
    try:
        update_all_symbols()
    except Exception as e:
        logging.error(f"Error while updating symbols in background: {str(e)}")

@update_bp.route('/update_all_symbols', methods=['POST'])
def update_all_symbols_endpoint():
    """
    Endpoint to update historical data for all stocks.
    """
    try:
        threading.Thread(target=update_all_symbols_in_background, daemon=True).start()
        return jsonify({"message": "All symbols update initiated successfully."}), 200
    except Exception as e:
        logging.error(f"Error in update_all_symbols endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bhavupdate_bp.route('/bhavcopy', methods=['POST'])
def upload_bhavcopy():
    """
    Endpoint to upload and process BhavCopy CSV file.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        result = process_bhavcopy(file)
        return jsonify({
            "message": "BhavCopy processed successfully.",
            "details": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
