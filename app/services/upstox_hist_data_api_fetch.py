# app/services/upstox_hist_data_api_fetch.py
import logging
import requests

def fetch_historical_data(symbol, start_date, end_date):
    """
    Fetch historical data from Upstox API for a specific stock symbol.
    """
    try:
        # Ensure URL encoding is correct for the symbol
        encoded_symbol = f"NSE_EQ%7C{symbol}"
        url = f'https://api.upstox.com/v2/historical-candle/{encoded_symbol}/day/{end_date}/{start_date}'
        headers = {'Accept': 'application/json'}
        
        # Log the URL and headers being used for the request
        logging.info(f"Fetching data for {symbol} from URL: {url}")

        # Send the request
        response = requests.get(url, headers=headers)
        
        # Log the response status and content
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response content: {response.text}")

        # Check for successful response
        if response.status_code == 200:
            try:
                data = response.json()
                logging.info(f"API response for {symbol}: {data}")  # Log the full response

                # Check if the response contains the expected data structure
                if 'data' in data and 'candles' in data['data']:
                    return data
                else:
                    logging.error(f"Missing 'data' or 'candles' in response for {symbol}. Response: {data}")
                    return None
            except ValueError as e:
                logging.error(f"Failed to parse JSON response for {symbol}: {str(e)}")
                return None
        else:
            logging.error(f"Error fetching data for {symbol}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed for {symbol}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error for {symbol}: {str(e)}")
        return None
