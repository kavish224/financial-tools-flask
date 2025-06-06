import logging
import requests
from datetime import datetime, timedelta
from app.services.database import get_db_connection
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_symbols_debug.log'),
        logging.StreamHandler()
    ]
)


def fetch_historical_data(isin, start_date, end_date):
    """
    Fetch historical data from the API for a specific ISIN.
    """
    try:
        encoded_symbol = f"NSE_EQ%7C{isin}"
        url = f'https://api.upstox.com/v2/historical-candle/{encoded_symbol}/day/{end_date}/{start_date}'
        headers = {'Accept': 'application/json'}

        logging.debug(f"Request URL: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'candles' in data['data']:
                return data['data']['candles']
            else:
                logging.error(f"Invalid response structure for ISIN {isin}: {data}")
                return None
        else:
            logging.error(f"API error for ISIN {isin}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Unexpected error fetching data for ISIN {isin}: {str(e)}")
        return None


def update_stock_data(symbol):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get ISIN for the symbol
        cursor.execute('SELECT "isin" FROM "StockSymbol" WHERE "symbol" = %s', (symbol,))
        result = cursor.fetchone()
        if not result:
            logging.error(f"❌ No ISIN found for symbol {symbol}. Skipping.")
            return
        isin = result[0]

        # Get latest date for this symbol in historical data
        cursor.execute(
            'SELECT MAX("date") FROM "HistoricalData1D" WHERE "symbol" = %s',
            (symbol,)
        )
        latest_date = cursor.fetchone()[0]

        if latest_date:
            start_date = latest_date.date() + timedelta(days=1)
        else:
            start_date = datetime(2019, 1, 1).date()

        end_date = datetime.today().date()

        if start_date > end_date:
            logging.info(f"🟡 No new data for symbol {symbol}.")
            return

        # Fetch candles using ISIN
        candles = fetch_historical_data(isin, start_date.isoformat(), end_date.isoformat())
        if not candles:
            logging.error(f"❌ No data fetched for symbol {symbol}. Skipping update.")
            return

        # Insert data into the database
        for candle in candles:
            timestamp = datetime.strptime(candle[0], '%Y-%m-%dT%H:%M:%S%z').date()
            open_price, high_price, low_price, close_price, volume = candle[1:6]

            cursor.execute(
                '''
                INSERT INTO "HistoricalData1D" (
                    "symbol", "date", "openPrice", "highPrice",
                    "lowPrice", "closePrice", "volume"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("symbol", "date") DO NOTHING
                ''',
                (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
            )

        conn.commit()
        logging.info(f"✅ Updated data for symbol {symbol}.")

    except Exception as e:
        logging.error(f"❌ Error updating data for symbol {symbol}: {str(e)}")
    finally:
        conn.close()


def update_all_symbols(batch_size=50, delay=1):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT "symbol" FROM "StockSymbol"')
        symbols = [row[0] for row in cursor.fetchall()]
        cursor.close()

        if not symbols:
            logging.warning("⚠️ No symbols found in the database.")
            return

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            for symbol in batch:
                update_stock_data(symbol)
            logging.info(f"🟢 Batch {i // batch_size + 1} processed.")
            time.sleep(delay)

    except Exception as e:
        logging.error(f"❌ Error during batch update: {str(e)}")
    finally:
        conn.close()
