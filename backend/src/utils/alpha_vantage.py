import os
import httpx
import logging
from typing import List, Dict, Any
from langsmith import traceable

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """
    Client for interacting with Alpha Vantage Intelligence APIs.
    Specifically focuses on News Sentiment for Market Insights.
    """
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not found in environment!")

    @traceable(name="Alpha Vantage API", run_type="tool")
    async def fetch_news_sentiment(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Fetches news articles and sentiment scores for a list of tickers.
        """
        if not self.api_key:
            return {"error": "API Key missing", "feed": []}

        # Join tickers for the API call (e.g. AAPL,TSLA)
        ticker_str = ",".join(tickers)
        
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker_str,
            "apikey": self.api_key,
            "sort": "LATEST",
            "limit": 50
        }

        async with httpx.AsyncClient() as client:
            try:
                print(f"[FINNIE-AI] 🌐 GET {self.BASE_URL}?tickers={ticker_str}")
                response = await client.get(self.BASE_URL, params=params, timeout=12.0)
                print(f"[FINNIE-AI] 📡 Response Status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                
                # Check for Alpha Vantage specific error messages (they return 200 for internal errors)
                if "Information" in data:
                    logger.error(f"Alpha Vantage Info: {data['Information']}")
                    return {"error": data["Information"], "feed": []}
                
                if "Note" in data:
                    logger.warning(f"Alpha Vantage Rate Limit: {data['Note']}")
                    return {"error": "Rate limit exceeded (Free tier)", "feed": []}

                return data
            except Exception as e:
                logger.error(f"Error fetching AV news: {e}")
                return {"error": str(e), "feed": []}
