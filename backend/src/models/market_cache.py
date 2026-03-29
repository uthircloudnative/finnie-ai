from sqlalchemy import Column, String, Integer, DateTime, Text
from src.database import Base
import datetime
import json

class MarketCache(Base):
    """
    SQLite-based cache for expensive API calls (Market News, Sentiment).
    Key format: 'NEWS:<TICKERS_JOINED>' or 'SENTIMENT:<TICKER>'
    """
    __tablename__ = "market_cache"

    key        = Column(String, primary_key=True)
    data_json  = Column(Text, nullable=False)
    timestamp  = Column(DateTime, default=datetime.datetime.utcnow)

    def is_expired(self, ttl_minutes: int = 30) -> bool:
        """Checks if the cached data is older than the TTL."""
        now = datetime.datetime.utcnow()
        age = now - self.timestamp
        return age.total_seconds() > (ttl_minutes * 60)

    @property
    def data(self) -> dict:
        return json.loads(self.data_json)

    @data.setter
    def data(self, value: dict):
        self.data_json = json.dumps(value)

    def __repr__(self) -> str:
        return f"<MarketCache key={self.key} age={datetime.datetime.utcnow() - self.timestamp}>"
