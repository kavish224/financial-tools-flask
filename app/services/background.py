import logging
import requests
from datetime import datetime, timedelta
from app.services.database import get_db_connection
import time
from typing import Optional, List

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StockDataUpdater:
    """Class to handle stock data updates"""

    def __init__(self, batch_size: int = 50, delay: float = 1.0, timeout: float = 10.0):
        self.batch_size = batch_size
        self.delay = delay
        self.timeout = timeout
        self.base_url = "https://api.upstox.com/v2/historical-candle"
        self.headers = {'Accept': 'application/json'}

    def fetch_historical_data(self, isin: str, start_date: str, end_date: str) -> Optional[List]:
        """Fetch historical data from the API for a specific ISIN."""
        try:
            encoded_symbol = f"NSE_EQ%7C{isin}"
            url = f'{self.base_url}/{encoded_symbol}/day/{end_date}/{start_date}'

            logger.debug(f"Fetching data for ISIN {isin}: {url}")

            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            if 'data' in data and 'candles' in data['data']:
                return data['data']['candles']
            else:
                logger.warning(f"No candle data found for ISIN {isin}")
                return []

        except requests.RequestException as e:
            logger.error(f"API request failed for ISIN {isin}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data for ISIN {isin}: {str(e)}")
            return None

    def update_stock_data(self, symbol: str) -> bool:
        """Update historical data for a single stock symbol."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT "isin" FROM "StockSymbol" WHERE "symbol" = %s', (symbol,))
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"No ISIN found for symbol {symbol}")
                    return False

                isin = result[0]

                cursor.execute(
                    'SELECT MAX("date") FROM "HistoricalData1D" WHERE "symbol" = %s',
                    (symbol,)
                )
                latest_date_result = cursor.fetchone()
                latest_date = latest_date_result[0] if latest_date_result[0] else None

                if latest_date:
                    start_date = latest_date.date() + timedelta(days=1)
                else:
                    start_date = datetime(2019, 1, 1).date()
                end_date = datetime.now().date()

                if start_date > end_date:
                    logger.debug(f"No new data needed for symbol {symbol}")
                    return True

                candles = self.fetch_historical_data(isin, start_date.isoformat(), end_date.isoformat())
                if candles is None:
                    logger.error(f"Failed to fetch candles for symbol {symbol}")
                    return False

                if not candles:
                    logger.debug(f"No new candles for symbol {symbol}")
                    return True

                inserted_count = 0
                for candle in candles:
                    try:
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
                        inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error processing candle for {symbol}: {str(e)}")
                        continue

                conn.commit()
                logger.info(f"Updated {inserted_count} records for symbol {symbol}")
                return True

        except Exception as e:
            logger.error(f"Error updating data for symbol {symbol}: {str(e)}")
            return False

def update_all_symbols(batch_size: int = 50, delay: float = 1.0):
    """Update historical data for all symbols in the database."""
    updater = StockDataUpdater(batch_size, delay, timeout=15.0)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT "symbol" FROM "StockSymbol" ORDER BY "symbol"')
            symbols = [row[0] for row in cursor.fetchall()]

        if not symbols:
            logger.warning("No symbols found in the database")
            return

        logger.info(f"Starting update for {len(symbols)} symbols")

        successful_updates = 0
        failed_updates = 0

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_start_time = time.time()

            for symbol in batch:
                if updater.update_stock_data(symbol):
                    successful_updates += 1
                else:
                    failed_updates += 1

            batch_time = time.time() - batch_start_time
            logger.info(f"Batch {i // batch_size + 1} completed in {batch_time:.2f}s")

            if i + batch_size < len(symbols):
                time.sleep(delay)

        logger.info(f"Update completed: {successful_updates} successful, {failed_updates} failed")

    except Exception as e:
        logger.error(f"Error during batch update: {str(e)}")
        raise
