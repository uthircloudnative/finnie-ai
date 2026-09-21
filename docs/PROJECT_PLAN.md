# finnie-ai - Production-Grade Multi-Agent Finance Guide

## 1. Executive Summary
Finnie is a state-of-the-art multi-agent system designed to bridge the financial literacy gap for beginner investors. Unlike generic chatbots, Finnie provides personalized, real-time, and grounded investment insights through a "Dashboard-First, Agent-Assisted" experience.

## 2. Comprehensive Requirements
### 2.1 Multi-Agent Financial Intelligence
- **Supervisor (Orchestrator)**: Uses LLM reasoning to decompose complex user queries and route them to specialized workers.
- **Financial Q&A Worker**: RAG-grounded agent using curated knowledge (Vanguard, Investor.gov, SEC).
- **Market Insights Worker**: Real-time tool-use agent (Alpha Vantage, NewsAPI) for stock trends and sentiment.
- **Portfolio Analyst Worker**: Mathematical engine calculating Sharpe ratios, diversification, and risk scores.
- **Goal Strategist Worker**: Probabilistic forecasting using Monte Carlo simulations for goals (e.g., retirement, home buying).
- **Compliance Guardian**: Mandatory post-processor ensuring all outputs contain $NFA (Not Financial Advice) disclaimers and adhere to SEC/FINRA-style safety guidelines.

### 2.2 Technical Requirements
- **Architecture**: Stateful Hub-and-Spoke pattern using **LangGraph**.
- **Grounding**: RAG pipeline with **FAISS/ChromaDB** for educational content.
- **Real-time Data**: API integrations for live market ticks and news feeds.
- **Quality**: 80%+ test coverage (Unit, Integration, E2E).
- **Observability**: Traceability of agent decisions and tool calls.

### 2.3 UI/UX: "Glass-Finance" Dashboard
- **Visuals**: Dark Mode, Glassmorphism, premium typography, and micro-animations.
- **Navigation**: Multi-tab layout (Dashboard, Portfolio, Insights, Chat).
- **Interactivity**: "What-if" sliders for goal planning and visual agent "thinking" states.

## 3. Implementation Plan (Detailed)

### Phase 1: Intelligence & Data Grounding [COMPLETED]
- **RAG Pipeline**: Implemented a vendor-agnostic infrastructure using an **Embeddings Factory** (supporting OpenAI, Azure, Hugging Face).
- **Vector Storage**: Established a hybrid ChromaDB setup (Local/Cloud) with pre-emptive storage optimization and CLI mode overrides.
- **Data Sourcing**: Successfully scraped and indexed fundamental financial definitions from Investor.gov with dynamic `ingested_date` metadata.

### Phase 2: Foundation (Skeleton) [COMPLETED]
- **Backend Infrastructure**: Initialized LangGraph `FinnieState`, implemented Supervisor routing (`RoutingDecision` with GPT-4o structured output).
- **FastAPI REST Layer**: Exposed `POST /chat` and `GET /health` endpoints; wired directly to the LangGraph `finnie_app`. CORS pre-configured for the React dev server.
- **API Models**: Created `src/models/chat.py` with `ChatRequest` / `ChatResponse` Pydantic schemas for type-safe API boundaries.
- **Agent Wiring**: Connected the Financial Q&A worker to the RAG collection (`educational_kb`) from Phase 1.
- **Frontend Scaffolding**: Initialized React/Vite + TypeScript in `frontend/`. Implemented the full "Glass-Finance" UI shell:
  - `tokens.css` + `global.css` — design system with all CSS custom properties
  - `Sidebar` with 5-tab navigation
  - **Live Chat tab** — `useChat` hook calls `POST /chat`; `ChatWindow`, `ChatInput`, `ThinkingIndicator` components; `$NFA` disclaimer footer
  - Static shells for Dashboard, Portfolio Analyst, Market Insights, and Goal Planner tabs (ready for Phase 3 agent wiring)

### Phase 3: Agent Integration & Analysis [COMPLETED]
- **Portfolio Analyst Agent** [COMPLETED]: Mathematical engine calculating live Beta, Volatility, and Diversification. Features country-specific benchmark routing (`^GSPC`, `^NSEI`, `^FTSE`, `^GSPTSE`, `^GDAXI`), All-Markets combined view, formatted 3-card AI insights, session-level client-side caching, and manual "Refresh Analysis" button to conserve LLM tokens.
- **Market Insights Agent** [COMPLETED]: Integrated Alpha Vantage live news & sentiment API with persistent 30-minute SQLite caching.
- **Goal Strategist Agent** [COMPLETED]: Vectorized 10,000-scenario Monte Carlo simulation engine cross-referenced against RAG-ingested 2026 IRS and regional tax rules (`goal_rules` collection).

### Phase 4: Hardening & Compliance [COMPLETED]
- **Compliance Guardian** [COMPLETED]: Post-processor node in LangGraph enforcing `$NFA` disclaimers across all agent outputs.
- **Observability**: Integrated LangSmith tracing and custom FastAPI `TraceContextMiddleware` header propagation.

### Phase 5: Deployment & Azure Containerization [COMPLETED]
- **Infrastructure**: Optimized multi-stage Docker build using Astral's `uv` slim base image with Gunicorn multi-worker backend server. Configured `ALLOWED_ORIGINS` CORS environment variable, `.dockerignore` bundle optimizations, and Azure App Service persistent storage (`/home/finnie.db`).

### Phase 6: Multi-Tenancy, User Authentication & Resilient Math Engine [COMPLETED]
- **User ORM & JWT Core**: Created `User` database schema in SQLite with UUID primary keys and direct `bcrypt` password hashing (Python 3.13 compatible).
- **Authentication Endpoints**: Built `POST /auth/register`, `POST /auth/login`, and `GET /auth/me` endpoints issuing stateless JWT tokens.
- **Backend API Security**: Injected `get_current_user` dependency across all FastAPI endpoints (`/portfolio`, `/dashboard`, `/chat`, `/portfolio/analysis`, `/market/news`, `/goals`), enforcing 100% tenant data isolation.
- **Frontend Auth System**: Created `AuthProvider` & `useAuth` hook, `AuthModal` component (Sign In, Registration), Sidebar profile display & Sign Out button, and `getAuthHeaders()` token injection across all custom hooks.
- **Diversification Score 3-Retry Engine**: Implemented 3-attempt exponential backoff retry loop for sector metadata calculations in `portfolio_analyst.py`. Returns `diversification_score = null` on retry failure to display an interactive retry tile button in the UI.

### Phase 7: Account Security, Recovery & Email Notification Subsystem [COMPLETED]
- **SPEC-06 Session-Scoped Authentication & Login Gate**: Mandatory gate mode for unauthenticated users, tab-isolated sessionStorage token lifecycle, and legacy storage cleansing.
- **SPEC-07 Goodbye Confirmation & Session Termination**: Dedicated confirmation page upon sign-out with user reassurance and clean re-login state machine.
- **SPEC-08 Password Recovery via OTP & Security Audit Trail**: Cryptographic 6-digit OTP generation, sliding rate limiting (3 requests/15m), strict 3-attempt brute force capping (`status = "FAILED"`), dual-origin forensic audit logging (`password_reset_audits`), automatic database migration, and active session revocation (`token_version`).
- **SPEC-09 Reusable Email Notification Engine**: Swappable transport layer (`BaseEmailProvider`) featuring REST API integration with Mailgun, local console fallback, responsive glassmorphic HTML templates with inlined CSS, and zero-exposure privacy protection.

## 4. RAG Integration Matrix (Learning Reference)


| UI Tab / Feature | RAG Required? | Data Sources | Implementation Summary |
| :--- | :--- | :--- | :--- |
| **Q&A Chatbot** | **YES** | Investor.gov, Textbooks | **Static Pipeline**: Scrape -> Chunk -> Index in ChromaDB. Agent uses `similarity_search` to define terms. |
| **Market Insights** | **YES** | NewsAPI, SEC Filings | **Transient Pipeline**: Fetch live news -> In-memory indexing -> Summary. Results expire after session. |
| **Portfolio Analyst** | **AUGMENTED** | Academic Papers | **Reference Pipeline**: Math is done locally; RAG is used to provide theoretical context (e.g., "Why diversification matters"). |
| **Goal Planning** | **YES** | IRS Tax Codes | **Validation Pipeline**: Agent queries tax limits/rules during simulation to ensure legal accuracy. |
| **Compliance** | **YES** | SEC Safety Guides | **Guardian Pipeline**: Check every final answer against SEC safety docs before user delivery. |

---

## 5. Portfolio Analyst — Correctness Fixes & Future Roadmap

### 5.1 Correctness Fixes Shipped (Sep 2026)

#### Fix 1 — Beta/Volatility Array Misalignment [FIXED]
**Problem:** `display_betas` was built from `search_symbols` (all tickers) while `display_vols` filtered for only symbols present in yfinance returns. If any ticker returned no data, the two arrays had different lengths, producing incorrect averages silently.

**Fix:** Both arrays are now built exclusively from `valid_symbols` — a single guarded list of symbols that exist in **both** `betas` and `volatilities` dicts. Any ticker that yfinance could not price is excluded cleanly and transparently instead of corrupting the averages.

#### Fix 2 — Real Diversification Score via HHI [FIXED]
**Problem:** `diversification_score` was hardcoded to `7` for every portfolio regardless of actual composition.

**Fix:** Score is now computed using the **Herfindahl-Hirschman Index (HHI)** on sector weights:
1. Fetch `sector` metadata for each valid holding via `yf.Ticker().info`
2. Compute `HHI = Σ(sector_weight²)` — ranges from `1/n` (perfectly spread) to `1.0` (single sector)
3. Normalise to a `0–10` scale: `score = 10 × (1 − (HHI − HHI_min) / (1 − HHI_min))`
4. Result: a 1-stock tech portfolio might score `0.0`; a 10-stock multi-sector portfolio might score `9.5`

---

### 5.2 Future Use Case Roadmap — Portfolio Analyst

#### 🔵 UC-PA-1: Full Portfolio Health Dashboard
**Priority:** High | **Effort:** Medium

Extend Stage 2 (Math Engine) to compute additional metrics from the already-fetched yfinance data:

| Metric | Formula | Value |
| :--- | :--- | :--- |
| **Sharpe Ratio** | `(portfolio_return − risk_free_rate) / portfolio_volatility` | Rewards-per-unit-risk |
| **Max Drawdown** | `min(cumulative_returns)` over trailing 1 year | Worst-case loss scenario |
| **Correlation Matrix** | `returns.corr()` across all holdings | Identifies hidden concentration |
| **Sector Breakdown %** | Weighted by market value per sector | Visual concentration heatmap |
| **Benchmark Return** | Portfolio return vs `^GSPC` / `^NSEI` / `^FTSE` | Are you beating the market? |

All inputs exist in the current yfinance fetch — no new API calls needed.

---

#### 🔵 UC-PA-2: What-If / Trade Simulator
**Priority:** High | **Effort:** Medium

Allow the user to input a proposed trade (e.g., "Add 10 NVDA") and get a **before vs after** comparison of key risk metrics — Beta, Volatility, Sharpe Ratio, Diversification Score — without executing the trade. Useful for daily investment decision-making.

**User flow:**
1. User types: *"What happens if I add 10 shares of NVDA?"*
2. Agent computes metrics for current portfolio
3. Agent computes metrics for portfolio + proposed trade
4. LLM synthesises the delta: "Adding NVDA increases your Tech concentration from 40% to 55% and raises Beta from 1.1 to 1.3"

---

#### 🔵 UC-PA-3: Daily Morning Brief (Proactive Agent)
**Priority:** High | **Effort:** Medium-High

Instead of requiring the user to manually trigger analysis, a scheduled or on-login proactive brief:
1. Computes delta since the last analysis (price moves, vol changes)
2. Flags any holding with `abs(daily_move) > 3%`
3. Checks if any stock has an earnings announcement in the next 7 days (yfinance `calendar`)
4. Pulls Alpha Vantage news only for flagged tickers (reduces API consumption)
5. Returns a concise "3 things to watch today" summary

---

#### 🔵 UC-PA-4: Technical Signal Layer
**Priority:** Medium | **Effort:** Medium

Add classic technical indicators computed on the same 1-year OHLCV data already fetched:

| Signal | Interpretation |
| :--- | :--- |
| **RSI (14-day)** | `> 70` = overbought, `< 30` = oversold |
| **50d / 200d MA Crossover** | Golden Cross (bullish) / Death Cross (bearish) |
| **Bollinger Band position** | Price at upper band = potential reversal |
| **Volume anomaly** | Volume > 2× 20-day avg = unusual activity |

LLM then interprets the combination of signals, not each in isolation.

---

#### 🟡 UC-PA-5: Rebalancing Advisor
**Priority:** Medium | **Effort:** High

User defines a target allocation (e.g., 60% equities, 20% bonds, 20% international). Agent:
1. Computes actual allocation from live prices
2. Calculates drift from target
3. Recommends specific buy/sell share counts to rebalance
4. Estimates short-term vs long-term capital gains tax impact using `added_date` from SQLite

---

#### 🟡 UC-PA-6: Multi-Currency P&L Tracker
**Priority:** Medium | **Effort:** Medium

For portfolios spanning USD, INR, GBP, EUR:
1. Fetch FX rates via yfinance (`USDINR=X`, `USDGBP=X`)
2. Convert all positions to user's base currency
3. Decompose P&L into **equity return** vs **currency return**
4. Flag if FX headwinds are eroding gains (e.g., INR depreciation hurting Indian holdings for a USD-base investor)

