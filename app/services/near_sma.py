from flask import Flask
from flask_cors import CORS
from flask_apscheduler import APScheduler
from app.routes.analytics import sma_nearby
from app.models import HistoricalData1D
from app.extensions import db, migrate
from app.routes import register_routes
from config import Config
import pandas as pd
import ta
from app.models import db, SMAResult
from app.services.near_sma import get_stocks_near_sma

def update_sma_results(sma_period, threshold_pct):
    results = get_stocks_near_sma(sma_period, threshold_pct)
    
    SMAResult.query.filter_by(sma_period=sma_period).delete()

    for r in results:
        entry = SMAResult(
            symbol=r["symbol"],
            sma_period=sma_period,
            threshold_pct=threshold_pct,
            close_price=r["close"],
            sma_value=r["sma"],
            deviation_pct=r["proximity_pct"]
        )
        db.session.add(entry)
    db.session.commit()

def get_stocks_near_sma(sma_window, threshold_pct):
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
