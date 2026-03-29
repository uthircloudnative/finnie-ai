import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.models.portfolio import Holding
from src.models.market_metadata import MarketExchange
from langsmith import traceable

@traceable(name="Dashboard Logic Engine", run_type="chain")
def build_dashboard_payload(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Constructs the dynamic global wealth dashboard payload.
    Groups user holdings by geography, maps to Yahoo Finance symbols,
    and returns a clean JSON summary mapping total wealth and 24h P&L.
    """
    # 1. Fetch user holdings
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    if not holdings:
        return {"total_assets": 0, "total_countries": 0, "portfolios": {}}

    # 2. Map the market Exchange suffixes from SQLite
    exchanges = db.query(MarketExchange).all()
    exchange_map = {ex.exchange_code: ex.yf_suffix for ex in exchanges}

    # Prepare data structures
    symbols_to_fetch = []
    symbol_to_holding = {}
    
    # 3. Build unique bucket objects for each distinct country
    countries_found = set(h.country for h in holdings)
    portfolios = {
        c: {
            "country_code": c,
            "total_value": 0.0,
            "daily_pnl": 0.0,
            "daily_pnl_percent": 0.0,
            "assets": []
        }
        for c in countries_found
    }

    # 4. Map user holdings strictly to yfinance query payloads
    for h in holdings:
        suffix = exchange_map.get(h.exchange, "")
        yf_symbol = f"{h.ticker}{suffix}"
        symbols_to_fetch.append(yf_symbol)
        
        # We store the reference so we can calculate after fetching
        symbol_to_holding[yf_symbol] = {
            "ticker": h.ticker,
            "shares": h.shares,
            "country": h.country
        }

    # 5. Fetch Bulk Live Market Data (5 days avoids weekend gaps)
    print(f"[Dashboard Engine] 🌐 Fetching live data for {symbols_to_fetch}")
    try:
        raw_data = yf.download(symbols_to_fetch, period="5d", progress=False)
        
        # Robust column access for Close price
        if isinstance(raw_data.columns, pd.MultiIndex):
            close_data = raw_data['Close']
        else:
            close_data = raw_data['Close']
            
    except Exception as e:
        print(f"[Dashboard Engine] ❌ External API Error: {e}")
        # Return graceful failure
        return {"total_assets": len(holdings), "total_countries": len(countries_found), "portfolios": portfolios, "error": True}

    # 6. Crunch Math & Populate Geography Buckets
    for yf_symbol in symbols_to_fetch:
        holding_meta = symbol_to_holding[yf_symbol]
        c = holding_meta["country"]
        shares = holding_meta["shares"]
        
        current_price = 0.0
        prev_close = 0.0
        
        try:
            # We must isolate the series for the specific ticker
            # If there's only one ticker fetched, yfinance returns a 1D Series, not a 2D DataFrame
            if len(symbols_to_fetch) == 1:
                series = close_data.dropna()
            else:
                if yf_symbol in close_data.columns:
                    series = close_data[yf_symbol].dropna()
                else:
                    raise KeyError("Symbol dropped by yfinance")
            
            if len(series) >= 2:
                current_price = float(series.iloc[-1])
                prev_close = float(series.iloc[-2])
            elif len(series) == 1:
                # Edge case where symbol just listed
                current_price = float(series.iloc[-1])
                prev_close = current_price
                
        except Exception as e:
            print(f"[Dashboard Engine] ⚠️ Data missing for {yf_symbol}: {e}")
            pass # Fails safely leaving prices at 0.0
            
        asset_pnl = (current_price - prev_close) * shares
        asset_pnl_percent = ((current_price / prev_close) - 1.0) * 100 if prev_close else 0.0
        total_value = current_price * shares
        
        # Aggregate to country bucket
        portfolios[c]["total_value"] += total_value
        portfolios[c]["daily_pnl"] += asset_pnl
        
        # Append line item
        portfolios[c]["assets"].append({
            "ticker": holding_meta["ticker"],
            "shares": shares,
            "current_price": round(current_price, 2),
            "prev_close": round(prev_close, 2),
            "asset_pnl": round(asset_pnl, 2),
            "asset_pnl_percent": round(asset_pnl_percent, 2),
            "total_value": round(total_value, 2)
        })

    # 7. Finalize aggregate percentage calculations
    for c in portfolios.keys():
        total_pnl = portfolios[c]["daily_pnl"]
        base_value = portfolios[c]["total_value"] - total_pnl
        if base_value > 0:
            portfolios[c]["daily_pnl_percent"] = round((total_pnl / base_value) * 100, 2)
        else:
            portfolios[c]["daily_pnl_percent"] = 0.0
            
        portfolios[c]["total_value"] = round(portfolios[c]["total_value"], 2)
        portfolios[c]["daily_pnl"] = round(portfolios[c]["daily_pnl"], 2)

    return {
        "total_assets": len(holdings),
        "total_countries": len(countries_found),
        "portfolios": portfolios
    }
