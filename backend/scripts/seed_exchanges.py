from src.database import get_db, init_db
from src.models.market_metadata import MarketExchange
from sqlalchemy.orm import Session

# ── Core Global Exchanges ────────────────────────────────────
CORE_EXCHANGES = [
    # US Markets (Default)
    {"country_name": "USA", "country_code": "US", "exchange_name": "New York Stock Exchange", "exchange_code": "NYSE", "av_suffix": "", "yf_suffix": ""},
    {"country_name": "USA", "country_code": "US", "exchange_name": "NASDAQ", "exchange_code": "NASDAQ", "av_suffix": "", "yf_suffix": ""},
    
    # Indian Markets
    {"country_name": "India", "country_code": "IN", "exchange_name": "National Stock Exchange", "exchange_code": "NSE", "av_suffix": ".NSE", "yf_suffix": ".NS"},
    {"country_name": "India", "country_code": "IN", "exchange_name": "Bombay Stock Exchange", "exchange_code": "BSE", "av_suffix": ".BSE", "yf_suffix": ".BO"},
    
    # UK Markets
    {"country_name": "UK", "country_code": "GB", "exchange_name": "London Stock Exchange", "exchange_code": "LSE", "av_suffix": ".L", "yf_suffix": ".L"},
    
    # Canadian Markets
    {"country_name": "Canada", "country_code": "CA", "exchange_name": "Toronto Stock Exchange", "exchange_code": "TSX", "av_suffix": ".TRT", "yf_suffix": ".TO"},
    
    # European Markets
    {"country_name": "Germany", "country_code": "DE", "exchange_name": "XETRA", "exchange_code": "XETRA", "av_suffix": ".DEX", "yf_suffix": ".DE"},
    {"country_name": "France", "country_code": "FR", "exchange_name": "Euronext Paris", "exchange_code": "PARIS", "av_suffix": ".PAR", "yf_suffix": ".PA"},
]

def seed():
    """Populate the market_exchanges table with core global data."""
    print("--- SEEDING MARKET METADATA ---")
    init_db()  # Ensure tables exist
    
    db: Session = next(get_db())
    
    # Clear existing data to avoid duplicates
    db.query(MarketExchange).delete()
    
    for ex in CORE_EXCHANGES:
        row = MarketExchange(**ex)
        db.add(row)
        print(f"Added: {ex['exchange_name']} ({ex['country_name']})")
        
    db.commit()
    print("--- SEEDING COMPLETE ---")

if __name__ == "__main__":
    seed()
