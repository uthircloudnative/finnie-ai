# finnie-ai: Architectural Design & System Depth

> **Last Updated:** September 2026 · v0.4.0

---

## 1. Multi-Agent Orchestration (LangGraph)

Finnie utilises a **Stateful Supervisor** pattern. The `FinnieState` TypedDict is the shared memory passed between every node in the graph.

### 1.1 The Graph State

```python
class FinnieState(TypedDict):
    messages:         Annotated[list[AnyMessage], add_messages]
    portfolio_data:   Optional[list[dict]]    # [{ticker, shares, exchange, country}]
    analysis_results: Optional[dict]          # {beta, volatility, diversification_score,
                                              #  country, benchmark_name, country_betas, …}
    market_context:   Optional[dict]
    goal_configuration: Optional[dict]        # {target_amount, target_year, country, …}
    next_step:        Optional[str]
    trace_id:         Optional[str]
    analysis_country: Optional[str]           # "US" | "IN" | "ALL" — country scope for Analyst
    user_id:          Optional[str]           # UUID string of authenticated active user
```

### 1.2 Agent Specialisation & Functionality Model

| Functionality / Agent | Execution Mode | Agent Model | Tool Calls | Responsibility |
|---|---|---|---|---|
| **User Auth** | Programmatic | None | None | Registration, login, profile management (`bcrypt` + JWT Bearer) |
| **Global Wealth Dashboard** | Programmatic | None | yfinance | Instant SQLite aggregation + live asset prices |
| **Portfolio Holdings** | Programmatic | None | None | User-isolated CRUD database operations |
| **Diversification Score Retry** | Programmatic | None | yfinance (3 retries) | Sector HHI calculation with 3-attempt exponential backoff retry loop |
| **Supervisor Agent** | AI Agentic | Multi-Agent Router | None | Decomposes query intent, routes to workers via `RouterChoice` |
| **Financial Q&A Worker** | AI Agentic | Single Agent Node | ChromaDB RAG | Semantic retrieval from `financial_kb` ChromaDB collection |
| **Market Insights Worker** | AI Agentic | Single Agent Node | Alpha Vantage API | Alpha Vantage news/sentiment + 30-min SQLite cache + LLM synthesis |
| **Portfolio Analyst Worker** | AI Agentic | Multi-Agent (Country) | yfinance + ChromaDB RAG | Country-aware Beta/Vol/HHI math + `analytical_kb` RAG + LLM report |
| **Goal Strategist Worker** | AI Agentic | Single Agent Node | Monte Carlo + ChromaDB RAG | 10,000 scenario simulation + `goal_rules` tax RAG + GPT-4o report |
| **Compliance Guardian** | Post-processor | Safety Node | None | Appends `$NFA` disclaimer to every agent output before `END` |

---

## 2. High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Client["📱 Frontend (React 18 + Vite + TypeScript)"]
        UI[Glass-Finance Dashboard & Views]
        AuthCtx[AuthContext · Token Store & Bearer Injection]
        AuthMod[AuthModal · Sign In / Register]
        UI --> AuthCtx
        AuthMod --> AuthCtx
    end

    AuthCtx -->|HTTPS + Bearer JWT| Backend[FastAPI Backend · Python 3.13]

    subgraph Security["🔐 Security & Data Layer"]
        Backend -->|Verify Token| JWT[JWT Core & bcrypt · jwt.py]
        Backend -->|User Context| ORM[(SQLite Database<br/>users · holdings · goals · market_cache)]
    end

    subgraph Programmatic["⚙️ Programmatic Services (Deterministic · No LLM)"]
        Backend -->|Auth Endpoints| AuthSvc["🔑 User Auth (/auth/register, /auth/login, /auth/me)"]
        Backend -->|Direct Engine| DashSvc["📊 Global Wealth Dashboard (/dashboard)"]
        Backend -->|CRUD Operations| PortSvc["💼 Portfolio Holdings (/portfolio, /portfolio/save)"]
        Backend -->|3-Attempt Backoff Retry| DivSvc["🎯 Diversification Score Retry (/portfolio/diversification)"]
    end

    subgraph AgentSystem["🤖 LangGraph Multi-Agent Orchestrator"]
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

    subgraph Tools["🛠️ Agent Tool & Knowledge Layer"]
        QA       -.-|Tool Call: RAG Search| Chroma[(ChromaDB Vector Store<br/>financial_kb · analytical_kb<br/>goal_rules · market_news_kb)]
        Analyst  -.-|Tool Call: Benchmark & Prices| YFinance[Yahoo Finance API]
        Analyst  -.-|Tool Call: RAG Search| Chroma
        Insights -.-|Tool Call: News & Sentiment| AlphaV[Alpha Vantage API<br/>30-min SQLite Cache]
        Goals    -.-|Tool Call: 10k Simulations| MonteCarlo[Monte Carlo Engine]
        Goals    -.-|Tool Call: RAG Search| Chroma
    end

    subgraph LLMService["🌐 External LLM Services"]
        AgentSystem -.-|LLM Reasoning| OpenAI{OpenAI GPT-4o / Azure OpenAI}
        Backend     -.-|Telemetry| LangSmith[LangSmith Observability]
    end
```

---

## 3. Portfolio Analyst — Country-Aware Flow (Sep 2026)

```mermaid
sequenceDiagram
    participant FE as Frontend (useCountryPortfolio)
    participant API as FastAPI /portfolio/analysis
    participant PA as portfolio_analyst_node
    participant YF as yfinance
    participant Chroma as ChromaDB (analytical_kb)
    participant LLM as GPT-4o

    Note over FE: Page load → batch-fetch ALL + each country in parallel
    FE->>API: GET /portfolio/analysis/user_1?country=IN
    API->>API: Filter holdings WHERE country='IN'
    API->>PA: state {portfolio_data, analysis_country='IN'}

    PA->>PA: Map exchange → yfinance suffix (.NS for NSE)
    PA->>PA: Lookup benchmark: IN → ^NSEI (NIFTY 50)
    PA->>YF: Download 1yr prices [RELIANCE.NS, INFY.NS, ^NSEI]
    YF-->>PA: OHLCV DataFrame

    PA->>PA: Compute Beta vs ^NSEI, Annual Vol, HHI score

    PA->>Chroma: search(query, k=4, target_country='IN')
    Chroma-->>PA: 4 RAG chunks (India-specific or GLOBAL fallback)

    PA->>LLM: [SystemPrompt + math + RAG + messages]
    LLM-->>PA: 3-section analysis report

    PA-->>API: {analysis_results: {beta, volatility, diversification_score,<br/>benchmark_name, country_betas, sectors, vol_thresholds}}
    API-->>FE: ChatResponse {reply, analysis_results}
    Note over FE: Tab switch = instant (cache hit, zero LLM call)
```

---

## 4. Country → Benchmark Routing

| Country Code | Benchmark Ticker | Benchmark Name | Vol Thresholds |
|---|---|---|---|
| US | `^GSPC` | S&P 500 | low < 15%, high > 25% |
| IN | `^NSEI` | NIFTY 50 | low < 20%, high > 35% |
| GB | `^FTSE` | FTSE 100 | low < 15%, high > 28% |
| CA | `^GSPTSE` | S&P/TSX | low < 15%, high > 25% |
| DE | `^GDAXI` | DAX | low < 15%, high > 28% |
| _fallback_ | `^GSPC` | S&P 500 | 15 / 25 |

---

## 5. Technical Stack

| Layer | Technology |
|---|---|
| **Backend runtime** | Python 3.13, uv, FastAPI, Uvicorn/Gunicorn |
| **Agent orchestration** | LangGraph (stateful graph), LangChain |
| **LLM** | OpenAI GPT-4o (vendor-agnostic via `init_chat_model`) |
| **Embeddings** | Factory pattern: OpenAI / Azure OpenAI / HuggingFace |
| **Vector store** | ChromaDB — on-disk local dev, Chroma Cloud in production |
| **Primary database** | SQLite (holdings, goals, market cache) via SQLAlchemy ORM |
| **Live market data** | yfinance (prices), Alpha Vantage (news/sentiment) |
| **Frontend** | React 18, TypeScript, Vite, Vanilla CSS |
| **Observability** | LangSmith traces, custom `TraceContextMiddleware` |
| **Containerisation** | Docker (uv slim image), Gunicorn multi-worker |
| **Cloud target** | Azure App Service (backend), Azure Static Web Apps (frontend) |

---

## 6. UX/UI: The "Glass-Finance" Philosophy

- **Aesthetics**: Dark Navy/Carbon (`#0a0b10`), translucent glass cards (Glassmorphism), `cyan-400` primary accent
- **Navigation**: Persistent left sidebar (Dashboard, My Holdings, Portfolio Analyst, Market Insights, Goal Planner, Chat)
- **Portfolio Analyst**: Country tab bar — `🌍 All Markets`, `🇺🇸 US`, `🇮🇳 India` etc. Batch-loaded on mount, tab switch is always instant
- **Insight Cards**: LLM output parsed into 3 labelled section cards (📈 Risk, 🎯 Diversification, 💡 Advice) with coloured left borders — no raw markdown
- **Feedback**: Skeleton shimmer loaders, agent "thinking" indicators, pulse animations on risk-tier badges
