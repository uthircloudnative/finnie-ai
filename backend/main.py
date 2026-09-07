"""
Finnie AI — FastAPI Application Entry Point
============================================
Run locally with:
    uv run uvicorn main:app --reload --port 8000

Endpoints:
    GET  /health                    - Liveness check (no LLM call)
    POST /chat                      - Send a message; get Finnie's response
    GET  /portfolio/{user_id}       - Fetch saved holdings for a user
    POST /portfolio/save            - Save/replace holdings for a user
"""
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Load .env before importing anything that needs API keys
load_dotenv()

from src.graph import finnie_app                      # noqa: E402
from src.models.chat import ChatRequest, ChatResponse  # noqa: E402
from src.database import get_db, init_db              # noqa: E402
from src.models.portfolio import Holding              # noqa: E402
from src.models.market_metadata import MarketExchange # noqa: E402
from src.models.goal import FinancialGoal           # noqa: E402
from src.utils.telemetry import TraceContextMiddleware, setup_telemetry_logging, trace_id_var # noqa: E402
from src.utils.dashboard_engine import build_dashboard_payload # noqa: E402
from src.agents.portfolio_analyst import compute_hhi_diversification # noqa: E402
from src.models.user import User # noqa: E402
from src.models.auth_schemas import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse # noqa: E402
from src.auth.jwt import hash_password, verify_password, create_access_token, get_current_user # noqa: E402

# ---------------------------------------------------------------------------
# Telemetry Bootstrap
# ---------------------------------------------------------------------------
setup_telemetry_logging()


# ---------------------------------------------------------------------------
# Pydantic schemas (request / response shapes for Portfolio endpoints)
# ---------------------------------------------------------------------------
class HoldingInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. 'AAPL'")
    shares: float = Field(..., gt=0, description="Number of shares held (must be > 0)")
    country: str = Field(default="US", description="ISO country code, e.g. 'US' or 'IN'")
    exchange: str = Field(default="NYSE", description="Exchange name, e.g. 'NASDAQ' or 'NSE'")


class SavePortfolioRequest(BaseModel):
    user_id: str = Field(default="user_1", description="User identifier")
    holdings: List[HoldingInput] = Field(..., min_length=1)


class HoldingResponse(BaseModel):
    ticker: str
    shares: float
    country: str
    exchange: str
    added_date: str  # ISO date string


class PortfolioResponse(BaseModel):
    user_id: str
    holdings: List[HoldingResponse]
    total_holdings: int


class ExchangeResponse(BaseModel):
    country_name: str
    country_code: str
    exchange_name: str
    exchange_code: str


class GoalRequest(BaseModel):
    user_id: str = Field(default="user_1")
    goal_name: str = Field(default="Retirement")
    target_amount: float
    target_year: int
    monthly_savings: float
    country: str = Field(default="US")


# ---------------------------------------------------------------------------
# App bootstrap — init DB on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup (idempotent — safe to call every time)."""
    init_db()
    yield


app = FastAPI(
    title="Finnie AI",
    description="Multi-agent personal finance guide powered by LangGraph.",
    version="0.1.0",
    lifespan=lifespan,
)

# Insert the Tracing middleware
app.add_middleware(TraceContextMiddleware)

# CORS origins — driven by env var so deployed frontends are not blocked.
# Local default: Vite dev server. Azure: set ALLOWED_ORIGINS to your Static Web App URL.
# Example: ALLOWED_ORIGINS="https://finnie-ai.azurestaticapps.net,https://www.finnie.app"
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://localhost:3000"
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Ops"])
async def health_check() -> dict:
    """Quick liveness probe — never touches the LLM."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------
@app.post("/auth/register", response_model=TokenResponse, tags=["Auth"])
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account and return a JWT access token."""
    existing_user = db.query(User).filter(User.email == req.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "email": new_user.email})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(new_user))


@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and return a JWT access token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@app.get("/auth/me", response_model=UserResponse, tags=["Auth"])
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Fetch profile details for the active authenticated user."""
    return UserResponse.model_validate(current_user)


@app.get("/metadata/exchanges", response_model=List[ExchangeResponse], tags=["Metadata"])
def get_exchanges(db: Session = Depends(get_db)) -> List[ExchangeResponse]:
    """
    Fetch the master list of supported global exchanges.
    Used for searchable dropdowns in the UI.
    """
    exchanges = db.query(MarketExchange).all()
    return [
        ExchangeResponse(
            country_name=ex.country_name,
            country_code=ex.country_code,
            exchange_name=ex.exchange_name,
            exchange_code=ex.exchange_code
        )
        for ex in exchanges
    ]


# ---------------------------------------------------------------------------
# Dashboard (Global Wealth View)
# ---------------------------------------------------------------------------
@app.get("/dashboard/{user_id}", tags=["Dashboard"])
@app.get("/dashboard", tags=["Dashboard"])
def get_dashboard(user_id: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lightning-fast, deterministic dashboard payload.
    Bypasses LLM entirely to strictly crunch SQLite and live yfinance data.
    """
    effective_id = current_user.id
    return build_dashboard_payload(effective_id, db)


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChatResponse:
    """
    Send a message to Finnie and receive her response.
    Injects the user's current holdings from SQLite into the graph state.
    """
    effective_id = current_user.id
    # 1. Fetch latest holdings to provide as context to any agent
    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    holdings = [{"ticker": r.ticker, "shares": r.shares} for r in rows]

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "portfolio_data": holdings,
        "next_step": request.preferred_worker,
        "analysis_results": request.analysis_context,
        "user_id": effective_id,
        "trace_id": trace_id_var.get()
    }

    try:
        t_id = trace_id_var.get()
        config = {"metadata": {"app_trace_id": t_id}} if t_id else {}
        final_state = await finnie_app.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent graph failed: {exc}") from exc

    messages = final_state.get("messages", [])
    last_message = messages[-1] if messages else None

    if last_message is None or last_message.type != "ai":
        raise HTTPException(
            status_code=500,
            detail=(
                f"Agent routed to '{final_state.get('next_step')}' "
                "but no reply was generated. This worker is not yet implemented."
            ),
        )

    return ChatResponse(
        reply=str(last_message.content),
        analysis_results=final_state.get("analysis_results")
    )


# ---------------------------------------------------------------------------
# Portfolio — My Holdings
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Portfolio — My Holdings
# ---------------------------------------------------------------------------
@app.get("/portfolio/analysis/{user_id}", response_model=ChatResponse, tags=["Portfolio"])
@app.get("/portfolio/analysis", response_model=ChatResponse, tags=["Portfolio"])
async def get_portfolio_analysis(
    user_id: Optional[str] = None,
    country: Optional[str] = Query(default=None, description="Filter analysis to a specific country code (e.g. 'US', 'IN'). Omit for all-markets view."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Trigger a full portfolio analysis report for the user.
    Optionally scoped to a single country for country-specific benchmark and RAG context.
    Forces the graph to start at the 'portfolio_analyst' node.
    """
    effective_id = current_user.id
    query = db.query(Holding).filter(Holding.user_id == effective_id)
    if country and country.upper() != "ALL":
        query = query.filter(Holding.country == country.upper())
    rows = query.all()

    if not rows:
        scope = f"in {country.upper()}" if country and country.upper() != "ALL" else ""
        return ChatResponse(reply=f"You don't have any holdings {scope}. Add some stocks in the 'My Holdings' tab first!".strip())

    # Pass exchange + country per holding so the analyst can route the correct benchmark
    holdings = [
        {"ticker": r.ticker, "shares": r.shares, "exchange": r.exchange, "country": r.country}
        for r in rows
    ]

    scope_label = country.upper() if country and country.upper() != "ALL" else "all markets"
    initial_state = {
        "messages": [HumanMessage(content=f"Please provide a full risk and diversification analysis of my {scope_label} holdings.")],
        "portfolio_data": holdings,
        "next_step": "PORTFOLIO_ANALYST",
        "analysis_country": country.upper() if country and country.upper() != "ALL" else "ALL",
        "user_id": effective_id,
        "trace_id": trace_id_var.get()
    }

    try:
        t_id = trace_id_var.get()
        config = {"metadata": {"app_trace_id": t_id}} if t_id else {}
        final_state = await finnie_app.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    messages = final_state.get("messages", [])
    return ChatResponse(
        reply=str(messages[-1].content) if messages else "Analysis failed.",
        analysis_results=final_state.get("analysis_results")
    )


@app.get("/portfolio/diversification/{user_id}", tags=["Portfolio"])
@app.get("/portfolio/diversification", tags=["Portfolio"])
async def get_portfolio_diversification(
    user_id: Optional[str] = None,
    country: Optional[str] = Query(default=None, description="Filter analysis to a specific country code (e.g. 'US', 'IN'). Omit for all-markets view."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    On-demand real-time calculation of diversification score for a user's holdings.
    Retries up to 3 times to fetch yfinance sector metadata.
    """
    effective_id = current_user.id
    query = db.query(Holding).filter(Holding.user_id == effective_id)
    if country and country.upper() != "ALL":
        query = query.filter(Holding.country == country.upper())
    rows = query.all()

    if not rows:
        return {"diversification_score": 0.0, "sectors": {}, "error": None}

    # Map symbols to exchange suffixes for yfinance lookup
    exchange_map = {row.exchange_code: row.yf_suffix for row in db.query(MarketExchange).all()}
    symbols = []
    for r in rows:
        suffix = exchange_map.get(r.exchange, "")
        symbol = f"{r.ticker}{suffix}" if suffix and not r.ticker.endswith(suffix) else r.ticker
        symbols.append(symbol)

    score, sectors = compute_hhi_diversification(symbols, max_retries=3)

    if score is None:
        return {
            "diversification_score": None,
            "sectors": {},
            "error": "Experiencing technical issue, try again later"
        }

    return {
        "diversification_score": score,
        "sectors": sectors,
        "error": None
    }


@app.get("/market/news/{user_id}", response_model=ChatResponse, tags=["Market"])
@app.get("/market/news", response_model=ChatResponse, tags=["Market"])
async def get_market_news(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Fetch the latest market news and sentiment pulse for the user's portfolio.
    Routes directly to the 'market_insights' agent.
    """
    effective_id = current_user.id
    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    # Even if no holdings, the agent can provide a general pulse
    holdings = [
        {"ticker": r.ticker, "shares": r.shares, "country": r.country, "exchange": r.exchange} 
        for r in rows
    ]

    initial_state = {
        "messages": [HumanMessage(content="What is the latest market pulse for my holdings?")],
        "portfolio_data": holdings,
        "next_step": "MARKET_INSIGHTS",
        "user_id": effective_id,
        "trace_id": trace_id_var.get()
    }

    try:
        t_id = trace_id_var.get()
        config = {"metadata": {"app_trace_id": t_id}} if t_id else {}
        final_state = await finnie_app.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Market news failed: {exc}") from exc

    messages = final_state.get("messages", [])
    return ChatResponse(
        reply=str(messages[-1].content) if messages else "No news found.",
        analysis_results=final_state.get("analysis_results")
    )


@app.get("/portfolio/{user_id}", response_model=PortfolioResponse, tags=["Portfolio"])
@app.get("/portfolio", response_model=PortfolioResponse, tags=["Portfolio"])
def get_portfolio(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PortfolioResponse:
    """
    Fetch all saved holdings for a user.
    Returns an empty holdings list if the user has no saved portfolio yet.
    """
    effective_id = current_user.id
    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    return PortfolioResponse(
        user_id=effective_id,
        holdings=[
            HoldingResponse(
                ticker=r.ticker.upper(),
                shares=r.shares,
                country=r.country,
                exchange=r.exchange,
                added_date=str(r.added_date),
            )
            for r in rows
        ],
        total_holdings=len(rows),
    )


@app.post("/portfolio/save", response_model=PortfolioResponse, tags=["Portfolio"])
def save_portfolio(
    req: SavePortfolioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PortfolioResponse:
    """
    Save (replace) the full portfolio for a user.

    Strategy: Delete-and-Replace
      - Delete all existing rows for this user_id
      - Insert the new set of holdings
    This ensures the saved state always perfectly mirrors what the user submitted.
    """
    effective_id = current_user.id
    # 1. Delete existing holdings for this user
    db.query(Holding).filter(Holding.user_id == effective_id).delete()

    # 2. Insert the new holdings
    new_rows = []
    for h in req.holdings:
        row = Holding(
            user_id=effective_id,
            ticker=h.ticker.upper(),
            shares=h.shares,
            country=h.country.upper() if h.country else "US",
            exchange=h.exchange.upper() if h.exchange else "NYSE",
            added_date=date.today(),
        )
        db.add(row)
        new_rows.append(row)

    db.commit()
    for row in new_rows:
        db.refresh(row)

    return PortfolioResponse(
        user_id=effective_id,
        holdings=[
            HoldingResponse(
                ticker=r.ticker,
                shares=r.shares,
                country=r.country,
                exchange=r.exchange,
                added_date=str(r.added_date),
            )
            for r in new_rows
        ],
        total_holdings=len(new_rows),
    )


# ---------------------------------------------------------------------------
# Goals — The Financial GPS
# ---------------------------------------------------------------------------
@app.get("/goals/{user_id}", tags=["Goals"])
@app.get("/goals", tags=["Goals"])
def get_user_goal(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch the current financial goal for a user."""
    effective_id = current_user.id
    goal = db.query(FinancialGoal).filter(FinancialGoal.user_id == effective_id).first()
    if not goal:
        return {"status": "no_goal"}
    return {
        "goal_name": goal.goal_name,
        "target_amount": goal.target_amount,
        "target_year": goal.target_year,
        "monthly_savings": goal.monthly_contribution,
        "country": goal.country
    }


@app.post("/goals/calculate", response_model=ChatResponse, tags=["Goals"])
async def calculate_goal_roadmap(
    req: GoalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Save the user's goal and trigger a full Monte Carlo / RAG roadmap generation.
    """
    effective_id = current_user.id
    # 1. Persist/Update the goal in SQLite
    existing = db.query(FinancialGoal).filter(FinancialGoal.user_id == effective_id).first()
    if existing:
        existing.goal_name = req.goal_name
        existing.target_amount = req.target_amount
        existing.target_year = req.target_year
        existing.monthly_contribution = req.monthly_savings
        existing.country = req.country
    else:
        new_goal = FinancialGoal(
            user_id=effective_id,
            goal_name=req.goal_name,
            target_amount=req.target_amount,
            target_year=req.target_year,
            monthly_contribution=req.monthly_savings,
            country=req.country
        )
        db.add(new_goal)

    db.commit()

    # 2. Fetch latest holdings and last analysis results for the graph
    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    holdings = [{"ticker": r.ticker, "shares": r.shares} for r in rows]

    # Pre-configure the graph state with the new goal data
    initial_state = {
        "messages": [HumanMessage(content=f"Analyze my {req.goal_name} roadmap.")],
        "portfolio_data": holdings,
        "goal_configuration": {
            "target_amount": req.target_amount,
            "target_year": req.target_year,
            "monthly_savings": req.monthly_savings,
            "country": req.country,
            "goal_name": req.goal_name,
            "user_id": effective_id
        },
        "next_step": "GOAL_STRATEGIST",
        "user_id": effective_id,
        "trace_id": trace_id_var.get()
    }

    try:
        t_id = trace_id_var.get()
        config = {"metadata": {"app_trace_id": t_id}} if t_id else {}
        final_state = await finnie_app.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Goal Roadmap failed: {exc}") from exc

    messages = final_state.get("messages", [])
    return ChatResponse(
        reply=str(messages[-1].content) if messages else "Roadmap generation failed.",
        analysis_results=final_state.get("analysis_results")
    )
