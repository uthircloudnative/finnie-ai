# Finnie AI: A Multi-Agent Finance Guide

Finnie AI is a production-grade financial assistant that delivers personalized advice, real-time market insights, and portfolio analysis through a specialized multi-agent system built with LangGraph.

## 🚀 Current Status: Phase 2 (Foundation) — FULLY COMPLETE

| Phase | Status |
|---|---|
| Phase 1 — RAG Pipeline & Data Grounding | ✅ Complete |
| Phase 2 — LangGraph Orchestrator + FastAPI REST Layer + React UI | ✅ Complete |
| Phase 3 — Market Insights, Portfolio & Goal Agents | 🔲 Next |
| Phase 4 — Hardening & Compliance | 🔲 Planned |
| Phase 5 — Deployment & Scale | 🔲 Planned |

The system is fully runnable end-to-end: ingest financial definitions → ChromaDB vector store → GPT-4o Supervisor Agent → RAG-grounded answers → REST API → **live React/Vite Glass-Finance UI**.

---

## ⚡ Quickstart (Backend Development)

Finnie AI uses **[uv](https://docs.astral.sh/uv/)** — a fast, modern Python package manager. No manual `venv` activation needed; `uv run` handles everything.

### Step 1 — Install uv (one-time)
```bash
brew install uv
```

### Step 2 — Enter the backend and sync dependencies
```bash
cd backend
uv sync
```

### Step 3 — Configure your environment
```bash
cp .env.example .env
# Open .env and fill in:
#   OPENAI_API_KEY=sk-...
#   LLM_PROVIDER=openai
#   LLM_MODEL=gpt-4o
#   EMBEDDING_PROVIDER=openai
```

---

## 🗄️ Component 1: RAG Ingestion Pipeline

Seeds ChromaDB with curated financial definitions scraped from Investor.gov.
Run this once before starting the API server.

```bash
cd backend

# Ingest data into local ChromaDB
uv run python scripts/ingest/investor_gov_scraper.py --db local

# (Optional) Verify retrieval is working
uv run python scripts/test_retrieval.py "What is an Index Fund?" USA
```

> **`--db` flag**: Use `--db local` for on-disk dev storage, `--db cloud` to push to Chroma Cloud (requires `CHROMA_API_KEY` in `.env`).

---

## 🤖 Component 2: Agent Graph (Standalone Test)

Tests the full LangGraph pipeline — Supervisor routing → Financial Q&A worker → answer — without the HTTP layer.

```bash
cd backend
uv run python tests/test_graph.py
```

Expected output: the Supervisor routes to `FINANCIAL_QA` for definitions, `MARKET_INSIGHTS` for news (stub), and `FINISH` for greetings.

---

## 🌐 Component 3: FastAPI REST API Server

Exposes the agent graph over HTTP so any frontend or client can call it.

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

### Available Endpoints

| Method | URL | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — no LLM call |
| `POST` | `/chat` | Send a message, get Finnie's response |
| `GET` | `/docs` | Interactive Swagger UI (auto-generated) |

### Test with curl
```bash
# Health check
curl http://localhost:8000/health

# Ask a financial question (routes to RAG-grounded Financial Q&A)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is an ETF?"}'

# Ask about market news (routes to Market Insights — stub, returns 500 until implemented)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is happening with Apple stock today?"}'
```

---

## 🖥️ Component 4: React/Vite Frontend UI

Serves the Glass-Finance web interface that connects to the FastAPI backend.

> **Prerequisite**: Node.js 18+ must be installed. Run `node -v` to verify.

```bash
cd frontend
npm install   # first time only
npm run dev
```

Open **`http://localhost:5173`** in your browser.

| Tab | Status | What it does |
|---|---|---|
| 💬 Deep Q&A | ✅ Live | Calls `POST /chat` — real RAG-grounded answers |
| 🏠 Dashboard | 🔲 Static shell | Wired to Portfolio Agent in Phase 3 |
| 📈 Portfolio Analyst | 🔲 Static shell | Wired to Portfolio Agent in Phase 3 |
| 🌐 Market Insights | 🔲 Static shell | Wired to Market Insights Agent in Phase 3 |
| 🎯 Goal Planner | 🔲 Static shell | Wired to Goal Strategist Agent in Phase 3 |

> **Tip**: The Deep Q&A tab is the only live tab. The other 4 tabs display static shells with placeholder data until Phase 3 agents are built.

---

## ⚙️ Configuration Reference

The system is fully vendor-agnostic. All behaviour is controlled via `.env`:

| Variable | Options | Default |
|---|---|---|
| `EMBEDDING_PROVIDER` | `openai`, `azure_openai`, `huggingface`, `fake` | `openai` |
| `LLM_PROVIDER` | `openai`, `azure_openai` | `openai` |
| `LLM_MODEL` | `gpt-4o`, `gpt-4o-mini`, etc. | `gpt-4o` |
| `CHROMA_API_KEY` | Your Chroma Cloud key | *(blank = local mode)* |

> **CLI Override**: Every script supports `--db local|cloud` to override `.env` without editing the file.

---

## 🎨 Interactive Prototype

To visualise the Glass-Finance UI vision:
1. Navigate to the `prototype/` directory.
2. Open `index.html` directly in your browser (no server needed).

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend Runtime | Python 3.13+, `uv` (package manager) |
| API Layer | FastAPI, Uvicorn |
| AI Orchestration | LangGraph, LangChain |
| LLM | OpenAI GPT-4o (vendor-swappable) |
| Vector Store | ChromaDB (local on-disk / Chroma Cloud) |
| Data Ingestion | BeautifulSoup, Requests |
| Frontend | React 19, Vite 6, TypeScript, Vanilla CSS |

---

## 📂 Core Documentation

| Doc | Purpose |
|---|---|
| [PROJECT_PLAN.md](./docs/PROJECT_PLAN.md) | Mission, features, and full roadmap |
| [DESIGN.md](./docs/DESIGN.md) | Technical architecture and agent graph design |
| [INGESTION_PIPELINES.md](./docs/INGESTION_PIPELINES.md) | How RAG data is sourced, chunked, and stored |
| [RAG_GUIDE.md](./docs/RAG_GUIDE.md) | Deep-dive into the retrieval strategy |
| [UI_DESIGN.md](./docs/UI_DESIGN.md) | Glass-Finance UX/UI specification |
| [STANDARDS.md](./docs/STANDARDS.md) | Engineering guidelines and AI policies |
| [PROGRESS_LOG.md](./docs/PROGRESS_LOG.md) | Session-by-session progress log |

---

## 👨‍💻 Contributing

Please adhere to the coding rules in [STANDARDS.md](./docs/STANDARDS.md) — specifically: **AI Assistants must never auto-commit or auto-push** code without explicit human review and approval.


