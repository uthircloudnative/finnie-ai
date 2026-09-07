import os
from datetime import datetime, timezone
from typing import List, Dict, Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.state import FinnieState
from src.models.market_cache import MarketCache
from src.utils.alpha_vantage import AlphaVantageClient

# ── Configuration ──────────────────────────────────────────
CACHE_TTL_MINUTES = 30
MAX_NEWS_ITEMS = 5 # Limit items per ticker for LLM context

def market_insights_node(state: FinnieState) -> dict:
    """
    Market Insights Agent - Analyzes REAL news and sentiment for the user's holdings.
    Uses a 30-minute SQLite cache to minimize Alpha Vantage API consumption.
    """
    holdings = state.get("portfolio_data", [])
    if not holdings:
        return {
            "messages": [AIMessage(content="You haven't added any stocks yet! Add some in 'My Holdings' so I can track the news for you.")],
            "next_step": None
        }

    # Extract tickers (unique list)
    tickers = list(set(h.get("ticker", "").upper() for h in holdings if h.get("ticker")))
    
    # 1. Check Cache vs Real API
    db: Session = SessionLocal()
    client = AlphaVantageClient()
    all_news_feed = []
    
    try:
        # We fetch news in 1 or 2 batches depending on what's in cache
        cache_key = f"NEWS:{','.join(sorted(tickers))}"
        cached_entry = db.query(MarketCache).filter(MarketCache.key == cache_key).first()
        
        if cached_entry and not cached_entry.is_expired(CACHE_TTL_MINUTES):
            print(f"[FINNIE-AI] 📥 CACHE HIT: Using stored news for {tickers}")
            raw_data = cached_entry.data
        else:
            print(f"[FINNIE-AI] 🌐 CACHE MISS: Fetching live data for {tickers} from Alpha Vantage...")
            raw_data = client.fetch_news_sentiment(tickers)
            
            # Update cache if we got a valid response (not an error)
            if "feed" in raw_data and not raw_data.get("error"):
                if cached_entry:
                    cached_entry.data = raw_data
                    cached_entry.timestamp = datetime.now(timezone.utc)
                else:
                    new_cache = MarketCache(key=cache_key)
                    new_cache.data = raw_data
                    db.add(new_cache)
                db.commit()

        all_news_feed = raw_data.get("feed", [])
        error_msg = raw_data.get("error")

    finally:
        db.close()

    # 2. Synthesize using LLM
    print(f"[FINNIE-AI] 🧠 Synthesizing report for {len(all_news_feed)} news items...")
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0.3)

    # Prepare context for the LLM
    # We only take the top several relevant items to keep the prompt clean
    context_snippets = []
    for item in all_news_feed[:15]: # Top 15 total
        sentiment = item.get("ticker_sentiment", [])
        # Filter for the user's specific tickers in the feed
        relevant_sentiment = [s for s in sentiment if s.get("ticker") in tickers]
        if relevant_sentiment:
            score = relevant_sentiment[0].get("ticker_sentiment_label", "Neutral")
            context_snippets.append(f"- {item['title']} (Ticker Sentiment: {score})")

    context_str = "\n".join(context_snippets) if context_snippets else "No recent news found for these specific tickers."
    
    if error_msg:
        context_str += f"\n\n(Note: There was an API issue: {error_msg})"

    system_prompt = (
        "You are Finnie, a sophisticated financial analyst. Your goal is to provide a "
        "concise 'Market Pulse' report for a user's stock portfolio.\n\n"
        "Instructions:\n"
        "1. Group the insights by sector or market if possible.\n"
        "2. Use emojis to indicate sentiment (📈 Bullish, 📉 Bearish, ➡️ Neutral).\n"
        "3. Focus on ONLY the tickers provided: " + ", ".join(tickers) + "\n"
        "4. Be conversational but grounded in the news provided.\n"
        "5. Keep it to 2-3 short paragraphs maximum."
    )

    human_query = (
        f"Here is the latest news feed for my holdings:\n\n{context_str}\n\n"
        "Please provide my personalized Market Pulse report."
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_query)
    ])

    return {
        "messages": [AIMessage(content=response.content)],
        "next_step": None
    }
