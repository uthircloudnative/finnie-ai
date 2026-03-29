# Portfolio Analyst Agent — End-to-End Guide

> **Status:** ✅ Fully Implemented (Backend + Frontend) | Production Ready

---

## What Does This Agent Do?

The **Portfolio Analyst Agent** receives a user's portfolio (list of stock tickers + weights) and produces a plain-English analysis covering:

| Capability | Example output |
|---|---|
| Risk-adjusted return | "Your Sharpe Ratio of 1.3 is above the 1.0 benchmark — good risk management." |
| Market sensitivity | "Your Beta of 1.4 means your portfolio moves 40% more than the market." |
| Drawdown risk | "Your worst historical loss was -22% — moderate downside risk." |
| Diversification | "75% in Tech is above the 30% sector limit — consider rebalancing." |
| Rebalancing advice | "Calendar-based annual rebalancing suits your risk profile." |

All explanations are **grounded in the `analytical_kb` RAG** — the agent never makes up definitions or benchmarks.

---

## Architecture Overview

```
User: "Analyse my portfolio: AAPL 40%, MSFT 30%, TSLA 20%, BND 10%"
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │  Supervisor Agent   │
                        │  (LangGraph router) │
                        └────────┬────────────┘
                                 │ routes to
                                 ▼
                    ┌────────────────────────────┐
                    │   Portfolio Analyst Agent  │
                    │                            │
                    │  1. Math Engine (yfinance) │
                    │  2. RAG Retrieval          │
                    │  3. LLM Synthesis          │
                    └────────────────────────────┘
                          │              │
              ┌───────────┘              └────────────┐
              ▼                                       ▼
   ┌─────────────────────┐              ┌─────────────────────────┐
   │  yfinance (live)    │              │  ChromaDB               │
   │                     │              │  Collection: analytical_kb│
   │ • Historical prices │              │                         │
   │ • Returns           │              │ • Sharpe Ratio theory   │
   │ • Volatility        │              │ • Beta explanation      │
   │ • Correlation       │              │ • MPT concepts          │
   └─────────────────────┘              │ • Diversification rules │
                                        │ • Rebalancing strategy  │
                                        └─────────────────────────┘
              │                                       │
              └──────────────┬────────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │   LLM (GPT-4o)  │
                    │                 │
                    │  Combines math  │
                    │  + RAG context  │
                    │  → beginner-    │
                    │    friendly     │
                    │    explanation  │
                    └─────────────────┘
```

---

## RAG Pipeline — `analytical_kb`

### What is stored in this RAG?

The `analytical_kb` collection contains **financial theory chunks** — definitions, formulas, benchmarks, and interpretation guides for portfolio metrics.

| Topic | Source | Category |
|---|---|---|
| Sharpe Ratio | Investopedia | `metric_benchmark` |
| Beta | Investopedia | `metric_benchmark` |
| Alpha | Investopedia | `metric_benchmark` |
| Maximum Drawdown | Investopedia | `metric_benchmark` |
| Modern Portfolio Theory | Investopedia | `theory` |
| Efficient Frontier | Investopedia | `theory` |
| Diversification | Investopedia | `diversification` |
| Portfolio Rebalancing | Investopedia | `strategy` |

### Ingestion Flow

```
Investopedia Pages (saved as HTML)
        │
        │  content/analtical_kb/*.html
        │
        ▼
load_html_analytical_kb.py
        │
        ├─ 1. Parse HTML → extract paragraphs
        │       selector: .article-body-content p
        │       filter:   min 60 chars, drop junk phrases
        │
        ├─ 2. Attach metadata to each document
        │       {
        │         topic:        "Sharpe Ratio",
        │         category:     "metric_benchmark",
        │         country:      "GLOBAL",
        │         source:       "https://investopedia.com/...",
        │         ingested_date: "2026-03-28"
        │       }
        │
        ├─ 3. Chunk with RecursiveCharacterTextSplitter
        │       chunk_size:    500 chars
        │       chunk_overlap: 50 chars
        │
        └─ 4. Embed + store in ChromaDB
                collection: analytical_kb
                193 chunks total (8 articles)
```

### Retrieval Flow (at query time)

```
Agent receives portfolio data
        │
        ▼
Compute metrics (yfinance):
  sharpe=1.3, beta=1.4, drawdown=-22%, sector_concentration=75%
        │
        ▼
Build RAG query per metric:
  "What is a good Sharpe Ratio benchmark?"
  "How to interpret a Beta above 1.0?"
  "What sector concentration limit is safe?"
        │
        ▼
VectorStoreManager.search(query, k=3)
  → semantic similarity search in analytical_kb
  → returns top-3 most relevant chunks
        │
        ▼
LLM prompt:
  "Given this portfolio data [math results]
   and this reference material [RAG chunks],
   explain the portfolio health in plain English."
        │
        ▼
Response to user ✅
```

---

## Multi-Country Support

All current content is tagged `country=GLOBAL` — universal investment theory that applies to any market.

When country-specific content is needed (e.g., tax rules, regulatory limits), save HTML files into a named sub-folder:

```
content/analtical_kb/             ← GLOBAL theory (loaded today)
content/analtical_kb/US/          ← US-specific (future)
content/analtical_kb/IN/          ← India-specific (future)
content/analtical_kb/UK/          ← UK-specific (future)
content/analtical_kb/AU/          ← Australia-specific (future)
```

The loader auto-detects the folder and tags chunks with the correct country code. No code changes needed.

The agent then does a **2-pass retrieval**:

```python
# 1. Country-specific rules (regulatory, tax)
country_chunks = store.search(query, k=3, target_country="IN")

# 2. Universal theory (always relevant)
global_chunks  = store.search(query, k=3, target_country="GLOBAL")

# Combined context passed to the LLM
context = country_chunks + global_chunks
```

---

## Files Reference

| File | Purpose |
|---|---|
| `backend/scripts/ingest/content/analtical_kb/*.html` | Source HTML pages (8 topics) |
| `backend/scripts/ingest/load_html_analytical_kb.py` | Ingestion script — HTML → ChromaDB |
| `backend/scripts/test_retrieval.py` | Generic retrieval tester (all collections) |
| `backend/src/utils/vector_store.py` | ChromaDB wrapper (local + cloud) |

---

## Running the Pipeline Locally

```bash
cd backend

# Step 1 — Load HTML files into local ChromaDB
uv run scripts/ingest/load_html_analytical_kb.py --db local --reset

# Step 2 — Verify retrieval works
uv run scripts/test_retrieval.py "What is a good Sharpe Ratio?" analytical_kb --db local
uv run scripts/test_retrieval.py "Explain Beta and market risk" analytical_kb --db local
uv run scripts/test_retrieval.py "How often should I rebalance?" analytical_kb --db local

# Step 3 — Load to Chroma Cloud (production)
uv run scripts/ingest/load_html_analytical_kb.py --db cloud --reset
```

### Expected test output

```
Chunk 1  |  topic=Sharpe Ratio  country=GLOBAL  category=metric_benchmark
Source : https://www.investopedia.com/terms/s/sharperatio.asp
Content:
Sharpe ratios above one are generally considered "good," offering excess
returns relative to volatility...
```

---

---

## 🔄 Analysis Trigger Flows

The Portfolio Analyst Agent can be invoked in three distinct ways to ensure both a structured reports and natural conversation.

### 1. Tab-Triggered (Structured Report)
When the user clicks the **Portfolio Analyst** tab in the UI:
- **Frontend**: Calls `GET /portfolio/analysis/{user_id}`.
- **Backend (`main.py`)**: 
    1. Fetches all holdings from SQLite.
    2. Packages these holdings into the `portfolio_data` field.
    3. Invokes the `portfolio_analyst` node directly.
- **Result**: A comprehensive dashboard featuring **Beta (vs S&P 500)**, **Annualized Volatility**, and a **Diversification Score**.

### 2. Tab-Specific Chat (Contextual Workshop)
Users can ask follow-up questions directly within the Analyst tab:
- **Context Hinting**: The frontend passes `preferred_worker="PORTFOLIO_ANALYST"` and `analysis_context` (the pre-calculated Beta/Vol).
- **Instant Response**: Finnie answers immediately about the specific metrics displayed on the dashboard without re-calculating data.

### 3. General Chat (Natural Language)
When the user types a question like *"Is my portfolio too tech-heavy?"* in the main Chat:
- **Supervisor**: Recognizes the intent and routes to `PORTFOLIO_ANALYST`.
- **Worker**: Analyzes the holdings stored in the database and responds within the conversation thread.

---

## 🛡️ Compliance & Safety

All outputs from the Portfolio Analyst Agent **must** pass through the **Compliance Guardian** post-processor node.

- **Requirement**: Every AI response related to portfolio analysis must be appended with the `$NFA` disclaimer.
- **Implementation**: A final node in the LangGraph enforces the disclaimer before the data reaches the client.

---

## 🏁 Phase 3 Completion Checklist

The Portfolio Analyst is now fully wired and functional.

- [x] **Step 1: State Update** — Added `analysis_results` and `portfolio_data` to `FinnieState`.
- [x] **Step 2: Analyst Worker** — Created `portfolio_analyst.py` with `yfinance` & robust MultiIndex handling.
- [x] **Step 3: API Integration** — Updated `main.py` with `/portfolio/analysis` and contextual `/chat` params.
- [x] **Step 4: Graph Wiring** — Registered all nodes and fixed conditional routing logic in `src/graph.py`.
- [x] **Step 5: UI Connection** — Built the split-view dashboard and interactive sidebar in `PortfolioAnalyst.tsx`.
