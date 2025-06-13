from flask import Blueprint, request, jsonify
import logging
import threading
from app.services.background import update_all_symbols
from app.services.bhavcopy_update import download_and_process_bhavcopy_nse

logger = logging.getLogger(__name__)
update_bp = Blueprint('update', __name__)
bhavupdate_bp = Blueprint('bhavupdate', __name__)

def update_all_symbols_in_background():
    """
    Run the update_all_symbols function in a separate thread.
    """
    try:
        logger.info("Starting background update of all symbols")
        update_all_symbols()
        logger.info("Background update completed successfully")
    except Exception as e:
        logging.error(f"Error while updating symbols in background: {str(e)}")

@update_bp.route('/update_all_symbols', methods=['POST'])
def update_all_symbols_endpoint():
    """
    Endpoint to update historical data for all stocks.
    """
    try:
        thread = threading.Thread(target=update_all_symbols_in_background, daemon=True)
        thread.start()
        return jsonify({
            "message": "All symbols update initiated successfully.",
            "status": "processing"
        }), 202
    except Exception as e:
        logging.error(f"Error in update_all_symbols endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bhavupdate_bp.route('/bhavcopy', methods=['POST'])
def upload_bhavcopy():
    """
    Endpoint to process BhavCopy CSV file.
    """
    try:
        result = download_and_process_bhavcopy_nse()
        return jsonify({
            "message": "BhavCopy processed successfully.",
            "details": result
        }), 200

    except Exception as e:
        logger.error(f"Error processing BhavCopy: {str(e)}")
        return jsonify({"error": str(e)}), 500
