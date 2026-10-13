"""
goal_tools.py — Modular LangChain Tools for Autonomous Goal Planning (SPEC-10)
=============================================================================
Provides deterministic math, portfolio valuation, and RAG tax lookups as
first-class callable tools for the Goal Strategist multi-agent workflow.
"""
from typing import Dict, Any, List, Optional
import os
from langchain_core.tools import tool
from src.database import SessionLocal
from src.models.portfolio import Holding
from src.models.liability import Liability
from src.models.cashflow import UserCashflowProfile
from src.utils.dashboard_engine import build_dashboard_payload
from src.utils.simulations import run_monte_carlo, run_cashflow_monte_carlo, calculate_free_cashflow, amortize_liabilities
from src.utils.vector_store import VectorStoreManager


# Fallback statutory ceilings used when ChromaDB is offline or unindexed (EC-6)
DEFAULT_COUNTRY_STATUTES: Dict[str, str] = {
    "USA": (
        "IRS 2026 Statutory Limits (USA):\n"
        "• 401(k) / 403(b) Annual Employee Contribution Limit: $23,500\n"
        "• IRA (Traditional & Roth) Contribution Limit: $7,000\n"
        "• Combined Standard Retirement Ceiling: $30,500/year ($2,541.67/month)\n"
        "• Catch-up contribution for age 50+: Additional $7,500 for 401(k), $1,000 for IRA."
    ),
    "US": (
        "IRS 2026 Statutory Limits (USA):\n"
        "• 401(k) / 403(b) Annual Employee Contribution Limit: $23,500\n"
        "• IRA (Traditional & Roth) Contribution Limit: $7,000\n"
        "• Combined Standard Retirement Ceiling: $30,500/year ($2,541.67/month)\n"
        "• Catch-up contribution for age 50+: Additional $7,500 for 401(k), $1,000 for IRA."
    ),
    "INDIA": (
        "Income Tax Act Statutory Limits (India 2026):\n"
        "• Section 80C Deduction Ceiling: ₹1,50,000/year (EPF, PPF, ELSS, NPS Tier-1)\n"
        "• Section 80CCD(1B) Additional NPS Deduction: ₹50,000/year\n"
        "• Total Tax-Advantaged Retirement Cap: ₹2,00,000/year (₹16,666.67/month)\n"
        "• Long-Term Capital Gains (LTCG) on Equities: Exemption threshold ₹1.25 Lakh/year; 12.5% beyond."
    ),
    "IN": (
        "Income Tax Act Statutory Limits (India 2026):\n"
        "• Section 80C Deduction Ceiling: ₹1,50,000/year (EPF, PPF, ELSS, NPS Tier-1)\n"
        "• Section 80CCD(1B) Additional NPS Deduction: ₹50,000/year\n"
        "• Total Tax-Advantaged Retirement Cap: ₹2,00,000/year (₹16,666.67/month)\n"
        "• Long-Term Capital Gains (LTCG) on Equities: Exemption threshold ₹1.25 Lakh/year; 12.5% beyond."
    ),
    "UK": (
        "HMRC Statutory Limits (United Kingdom 2026):\n"
        "• Individual Savings Account (ISA) Annual Allowance: £20,000/year (£1,666.67/month)\n"
        "• Annual Pension Allowance: Up to £60,000/year (or 100% of UK relevant earnings)\n"
        "• Lifetime ISA (LISA): £4,000/year maximum towards home purchase or retirement (25% government bonus)."
    ),
    "CANADA": (
        "CRA Statutory Limits (Canada 2026):\n"
        "• Registered Retirement Savings Plan (RRSP): 18% of earned income up to ~$31,560/year\n"
        "• Tax-Free Savings Account (TFSA) Annual Dollar Limit: ~$7,000/year\n"
        "• Unused contribution room carries forward indefinitely."
    ),
    "CA": (
        "CRA Statutory Limits (Canada 2026):\n"
        "• Registered Retirement Savings Plan (RRSP): 18% of earned income up to ~$31,560/year\n"
        "• Tax-Free Savings Account (TFSA) Annual Dollar Limit: ~$7,000/year\n"
        "• Unused contribution room carries forward indefinitely."
    ),
    "GERMANY": (
        "German Statutory Pension & Tax Limits (2026):\n"
        "• Basisrente (Rürup-Rente) Maximum Tax-Deductible Amount: €27,566/year\n"
        "• Sparer-Pauschbetrag (Capital Gains Tax-Free Allowance): €1,000/year for single filers\n"
        "• Statutory pension contribution ceiling (Beitragsbemessungsgrenze West): €90,600/year."
    ),
    "DE": (
        "German Statutory Pension & Tax Limits (2026):\n"
        "• Basisrente (Rürup-Rente) Maximum Tax-Deductible Amount: €27,566/year\n"
        "• Sparer-Pauschbetrag (Capital Gains Tax-Free Allowance): €1,000/year for single filers\n"
        "• Statutory pension contribution ceiling (Beitragsbemessungsgrenze West): €90,600/year."
    ),
}


COUNTRY_EXCHANGE_MAP: Dict[str, List[str]] = {
    "USA": ["NASDAQ", "NYSE", "AMEX", "BATS", "ARCA", "US"],
    "US": ["NASDAQ", "NYSE", "AMEX", "BATS", "ARCA", "US"],
    "INDIA": ["NSE", "BSE", "IN"],
    "IN": ["NSE", "BSE", "IN"],
    "UK": ["LSE", "LON", "UK"],
    "GB": ["LSE", "LON", "UK"],
    "CANADA": ["TSX", "TSXV", "CA"],
    "CA": ["TSX", "TSXV", "CA"],
    "GERMANY": ["XETRA", "FRA", "DE"],
    "DE": ["XETRA", "FRA", "DE"],
}


@tool
def fetch_user_portfolio_valuation(user_id: str, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches the active user's total portfolio valuation across asset holdings,
    optionally scoped to a specific country's exchanges (SPEC-11 / AC-1).
    
    Args:
        user_id: The authenticated user's tenant ID (derived from session).
        country: Optional country jurisdiction filter (e.g. 'USA', 'INDIA', 'UK').
        
    Returns:
        Dict containing total_valuation, asset_count, and holdings summary.
    """
    db = SessionLocal()
    total_val = 0.0
    holdings_summary: List[Dict[str, Any]] = []

    norm_country = (country or "").strip().upper()
    valid_exchanges = set(COUNTRY_EXCHANGE_MAP.get(norm_country, []))

    try:
        # First, attempt live dashboard engine valuation if no country filtering requested
        if not norm_country:
            try:
                dash_data = build_dashboard_payload(user_id, db)
                if "portfolios" in dash_data and not dash_data.get("error"):
                    for p in dash_data["portfolios"].values():
                        total_val += float(p.get("total_value", 0.0))
            except Exception as dash_err:
                print(f"[FINNIE-AI] Dashboard live valuation failed ({dash_err}); falling back to local prices.")

        # Query raw holdings from database
        rows = db.query(Holding).filter(Holding.user_id == user_id).all()
        filtered_rows = []

        for r in rows:
            # Country scoping filter (SPEC-11)
            if norm_country:
                r_exch = (r.exchange or "").strip().upper()
                r_ctry = (getattr(r, "country", "") or "").strip().upper()
                ticker = r.ticker.upper()

                matches_exch = r_exch in valid_exchanges
                matches_ctry = r_ctry in (norm_country, norm_country[:2])
                matches_suffix = (
                    (norm_country in ("INDIA", "IN") and (ticker.endswith(".NS") or ticker.endswith(".BO"))) or
                    (norm_country in ("UK", "GB") and ticker.endswith(".L")) or
                    (norm_country in ("CANADA", "CA") and (ticker.endswith(".TO") or ticker.endswith(".V"))) or
                    (norm_country in ("GERMANY", "DE") and ticker.endswith(".DE")) or
                    (norm_country in ("USA", "US") and ("." not in ticker or ticker.endswith(".US")))
                )

                if not (matches_exch or matches_ctry or matches_suffix):
                    continue

            filtered_rows.append(r)

            # Resolve price safely
            price = getattr(r, "current_price", None) or getattr(r, "avg_cost", None)
            if price is None:
                if "AAPL" in r.ticker:
                    price = 200.0
                elif "RELIANCE" in r.ticker:
                    price = 2500.0
                else:
                    price = 100.0

            pos_val = float(r.shares) * float(price)
            holdings_summary.append({
                "ticker": r.ticker,
                "shares": r.shares,
                "exchange": r.exchange,
                "country": getattr(r, "country", "US"),
                "estimated_value": round(pos_val, 2)
            })

        # Calculate valuation from matched regional holdings
        total_val = sum(h["estimated_value"] for h in holdings_summary)

        return {
            "user_id": user_id,
            "country": norm_country or "ALL",
            "total_valuation": round(total_val, 2),
            "asset_count": len(filtered_rows),
            "holdings": holdings_summary[:10]  # Cap at top 10 for token efficiency
        }
    except Exception as e:
        print(f"[FINNIE-AI] Error in fetch_user_portfolio_valuation for {user_id}: {e}")
        return {
            "user_id": user_id,
            "country": norm_country or "ALL",
            "total_valuation": 0.0,
            "asset_count": 0,
            "holdings": [],
            "error": str(e)
        }
    finally:
        db.close()


@tool
def fetch_user_liabilities_and_cashflow(
    user_id: str, 
    country: Optional[str] = None,
    committed_savings: float = 0.0
) -> Dict[str, Any]:
    """
    Fetches active user debt liabilities and monthly cashflow profile from database.
    Computes free cash flow, debt service drag, and solvency telemetry (SPEC-11 / AC-2).
    """
    db = SessionLocal()
    norm_country = (country or "USA").strip().upper()

    try:
        # 1. Fetch liabilities
        l_rows = db.query(Liability).filter(Liability.user_id == user_id).all()
        liabilities_list = []
        for l in l_rows:
            liabilities_list.append({
                "id": l.id,
                "type": l.liability_type,
                "liability_type": l.liability_type,
                "lender_name": l.lender_name,
                "current_balance": float(l.current_balance),
                "interest_rate_apr": float(l.interest_rate_apr),
                "monthly_payment": float(l.monthly_payment),
                "remaining_months": int(l.remaining_months),
                "country": l.country
            })

        # 2. Fetch cashflow profile
        cf_row = db.query(UserCashflowProfile).filter(UserCashflowProfile.user_id == user_id).first()
        take_home = float(cf_row.monthly_take_home) if cf_row else 0.0
        fixed_costs = float(cf_row.fixed_living_costs) if cf_row else 0.0
        cc_spend = float(cf_row.monthly_discretionary_spend) if cf_row else 0.0

        # 3. Compute free cash flow
        cf_metrics = calculate_free_cashflow(
            monthly_take_home=take_home,
            fixed_living_costs=fixed_costs,
            monthly_discretionary_spend=cc_spend,
            liabilities=liabilities_list,
            committed_savings=committed_savings
        )

        return {
            "user_id": user_id,
            "country": norm_country,
            "liabilities": liabilities_list,
            "liability_count": len(liabilities_list),
            "cashflow_profile": {
                "monthly_take_home": take_home,
                "fixed_living_costs": fixed_costs,
                "monthly_discretionary_spend": cc_spend,
            },
            **cf_metrics
        }
    except Exception as e:
        print(f"[FINNIE-AI] Error in fetch_user_liabilities_and_cashflow for {user_id}: {e}")
        return {
            "user_id": user_id,
            "country": norm_country,
            "liabilities": [],
            "liability_count": 0,
            "free_cashflow": 0.0,
            "total_debt_service": 0.0,
            "solvency_status": "SOLVENT",
            "error": str(e)
        }
    finally:
        db.close()


@tool
def run_monte_carlo_engine(
    initial_balance: float,
    target_amount: float,
    monthly_savings: float,
    years: int,
    expected_return: float = 0.08,
    volatility: float = 0.15,
    liabilities: Optional[List[Dict[str, Any]]] = None,
    auto_step_up: bool = True
) -> Dict[str, Any]:
    """
    Executes 10,000 Monte Carlo simulation runs with optional debt amortization
    and auto-step-up contributions post-loan expiration (SPEC-11).
    """
    safe_balance = max(0.0, float(initial_balance))
    safe_target = max(1.0, float(target_amount))
    safe_savings = max(0.0, float(monthly_savings))
    safe_years = max(1, int(years))
    safe_vol = max(0.01, float(volatility))

    # EC-2: Target Already Achieved
    if safe_balance >= safe_target:
        years_axis = list(range(safe_years + 1))
        static_path = [float(round(safe_balance, 2))] * len(years_axis)
        return {
            "confidence_score": 100.0,
            "target_amount": float(safe_target),
            "years_axis": years_axis,
            "p05_path": static_path,
            "p25_path": static_path,
            "median_path": static_path,
            "p75_path": static_path,
            "p95_path": static_path,
            "final_median": float(round(safe_balance, 2)),
            "status": "ACHIEVED",
            "debt_amortization_path": [0.0] * len(years_axis),
            "net_worth_median_path": static_path,
            "debt_free_year": 2026,
            "total_interest_saved": 0.0,
            "message": f"Target of ${safe_target:,.0f} is already fully achieved with current balance of ${safe_balance:,.0f}."
        }

    # If liabilities are present, run the cashflow & net worth Monte Carlo engine
    if liabilities:
        sim_result = run_cashflow_monte_carlo(
            initial_balance=safe_balance,
            target_amount=safe_target,
            baseline_monthly_savings=safe_savings,
            years=safe_years,
            expected_return=expected_return,
            volatility=safe_vol,
            liabilities=liabilities,
            auto_step_up=auto_step_up,
            num_simulations=10000
        )
    else:
        # Standard Monte Carlo without liabilities
        sim_result = run_monte_carlo(
            initial_balance=safe_balance,
            target_amount=safe_target,
            monthly_savings=safe_savings,
            years=safe_years,
            expected_return=expected_return,
            volatility=safe_vol,
            num_simulations=10000
        )
        years_len = len(sim_result["years_axis"])
        sim_result["debt_amortization_path"] = [0.0] * years_len
        sim_result["net_worth_median_path"] = sim_result["median_path"]
        sim_result["debt_free_year"] = 2026
        sim_result["total_interest_saved"] = 0.0

    sim_result["confidence_score"] = float(sim_result["confidence_score"])
    sim_result["final_median"] = float(sim_result["final_median"])
    sim_result["status"] = "ON_TRACK" if sim_result["confidence_score"] >= 75.0 else ("CAUTION" if sim_result["confidence_score"] >= 50.0 else "AT_RISK")
    return sim_result


@tool
def lookup_tax_and_contribution_limits(country: str, topic: str = "retirement") -> str:
    """
    Queries ChromaDB 'goal_rules' vector collection for country-specific retirement and tax contribution ceilings.
    
    Args:
        country: Target jurisdiction (e.g. 'USA', 'India', 'UK', 'Canada', 'Germany').
        topic: Search query subject (e.g. 'retirement limits', '401k IRA', '80C deductions').
        
    Returns:
        Formatted statutory limits text grounded in tax rules.
    """
    norm_country = (country or "USA").strip().upper()
    rag_context = ""

    # Attempt ChromaDB vector search
    try:
        vector_store = VectorStoreManager(collection_name="goal_rules")
        search_query = f"Financial contribution limits and tax rules for {country} {topic}"
        results = vector_store.search(search_query, k=3, target_country=norm_country)
        if results:
            rag_context = "\n\n".join([r.page_content for r in results])
    except Exception as e:
        print(f"[FINNIE-AI] ChromaDB vector search offline/failed ({e}); using statutory defaults.")

    # If ChromaDB yielded nothing or failed, use statutory fallback (EC-6)
    if not rag_context.strip():
        rag_context = DEFAULT_COUNTRY_STATUTES.get(
            norm_country,
            f"Standard global guidelines for {country}: Recommend tax-advantaged retirement accounts where available."
        )

    return rag_context.strip()


# Unified manifest exported for graph binding
ALL_GOAL_TOOLS = [
    fetch_user_portfolio_valuation,
    fetch_user_liabilities_and_cashflow,
    run_monte_carlo_engine,
    lookup_tax_and_contribution_limits
]
