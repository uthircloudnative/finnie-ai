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

### Phase 3: Agent Integration & Analysis
- **Worker Workers**: Connect the specialized Agents (Portfolio, Market, Goal) to the RAG tools built in Phase 1.
- **Goal Engine**: Developing Monte Carlo simulation tools for the Goal Strategist.

### Phase 4: Hardening & Compliance
- **Compliance**: Implement the Guardian node to scan all messages for risk disclaimers.
- **Testing**: Reach 80%+ coverage with Pytest and Playwright.

### Phase 5: Deployment & Scale
- **Infrastructure**: CI/CD pipeline, FastAPI performance tuning, and Cloud deployment.
## 4. RAG Integration Matrix (Learning Reference)

| UI Tab / Feature | RAG Required? | Data Sources | Implementation Summary |
| :--- | :--- | :--- | :--- |
| **Q&A Chatbot** | **YES** | Investor.gov, Textbooks | **Static Pipeline**: Scrape -> Chunk -> Index in ChromaDB. Agent uses `similarity_search` to define terms. |
| **Market Insights** | **YES** | NewsAPI, SEC Filings | **Transient Pipeline**: Fetch live news -> In-memory indexing -> Summary. Results expire after session. |
| **Portfolio Analyst** | **AUGMENTED** | Academic Papers | **Reference Pipeline**: Math is done locally; RAG is used to provide theoretical context (e.g., "Why diversification matters"). |
| **Goal Planning** | **YES** | IRS Tax Codes | **Validation Pipeline**: Agent queries tax limits/rules during simulation to ensure legal accuracy. |
| **Compliance** | **YES** | SEC Safety Guides | **Guardian Pipeline**: Check every final answer against SEC safety docs before user delivery. |
