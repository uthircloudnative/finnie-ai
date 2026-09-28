"""
goal_auditor.py — Reflection / Critic Node for Autonomous Financial GPS (SPEC-10)
================================================================================
Audits proposed goals against country statutory contribution ceilings (IRS, HMRC,
Income Tax Act India, etc.). If limits are breached without appropriate guidance,
triggers a reflection loop back to the Goal Strategist (capped at 2 retries).
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from src.models.state import FinnieState


# Statutory monthly deduction / contribution ceilings for reflection checks
STATUTORY_MONTHLY_LIMITS = {
    "USA": 2541.67,     # $30,500/year (401k $23.5k + IRA $7k)
    "US": 2541.67,
    "INDIA": 16666.67,  # ₹2,00,000/year (80C ₹1.5L + 80CCD(1B) ₹50k)
    "IN": 16666.67,
    "UK": 1666.67,      # £20,000/year (ISA annual allowance)
    "CANADA": 2630.00,  # ~$31,560/year RRSP
    "CA": 2630.00,
    "GERMANY": 2297.00, # €27,566/year Basisrente
    "DE": 2297.00,
}

STATUTORY_KEYWORDS = {
    "USA": ["taxable", "brokerage", "after-tax", "spillover", "non-retirement"],
    "US": ["taxable", "brokerage", "after-tax", "spillover", "non-retirement"],
    "INDIA": ["mutual fund", "equity", "non-80c", "taxable", "direct equity"],
    "IN": ["mutual fund", "equity", "non-80c", "taxable", "direct equity"],
    "UK": ["sipp", "pension", "taxable", "general investment", "gia"],
    "CANADA": ["tfsa", "taxable", "non-registered"],
    "CA": ["tfsa", "taxable", "non-registered"],
    "GERMANY": ["etf", "depot", "taxable", "anlage"],
    "DE": ["etf", "depot", "taxable", "anlage"],
}


def goal_auditor_node(state: FinnieState) -> Dict[str, Any]:
    """
    Reflection node that audits the synthesized roadmap against jurisdiction rules.
    
    If limits are exceeded and no mitigation is mentioned:
      - retry_count < 2: Sets critic_feedback and prompts goal_strategist to revise.
      - retry_count >= 2: Appends statutory warning callout to report to avoid infinite loops.
    """
    print("[FINNIE-AI] 🔍 Entering Goal Auditor Node (Deterministic Critic / Reflection, 0 LLM calls)...")
    config = state.get("goal_configuration") or {}
    messages = state.get("messages") or []
    savings = float(config.get("monthly_savings", 0.0))
    country = str(config.get("country", "USA")).strip().upper()
    retry_count = int(state.get("critic_retry_count") or 0)

    # Check for statutory limit breach
    limit = STATUTORY_MONTHLY_LIMITS.get(country)
    violation = None

    if limit and savings > limit:
        last_ai_content = ""
        for m in reversed(messages):
            if hasattr(m, "type") and m.type == "ai":
                last_ai_content = m.content.lower()
                break

        keywords = STATUTORY_KEYWORDS.get(country, ["taxable", "brokerage"])
        has_mitigation = any(kw in last_ai_content for kw in keywords)

        if not has_mitigation:
            if country in ("USA", "US"):
                violation = (
                    f"Monthly contribution of ${savings:,.2f} exceeds the 2026 combined IRS retirement "
                    f"contribution limit ($2,541.67/mo). The roadmap MUST explicitly advise directing the "
                    f"surplus beyond $2,541.67 into a taxable brokerage account."
                )
            elif country in ("INDIA", "IN"):
                violation = (
                    f"Monthly contribution of ₹{savings:,.2f} exceeds the 2026 Section 80C + 80CCD(1B) "
                    f"tax deduction ceiling of ₹16,666.67/mo. The roadmap MUST advise directing surplus savings "
                    f"into non-80C equity mutual funds or direct equities."
                )
            elif country == "UK":
                violation = (
                    f"Monthly contribution of £{savings:,.2f} exceeds the annual ISA allowance of "
                    f"£1,666.67/mo. The roadmap MUST advise utilizing personal pensions (SIPP) or "
                    f"general investment accounts for the excess."
                )
            else:
                violation = (
                    f"Monthly savings of {savings:,.2f} exceeds standard tax-advantaged account ceilings for {country}. "
                    f"The roadmap MUST advise splitting savings between tax-advantaged and taxable investment vehicles."
                )

    if violation:
        if retry_count < 2:
            print(f"[FINNIE-AI] ⚠️ Goal Auditor detected violation (attempt {retry_count + 1}/2): {violation}")
            return {
                "critic_feedback": violation,
                "critic_retry_count": retry_count + 1
            }
        else:
            print(f"[FINNIE-AI] ⚠️ Goal Auditor retry threshold reached ({retry_count}). Appending statutory callout.")
            # Gracefully append caution callout to avoid crashing
            last_msg = messages[-1] if messages else None
            callout = f"\n\n> ⚠️ **Statutory Notice**: {violation}"
            updates: Dict[str, Any] = {
                "critic_feedback": None,
                "critic_retry_count": retry_count
            }
            if last_msg and hasattr(last_msg, "content"):
                updates["messages"] = [AIMessage(content=last_msg.content + callout, id=last_msg.id)]
            return updates

    print("[FINNIE-AI] ✅ Goal Auditor approved strategy. All statutory bounds satisfied.")
    return {
        "critic_feedback": None,
        "critic_retry_count": 0
    }
