"""
portfolio.py — SQLAlchemy ORM model for user holdings
======================================================
Stores each holding as a (user_id, ticker, shares) row.
Weights are NOT stored — always computed at query time from live market prices.
"""
from datetime import date
from sqlalchemy import Column, String, Integer, Date, Float
from src.database import Base


class Holding(Base):
    """One row = one ticker position for one user."""
    __tablename__ = "holdings"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(String, nullable=False, index=True)  # e.g. "user_1"
    ticker   = Column(String, nullable=False)               # e.g. "AAPL"
    shares   = Column(Float, nullable=False)                # e.g. 10.5
    country  = Column(String, default="US")                 # e.g. "US", "IN", "UK"
    exchange = Column(String, default="NYSE")               # e.g. "NSE", "BSE", "NASDAQ"
    added_date = Column(Date, default=date.today)

    def __repr__(self) -> str:
        return f"<Holding user={self.user_id} ticker={self.ticker} shares={self.shares} country={self.country}>"
