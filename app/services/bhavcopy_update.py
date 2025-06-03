import csv
from datetime import datetime
from sqlalchemy import exists
from app.models import HistoricalData1D, StockSymbol, db

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
            # Extract data from the BhavCopy row
            date = datetime.strptime(row['TradDt'], '%Y-%m-%d').date()
            isin = row['ISIN']
            open_price = float(row['OpnPric']) if row['OpnPric'] else None
            high_price = float(row['HghPric']) if row['HghPric'] else None
            low_price = float(row['LwPric']) if row['LwPric'] else None
            close_price = float(row['ClsPric']) if row['ClsPric'] else None
            volume = int(row['TtlTradgVol']) if row['TtlTradgVol'] else None

            # Check if ISIN exists in stock_symbols and get corresponding symbol
            stock_symbol = StockSymbol.query.filter_by(isin=isin).first()
            if not stock_symbol:
                skipped_records += 1  # Skip if ISIN not found
                continue
            symbol = stock_symbol.symbol

            # Check if record for the trading day already exists
            record_exists = db.session.query(
                exists().where(HistoricalData1D.symbol == symbol).where(HistoricalData1D.date == date)
            ).scalar()

            if record_exists:
                skipped_records += 1  # Skip if record already exists
                continue

            # Insert new record into historical_data_1d
            new_record = HistoricalData1D(
                symbol=symbol,
                date=date,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume
            )
            db.session.add(new_record)
            records_inserted += 1

        except Exception as e:
            print(f"Error processing row {row}: {e}")
            skipped_records += 1

    db.session.commit()

    return {"inserted": records_inserted, "skipped": skipped_records}
