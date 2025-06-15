from app.models import HistoricalData1D, SMACrossResult
from app.extensions import db
from sqlalchemy import func
import pandas as pd
import ta
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def sanitize_result(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "symbol": str(r["symbol"]),
        "sma_short": float(r["sma_short"]),
        "sma_long": float(r["sma_long"]),
        "signal": str(r["signal"])
    }


def update_sma_cross_results(short_window: int, long_window: int) -> int:
    """
    Updates today's SMA cross results.
    """
    try:
        logger.info(f"Updating SMA cross results for short_window={short_window}, long_window={long_window}")
        results = get_sma_cross_signals(short_window, long_window)

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        inserted_count = 0

        for r in results:
            try:
                r = sanitize_result(r)

                existing = SMACrossResult.query.filter(
                    SMACrossResult.symbol == r["symbol"],
                    SMACrossResult.short_window == short_window,
                    SMACrossResult.long_window == long_window,
                    SMACrossResult.date_generated >= today_start,
                    SMACrossResult.date_generated < tomorrow_start
                ).first()

                if existing:
                    logger.debug(f"Skipping duplicate for {r['symbol']} on {today_start.date()}")
                    continue

                entry = SMACrossResult(
                    symbol=r["symbol"],
                    short_window=short_window,
                    long_window=long_window,
                    sma_short=r["sma_short"],
                    sma_long=r["sma_long"],
                    signal=r["signal"]
                )

                db.session.add(entry)
                inserted_count += 1

            except Exception as e:
                logger.exception(f"Error processing result for {r.get('symbol', 'unknown')}", exc_info=True)
                continue

        # Clean up old results
        cutoff_datetime = datetime.utcnow() - timedelta(days=7)
        deleted = SMACrossResult.query.filter(
            SMACrossResult.short_window == short_window,
            SMACrossResult.long_window == long_window,
            SMACrossResult.date_generated < cutoff_datetime
        ).delete()
        logger.info(f"Deleted {deleted} old SMA cross results older than {cutoff_datetime.date()}")

        db.session.commit()
        logger.info(f"Inserted {inserted_count} new SMA cross results")
        return inserted_count

    except Exception as e:
        db.session.rollback()
        logger.exception("Error updating SMA cross results", exc_info=True)
        raise



def get_sma_cross_signals(short_window: int, long_window: int) -> List[Dict[str, Any]]:
    """
    Get SMA crossing signals for all eligible stocks.

    Args:
        short_window (int): Short period SMA window.
        long_window (int): Long period SMA window.

    Returns:
        List: List of SMA crossing signals.
    """
    try:
        logger.info(f"Calculating SMA crossing signals with short_window={short_window} and long_window={long_window}")

        symbols_with_count = (
            db.session.query(HistoricalData1D.symbol)
            .group_by(HistoricalData1D.symbol)
            .having(func.count(HistoricalData1D.id) >= long_window)
            .all()
        )

        logger.info(f"Found {len(symbols_with_count)} symbols with sufficient data")

        results = []
        processed_count = 0

        for (symbol,) in symbols_with_count:
            try:
                rows = (
                    db.session.query(HistoricalData1D)
                    .filter(HistoricalData1D.symbol == symbol)
                    .filter(HistoricalData1D.close_price.isnot(None))
                    .order_by(HistoricalData1D.date.asc())
                    .all()
                )

                if len(rows) < long_window:
                    continue

                df = pd.DataFrame([
                    {"date": r.date, "close": float(r.close_price)}
                    for r in rows if r.close_price is not None
                ])

                if df.empty or df['close'].isnull().any():
                    continue

                df["sma_short"] = ta.trend.sma_indicator(df['close'], window=short_window)
                df["sma_long"] = ta.trend.sma_indicator(df['close'], window=long_window)

                if len(df) < 2 or pd.isna(df.iloc[-1]['sma_short']) or pd.isna(df.iloc[-1]['sma_long']):
                    continue

                yesterday = df.iloc[-2]
                today = df.iloc[-1]

                if yesterday['sma_short'] < yesterday['sma_long'] and today['sma_short'] > today['sma_long']:
                    signal = "bullish"
                elif yesterday['sma_short'] > yesterday['sma_long'] and today['sma_short'] < today['sma_long']:
                    signal = "bearish"
                else:
                    continue

                result = {
                    "symbol": symbol,
                    "sma_short": round(float(today['sma_short']), 2),
                    "sma_long": round(float(today['sma_long']), 2),
                    "signal": signal
                }
                results.append(result)

                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} symbols...")

            except Exception as e:
                logger.exception(f"Error processing symbol {symbol}", exc_info=True)
                continue

        logger.info(f"Found {len(results)} SMA crossing signals")
        return results

    except Exception as e:
        logger.exception("Error in get_sma_cross_signals", exc_info=True)
        raise