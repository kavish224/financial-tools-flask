from flask import Blueprint, request, jsonify
import logging
import threading
import time
from datetime import datetime
from app.services.background import update_all_symbols
from app.services.bhavcopy_update import download_and_process_bhavcopy_nse

logger = logging.getLogger(__name__)
update_bp = Blueprint('update', __name__)
bhavupdate_bp = Blueprint('bhavupdate', __name__)
_background_tasks = {}
def update_all_symbols_in_background():
    """
    Run the update_all_symbols function in a separate thread.
    """
    task_id = f"update_symbols_{int(time.time())}"
    _background_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.utcnow().isoformat(),
        'message': 'Updating all symbols'
    }
    try:
        logger.info(f"Starting background update of all symbols - Task ID: {task_id}")
        update_all_symbols()
        _background_tasks[task_id].update({
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat(),
            'message': 'All symbols updated successfully'
        })
        logger.info(f"Background update completed successfully - Task ID: {task_id}")
    except Exception as e:
        error_msg = f"Error while updating symbols: {str(e)}"
        _background_tasks[task_id].update({
            'status': 'failed',
            'completed_at': datetime.utcnow().isoformat(),
            'error': error_msg
        })
        logger.error(f"Background update failed - Task ID: {task_id}: {error_msg}")
    finally:
        if len(_background_tasks) > 10:
            oldest_keys = sorted(_background_tasks.keys())[:-10]
            for key in oldest_keys:
                del _background_tasks[key]

@update_bp.route('/update_all_symbols', methods=['POST'])
def update_all_symbols_endpoint():
    """
    Endpoint to update historical data for all stocks.
    """
    try:
        running_tasks = [task for task in _background_tasks.values() if task['status'] == 'running']
        if running_tasks:
            return jsonify({
                "error": "Update is already in progress",
                "status": "rejected",
                "running_since": running_tasks[0]['started_at']
            }), 409
        thread = threading.Thread(target=update_all_symbols_in_background, daemon=True)
        thread.start()
        logger.info("All symbols update initiated via API")
        return jsonify({
            "message": "All symbols update initiated successfully",
            "status": "processing",
            "initiated_at": datetime.utcnow().isoformat()
        }), 202
    except Exception as e:
        error_msg = f"Error in update_all_symbols endpoint: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "error": "Internal server error",
            "message": "Failed to initiate update process"
        }), 500

@update_bp.route('/update_all_symbols/status', methods=['GET'])
def get_update_status():
    """
    Get status of background update tasks.
    """
    try:
        return jsonify({
            "tasks": _background_tasks,
            "active_tasks": len([t for t in _background_tasks.values() if t['status'] == 'running'])
        }), 200
    except Exception as e:
        logger.error(f"Error getting update status: {str(e)}")
        return jsonify({"error": "Failed to get status"}), 500

@bhavupdate_bp.route('/bhavcopy', methods=['POST'])
def upload_bhavcopy():
    """
    Endpoint to process BhavCopy CSV file.
    """
    try:
        start_time = time.time()
        logger.info("BhavCopy processing initiated via API")
        result = download_and_process_bhavcopy_nse()
        processing_time = round(time.time() - start_time, 2)
        logger.info(f"BhavCopy processing completed in {processing_time}s")
        return jsonify({
            "message": "BhavCopy processed successfully",
            "details": result,
            "processing_time_seconds": processing_time,
            "processed_at": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        error_msg = f"Error processing BhavCopy: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "error": "BhavCopy processing failed",
            "message": "Failed to process BhavCopy data"
        }), 500
