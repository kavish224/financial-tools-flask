from app.extensions import db

class StockSymbol(db.Model):
    __tablename__ = 'StockSymbol'  # Match actual table name

    id = db.Column(db.Integer, primary_key=True)
    isin = db.Column(db.String, unique=True, nullable=False)
    symbol = db.Column(db.String, unique=True, nullable=False)  # FK target
    company_name = db.Column('companyName', db.Text, nullable=True)
    industry = db.Column('industry', db.Text, nullable=True)
    series = db.Column('series', db.String(10), nullable=True)
    created_at = db.Column('createdAt', db.DateTime(timezone=True), server_default=db.func.current_timestamp())
    updated_at = db.Column('updatedAt', db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    historical_data = db.relationship(
        'HistoricalData1D',
        back_populates='stock_symbol',
        lazy=True,
        primaryjoin='StockSymbol.symbol == foreign(HistoricalData1D.symbol)'
    )


class HistoricalData1D(db.Model):
    __tablename__ = 'HistoricalData1D'  # Match actual table name

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String, db.ForeignKey('StockSymbol.symbol'), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    open_price = db.Column('openPrice', db.Float, nullable=True)
    close_price = db.Column('closePrice', db.Float, nullable=True)
    high_price = db.Column('highPrice', db.Float, nullable=True)
    low_price = db.Column('lowPrice', db.Float, nullable=True)
    volume = db.Column(db.BigInteger, nullable=True)
    open_interest = db.Column('openInterest', db.BigInteger, nullable=True)
    created_at = db.Column('createdAt', db.DateTime(timezone=True), server_default=db.func.current_timestamp())

    stock_symbol = db.relationship(
        'StockSymbol',
        back_populates='historical_data',
        lazy=True
    )
