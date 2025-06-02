# app/models.py
from app.extensions import db

class StockSymbol(db.Model):
    __tablename__ = 'stock_symbols'

    isin = db.Column(db.String(20), primary_key=True, unique=True, nullable=False)
    company_name = db.Column('Company Name', db.Text, nullable=True)
    industry = db.Column('Industry', db.Text, nullable=True)
    symbol = db.Column('Symbol', db.String(10), nullable=False)
    series = db.Column('Series', db.String(10), nullable=True)

    # Use back_populates to define the reverse relationship
    historical_data = db.relationship('HistoricalData1D', back_populates='stock_symbol', lazy=True)


class HistoricalData1D(db.Model):
    __tablename__ = 'historical_data_1d'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), db.ForeignKey('stock_symbols.isin'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Numeric, nullable=True)
    close_price = db.Column(db.Numeric, nullable=True)
    high_price = db.Column(db.Numeric, nullable=True)
    low_price = db.Column(db.Numeric, nullable=True)
    volume = db.Column(db.BigInteger, nullable=True)

    # Use back_populates to define the reverse relationship
    stock_symbol = db.relationship('StockSymbol', back_populates='historical_data', lazy=True)
