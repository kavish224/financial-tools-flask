import pandas as pd
from sqlalchemy import text
from app.services.database import db_session

def calculate_sma_crossings():
    """
    Calculate SMA50 crossings for all stocks and include stock names in the results.
    """
    query = text("""
        SELECT hd.symbol, hd.date, hd.close_price, ss."Company Name" AS company_name
        FROM historical_data_1d hd
        JOIN stock_symbols ss ON hd.symbol = ss.isin
        ORDER BY hd.symbol, hd.date
    """)
    
    data = pd.read_sql(query, db_session.bind)
    
    if data.empty:
        return []
    
    results = []
    grouped = data.groupby("symbol")
    
    for group in grouped:
        group = group.sort_values("date")
        group["SMA50"] = group["close_price"].rolling(window=50).mean()
        group["Crossings"] = 0
        
        cross_below_indexes = (group["close_price"].shift(1) > group["SMA50"].shift(1)) & (group["close_price"] < group["SMA50"])
        cross_above_indexes = (group["close_price"].shift(1) < group["SMA50"].shift(1)) & (group["close_price"] > group["SMA50"])
        
        group.loc[cross_below_indexes, "Crossings"] = -1
        group.loc[cross_above_indexes, "Crossings"] = 1
        
        crossings = group[group["Crossings"] != 0]
        for _, row in crossings.iterrows():
            results.append({
                "symbol": row["symbol"],
                "stock_name": row["company_name"],
                "date": row["date"].strftime("%Y-%m-%d"),
                "price": round(float(row["close_price"]), 2),
                "sma50": round(float(row["SMA50"]), 2),
                "crossing": "above" if row["Crossings"] == 1 else "below"
            })
    
    return results


def calculate_golden_cross():
    """
    Calculate Golden Cross and Death Cross for all stocks and include stock names in the results.
    """
    query = text("""
        SELECT hd.symbol, hd.date, hd.close_price, ss."Company Name" AS company_name
        FROM historical_data_1d hd
        JOIN stock_symbols ss ON hd.symbol = ss.isin
        ORDER BY hd.symbol, hd.date
    """)

    data = pd.read_sql(query, db_session.bind)

    if data.empty:
        return []

    results = []
    grouped = data.groupby("symbol")

    for symbol, group in grouped:
        group = group.sort_values("date")
        group["SMA50"] = group["close_price"].rolling(window=50).mean()
        group["SMA200"] = group["close_price"].rolling(window=200).mean()
        group["Crossings"] = 0

        cross_below_indexes = (group["SMA50"].shift(1) > group["SMA200"].shift(1)) & (group["SMA50"] < group["SMA200"])
        cross_above_indexes = (group["SMA50"].shift(1) < group["SMA200"].shift(1)) & (group["SMA50"] > group["SMA200"])

        group.loc[cross_below_indexes, "Crossings"] = -1
        group.loc[cross_above_indexes, "Crossings"] = 1

        crossings = group[group["Crossings"] != 0]
        for _, row in crossings.iterrows():
            results.append({
                "symbol": row["symbol"],
                "stock_name": row["company_name"],
                "date": row["date"].strftime("%Y-%m-%d"),
                "price": round(float(row["close_price"]), 2),
                "sma50": round(float(row["SMA50"]), 2) if pd.notna(row["SMA50"]) else None,
                "sma200": round(float(row["SMA200"]), 2) if pd.notna(row["SMA200"]) else None,
                "crossing": "golden" if row["Crossings"] == 1 else "death"
            })

    return results
