# finnie-ai: Architectural Design & System Depth

## 1. Multi-Agent Orchestration (LangGraph)
Finnie utilizes a **Stateful Supervisor** pattern to manage complex financial workflows.

### 1.1 The Graph State
```python
class FinnieState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_portfolio: Optional[dict]
    market_context: Optional[dict]
    goals: list[dict]
    next_step: str
```

### 1.2 Agent Specialization
- **Supervisor (LLM: GPT-4o)**: Decomposes tasks. Routes to workers using structured output (`RouterChoice`).
- **Financial Q&A**: RAG-based retrieval from a vector store (FAISS/ChromaDB).
- **Market Insights**: Dynamic tool use (Python REPL/Stock APIs) to interpret live data.
- **Portfolio Analyst**: Data-intensive node for calculating financial metrics.
- **Goal Strategist**: Probabilistic forecasting engine.
- **Compliance Guardian**: Post-generation validator scanning for regulatory compliance and risk disclaimers.

## 2. Technical Stack
- **Backend Core**: Python 3.12+, FastAPI, LangGraph, Pydantic AI.
- **Frontend Core**: React 18, Vite, TypeScript, Framer Motion (Animations).
- **Intelligence**: OpenAI GPT-4o, **Vendor-agnostic Embeddings Factory** (supporting OpenAI, Azure, and Hugging Face).
- **Persistence & Retrieval**: 
    - **Vector Store**: ChromaDB (**Hybrid**: On-disk for local dev, **Chroma Cloud** for production).
    - **Session Cache**: Redis (for graph state persistence).
    - **Primary DB**: PostgreSQL (User profiles and historical portfolio data).

## 3. UX/UI: The "Glass-Finance" Philosophy
- **Aesthetics**: Dark Navy/Carbon background (`#0a0b10`), white translucent cards (Glassmorphism), primary accent `cyan-400`.
- **Navigation**: Persistent multi-tab sidebar (Dashboard, Portfolio, Insights, Chat).
- **Feedback**: Skeleton loaders and agent "thinking" statuses to manage async latency.
