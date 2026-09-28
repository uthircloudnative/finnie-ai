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
from src.utils.dashboard_engine import build_dashboard_payload
from src.utils.simulations import run_monte_carlo
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


@tool
def fetch_user_portfolio_valuation(user_id: str) -> Dict[str, Any]:
    """
    Fetches the active user's total portfolio valuation across all asset holdings.
    
    Args:
        user_id: The authenticated user's tenant ID (derived from session).
        
    Returns:
        Dict containing total_valuation, asset_count, and holdings_summary.
    """
    db = SessionLocal()
    total_val = 0.0
    holdings_summary: List[Dict[str, Any]] = []

    try:
        # First, attempt live dashboard engine valuation (handles Yahoo Finance live prices)
        try:
            dash_data = build_dashboard_payload(user_id, db)
            if "portfolios" in dash_data and not dash_data.get("error"):
                for p in dash_data["portfolios"].values():
                    total_val += float(p.get("total_value", 0.0))
        except Exception as dash_err:
            print(f"[FINNIE-AI] Dashboard live valuation failed ({dash_err}); falling back to local prices.")

        # Query raw holdings from database
        rows = db.query(Holding).filter(Holding.user_id == user_id).all()
        for r in rows:
            pos_val = float(r.shares) * float(r.current_price or r.avg_cost or 0.0)
            holdings_summary.append({
                "ticker": r.ticker,
                "shares": r.shares,
                "exchange": r.exchange,
                "estimated_value": round(pos_val, 2)
            })

        # If live dashboard produced 0.0 but local holdings exist, use sum of local holdings
        if total_val <= 0.0 and holdings_summary:
            total_val = sum(h["estimated_value"] for h in holdings_summary)

        return {
            "user_id": user_id,
            "total_valuation": round(total_val, 2),
            "asset_count": len(rows),
            "holdings": holdings_summary[:10]  # Cap at top 10 for token efficiency
        }
    except Exception as e:
        print(f"[FINNIE-AI] Error in fetch_user_portfolio_valuation for {user_id}: {e}")
        return {
            "user_id": user_id,
            "total_valuation": 0.0,
            "asset_count": 0,
            "holdings": [],
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
    volatility: float = 0.15
) -> Dict[str, Any]:
    """
    Executes 10,000 Monte Carlo simulation runs and returns confidence score, median, and percentiles.
    
    Args:
        initial_balance: Current starting balance or portfolio value (defensively clamped >= 0).
        target_amount: Target goal amount to achieve (must be > 0).
        monthly_savings: Planned monthly contribution (defensively clamped >= 0).
        years: Time horizon in years (defensively clamped to minimum 1 year).
        expected_return: Expected annual return rate (default 0.08 for 8%).
        volatility: Annual portfolio volatility (default 0.15 for 15%).
        
    Returns:
        Dict containing confidence_score, target_amount, median_path, and percentiles for Fan Chart.
    """
    # Defensive bounds checking (EC-1, EC-3, EC-4)
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
            "message": f"Target of ${safe_target:,.0f} is already fully achieved with current balance of ${safe_balance:,.0f}."
        }

    # Execute numpy simulation
    sim_result = run_monte_carlo(
        initial_balance=safe_balance,
        target_amount=safe_target,
        monthly_savings=safe_savings,
        years=safe_years,
        expected_return=expected_return,
        volatility=safe_vol,
        num_simulations=10000
    )
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
    run_monte_carlo_engine,
    lookup_tax_and_contribution_limits
]
