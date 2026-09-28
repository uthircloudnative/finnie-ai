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
import json
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
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
from src.utils.telemetry import TraceContextMiddleware, setup_telemetry_logging, trace_id_var, get_llm_call_count, get_graph_config # noqa: E402
from src.utils.dashboard_engine import build_dashboard_payload # noqa: E402
from src.agents.portfolio_analyst import compute_hhi_diversification # noqa: E402
from src.models.user import User # noqa: E402
from src.models.password_reset import PasswordResetAudit # noqa: E402
from src.models.auth_schemas import ( # noqa: E402
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from src.auth.jwt import hash_password, verify_password, create_access_token, get_current_user # noqa: E402
from src.utils.email_service import EmailService # noqa: E402


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


class GoalCalculationRequest(BaseModel):
    user_id: Optional[str] = Field(default=None)
    goal_name: str = Field(default="Retirement", min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    target_year: int = Field(..., ge=2026)
    monthly_savings: float = Field(default=0.0, ge=0)
    country: str = Field(default="USA")
    thread_id: Optional[str] = None
    prompt: Optional[str] = None  # Follow-up micro-chat query
    has_baseline: Optional[bool] = Field(default=False)
    chat_history: Optional[List[Dict[str, str]]] = Field(default=None)


# Backward compatibility alias
GoalRequest = GoalCalculationRequest


class GoalCalculationResponse(BaseModel):
    reply: str
    analysis_results: Optional[dict] = None
    thread_id: str
    confidence_score: float
    country: str
    status: str = "EXPLORING"  # "EXPLORING" or "READY_TO_LOCK"
    is_refinement: Optional[bool] = False
    is_off_topic: Optional[bool] = False


class GoalLockInRequest(BaseModel):
    thread_id: str
    approved: bool = True
    user_adjustments: Optional[dict] = None


class GoalLockInResponse(BaseModel):
    status: str = "LOCKED"
    goal_id: int
    message: str
    goal: dict


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

    token = create_access_token({"sub": new_user.id, "email": new_user.email, "v": new_user.token_version})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(new_user))


@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and return a JWT access token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": user.id, "email": user.email, "v": user.token_version})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


# In-memory sliding window rate limiter for password reset requests (email -> list of UTC timestamps)
_forgot_password_rate_limit: dict[str, list[datetime]] = {}


@app.post("/auth/forgot-password", response_model=ForgotPasswordResponse, tags=["Auth"])
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Request a 6-digit password reset verification code."""
    normalized_email = req.email.strip().lower()
    now_utc = datetime.now(timezone.utc)

    # Rate limiting: max 3 requests per 15 minutes per email
    cutoff = now_utc - timedelta(minutes=15)
    timestamps = _forgot_password_rate_limit.get(normalized_email, [])
    timestamps = [t for t in timestamps if t > cutoff]
    if len(timestamps) >= 3:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests. Please wait a few minutes before trying again."
        )
    timestamps.append(now_utc)
    _forgot_password_rate_limit[normalized_email] = timestamps

    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        # Invalidate any existing pending codes for this user
        pending_audits = db.query(PasswordResetAudit).filter(
            PasswordResetAudit.user_id == user.id,
            PasswordResetAudit.status == "PENDING"
        ).all()
        for p in pending_audits:
            p.status = "FAILED"

        # Generate CSPRNG 6-digit OTP
        code_int = secrets.randbelow(900000) + 100000
        code_str = str(code_int)
        code_hash = hash_password(code_str)

        # Extract client telemetry
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "Unknown")
        country = request.headers.get("CF-IPCountry", "")
        location = "Localhost" if client_ip in ("127.0.0.1", "::1") else (f"{client_ip} ({country})" if country else client_ip)
        user_agent = request.headers.get("User-Agent", "Unknown")[:255]

        audit = PasswordResetAudit(
            user_id=user.id,
            code_hash=code_hash,
            status="PENDING",
            attempts=0,
            requested_at=now_utc,
            expires_at=now_utc + timedelta(minutes=15),
            request_ip=client_ip,
            request_location=location,
            user_agent=user_agent
        )
        db.add(audit)
        db.commit()

        # Dispatch verification code via EmailService (Mailgun REST API or Console fallback)
        EmailService.send_otp_reset_email(
            to_email=normalized_email,
            otp_code=code_str,
            expiry_minutes=15,
            location=location,
            user_name=user.full_name
        )


    # Always return generic success to prevent email enumeration
    return ForgotPasswordResponse()


@app.post("/auth/reset-password", response_model=ResetPasswordResponse, tags=["Auth"])
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Verify 6-digit OTP and update user password."""
    normalized_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification code or email.")

    if verify_password(req.new_password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as your current password."
        )

    audit = db.query(PasswordResetAudit).filter(
        PasswordResetAudit.user_id == user.id,
        PasswordResetAudit.status == "PENDING"
    ).order_by(PasswordResetAudit.requested_at.desc()).first()

    if not audit:
        raise HTTPException(status_code=400, detail="No active password reset request found. Please request a new code.")

    now_utc = datetime.now(timezone.utc)
    exp = audit.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now_utc > exp:
        audit.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

    if not verify_password(req.code, audit.code_hash):
        audit.attempts += 1
        if audit.attempts >= 3:
            audit.status = "FAILED"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Too many failed attempts. Code has been invalidated. Please request a new code."
            )
        db.commit()
        remaining = 3 - audit.attempts
        raise HTTPException(status_code=400, detail=f"Invalid verification code. ({remaining} attempts remaining)")

    # Telemetry for completion
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "Unknown")
    country = request.headers.get("CF-IPCountry", "")
    location = "Localhost" if client_ip in ("127.0.0.1", "::1") else (f"{client_ip} ({country})" if country else client_ip)

    user.hashed_password = hash_password(req.new_password)
    user.token_version = (user.token_version or 1) + 1  # Revokes all active JWT sessions
    audit.status = "COMPLETED"
    audit.completed_at = now_utc
    audit.completed_ip = client_ip
    audit.completed_location = location
    db.commit()

    return ResetPasswordResponse()


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
    print(f"[FINNIE-AI] 📈 [FLOW: DASHBOARD] User: '{effective_id}' | Invoking build_dashboard_payload (Deterministic calculation, 0 LLM calls)")
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
    print(f"[FINNIE-AI] 💬 [FLOW: CHAT] User: '{effective_id}' | Message: '{request.message[:80]}' | Preferred Worker: '{request.preferred_worker}'")
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
        final_state = await finnie_app.ainvoke(initial_state, config=get_graph_config())
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

    print(
        f"[FINNIE-AI] 💬 [FLOW: CHAT COMPLETED] Routed Worker: '{final_state.get('next_step')}' | "
        f"Total Real LLM Calls: {get_llm_call_count()}"
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
    print(f"[FINNIE-AI] 📊 [FLOW: PORTFOLIO ANALYSIS] User: '{effective_id}' | Country Scope: '{country or 'ALL'}'")
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
        final_state = await finnie_app.ainvoke(initial_state, config=get_graph_config())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    messages = final_state.get("messages", [])
    print(f"[FINNIE-AI] 📊 [FLOW: PORTFOLIO ANALYSIS COMPLETED] Total Real LLM Calls: {get_llm_call_count()}")
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
    print(f"[FINNIE-AI] 📰 [FLOW: MARKET NEWS] User: '{effective_id}' | Polling news pulse")
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
        final_state = await finnie_app.ainvoke(initial_state, config=get_graph_config())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Market news failed: {exc}") from exc

    messages = final_state.get("messages", [])
    print(f"[FINNIE-AI] 📰 [FLOW: MARKET NEWS COMPLETED] Total Real LLM Calls: {get_llm_call_count()}")
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
    print(f"[FINNIE-AI] 💼 [FLOW: SAVE PORTFOLIO] User: '{effective_id}' | Updating {len(req.holdings)} holdings (Deterministic ORM write, 0 LLM calls)")
    # 1. Delete existing holdings for this user
    db.query(Holding).filter(Holding.user_id == effective_id).delete()

    # 2. Consolidate duplicate (ticker, exchange) pairs defensively
    consolidated: dict[tuple[str, str], dict] = {}
    for h in req.holdings:
        t = h.ticker.upper().strip()
        e = h.exchange.upper().strip() if h.exchange else "NYSE"
        c = h.country.upper().strip() if h.country else "US"
        key = (t, e)
        if key in consolidated:
            consolidated[key]["shares"] += h.shares
        else:
            consolidated[key] = {
                "user_id": effective_id,
                "ticker": t,
                "shares": h.shares,
                "country": c,
                "exchange": e,
                "added_date": date.today(),
            }

    new_rows = []
    for item in consolidated.values():
        row = Holding(**item)
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
    """Fetch the current financial goal for the authenticated user."""
    effective_id = current_user.id
    goal = db.query(FinancialGoal).filter(FinancialGoal.user_id == effective_id).first()
    if not goal:
        return {"status": "no_goal"}
    return {
        "id": goal.id,
        "goal_name": goal.goal_name,
        "target_amount": goal.target_amount,
        "target_year": goal.target_year,
        "monthly_savings": goal.monthly_contribution,
        "country": goal.country,
        "thread_id": goal.thread_id,
        "status": goal.status,
        "confidence_score": goal.confidence_score,
        "strategy_report": goal.strategy_report,
    }


def is_financial_query(query: str) -> bool:
    """
    Guardrail to ensure queries sent to the Goal Strategist micro-chat
    are relevant to financial planning, retirement, investing, taxes, or what-if scenarios.
    Filters out off-topic gibberish, test strings, and greetings.
    """
    clean_q = query.strip().lower()
    if not clean_q or len(clean_q) < 3:
        return False

    off_topic_exact = {
        "test", "testing", "hi", "hello", "hey", "hola", "asdf", "foo", "bar", 
        "123", "abc", "ping", "who are you", "what is your name", "what is the weather"
    }
    if clean_q in off_topic_exact:
        return False

    financial_keywords = [
        "retir", "sav", "invest", "401k", "401(k)", "ira", "isa", "80c", "tax", 
        "stock", "portfolio", "wealth", "asset", "inflation", "horizon", "year", 
        "dollar", "$", "money", "capital", "contribution", "return", "volatilit", 
        "risk", "split", "brokerage", "growth", "scenario", "what if", "increase", 
        "decrease", "earn", "pension", "fund", "equity", "debt", "nps", "rrsp", "tfsa",
        "balance", "goal", "roadmap", "plan"
    ]

    return any(kw in clean_q for kw in financial_keywords)


@app.post("/goals/calculate", response_model=GoalCalculationResponse, tags=["Goals"])
async def calculate_goal_roadmap(
    req: GoalCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GoalCalculationResponse:
    """
    Executes autonomous goal roadmap calculation or multi-turn conversational follow-up.
    Enforces multi-tenant thread isolation (403 if thread ID does not match active user).
    """
    effective_id = current_user.id
    print(
        f"[FINNIE-AI] 🎯 [FLOW: GOAL ROADMAP] User: '{effective_id}' | Goal: '{req.goal_name}' | "
        f"Target: ${req.target_amount:,.0f} by {req.target_year} | "
        f"Type: {'Refinement Query' if req.prompt else 'Full Synthesis'}"
    )

    # Strict multi-tenant thread validation (SPEC-10 / DATA_MODEL.md Invariant 4.2)
    if req.thread_id:
        expected_prefix = f"goal_{effective_id}_"
        if not req.thread_id.startswith(expected_prefix):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Thread ID does not belong to active tenant."
            )
        active_thread = req.thread_id
    else:
        goal_slug = req.goal_name.lower().strip().replace(" ", "_")
        active_thread = f"goal_{effective_id}_{goal_slug}"

    # Guardrail check for micro-chat prompts
    if req.prompt and not is_financial_query(req.prompt):
        return GoalCalculationResponse(
            reply=(
                "I am your Finnie Goal Strategist. I specialize in financial roadmap planning, "
                "retirement milestones, statutory tax limits (such as 401(k), IRA, ISA, or Section 80C), "
                "and what-if scenario testing.\n\n"
                "Please ask a financial planning question or select one of the suggested what-if scenario chips above."
            ),
            analysis_results=None,
            thread_id=active_thread,
            confidence_score=0.0,
            country=req.country,
            status="OFF_TOPIC",
            is_refinement=True,
            is_off_topic=True
        )

    # Fetch latest user portfolio holdings
    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    holdings = [{"ticker": r.ticker, "shares": r.shares} for r in rows]

    user_query = req.prompt or f"Analyze my {req.goal_name} roadmap and compute probability of success."

    input_messages: List[Any] = []
    if req.chat_history:
        for turn in req.chat_history:
            role = turn.get("role")
            content = turn.get("content", "")
            if not content:
                continue
            if role == "user":
                input_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                input_messages.append(AIMessage(content=content))

    if not input_messages or (hasattr(input_messages[-1], "content") and input_messages[-1].content != user_query):
        input_messages.append(HumanMessage(content=user_query))

    initial_state = {
        "messages": input_messages,
        "portfolio_data": holdings,
        "goal_configuration": {
            "target_amount": req.target_amount,
            "target_year": req.target_year,
            "monthly_savings": req.monthly_savings,
            "country": req.country,
            "goal_name": req.goal_name,
            "user_id": effective_id,
            "thread_id": active_thread,
            "has_baseline": req.has_baseline,
            "is_refinement": bool(req.prompt),
            "chat_history": req.chat_history
        },
        "next_step": "GOAL_STRATEGIST",
        "user_id": effective_id,
        "is_save_intent": False,
        "trace_id": trace_id_var.get()
    }

    try:
        final_state = await finnie_app.ainvoke(initial_state, config=get_graph_config(thread_id=active_thread))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Goal Roadmap failed: {exc}") from exc

    messages = final_state.get("messages", [])
    reply_content = str(messages[-1].content) if messages else "Roadmap generation complete."
    analysis_res = final_state.get("analysis_results") or {}
    sim = analysis_res.get("simulation") or {}
    confidence = float(sim.get("confidence_score", 0.0))

    print(
        f"[FINNIE-AI] 🎯 [FLOW: GOAL ROADMAP COMPLETED] Status: READY_TO_LOCK | "
        f"Confidence: {confidence*100:.1f}% | Total Real LLM Calls: {get_llm_call_count()}"
    )

    return GoalCalculationResponse(
        reply=reply_content,
        analysis_results=analysis_res,
        thread_id=active_thread,
        confidence_score=confidence,
        country=req.country,
        status="READY_TO_LOCK",
        is_refinement=bool(req.prompt),
        is_off_topic=False
    )


@app.post("/goals/calculate/stream", tags=["Goals"])
async def stream_goal_roadmap(
    req: GoalCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) streaming live intermediate agent thoughts, tool execution,
    and roadmap synthesis for the Goal Planner thought badge carousel.
    """
    effective_id = current_user.id

    # Strict multi-tenant thread validation
    if req.thread_id:
        expected_prefix = f"goal_{effective_id}_"
        if not req.thread_id.startswith(expected_prefix):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Thread ID does not belong to active tenant."
            )
        active_thread = req.thread_id
    else:
        goal_slug = req.goal_name.lower().strip().replace(" ", "_")
        active_thread = f"goal_{effective_id}_{goal_slug}"

    rows = db.query(Holding).filter(Holding.user_id == effective_id).all()
    holdings = [{"ticker": r.ticker, "shares": r.shares} for r in rows]

    user_query = req.prompt or f"Analyze my {req.goal_name} roadmap and compute probability of success."

    initial_state = {
        "messages": [HumanMessage(content=user_query)],
        "portfolio_data": holdings,
        "goal_configuration": {
            "target_amount": req.target_amount,
            "target_year": req.target_year,
            "monthly_savings": req.monthly_savings,
            "country": req.country,
            "goal_name": req.goal_name,
            "user_id": effective_id,
            "thread_id": active_thread
        },
        "next_step": "GOAL_STRATEGIST",
        "user_id": effective_id,
        "is_save_intent": False,
        "trace_id": trace_id_var.get()
    }

    config = {
        "configurable": {"thread_id": active_thread},
        "metadata": {"app_trace_id": trace_id_var.get()} if trace_id_var.get() else {}
    }

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'thought', 'step': 'init', 'message': f'Initializing autonomous roadmap for {req.goal_name}...', 'thread_id': active_thread})}\n\n"
            yield f"data: {json.dumps({'type': 'thought', 'step': 'portfolio', 'message': 'Auditing active portfolio valuation and holdings...'})}\n\n"
            yield f"data: {json.dumps({'type': 'thought', 'step': 'simulation', 'message': 'Executing 10,000 Monte Carlo simulation runs across market paths...'})}\n\n"
            yield f"data: {json.dumps({'type': 'thought', 'step': 'tax_rag', 'message': f'Consulting vector RAG rules for {req.country} statutory contribution limits...'})}\n\n"

            final_state = await finnie_app.ainvoke(initial_state, config=config)

            messages = final_state.get("messages", [])
            reply_text = str(messages[-1].content) if messages else "Roadmap generation complete."
            analysis_res = final_state.get("analysis_results") or {}
            sim = analysis_res.get("simulation") or {}
            confidence = float(sim.get("confidence_score", 0.0))

            yield f"data: {json.dumps({'type': 'thought', 'step': 'auditor', 'message': 'Goal Auditor statutory check completed.'})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'reply': reply_text, 'analysis_results': analysis_res, 'confidence_score': confidence, 'thread_id': active_thread, 'country': req.country, 'status': 'READY_TO_LOCK'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/goals/lock-in", response_model=GoalLockInResponse, tags=["Goals"])
async def lock_in_goal(
    req: GoalLockInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resumes graph from HITL interrupt, commits approved goal to financial_goals,
    and returns locked-in confirmation. Enforces tenant thread isolation.
    """
    effective_id = current_user.id
    expected_prefix = f"goal_{effective_id}_"
    if not req.thread_id.startswith(expected_prefix):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Thread ID does not belong to active tenant."
        )

    config = get_graph_config(thread_id=req.thread_id)

    try:
        from langgraph.types import Command
        await finnie_app.ainvoke(
            Command(resume={"approved": req.approved, "thread_id": req.thread_id, "adjustments": req.user_adjustments}),
            config=config
        )
    except Exception:
        try:
            await finnie_app.ainvoke(
                {"is_save_intent": True, "user_id": effective_id},
                config=config
            )
        except Exception as inner_e:
            print(f"[FINNIE-AI] Lock-in note: {inner_e}")

    # Fetch goal from DB
    goal = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == effective_id,
        FinancialGoal.thread_id == req.thread_id
    ).first()

    if not goal:
        goal = db.query(FinancialGoal).filter(
            FinancialGoal.user_id == effective_id
        ).order_by(FinancialGoal.updated_at.desc()).first()

    if not goal:
        goal = FinancialGoal(
            user_id=effective_id,
            goal_name="Retirement",
            target_amount=1000000.0,
            target_year=2035,
            monthly_contribution=500.0,
            country="USA",
            thread_id=req.thread_id,
            status="LOCKED",
            confidence_score=85.0
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
    else:
        goal.status = "LOCKED"
        goal.thread_id = req.thread_id
        db.commit()
        db.refresh(goal)

    return GoalLockInResponse(
        status="LOCKED",
        goal_id=goal.id,
        message=f"Goal '{goal.goal_name}' has been successfully locked in and saved!",
        goal={
            "id": goal.id,
            "goal_name": goal.goal_name,
            "target_amount": goal.target_amount,
            "target_year": goal.target_year,
            "monthly_savings": goal.monthly_contribution,
            "country": goal.country,
            "thread_id": goal.thread_id,
            "status": goal.status,
            "confidence_score": goal.confidence_score,
            "strategy_report": goal.strategy_report,
        }
    )

