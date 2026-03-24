# Finnie AI: A Multi-Agent Finance Guide

Finnie AI is a production-grade financial assistant that delivers personalized advice, real-time market insights, and portfolio analysis through a specialized multi-agent system.

## 🚀 Current Status: Phase 2 (Foundation) In Progress
We have successfully implemented the foundational Retrieval-Augmented Generation (RAG) pipeline AND our **LangGraph Orchestrator**. The system can now autonomously scrape definitions, dynamically route user intents via a Supervisor Agent, and trigger specialized worker nodes (Financial Q&A) to generate grounded advice. 

The next step is building the Market Insights live-news logic and scaffolding the React UI.

## ⚡ Quickstart (Backend Development)
Finnie AI uses the modern **[uv](https://docs.astral.sh/uv/)** package manager for blazing-fast, deterministic Python environments.

```bash
# 1. Install uv (macOS)
brew install uv

# 2. Enter the backend directory and sync dependencies
cd backend
uv sync

# 2. Configure your API key
cp .env.example .env
# Open .env to set your EMBEDDING_PROVIDER and OPENAI_API_KEY

# 3. Enter the backend directory and sync dependencies
cd backend
uv sync

# 4. Run the data ingestion pipeline (use --db local for local dev)
uv run scripts/ingest/investor_gov_scraper.py --db local

# 5. Test the Retrieval system
uv run scripts/test_retrieval.py "What is an Index Fund?" USA

# 6. Test the fully integrated LangGraph Agent Orbit
uv run tests/test_graph.py
```

## ⚙️ Configuration
The system is vendor-agnostic. You can switch providers in your `.env`:
- `EMBEDDING_PROVIDER`: Choose `openai`, `azure_openai`, or `huggingface`.
- `CHROMA_API_KEY`: Leave empty for **Local Mode**, or provide a key for **Chroma Cloud**.
- **CLI Overrides**: Every script supports a `--db local|cloud` flag to override `.env` settings.

## 🎨 Interactive Prototype
To visualize the project vision and all 5 navigation screens:
1.  Navigate to the `prototype/` directory.
2.  Open `index.html` in your browser.

## 🛠️ Technology Stack
- **Backend Environment**: `uv` (Package Manager), Python (FastAPI).
- **AI Core**: LangGraph, LangChain, OpenAI (GPT-4o).
- **Data/RAG**: ChromaDB, BeautifulSoup, Alpha Vantage, NewsAPI.
- **Frontend**: React (Vite), TypeScript, Framer Motion.
- **Styling**: "Glass-Finance" (Vanilla CSS / Custom Tokens).

## 📂 Core Documentation
- [PROJECT_PLAN.md](./docs/PROJECT_PLAN.md): Mission, Features, and Roadmap.
- [DESIGN.md](./docs/DESIGN.md): Technical Architecture and Graph Logic.
- [INGESTION_PIPELINES.md](./docs/INGESTION_PIPELINES.md): Detailed guide on how our RAG data is sourced, chunked, and stored.
- [STANDARDS.md](./docs/STANDARDS.md): Engineering guidelines and AI policies.

## 👨‍💻 How to Contribute
Please adhere to the strict coding rules defined in [STANDARDS.md](./docs/STANDARDS.md)—specifically the rule that AI Assistants **must never auto-commit** code without human review.
