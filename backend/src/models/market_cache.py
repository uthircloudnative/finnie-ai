from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, DateTime, Text
from src.database import Base


class MarketCache(Base):
    """
    SQLite-based cache for expensive API calls (Market News, Sentiment).
    Key format: 'NEWS:<TICKERS_JOINED>' or 'SENTIMENT:<TICKER>'
    """
    __tablename__ = "market_cache"

    key        = Column(String, primary_key=True)
    data_json  = Column(Text, nullable=False)
    timestamp  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def is_expired(self, ttl_minutes: int = 30) -> bool:
        """Checks if the cached data is older than the TTL."""
        now = datetime.now(timezone.utc)
        ts = self.timestamp
        if ts is None:
            return True
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = now - ts
        return age.total_seconds() > (ttl_minutes * 60)

    @property
    def data(self) -> dict:
        return json.loads(self.data_json)

    @data.setter
    def data(self, value: dict):
        self.data_json = json.dumps(value)

    def __repr__(self) -> str:
        now = datetime.now(timezone.utc)
        ts = self.timestamp
        if ts is not None and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age_str = str(now - ts) if ts else "unknown"
        return f"<MarketCache key={self.key} age={age_str}>"

