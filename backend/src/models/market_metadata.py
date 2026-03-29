from sqlalchemy import Column, String, Integer
from src.database import Base

class MarketExchange(Base):
    """
    Master table for global stock exchanges.
    Maps human-readable names to API-specific suffixes.
    """
    __tablename__ = "market_exchanges"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    country_name  = Column(String, nullable=False)  # e.g. "India"
    country_code  = Column(String, nullable=False)  # e.g. "IN"
    exchange_name = Column(String, nullable=False)  # e.g. "National Stock Exchange"
    exchange_code = Column(String, nullable=False)  # e.g. "NSE"
    av_suffix     = Column(String, default="")      # e.g. ".NSE"
    yf_suffix     = Column(String, default="")      # e.g. ".NS"

    def __repr__(self) -> str:
        return f"<MarketExchange {self.exchange_code} ({self.country_name})>"
