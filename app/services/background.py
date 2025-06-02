# app/services/background.py
import logging
import requests
from datetime import datetime, timedelta
from app.services.database import get_db_connection
import time
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_symbols_debug.log'),  # Save logs to file
        logging.StreamHandler()  # Print logs to console
    ]
)

def fetch_historical_data(symbol, start_date, end_date):
    """
    Fetch historical data from the API for a specific stock symbol.
    """
    try:
        encoded_symbol = f"NSE_EQ%7C{symbol}"
        url = f'https://api.upstox.com/v2/historical-candle/{encoded_symbol}/day/{end_date}/{start_date}'
        headers = {'Accept': 'application/json'}

        logging.debug(f"Request URL: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'candles' in data['data']:
                return data['data']['candles']
            else:
                logging.error(f"Invalid response structure for {symbol}: {data}")
                return None
        else:
            logging.error(f"API error for {symbol}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Unexpected error fetching data for {symbol}: {str(e)}")
        return None

def update_stock_data(isin):
    """
    Update historical data for a single ISIN.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch latest date from the database
        cursor.execute(
            "SELECT MAX(date) FROM historical_data_1d WHERE symbol = %s",
            (isin,)
        )
        latest_date = cursor.fetchone()[0]

        # Calculate date range for fetching new data
        start_date = (latest_date + timedelta(days=1)) if latest_date else datetime(2019, 1, 1).date()
        end_date = datetime.today().date()

        if start_date > end_date:
            logging.info(f"No new data for ISIN {isin}.")
            return

        # Fetch historical data
        candles = fetch_historical_data(isin, start_date.isoformat(), end_date.isoformat())
        if not candles:
            logging.error(f"No data fetched for ISIN {isin}. Skipping update.")
            return

        # Insert new data into the database
        for candle in candles:
            timestamp = datetime.strptime(candle[0], '%Y-%m-%dT%H:%M:%S%z').date()
            open_price, high_price, low_price, close_price, volume = candle[1:6]
            cursor.execute(
                """
                INSERT INTO historical_data_1d (symbol, date, open_price, high_price, low_price, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO NOTHING
                """,
                (isin, timestamp, open_price, high_price, low_price, close_price, volume)
            )
        conn.commit()
        logging.info(f"Updated data for ISIN {isin}.")
    except Exception as e:
        logging.error(f"Error updating data for ISIN {isin}: {str(e)}")
    finally:
        conn.close()

def update_all_symbols(batch_size=50, delay=1):
    """
    Update historical data for all symbols in batches.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all ISINs from the database
        cursor.execute("SELECT isin FROM stock_symbols")
        isins = [row[0] for row in cursor.fetchall()]
        cursor.close()

        if not isins:
            logging.warning("No ISINs found in the database.")
            return

        for i in range(0, len(isins), batch_size):
            batch = isins[i:i + batch_size]
            for isin in batch:
                update_stock_data(isin)
            logging.info(f"Batch {i // batch_size + 1} processed.")
            time.sleep(delay)

    except Exception as e:
        logging.error(f"Error during batch update: {str(e)}")
    finally:
        conn.close()
