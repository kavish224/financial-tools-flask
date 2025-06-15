from app.models import HistoricalData1D, SMAResult, StockSymbol
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
        "close": float(r["close"]),
        "sma": float(r["sma"]),
        "proximity_pct": float(r["proximity_pct"])
    }


def update_sma_results(sma_period: int, threshold_pct: float) -> int:
    """
    Updates today's SMA results.
    """
    try:
        logger.info(f"Updating SMA results for period {sma_period}, threshold {threshold_pct}%")
        results = get_stocks_near_sma(sma_period, threshold_pct)

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        inserted_count = 0

        for r in results:
            try:
                r = sanitize_result(r)

                existing = SMAResult.query.filter(
                    SMAResult.symbol == r["symbol"],
                    SMAResult.sma_period == sma_period,
                    SMAResult.date_generated >= today_start,
                    SMAResult.date_generated < tomorrow_start
                ).first()

                if existing:
                    logger.debug(f"Skipping duplicate for {r['symbol']} on {today_start.date()}")
                    continue

                entry = SMAResult(
                    symbol=r["symbol"],
                    sma_period=sma_period,
                    threshold_pct=threshold_pct,
                    close_price=r["close"],
                    sma_value=r["sma"],
                    deviation_pct=r["proximity_pct"]
                )
                db.session.add(entry)
                inserted_count += 1

            except Exception as e:
                logger.exception(f"Error processing result for {r.get('symbol', 'unknown')}", exc_info=True)
                continue

        # Clean up old results
        cutoff_datetime = datetime.utcnow() - timedelta(days=7)
        deleted = SMAResult.query.filter(
            SMAResult.sma_period == sma_period,
            SMAResult.date_generated < cutoff_datetime
        ).delete()
        logger.info(f"Deleted {deleted} old SMA results older than {cutoff_datetime.date()}")

        db.session.commit()
        logger.info(f"Inserted {inserted_count} new SMA results")
        return inserted_count

    except Exception as e:
        db.session.rollback()
        logger.exception("Error updating SMA results", exc_info=True)
        raise


def get_stocks_near_sma(sma_window: int, threshold_pct: float) -> List[Dict[str, Any]]:
    """
    Get stocks that are near their SMA.

    Args:
        sma_window (int): SMA window period.
        threshold_pct (float): Threshold percentage.

    Returns:
        List: List of stocks near SMA.
    """
    try:
        logger.info(f"Calculating stocks near SMA{sma_window} within {threshold_pct}%")
        
        symbols_with_count = (
            db.session.query(HistoricalData1D.symbol)
            .group_by(HistoricalData1D.symbol)
            .having(func.count(HistoricalData1D.id) >= sma_window)
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

                if len(rows) < sma_window:
                    continue

                df = pd.DataFrame([
                    {'date': r.date, 'close': float(r.close_price)}
                    for r in rows if r.close_price is not None
                ])

                if df.empty or df['close'].isnull().any():
                    continue

                df["sma"] = ta.trend.sma_indicator(df['close'], window=sma_window)

                latest = df.iloc[-1]

                if pd.isna(latest['sma']):
                    continue

                proximity_pct = abs(latest['close'] - latest['sma']) / latest['sma'] * 100

                if proximity_pct <= threshold_pct:
                    result = {
                        "symbol": symbol,
                        "close": round(float(latest['close']), 2),
                        "sma": round(float(latest['sma']), 2),
                        "proximity_pct": round(float(proximity_pct), 2)
                    }
                    results.append(result)

                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} symbols...")

            except Exception as e:
                logger.exception(f"Error processing symbol {symbol}", exc_info=True)
                continue

        logger.info(f"Found {len(results)} stocks near SMA{sma_window}")
        return results

    except Exception as e:
        logger.exception("Error in get_stocks_near_sma", exc_info=True)
        raise


def backfill_sma_results(sma_period: int, threshold_pct: float, days: int = 7) -> None:
    """
    Backfill SMA results for the past `days` number of days.

    Args:
        sma_period (int): SMA window period.
        threshold_pct (float): Proximity threshold.
        days (int): Number of days to backfill.
    """
    try:
        logger.info(f"Backfilling SMA results for the last {days} days")

        symbols_with_count = (
            db.session.query(HistoricalData1D.symbol)
            .group_by(HistoricalData1D.symbol)
            .having(func.count(HistoricalData1D.id) >= sma_period + days)
            .all()
        )

        for i in range(days):
            target_date = datetime.utcnow().date() - timedelta(days=i)
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            logger.info(f"Processing SMA for date: {target_date}")

            for (symbol,) in symbols_with_count:
                try:
                    rows = (
                        db.session.query(HistoricalData1D)
                        .filter(HistoricalData1D.symbol == symbol)
                        .filter(HistoricalData1D.date <= day_end)
                        .filter(HistoricalData1D.close_price.isnot(None))
                        .order_by(HistoricalData1D.date.asc())
                        .all()
                    )

                    if len(rows) < sma_period:
                        continue

                    df = pd.DataFrame([
                        {'date': r.date, 'close': float(r.close_price)}
                        for r in rows if r.date <= day_end
                    ])

                    df = df[df['date'] <= pd.Timestamp(day_end)]

                    if df.empty or df['close'].isnull().any():
                        continue

                    df["sma"] = ta.trend.sma_indicator(df['close'], window=sma_period)

                    match = df[df['date'].dt.date == target_date]

                    if match.empty:
                        continue

                    latest = match.iloc[-1]

                    if pd.isna(latest['sma']):
                        continue

                    proximity_pct = abs(latest['close'] - latest['sma']) / latest['sma'] * 100
                    if proximity_pct > threshold_pct:
                        continue

                    existing = SMAResult.query.filter(
                        SMAResult.symbol == symbol,
                        SMAResult.sma_period == sma_period,
                        SMAResult.date_generated >= day_start,
                        SMAResult.date_generated < day_end
                    ).first()

                    if existing:
                        continue

                    entry = SMAResult(
                        symbol=symbol,
                        sma_period=sma_period,
                        threshold_pct=threshold_pct,
                        close_price=round(float(latest['close']), 2),
                        sma_value=round(float(latest['sma']), 2),
                        deviation_pct=round(float(proximity_pct), 2),
                        date_generated=day_start
                    )
                    db.session.add(entry)

                except Exception as e:
                    logger.exception(f"Error processing symbol {symbol} on {target_date}", exc_info=True)
                    continue

            db.session.commit()
            logger.info(f"Finished inserting SMA results for {target_date}")

    except Exception as e:
        db.session.rollback()
        logger.exception("Error in backfill_sma_results", exc_info=True)
        raise
