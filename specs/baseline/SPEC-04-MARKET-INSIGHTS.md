# Baseline Spec: SPEC-04 — Market Insights & Real-Time Sentiment

> **Status**: 🟢 **VERIFIED & IN PRODUCTION**  
> **Scope**: Real-Time Financial News, Sentiment Analysis, Rate-Limit Caching, LangGraph Agent

---

## 1. 🎯 Business Objective & Domain Rules
- **Problem**: Retail investors face constant market noise across financial media. They require a concise, synthesized daily market pulse that correlates breaking global headlines directly to their individual portfolio holdings.
- **Sentiment Classification**: Raw news sentiment scores must be distilled into actionable, intuitive signals:
  - 📈 **Bullish**: Positive sentiment score ($\ge +0.15$)
  - 📉 **Bearish**: Negative sentiment score ($\le -0.15$)
  - ➡️ **Neutral**: Neutral range ($-0.15 < \text{score} < +0.15$)
- **Exchange Ticker Normalization**: Holdings across global exchanges must be properly mapped to external provider format (e.g. Indian NSE tickers mapped to `.NS` suffix).
- **API Rate-Limit Protection**: External financial API calls (Alpha Vantage) are constrained by tight query limits. The agent must enforce a **30-minute persistent caching layer** in SQLite to avoid rate-limiting errors and latency spikes.
- **Compliance Enforcement**: Every market sentiment summary must conclude with the mandatory `$NFA` disclaimer.

---

## 2. 🔌 Technical Contracts & Endpoints

### A. API Endpoints
- `GET /market/news`: Fetches or generates a consolidated market pulse based on the user's holdings.
  - **Query Params**: `limit: int = 5`
  - **Response Payload**:
    ```python
    class NewsItem(BaseModel):
        title: str
        url: str
        source: str
        summary: str
        overall_sentiment_label: str    # "Bullish", "Bearish", "Neutral"
        overall_sentiment_score: float
        time_published: str

    class MarketNewsResponse(BaseModel):
        pulse_summary: str              # AI-synthesized market pulse
        sentiment: str                  # Aggregate: "Bullish" | "Bearish" | "Neutral"
        articles: List[NewsItem]
        cached: bool                    # Indicates if served from SQLite cache
        disclaimer: str
    ```

### B. Persistent Cache Model (`backend/src/models/market_cache.py`)
```python
class MarketCache(Base):
    __tablename__ = "market_cache"
    cache_key   = Column(String, primary_key=True)  # e.g., "NEWS:AAPL,MSFT,NVDA"
    payload     = Column(Text, nullable=False)      # JSON-serialized response
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def is_expired(self, ttl_minutes: int = 30) -> bool:
        # Defensively normalizes naive SQLite timestamps to UTC
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - created > timedelta(minutes=ttl_minutes)
```

### C. Agent Topology & LangGraph Wiring
- **Node Function**: Synchronous `def market_insights_node(state: FinnieState) -> dict`.
- **Flow**:
  1. Inspect SQLite `market_cache` for existing `NEWS:<TICKERS>` entry.
  2. If entry exists and `not entry.is_expired(30)`, return cached payload.
  3. If missing or expired, fetch live articles from Alpha Vantage `NEWS_SENTIMENT`.
  4. Synthesize overall portfolio sentiment pulse via LLM.
  5. Save new result to `market_cache`.
  6. Route to `compliance_guardian_node`.
- **Graph Path**: `supervisor_node` ➔ `market_insights_node` ➔ `compliance_guardian_node` ➔ `END`.

---

## 3. 🖥️ Frontend Architecture & Presentation
- **Hook**: `useMarketInsights.ts`:
  - Fetches and manages market pulse news, handles refresh actions, and tracks loading/error states.
- **Component**: `MarketInsights.tsx`:
  - Glassmorphic hero summary card with sentiment badge (Bullish/Bearish/Neutral).
  - Chronological article stream with domain source tags, timestamps, and article sentiment pills.
  - Direct outbound article links opening safely in new browser tabs (`target="_blank" rel="noopener noreferrer"`).

---

## 4. ✅ Verified Acceptance Criteria (Regression Baseline)
- [x] **AC-1**: Requesting `/market/news` within 30 minutes of a previous fetch returns cached results with `cached: true` without hitting Alpha Vantage.
- [x] **AC-2**: `MarketCache.is_expired()` correctly computes expiration against UTC without raising `TypeError: can't subtract offset-naive and offset-aware datetimes`.
- [x] **AC-3**: External API rate limit errors degrade gracefully into a cached or informative fallback summary rather than raising a 500 error.
- [x] **AC-4**: All returned responses include the `$NFA` disclaimer.
- [x] **AC-5**: Offline unit tests in `test_unit.py` (`test_market_cache_expiration_fresh`, `test_market_cache_expiration_stale`) pass cleanly.
