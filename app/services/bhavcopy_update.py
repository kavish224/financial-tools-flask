from app.models import HistoricalData1D, StockSymbol, db
from sqlalchemy import exists
from io import BytesIO
from datetime import datetime, date
import csv
import logging
import requests
import zipfile
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def safe_float(value: str) -> Optional[float]:
    try:
        return float(value) if value.strip() != '' else None
    except (ValueError, AttributeError):
        return None


def safe_int(value: str) -> Optional[int]:
    try:
        return int(value) if value.strip() != '' else None
    except (ValueError, AttributeError):
        return None


def process_bhavcopy(file) -> Dict[str, int]:
    try:
        content = file.read().decode('utf-8')
        data = csv.DictReader(content.splitlines())

        records_inserted = 0
        skipped_records = 0
        error_records = 0

        existing_isins = set(isin[0] for isin in db.session.query(StockSymbol.isin).all())
        batch_size = 1000
        batch_records = []

        for row_num, row in enumerate(data, 1):
            try:
                if row.get("SctySrs", "").strip() != "EQ":
                    skipped_records += 1
                    continue

                if not all(key in row for key in ['TradDt', 'ISIN']):
                    logger.warning(f"Row {row_num}: Missing required fields")
                    error_records += 1
                    continue

                try:
                    trade_date = datetime.strptime(row['TradDt'], '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Row {row_num}: Invalid date format: {row['TradDt']}")
                    error_records += 1
                    continue

                isin = row['ISIN'].strip()
                if not isin or isin not in existing_isins:
                    skipped_records += 1
                    continue

                open_price = safe_float(row.get('OpnPric'))
                high_price = safe_float(row.get('HghPric'))
                low_price = safe_float(row.get('LwPric'))
                close_price = safe_float(row.get('ClsPric'))
                volume = safe_int(row.get('TtlTradgVol'))

                stock_symbol = StockSymbol.query.filter_by(isin=isin).first()
                if not stock_symbol:
                    skipped_records += 1
                    continue

                symbol_fk = stock_symbol.symbol

                record_exists = db.session.query(
                    exists().where(
                        (HistoricalData1D.symbol == symbol_fk) &
                        (HistoricalData1D.date == trade_date)
                    )
                ).scalar()

                if record_exists:
                    skipped_records += 1
                    continue

                batch_records.append({
                    'symbol': symbol_fk,
                    'date': trade_date,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume,
                    'open_interest': None
                })

                if len(batch_records) >= batch_size:
                    records_inserted += _insert_batch(batch_records)
                    batch_records = []

            except Exception as e:
                logger.exception(f"Error processing row {row_num}", exc_info=True)
                error_records += 1
                continue

        if batch_records:
            records_inserted += _insert_batch(batch_records)

        db.session.commit()

        result = {
            "inserted": records_inserted,
            "skipped": skipped_records,
            "errors": error_records,
            "total_processed": records_inserted + skipped_records + error_records
        }

        logger.info(f"BhavCopy processing completed: {result}")
        return result

    except Exception as e:
        db.session.rollback()
        logger.exception("Error processing BhavCopy file", exc_info=True)
        raise


def _insert_batch(batch_records) -> int:
    try:
        for record_data in batch_records:
            new_record = HistoricalData1D(**record_data)
            db.session.add(new_record)

        db.session.flush()
        return len(batch_records)

    except Exception as e:
        logger.exception("Error inserting batch", exc_info=True)
        db.session.rollback()
        return 0


def download_and_process_bhavcopy_nse(target_date: Optional[date] = None) -> Dict[str, Any]:
    if not target_date:
        target_date = datetime.today().date()

    yyyymmdd = target_date.strftime('%Y%m%d')
    url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/"
    }

    try:
        logger.info(f"Downloading BhavCopy: {url}")
        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code != 200:
            logger.warning(f"BhavCopy download failed: {response.status_code}")
            return {"status": "error", "reason": "File not found or inaccessible"}

        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            file_name = zip_ref.namelist()[0]
            with zip_ref.open(file_name) as csv_file:
                result = process_bhavcopy(csv_file)
                return result

    except Exception as e:
        logger.exception("Error downloading or processing BhavCopy", exc_info=True)
        return {"status": "error", "reason": str(e)}
