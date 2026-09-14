# Finnie AI — Code Review & Improvement Roadmap

> **Reviewer:** Antigravity AI Lead Engineer  
> **Review Date:** July 26, 2026  
> **Codebase Version:** v0.1.0  
> **Stack:** Python 3.13 · FastAPI · LangGraph · React/TypeScript · SQLite · ChromaDB  
> **Overall Score: 6.5 / 10** — Excellent foundation, significant gaps to close before production.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Assessment](#1-architecture-assessment)
3. [Security Review](#2-security-review)
4. [Financial Math Correctness](#3-financial-math-correctness)
5. [Agent & LangGraph Implementation](#4-agent--langgraph-implementation)
6. [Database & Data Layer](#5-database--data-layer)
7. [API Design](#6-api-design)
8. [Frontend Review](#7-frontend-review)
9. [DevOps & Infrastructure](#8-devops--infrastructure)
10. [Testing Coverage](#9-testing-coverage)
11. [Prioritized Improvement Roadmap](#10-prioritized-improvement-roadmap)
12. [Business Perspective](#11-business-perspective)
13. [What's Done Exceptionally Well](#12-whats-done-exceptionally-well)
14. [Changelog](#changelog)

---

## Executive Summary

Finnie AI is a well-architected, thoughtfully designed **multi-agent financial assistant** demonstrating strong engineering fundamentals for a Phase 1 prototype. The supervisor-routing pattern is correctly implemented, the RAG pipeline is functional, and the frontend UX is polished.

However, there are **critical security gaps**, **correctness issues** in financial math, a **broken async/sync contract** across agents, and **production-readiness gaps** that must be addressed before any real-user deployment.

---

## 1. Architecture Assessment

**Score: 8 / 10** — Well-designed, one structural flaw.

### ✅ Strengths

- **Supervisor-Router Pattern** is correctly implemented in `src/graph.py`. The conditional `START` edge elegantly supports both supervised routing and direct API-bypass, avoiding a full LLM call when the endpoint already knows the intent.
- **Separation of Concerns** is clean: agents are self-contained nodes, utilities are decoupled, and ORM models don't bleed into business logic.
- **Compliance-as-a-Gateway**: routing every agent through the `compliance_guardian_node` before `END` is a sound architectural pattern — it ensures $NFA disclaimers are never skipped.
- **Embeddings Factory** in `src/utils/embeddings_factory.py` is an excellent vendor-agnostic abstraction.

### ❌ Critical Structural Flaw: Async/Sync Mismatch

`src/agents/market_insights.py` defines `market_insights_node` as `async def`, while all other nodes (`supervisor`, `portfolio_analyst`, `qa_agent`, `compliance`, `goal_strategist`) are **synchronous `def`**. LangGraph's compiled graph can deadlock or raise a `RuntimeError` when mixing sync and async nodes during `ainvoke()`.

```python
# market_insights.py — BUG
async def market_insights_node(state: FinnieState) -> dict:  # ← async

# All other agents — SYNC
def portfolio_analyst_node(state: FinnieState) -> dict:      # ← sync
def supervisor_node(state: FinnieState) -> dict:             # ← sync
```

**Fix:** Make all nodes `async def` (preferred for I/O-bound work), or keep all sync and wrap the Alpha Vantage call using `asyncio.run()` inside a thread executor.

---

## 2. Security Review

**Score: 3 / 10** — Multiple critical vulnerabilities.

### 🔴 CRITICAL — No Authentication

Every endpoint is completely open. The `user_id` is accepted verbatim from the client without JWT, session, or API key validation. Any external party can:

- Overwrite `user_1`'s entire portfolio via `POST /portfolio/save`
- Read any user's holdings via `GET /portfolio/{user_id}`
- Trigger expensive LLM calls (costing API money) via `POST /chat`

**Location:** `backend/main.py:173` — the `/chat` endpoint hardcodes `"user_1"`.

```python
# main.py — CRITICAL BUG
rows = db.query(Holding).filter(Holding.user_id == "user_1").all()  # ← hardcoded!
```

**Fix Required:** Implement JWT-based authentication (e.g., `python-jose` + FastAPI `Security` dependency). Derive `user_id` from the validated token, never from the request body.

---

### 🔴 HIGH — CORS Policy Too Permissive

`backend/main.py:109–121`:

```python
allow_methods=["*"],
allow_headers=["*"],
```

Combined with `allow_credentials=True`, this violates the CORS spec — browsers block wildcard origins with credentials enabled. In production, enumerate exact methods and headers.

---

### 🟡 MEDIUM — Chroma Tenant UUID in Source Control

`backend/.env.example:29` contains a real Chroma Cloud tenant UUID:

```
CHROMA_TENANT="593f59c6-1467-4da4-9b5d-e58042e3976d"
```

**Action:** Treat this as compromised. Rotate the Chroma Cloud tenant credentials and replace with a placeholder in the example file.

---

### 🟡 MEDIUM — No Rate Limiting on LLM Endpoints

`POST /chat`, `POST /goals/calculate`, and `GET /portfolio/analysis/{user_id}` all trigger expensive OpenAI API calls with no throttling. A single abusive user or bot could incur massive costs.

**Fix:** Add `slowapi` middleware with per-IP limits on all AI-triggering endpoints.

---

### 🟡 MEDIUM — No Input Sanitization on Ticker Symbols

`src/agents/portfolio_analyst.py:47`:

```python
ticker = h["ticker"].upper()
full_symbol = f"{ticker}{suffix}"
# → Passed directly to yf.download()
```

A malicious ticker string could cause unexpected behavior. Validate tickers against a regex allowlist (e.g., `^[A-Z0-9.^-]{1,12}$`).

---

## 3. Financial Math Correctness

**Score: 6 / 10** — Monte Carlo engine is sound; portfolio math has defects.

### ✅ Monte Carlo Simulation — Mostly Correct (`src/utils/simulations.py`)

The implementation correctly uses:
- Monthly compounding: `monthly_mean = (1 + expected_return)^(1/12) - 1` ✅
- Volatility scaling: `monthly_vol = volatility / sqrt(12)` ✅
- Vectorized NumPy operations for performance ✅
- Percentile fan chart extraction at yearly snapshots ✅

---

### ❌ Bug 1 — Hardcoded 2024 Base Year

**Location:** `src/agents/goal_strategist.py:44`

```python
years = max(1, config.get("target_year", 2035) - 2024)  # ← hardcoded 2024
```

This understates every user's time horizon by the number of years since 2024. Replace with `datetime.now().year`.

```python
# Fix
from datetime import datetime
years = max(1, config.get("target_year", 2035) - datetime.now().year)
```

---

### ❌ Bug 2 — Mock $100 Stock Price as Monte Carlo Input

**Location:** `src/agents/goal_strategist.py:50`

```python
initial_val = sum(h.get("shares", 0) * 100 for h in state.get("portfolio_data", []))  # Mock price $100
```

Assigning a flat $100 price to every holding produces wildly inaccurate Monte Carlo starting balances. The dashboard already fetches live prices via yfinance — that data should be passed into `goal_configuration` for use here.

---

### 🟡 Diversification Score Hardcoded

**Location:** `src/agents/portfolio_analyst.py:152`

```python
"diversification_score": 7,  # ← always 7, regardless of portfolio
```

Replace with a real calculation — Herfindahl-Hirschman Index (HHI) of sector/country weights, or a portfolio correlation matrix from the actual return data.

---

### 🟡 Beta Calculation Edge Cases

**Location:** `src/agents/portfolio_analyst.py:98-99`

```python
display_vols = [volatilities[s] for s in search_symbols if s in volatilities]
```

If a symbol is missing from `volatilities` (new listing, data gap), `display_betas` and `display_vols` arrays become misaligned, producing incorrect averages. Align both arrays against the same symbol list.

---

## 4. Agent & LangGraph Implementation

**Score: 7 / 10** — Solid routing, state management improvements needed.

### ✅ Strengths

- `RoutingDecision` Pydantic structured output in the supervisor is the correct pattern for reliable routing.
- `add_messages` reducer in `FinnieState` correctly accumulates conversation history.
- Country-based metadata filtering in ChromaDB RAG is well thought out.
- `start_node` bypass for direct API routing avoids unnecessary LLM calls.

---

### ❌ LLM Client Re-initialized on Every Request

**Location:** `src/agents/supervisor.py:32`, all other agents

```python
llm = init_chat_model(model=model_name, model_provider=provider, temperature=0)
```

All 4 agents call `init_chat_model()` on every single request invocation. **Fix:** Initialize LLM clients at module level (singleton pattern).

```python
# Recommended pattern (module level)
_llm: ChatOpenAI | None = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = init_chat_model(...)
    return _llm
```

---

### ❌ VectorStoreManager Created on Every Agent Call

**Location:** `src/agents/portfolio_analyst.py:121`, `src/agents/qa_agent.py:18`

```python
db = VectorStoreManager(collection_name="analytical_kb")
```

`VectorStoreManager.__init__` establishes a ChromaDB connection and loads the embedding model on every call. **Fix:** Use a module-level singleton or application-scoped dependency injection.

---

### 🟡 Session Leak Risk in Agents

**Location:** `src/agents/portfolio_analyst.py:34–39`, `src/agents/market_insights.py`

```python
db_session = SessionLocal()
try:
    ...
finally:
    db_session.close()
```

Agents create raw `SessionLocal()` instances instead of receiving one via FastAPI's `Depends(get_db)`. An exception before the `try` block would leak the session. **Fix:** Pass the DB session through the graph `state` dict or use a `with SessionLocal() as db_session:` context manager.

---

### 🟡 Compliance Node — Message Replacement Semantics

**Location:** `src/agents/compliance.py:23`

```python
new_msg = AIMessage(content=new_content, id=last_message.id)
return {"messages": [new_msg]}
```

Returning the same message ID should trigger LangGraph's `add_messages` deduplication/replacement behavior, but this is version-dependent. **Add a unit test** to confirm the disclaimer replaces (not duplicates) the last message.

---

### 🟡 Goal Strategist Ignores Conversation History

**Location:** `src/agents/goal_strategist.py:118`

```python
ai_response = llm.invoke([SystemMessage(content=system_prompt)])
# ← No *state["messages"] unpacking — conversation history is ignored
```

Every other agent correctly passes the full chat history. Confirm if this is intentional or a bug.

---

### 🟡 Dead Code — `stubs.py`

`src/agents/stubs.py` contains old placeholder implementations for `market_insights_node` and `goal_strategist_node`. These were superseded by the real implementations but never removed. Delete this file.

---

## 5. Database & Data Layer

**Score: 7 / 10** — Clean ORM, scalability concerns.

### ✅ Strengths

- Clean SQLAlchemy ORM with a shared `Base` declarative class.
- `get_db()` generator with guaranteed cleanup in `finally`.
- `MarketCache` with TTL validation is a smart use of SQLite as a lightweight API response cache.
- `DB_PATH` environment override for Azure deployment is forward-thinking.

---

### ❌ No Composite Unique Constraint on Holdings

**Location:** `src/models/portfolio.py`

The `holdings` table has no `UniqueConstraint` on `(user_id, ticker, exchange)`. Two concurrent `POST /portfolio/save` requests could create duplicate rows despite the delete-and-replace strategy.

```python
# Fix: Add to Holding model
__table_args__ = (
    UniqueConstraint('user_id', 'ticker', 'exchange', name='uq_user_ticker_exchange'),
)
```

---

### 🟡 `datetime.utcnow()` is Deprecated in Python 3.12+

**Location:** `src/models/goal.py:30–31`, `src/models/market_cache.py:15`

```python
# Before
created_at = Column(DateTime, default=datetime.utcnow)

# After
from datetime import datetime, timezone
created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

---

### 🟡 SQLite Blocks Multi-Instance Production

SQLite with `check_same_thread=False` is fine for local development but:
1. Does not support concurrent writes under load.
2. Cannot be shared across multiple server replicas.
3. Azure App Service restarts may wipe ephemeral storage.

**Migrate to PostgreSQL before any production launch.** The `database.py` comment already documents the migration path — only `DATABASE_URL` needs to change.

---

## 6. API Design

**Score: 7 / 10** — RESTful, minor endpoint design issues.

### ✅ Strengths

- Consistent use of Pydantic models for request/response validation.
- `response_model` declarations on all endpoints.
- FastAPI tags for clean Swagger grouping.

---

### ❌ `GET /portfolio/analysis/{user_id}` Should Be POST

**Location:** `backend/main.py:212`

This endpoint triggers an LLM invocation — a long-running, expensive, non-idempotent operation. Using HTTP `GET` violates REST semantics. Change to `POST /portfolio/analysis`.

---

### 🟡 Inconsistent Error Response Schema

- Some endpoints return `{"status": "no_goal"}` dicts (e.g., `main.py:364`)
- Others raise `HTTPException` with proper status codes
- The `/portfolio/analysis` endpoint on line 247 silently returns `"Analysis failed."` on error instead of a 500

**Fix:** Define a standard error response schema (`ErrorResponse`) and use it consistently.

---

### 🟡 Verb-Path Mixing is Inconsistent with REST

Mixing resource-oriented paths (`/portfolio/{user_id}`) with verb-paths (`/portfolio/save`) is inconsistent. REST convention would be `POST /portfolio` (create) or `PUT /portfolio/{user_id}` (replace).

---

## 7. Frontend Review

**Score: 7.5 / 10** — Clean React patterns, state management concerns.

### ✅ Strengths

- Custom hook pattern (`usePortfolio`, `useChat`, `useGoalStrategist`) cleanly separates API logic from UI — excellent React architecture.
- `crypto.randomUUID()` for stable React keys in `MyHoldings`.
- Parallel fetch with `Promise.all` in `usePortfolio`.
- TypeScript interfaces are well-defined and exported.

---

### ❌ Markdown Not Rendered in Goal Roadmap

**Location:** `src/components/Goals/GoalPlanner.tsx:288–290`

```tsx
{roadmap?.split('\n').map((line, i) => (
  <p key={i}>{line}</p>   // ← Raw markdown displayed as plain text
))}
```

The LLM returns Markdown (`###` headers, `**bold**`, bullet points). Users see raw syntax characters.

**Fix:** Add `react-markdown`:

```bash
npm install react-markdown
```

```tsx
import ReactMarkdown from 'react-markdown'
<ReactMarkdown>{roadmap}</ReactMarkdown>
```

---

### ❌ `API_BASE` Duplicated Across All Hooks

**Location:** All 5+ hook files

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

**Fix:** Create `src/config.ts`:

```typescript
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const USER_ID = 'user_1'
```

---

### 🟡 `USER_ID` Hardcoded in Frontend

```typescript
const USER_ID = 'user_1' // Hardcoded for Phase 3
```

This is correctly flagged in a comment but means every user of the deployed app shares the same data. Must be resolved as part of the authentication implementation.

---

### 🟡 Tab State Not Persisted Across Browser Refresh

**Location:** `src/App.tsx:14`

```typescript
const [activeTab, setActiveTab] = useState<TabId>('chat')
```

Refreshing always resets to the `chat` tab. **Fix:** Use URL hash routing or `React Router` to make tabs deep-linkable and refresh-safe.

---

### 🟡 Heavy Components Refetch on Every Tab Switch

Components like `Dashboard` refetch live yfinance data every time they mount. When a user switches tabs back and forth, redundant API calls are made.

**Fix:** Use `React Query` (`@tanstack/react-query`) for intelligent caching, or prevent unmounting with conditional `display: none` styling.

---

### 🟡 Accessibility Gap on New Holdings Rows

**Location:** `src/components/Portfolio/MyHoldings.tsx:123`

`autoFocus` on new rows doesn't announce the new row to screen readers.

**Fix:** Add `aria-live="polite"` on the holdings list container.

---

## 8. DevOps & Infrastructure

**Score: 6 / 10** — Good Docker setup, critical path mismatch.

### 🔴 CRITICAL — Volume Path Mismatch

**Location:** `docker-compose.yml:16` vs `src/utils/vector_store.py`

`docker-compose.yml` maps:
```yaml
- ./backend/chroma_data_local:/app/chroma_data_local
```

But the code writes to:
```python
LOCAL_DB_DIR = os.path.join(BASE_DIR, "chroma_db")  # ← different directory!
```

**These paths do not match.** Data ingested locally will NOT be visible inside the Docker container. Either align the environment variable or update the volume mount to `./backend/chroma_db:/app/src/chroma_db`.

---

### 🟡 Deprecated `version` Key in Docker Compose

**Location:** `docker-compose.yml:3`

```yaml
version: '3.8'  # ← deprecated in Docker Compose v2+
```

Remove this line.

---

### 🟡 No Health Check in Docker Compose

The `depends_on: backend` only waits for the container to *start*, not for FastAPI to be *ready*. This causes 502 errors on fresh container starts.

```yaml
# Add to backend service in docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:80/health"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 15s
```

---

## 9. Testing Coverage

**Score: 2 / 10** — Critically under-tested.

### Current State

| Type | Count | Notes |
|---|---|---|
| Integration tests | 1 | `tests/test_graph.py` — full real LLM invocation, not a true unit test |
| Script-level manual tests | 3 | `backend/scripts/test_*.py` — debugging utilities |
| Unit tests | 0 | None |
| Frontend tests | 0 | None |

### Required Tests (by Priority)

| Priority | Test | Rationale |
|---|---|---|
| 🔴 P0 | Monte Carlo math unit test | Verify simulation math against known analytical inputs |
| 🔴 P0 | Beta/Volatility calculation unit test | Verify edge cases: NaN, missing ticker, single-asset portfolio |
| 🔴 P0 | API endpoint integration tests (`pytest` + `TestClient`) | Prevent regressions on save/fetch/calculate endpoints |
| 🟡 P1 | Compliance node unit test | Confirm disclaimer replaces (not duplicates) the last message |
| 🟡 P1 | Supervisor routing test with mocked LLM | Verify correct routing decision for 5 intent types |
| 🟡 P2 | Frontend component tests with Vitest | `MyHoldings` form validation, `GoalPlanner` chart data mapping |

---

## 10. Prioritized Improvement Roadmap

### Phase 1 — Critical Fixes (Shipped September 2026)

| # | Issue | Location | Effort | Status |
|---|---|---|---|---|
| 1 | Add JWT authentication; derive `user_id` from token | `main.py` + `jwt.py` + `user.py` | 🔴 High | ✅ **SHIPPED** |
| 2 | Fix async/sync node mismatch — make `market_insights_node` sync | `src/agents/market_insights.py` | 🟢 Low | ✅ **SHIPPED** |
| 3 | Fix `chroma_data_local` vs `chroma_db` Docker volume path mismatch | `docker-compose.yml` | 🟢 Low | ✅ **SHIPPED** |
| 4 | Fix hardcoded `2024` base year in simulation | `src/agents/goal_strategist.py:44` | 🟢 Low | ✅ **SHIPPED** |
| 5 | Replace mock $100 price with live yfinance prices for Monte Carlo | `src/agents/goal_strategist.py:50` | 🟡 Medium | ✅ **SHIPPED** |
| 6 | Implement real diversification score (HHI) + 3-attempt retry loop | `src/agents/portfolio_analyst.py` | 🟡 Medium | ✅ **SHIPPED** |

### Phase 2 — Quality & Correctness

| # | Issue | Location | Effort | Status |
|---|---|---|---|---|
| 7 | Add `UniqueConstraint` to holdings table | `src/models/portfolio.py` | 🟢 Low | ✅ **SHIPPED** |
| 8 | Replace `datetime.utcnow()` with timezone-aware equivalent | `src/models/goal.py`, `market_cache.py` | 🟢 Low | ✅ **SHIPPED** |
| 9 | Singleton LLM and VectorStore instances | All agent files | 🟡 Medium | ⏳ Planned |
| 10 | Add rate limiting (`slowapi`) on LLM-triggering endpoints | `main.py` | 🟡 Medium | ⏳ Planned |
| 11 | Structured markdown rendering for roadmap | `GoalPlanner.tsx`, `RoadmapRenderer.tsx` | 🟢 Low | ✅ **SHIPPED** |
| 12 | Centralize `API_BASE` and endpoints | All hook files → `src/config.ts` | 🟢 Low | ✅ **SHIPPED** |
| 13 | Rotate and remove Chroma tenant UUID from `.env.example` | `.env.example` | 🟢 Low | ⏳ Planned |
| 14 | Add `aria-live` to holdings list for accessibility | `MyHoldings.tsx` | 🟢 Low | ⏳ Planned |
| 15 | Delete dead code `src/agents/stubs.py` | `src/agents/stubs.py` | 🟢 Low | ✅ **SHIPPED** |

### Phase 3 — Production Hardening

| # | Issue | Effort |
|---|---|---|
| 16 | Migrate SQLite → PostgreSQL | 🔴 High |
| 17 | Add `pytest` unit test suite targeting 80%+ coverage | 🔴 High |
| 18 | Add Docker `healthcheck` directives to all services | 🟢 Low |
| 19 | Implement React Router for deep-linkable tabs | 🟡 Medium |
| 20 | Add structured logging with `structlog` | 🟡 Medium |
| 21 | Change `GET /portfolio/analysis` to `POST` | 🟢 Low |
| 22 | Standardize error response schema across all endpoints | 🟡 Medium |

---

## 11. Business Perspective

### Strengths (Business Value)

- **Multi-jurisdiction support** (US/India/UK/Canada/Germany) is a genuine market differentiator
- **RAG-grounded responses** reduce hallucination risk — critical for financial advice where accuracy has legal implications
- **Monte Carlo simulations** provide real mathematical substance beyond simple chatbot responses
- **$NFA disclaimer pipeline** via the compliance node demonstrates regulatory awareness
- **Live market data** via yfinance + Alpha Vantage elevates this beyond static advice tools

### Business Risk Areas

| Risk | Severity | Note |
|---|---|---|
| Single-user architecture | 🔴 Critical | Hardcoded `user_1` cannot serve real multi-user traffic without a complete auth rework |
| OpenAI dependency lock-in | 🟡 Medium | All LLM costs flow through OpenAI — no cost optimization or fallback for outages |
| Alpha Vantage free tier | 🟡 Medium | Free tier rate limits will throttle Market Insights under any real usage |
| Legal exposure from RAG content | 🟡 Medium | IRS/tax rule content could contain inaccuracies that create liability |
| No data privacy / deletion mechanism | 🟡 Medium | Required for GDPR/CCPA compliance before any production launch |

---

## 12. What's Done Exceptionally Well

| # | Feature | Why It's Great |
|---|---|---|
| 1 | **LangGraph supervisor routing with `start_node` bypass** | Clean, extensible; correctly skips the LLM when endpoint intent is known |
| 2 | **Embeddings factory pattern** | Switch embedding providers (OpenAI → Azure → HuggingFace) with zero code changes |
| 3 | **SQLite API cache (`MarketCache`) with TTL** | Clever and cost-effective — avoids paid Alpha Vantage API overuse |
| 4 | **Frontend custom hook architecture** | Full separation of API logic from UI components — textbook React architecture |
| 5 | **ChromaDB country metadata filtering for RAG** | Applying geographic RAG filtering to regulatory content is domain-appropriate and technically sound |

---

## Changelog

| Date | Version | Author | Changes |
|---|---|---|---|
| 2026-07-26 | v1.0 | Antigravity AI | Initial comprehensive review of v0.1.0 codebase |

---

*Refer to `docs/STANDARDS.md` for engineering guidelines. Cross-reference `docs/PROGRESS_LOG.md` when marking items complete.*
