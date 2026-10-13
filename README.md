# Finnie AI: A Multi-Agent Finance Guide

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-1C3C3C.svg?style=flat&logo=langchain&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/OpenAI-412991.svg?style=flat&logo=openai&logoColor=white" alt="OpenAI" />
  <img src="https://img.shields.io/badge/React-19-20232A.svg?style=flat&logo=react&logoColor=%2361DAFB" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-007ACC.svg?style=flat&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Vite-B73BFE.svg?style=flat&logo=vite&logoColor=%23FFD62E" alt="Vite" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy 2.0" />
  <img src="https://img.shields.io/badge/SQLite-003B57.svg?style=flat&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/ChromaDB-FF6B6B.svg?style=flat" alt="ChromaDB" />
  <img src="https://img.shields.io/badge/Mailgun-F05A28.svg?style=flat&logo=mailgun&logoColor=white" alt="Mailgun" />
  <img src="https://img.shields.io/badge/JWT_Auth-000000.svg?style=flat&logo=jsonwebtokens&logoColor=white" alt="JWT Auth" />
  <img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Docker_Compose-2496ED.svg?style=flat&logo=docker&logoColor=white" alt="Docker Compose" />
  <img src="https://img.shields.io/badge/Azure-0089D6.svg?style=flat&logo=microsoftazure&logoColor=white" alt="Azure" />
</p>

## What is Finnie AI?

Finnie AI is a premium, production-grade financial assistant that delivers personalized advice, real-time market insights, and multi-currency portfolio analysis using a highly specialized multi-agent system built with LangGraph.

Instead of relying on a single underlying chat model, Finnie uses a **Supervisor Routing Architecture**. When a user submits a query, the Supervisor analyzes the intent and explicitly routes the task to specialized sub-agents:
- **Financial Q&A Agent**: Retrieves complex tax and investing theory directly from ChromaDB.
- **Portfolio Analyst Agent**: Securely reads the user's local SQLite holdings and executes live algorithmic calculations against Yahoo Finance market data.
- **Goal Strategist Agent**: Calculates multi-decade Monte Carlo simulations to plot safe retirement horizons.

### High-Level Architecture & Agent-vs-Programmatic Functionality Breakdown

```mermaid
graph TD
    subgraph Client["Frontend (React 19 + Vite + TypeScript)"]
        UI[Glass-Finance Dashboard & Views]
        AuthCtx[AuthContext · Token Store & Bearer Injection]
        AuthMod[AuthModal · Sign In / Register / Forgot Password]
        UI --> AuthCtx
        AuthMod --> AuthCtx
    end

    AuthCtx -->|HTTPS + Bearer JWT| Backend[FastAPI Backend · Python 3.13]

    subgraph Security["Security & Data Layer"]
        Backend -->|Verify Token & Version| JWT[JWT Core & bcrypt · jwt.py]
        Backend -->|User & Audit Context| ORM[(SQLite Database<br/>users · password_reset_audits<br/>holdings · goals · market_cache)]
    end

    subgraph Programmatic["Programmatic Services (Deterministic · No LLM)"]
        Backend -->|Auth Endpoints| AuthSvc["User Auth (/auth/register, /auth/login, /auth/me)"]
        Backend -->|Recovery Endpoints| RecovSvc["Password Recovery (/auth/forgot-password, /auth/reset-password)"]
        Backend -->|Direct Engine| DashSvc["Global Wealth Dashboard (/dashboard)"]
        Backend -->|CRUD Operations| PortSvc["Portfolio Holdings (/portfolio, /portfolio/save)"]
        Backend -->|3-Attempt Backoff Retry| DivSvc["Diversification Score Retry (/portfolio/diversification)"]
    end

    subgraph AgentSystem["LangGraph Multi-Agent Orchestrator"]
        Backend -->|ainvoke| LangGraph[LangGraph Stateful Supervisor]

        LangGraph -->|Multi-Agent Intent Router| Sup[Supervisor Agent Node]
        
        Sup -->|route: FINANCIAL_QA| QA[Financial Q&A Worker Node]
        Backend -->|Direct Route: PORTFOLIO_ANALYST| Analyst[Portfolio Analyst Worker Node]
        Backend -->|Direct Route: MARKET_INSIGHTS| Insights[Market Insights Worker Node]
        Backend -->|Direct Route: GOAL_STRATEGIST| Goals[Goal Strategist Worker Node]

        QA       -->|POST-node| Compliance[Compliance Guardian Node]
        Analyst  -->|POST-node| Compliance
        Insights -->|POST-node| Compliance
        Goals    -->|POST-node| Compliance

        Compliance --> END([END])
    end

    subgraph Tools["Agent Tool & Knowledge Layer"]
        QA       -.-|Tool Call: RAG Search| Chroma[(ChromaDB Vector Store<br/>financial_kb · analytical_kb<br/>goal_rules · market_news_kb)]
        Analyst  -.-|Tool Call: Benchmark & Prices| YFinance[Yahoo Finance API]
        Analyst  -.-|Tool Call: RAG Search| Chroma
        Insights -.-|Tool Call: News & Sentiment| AlphaV[Alpha Vantage API<br/>30-min SQLite Cache]
        Goals    -.-|Tool Call: 10k Simulations| MonteCarlo[Monte Carlo Engine]
        Goals    -.-|Tool Call: RAG Search| Chroma
    end

    subgraph ExternalServices["External Services"]
        AgentSystem -.-|LLM Reasoning| OpenAI{OpenAI GPT-4o / Azure OpenAI}
        Backend     -.-|Telemetry| LangSmith[LangSmith Observability]
        RecovSvc    -.-|Transactional Email| Mailgun[Mailgun REST API / Console Fallback]
    end
```

### Functionality & Execution Breakdown

| Functionality | Primary Endpoint | Execution Mode | Agent Model | Tool Calls Required | Description |
|---|---|---|---|---|---|
| **User Auth & Profile** | `/auth/register`<br/>`/auth/login`<br/>`/auth/me` | **Programmatic** | *None (No LLM)* | *None* | Fast, deterministic JWT generation, password hashing (`bcrypt`), and user profile persistence. |
| **Password Recovery** | `/auth/forgot-password`<br/>`/auth/reset-password` | **Programmatic** | *None (No LLM)* | *Mailgun REST API* | 6-digit CSPRNG OTP, sliding rate-limiting (3/15m), strict 3-attempt limit, dual-origin audit trail (`password_reset_audits`), and session revocation (`token_version`). |
| **Global Wealth View** | `/dashboard` | **Programmatic** | *None (No LLM)* | *yfinance price lookup* | Lightning-fast deterministic SQLite crunching and live market prices without LLM latency. |
| **My Holdings CRUD** | `/portfolio`<br/>`/portfolio/save` | **Programmatic** | *None (No LLM)* | *None* | Multi-tenant portfolio CRUD operations with user isolation. |
| **Diversification Score Tile Retry** | `/portfolio/diversification` | **Programmatic** | *None (No LLM)* | *yfinance sector info (3 retries)* | 3-attempt exponential backoff engine for sector Herfindahl-Hirschman Index (HHI) score. Shows manual retry button on tile if retries fail. |
| **Deep Q&A Chat** | `/chat` | **AI Agentic** | **Multi-Agent Router** | ChromaDB RAG search | Supervisor Agent routes intent to Financial Q&A Agent → RAG search → Compliance Agent. |
| **Portfolio Analyst** | `/portfolio/analysis` | **AI Agentic** | **Multi-Agent (Country-Aware)** | Benchmark routing + yfinance + ChromaDB RAG | Calculates Beta/Volatility/HHI, conducts 2-pass RAG, synthesizes 3-card formatted insights, and provides on-demand `CopilotDrawer` interaction. |
| **Market Insights** | `/market/news` | **AI Agentic** | **Single Agent** | Alpha Vantage API + 30-min SQLite Cache | Direct route to Market Insights Agent for stock news & sentiment analysis with on-demand `CopilotDrawer` ticker deep-dive. |
| **Goal Planner (Financial GPS)** | `/goals/calculate`<br/>`/goals`<br/>`/goals/liabilities`<br/>`/goals/cashflow` | **AI Agentic + Deterministic Math** | **Hybrid Bootstrap Multi-Agent** (`goal_strategist` + `goal_auditor` + `hitl_gatekeeper`) | 10k Monte Carlo Engine + Dynamic Debt Amortization + Tax Limit RAG + Regional Portfolio Scoping | Autonomous financial GPS with country-scoped equity ingestion, live cash flow solvency meters, multi-loan amortization, twin synchronized charts (Projected Growth & Real Net Worth), upfront action levers (Debt Avalanche & Post-Loan Step-Up), human-in-the-loop strategy lock-in, and interactive `Ask Finnie` what-if copilot. |


> **Preview Gallery:** Check out the [UI Preview Gallery](./docs/UI_PREVIEW.md) to see high-fidelity mockups of the finished Dashboard and Market Insights interfaces before you start the installation!

### Production Cloud Deployment Architecture (Microsoft Azure + GHCR)

Finnie AI is architected for zero-maintenance, low-cost deployment (~$5–$15/month) combining GitHub Container Registry, Azure Static Web Apps, and Azure Container Apps with custom domain routing and persistent database storage:

```mermaid
graph TD
    User([User Web Browser]):::clientStyle

    subgraph DNS["DNS & Custom Domain Layer (Free SSL / TLS)"]
        FrontDomain["Frontend Custom DNS<br/>app.yourdomain.com<br/>CNAME -> *.azurestaticapps.net"]:::dnsStyle
        ApiDomain["Backend Custom DNS<br/>api.yourdomain.com<br/>CNAME -> *.azurecontainerapps.io"]:::dnsStyle
    end

    User -->|HTTPS 443| FrontDomain
    User -->|HTTPS 443 / REST| ApiDomain

    subgraph GitHub["GitHub Ecosystem (Zero-Cost CI/CD & Registry)"]
        GitRepo["GitHub Repository<br/>finnie-ai"]:::githubStyle
        GHActions["GitHub Actions CI/CD<br/>.github/workflows/deploy-backend.yml"]:::githubStyle
        GHCR[("GitHub Container Registry (GHCR)<br/>ghcr.io/org/finnie-backend:latest")]:::githubStyle
        GitRepo --> GHActions
        GHActions -->|Build & Push OCI Image| GHCR
    end

    subgraph Azure["Microsoft Azure Cloud Infrastructure"]
        subgraph SWA["Azure Static Web Apps (Free Tier)"]
            StaticApp["Azure Static Web App (finnie-frontend)<br/>Global Edge CDN · React 19 Vite SPA<br/>Free Auto-Renewing SSL Certificate"]:::azureFrontend
        end

        subgraph ACA["Azure Container Apps (Consumption Plan)"]
            ACAIngress["Azure Container Apps Ingress<br/>HTTPS Port 443 -> Container Port 80<br/>Free Auto-Renewing SSL Certificate"]:::azureBackend
            Container["Azure Container App (finnie-backend)<br/>0.5 vCPU · 1.0 GiB RAM · minReplicas=1, maxReplicas=1<br/>FastAPI · LangGraph · Gunicorn Multi-Worker"]:::azureBackend
            ACAIngress --> Container
        end

        subgraph Storage["Azure Persistence Layer"]
            AzureFiles[("Azure Files Storage Share (finnie-db-share)<br/>Standard LRS · Storage Account finnieprodstorage<br/>Mounted at /mnt/data/finnie.db via SMB")]:::azureStorage
            PostgreSHook[("Azure Database for PostgreSQL Flexible Server<br/>B1ms Burstable Instance<br/>Reserved Migration Hook via DATABASE_URL")]:::azureStorage
        end

        subgraph VectorStore["Semantic Retrieval Layer"]
            ChromaStore[("ChromaDB Vector Store Engine<br/>Collections: financial_kb · analytical_kb · goal_rules")]:::vectorStyle
        end
    end

    FrontDomain --> StaticApp
    ApiDomain --> ACAIngress
    GHCR -.->|Deploy Trigger / Secure Pull via PAT| Container
    Container -->|Persistent File I/O| AzureFiles
    Container -.->|Semantic RAG Queries| ChromaStore

    subgraph External["External Integrated APIs"]
        OpenAI["OpenAI API Service<br/>GPT-4o & GPT-4o-mini"]:::externalStyle
        YFinance["Yahoo Finance Market Service<br/>Live Market Quotes & Benchmarks"]:::externalStyle
        AlphaV["Alpha Vantage API Service<br/>News Sentiment & Stock Intel"]:::externalStyle
        Mailgun["Mailgun REST API Service<br/>Transactional OTP Password Resets"]:::externalStyle
    end

    Container --> OpenAI
    Container --> YFinance
    Container --> AlphaV
    Container --> Mailgun

    classDef clientStyle fill:#EBF3FC,stroke:#0078D4,stroke-width:2px,color:#002050;
    classDef dnsStyle fill:#E6F7FF,stroke:#0098FF,stroke-width:2px,color:#003A8C;
    classDef githubStyle fill:#F5EEF8,stroke:#6E40C9,stroke-width:2px,color:#24292F;
    classDef azureFrontend fill:#E6F4EA,stroke:#137333,stroke-width:2px,color:#0B5120;
    classDef azureBackend fill:#E3F2FD,stroke:#0078D4,stroke-width:2px,color:#0D47A1;
    classDef azureStorage fill:#FFF8E1,stroke:#F57C00,stroke-width:2px,color:#E65100;
    classDef vectorStyle fill:#F3E5F5,stroke:#8E24AA,stroke-width:2px,color:#4A148C;
    classDef externalStyle fill:#FBE9E7,stroke:#D84315,stroke-width:2px,color:#BF360C;
```

#### Cloud Architecture Decisions & Reference Matrix

| Component | Target Service | Cost Strategy | Architecture Notes |
|---|---|---|---|
| **Frontend Hosting** | Azure Static Web Apps | **$0.00** (Free Tier) | Global CDN edge caching, automatic GitHub builds (`dist`), custom domain `app.yourdomain.com` with free auto-renewing SSL. |
| **Container Registry** | GitHub Container Registry (`ghcr.io`) | **$0.00** (Free Tier) | Built via GitHub Actions (`deploy-backend.yml`), eliminating Azure Container Registry ($5/mo) costs. |
| **Backend Compute** | Azure Container Apps | **~$5.00 – $12.00 / mo** | Serverless Linux container (0.5 vCPU, 1.0 GiB RAM), Gunicorn/Uvicorn workers, custom domain `api.yourdomain.com` with free auto-renewing SSL. |
| **Database Storage** | Azure Files (Standard LRS) | **~$0.10 – $0.30 / mo** | Persistent SMB file share mounted at `/mnt/data/finnie.db`. Single-replica invariant (`minReplicas: 1, maxReplicas: 1`) prevents SQLite file-locking conflicts. |
| **Future Database Hook** | Azure PostgreSQL Flexible Server | Ready for Zero-Code Swap | Swap `DB_PATH` for `DATABASE_URL=postgresql://...` to enable multi-replica horizontal scaling (`maxReplicas > 1`). |
| **Vector Store** | ChromaDB Cloud / Local Volume | **$0.00** (Free Tier / Mounted) | Regulatory, analytical, and goal planning semantic vector embeddings. |
| **Custom Domains & SSL** | Domain Registrar DNS | **$0.00** (Azure Managed SSL) | CNAME records point `app.yourdomain.com` and `api.yourdomain.com` with automated TLS certificate generation. |

---

## Complete Setup Guide

Follow these steps in exact order to configure, ingest data, and launch both the backend and frontend of Finnie AI on your local machine.

### Step 1: Core Backend Setup
Finnie AI uses **[uv](https://docs.astral.sh/uv/)**—a lightning-fast Python package manager.

1. **Install uv** (one-time setup if you don't have it):
   ```bash
   brew install uv
   ```
2. **Sync Dependencies**:
   ```bash
   cd backend
   uv sync
   ```
3. **Set your Environment**:
   Duplicate `.env.example` to `.env` and fill in your keys (OpenAI, LangSmith, AlphaVantage, etc.):
   ```bash
   cp .env.example .env
   ```

---

### Step 2: Data Ingestion (ChromaDB Vector Store)

Finnie relies on three distinct "Knowledge Bases" stored in ChromaDB to provide theoretically grounded RAG answers. You must ingest this data before the agents can function properly.

We have built a flexible routing system allowing you to test locally for free, or push to the Cloud.

#### Option A: Ingesting to Local Disk (Default)
If you want to save the databases strictly to a hidden folder on your hard drive (`chroma_data_local`):
```bash
# Ingest definitions & introductory data
uv run python scripts/ingest/investor_gov_scraper.py --db local --reset

# Ingest deep theoretical and analytical benchmarks
uv run python scripts/ingest/load_html_analytical_kb.py --db local --reset

# Ingest 2026 US IRS & India Tax Rules for Goal Planning
uv run python scripts/ingest/ingest_regulatory_kb.py --db local --reset
```

> **Note**: The `--reset` flag ensures that if you run the script multiple times, it deletes the old collection before re-uploading, preventing duplicate chunks!

#### Option B: Ingesting to ChromaDB Cloud (Production)
If you want to view and manage these collections on your web dashboard, you must provide your `CHROMA_API_KEY` in `.env` and use the `--db cloud` flag:
```bash
uv run python scripts/ingest/investor_gov_scraper.py --db cloud --reset
uv run python scripts/ingest/load_html_analytical_kb.py --db cloud --reset
uv run python scripts/ingest/ingest_regulatory_kb.py --db cloud --reset
```

---

### Step 3: Starting the Backend Application

Once your data is successfully ingested, boot the FastAPI server to expose the Multi-Agent orchestrator.

```bash
# Ensure you are still in the backend folder
uv run uvicorn main:app --reload --port 8000
```
*The backend is now actively listening on `http://localhost:8000`.*

---

### Step 4: Testing Agents as Standalone (CLI)

You can test the core LangGraph reasoning engines directly via the terminal without needing the frontend. Open a **new terminal tab** and run:

```bash
cd backend

# Test the core Supervisor routing and RAG Q&A
uv run python tests/test_graph.py

# Alternatively, test specific endpoints via cURL
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the Sharpe Ratio to me."}'
```
*You should see detailed Trace IDs and agent hand-offs print directly in your server logs!*

---

### Step 5: Starting the Frontend App

The frontend is a gorgeous, responsive React + Vite application styled with Vanilla CSS `glass-morphism` tokens.

Open a **new terminal tab**:
```bash
cd frontend

# Install Node dependencies (first time only)
npm install

# Start the Vite development server
npm run dev
```

---

### Step 6: Testing End-to-End via Browser

Your full-stack application is now online!

Open your web browser and navigate to:
**`http://localhost:5173`**

You can now test all features natively:
1. **Executive Edge (Dashboard)**: Automatically fetches live `yfinance` market data for dynamic multi-country wealth tracking.
2. **My Holdings**: Add sample stocks (`AAPL`, `RELIANCE.NS`, etc.) grouped by country into your SQLite database.
3. **Portfolio Analyst**: Features country-specific benchmark routing (`^GSPC` for US, `^NSEI` for India, `^FTSE` for UK, etc.), All-Markets combined view, formatted 3-card AI insights, instant session caching, manual "Refresh Analysis" button, and on-demand **Portfolio Deep-Dive Copilot Drawer**.
4. **Market Insights**: Fetches real-time sentiment analysis from Alpha Vantage with persistent 30-minute SQLite caching and **Ticker Deep-Dive Copilot Drawer**.
5. **Goal Planner**: Runs 10,000-scenario Monte Carlo simulations cross-referenced against RAG-ingested tax rules, with Recharts fan chart, interactive milestone synthesis, and **Autonomous Strategy Copilot Drawer** with what-if scenario chips!

---

## Core Architecture Documentation

If you want to dive deeper into how specific features were engineered, check the streamlined documentation suite:

| Document | Focus Area | Contents & Implementation Details |
|---|---|---|
| [**AGENTS.md**](./AGENTS.md) | Universal Agent Constitution | Coding standards, 4-space/2-space indentation rules, and feature lifecycles |
| [**Goal Planner Deep-Dive**](./docs/agentic_architecture/GOAL_PLANNER.md) | Agentic Use Case Architecture | End-to-end technical implementation of the Goal Planner, 10k Monte Carlo engine, statutory tax RAG, and Copilot Drawer |
| [**DATA_MODEL.md**](./docs/DATA_MODEL.md) | Database Architecture & ERD | Single source of truth for all 7 database tables, ER diagram, constraints, and migrations |
| [**specs/**](./specs/) | Spec-Driven Development (SDD) | Baseline verified specs (SPEC-01 to 05) & upcoming feature spec templates |
| [**FEATURES_AND_AGENTS.md**](./docs/FEATURES_AND_AGENTS.md) | Feature Intelligence | Technical & functional specifications for all 5 core features and agent nodes |
| [**ARCHITECTURE.md**](./docs/ARCHITECTURE.md) | System Architecture | LangGraph hub-and-spoke topologies, state schemas, and LangSmith observability |
| [**KNOWLEDGE_BASE_AND_RAG.md**](./docs/KNOWLEDGE_BASE_AND_RAG.md) | Grounding & Vectors | ChromaDB 3-collection strategy, embeddings factory, and scraping pipelines |
| [**UI_DESIGN_SYSTEM.md**](./docs/UI_DESIGN_SYSTEM.md) | Glass-Finance UX | Design tokens, custom hook architecture, `RoadmapRenderer`, and design standards |
| [**UI_PREVIEW.md**](./docs/UI_PREVIEW.md) | Visual UI Gallery | High-fidelity screenshots for all 6 workspace dashboards and agent views |
| [**DEPLOYMENT.md**](./docs/DEPLOYMENT.md) | Cloud & Containers | Multi-worker Gunicorn Docker setup, persistent mounts, and Azure deployment |
| [**PROGRESS_LOG.md**](./docs/PROGRESS_LOG.md) | Progress & Changelog | Date-stamped accomplishment logs, phase completions, and test records |
| [**PROJECT_PLAN.md**](./docs/PROJECT_PLAN.md) | Product Roadmap | Strategic vision, future analytical use-cases (UC-PA-1 through UC-PA-6) |
| [**CODE_REVIEW.md**](./docs/CODE_REVIEW.md) | Technical Debt & Audit | Senior engineering review and prioritized improvement roadmap |

