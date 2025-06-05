# ✅ services/near_sma.py
import pandas as pd
from app.models import HistoricalData1D
from app.extensions import db
import ta

def get_stocks_near_sma(sma_window=50, threshold_pct=2.0):
    # Fetch all symbols
    symbols = db.session.query(HistoricalData1D.symbol).distinct().all()
    symbols = [s[0] for s in symbols]

    results = []

    for symbol in symbols:
        # Query historical data for each symbol
        rows = (
            db.session.query(HistoricalData1D)
            .filter(HistoricalData1D.symbol == symbol)
            .order_by(HistoricalData1D.date.asc())
            .all()
        )

        if len(rows) < sma_window:
            continue

        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': r.date,
            'close': r.close_price
        } for r in rows])

        if df['close'].isnull().any():
            continue

        df["sma"] = ta.trend.sma_indicator(df['close'], window=sma_window)
        latest = df.iloc[-1]

        if pd.isna(latest['sma']):
            continue

        proximity_pct = abs(latest['close'] - latest['sma']) / latest['sma'] * 100

        if proximity_pct <= threshold_pct:
            results.append({
                "symbol": symbol,
                "close": round(latest['close'], 2),
                "sma": round(latest['sma'], 2),
                "proximity_pct": round(proximity_pct, 2)
            })

    return results
