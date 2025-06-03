import csv
from datetime import datetime
from sqlalchemy import exists
from app.models import HistoricalData1D, StockSymbol, db

def safe_float(value):
    try:
        return float(value) if value.strip() != '' else None
    except (ValueError, AttributeError):
        return None

def safe_int(value):
    try:
        return int(value) if value.strip() != '' else None
    except (ValueError, AttributeError):
        return None

def process_bhavcopy(file):
    """
    Processes the BhavCopy CSV file to update the database with new trading data.
    :param file: File object containing BhavCopy data.
    :return: Dictionary summarizing the update.
    """
    data = csv.DictReader(file.read().decode('utf-8').splitlines())
    records_inserted = 0
    skipped_records = 0

    for row in data:
        try:
            date = datetime.strptime(row['TradDt'], '%Y-%m-%d').date()
            isin = row['ISIN'].strip()

            open_price = safe_float(row['OpnPric'])
            high_price = safe_float(row['HghPric'])
            low_price = safe_float(row['LwPric'])
            close_price = safe_float(row['ClsPric'])
            volume = safe_int(row['TtlTradgVol'])

            # Lookup StockSymbol by ISIN
            stock_symbol = StockSymbol.query.filter_by(isin=isin).first()
            if not stock_symbol:
                skipped_records += 1
                continue

            symbol_fk = stock_symbol.symbol  # ✅ Use ticker symbol here, not ISIN

            # Check if record already exists
            record_exists = db.session.query(
                exists().where(HistoricalData1D.symbol == symbol_fk).where(HistoricalData1D.date == date)
            ).scalar()

            if record_exists:
                skipped_records += 1
                continue

            # Insert new record
            new_record = HistoricalData1D(
                symbol=symbol_fk,
                date=date,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                open_interest=None
            )
            db.session.add(new_record)
            records_inserted += 1

        except Exception as e:
            print(f"Error processing row {row}: {e}")
            db.session.rollback()
            skipped_records += 1

    db.session.commit()
    return {"inserted": records_inserted, "skipped": skipped_records}
