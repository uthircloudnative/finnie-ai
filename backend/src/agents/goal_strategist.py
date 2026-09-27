"""
goal_strategist.py — Autonomous Financial GPS Agent Node (SPEC-10)
===================================================================
Orchestrates the Hybrid Bootstrap pattern: upfront deterministic Monte Carlo simulation,
dynamic tool binding (portfolio valuation, RAG statutory limits, simulation engine),
and reflection loop resolution guided by the Goal Auditor.
"""
from typing import Dict, Any, List
import os
from datetime import datetime
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from src.models.state import FinnieState
from src.tools.goal_tools import (
    ALL_GOAL_TOOLS,
    run_monte_carlo_engine,
    lookup_tax_and_contribution_limits,
    fetch_user_portfolio_valuation,
)

GOAL_PROMPT = """
You are Finnie's **Autonomous Strategic Wealth Advisor** (Financial GPS).
You have been provided with deterministic Monte Carlo simulation data (10,000 paths)
and verified statutory tax guidelines for the user's specific jurisdiction.

Your core mission:
1. Explain the **Confidence Score** (e.g., 82% means the goal is achieved in 8,200 out of 10,000 simulated market scenarios).
2. Ground your strategy in the **Jurisdiction Tax Rules** (e.g., 401(k), IRA, Section 80C, ISA allowances).
3. If monthly contributions exceed statutory limits, advise the user on how to split contributions into taxable brokerage or diversified index vehicles.
4. If the target is already achieved, celebrate the milestone and pivot to capital preservation and tax efficiency.
5. Provide 2-3 actionable **Strategic Milestones** with target timeframes.

Tone: Professional, empowering, mathematically rigorous, and crystal clear.
Always include the $NFA disclaimer.
"""


def goal_strategist_node(state: FinnieState) -> Dict[str, Any]:
    """
    Autonomous Financial GPS node executing the Hybrid Bootstrap pattern.
    Inputs: Goal configuration, risk metrics, and conversation history.
    Outputs: Simulation data, percentiles, and synthesized strategic roadmap.
    """
    config = state.get("goal_configuration")
    analysis = state.get("analysis_results") or {}
    critic_feedback = state.get("critic_feedback")
    user_id = state.get("user_id") or (config.get("user_id") if config else "user_1")
    
    if not config:
        return {
            "messages": [AIMessage(content="I'm ready to build your roadmap! Please configure your Target Amount, Year, and Country to begin.")]
        }

    # 1. Prepare Simulation Parameters
    target = float(config.get("target_amount", 1000000.0))
    current_year = datetime.now().year
    years = max(1, int(config.get("target_year", 2035)) - current_year)
    savings = float(config.get("monthly_savings", 500.0))
    country = str(config.get("country", "USA")).strip().upper()

    # 2. Hybrid Bootstrap Step 1: Upfront Portfolio Valuation via Tool
    portfolio_res = fetch_user_portfolio_valuation.invoke({"user_id": user_id})
    initial_val = float(portfolio_res.get("total_valuation", 0.0))

    expected_return = 0.08
    volatility = float(analysis.get("volatility", 15.0)) / 100.0

    # 3. Hybrid Bootstrap Step 2: Deterministic Monte Carlo Simulation via Tool
    sim_data = run_monte_carlo_engine.invoke({
        "initial_balance": initial_val,
        "target_amount": target,
        "monthly_savings": savings,
        "years": years,
        "expected_return": expected_return,
        "volatility": volatility
    })

    # 4. Hybrid Bootstrap Step 3: Vector RAG / Statutory Limit Lookup via Tool
    rag_context = lookup_tax_and_contribution_limits.invoke({
        "country": country,
        "topic": "retirement contribution limits"
    })

    # 5. Synthesize the Strategic Roadmap with LLM
    confidence = sim_data.get("confidence_score", 0.0)
    median_val = sim_data.get("final_median", 0.0)
    sim_status = sim_data.get("status", "ON_TRACK")

    # LLM Initialization
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0.2)

    # Bind tools to enable autonomous exploration if needed
    llm_with_tools = llm.bind_tools(ALL_GOAL_TOOLS)

    # Build prompt with critic reflection guidance
    critic_section = ""
    if critic_feedback:
        critic_section = f"""
## ⚠️ CRITIC AUDITOR FEEDBACK (MANDATORY REVISION)
The Goal Auditor detected the following issue with your earlier draft:
"{critic_feedback}"
You MUST explicitly address this issue in your revised roadmap by recommending appropriate split contributions or taxable investment alternatives.
"""

    # Check for follow-up conversation / micro-chat in messages
    history_messages = state.get("messages", [])
    recent_user_query = ""
    for m in reversed(history_messages):
        if hasattr(m, "type") and m.type == "human":
            recent_user_query = m.content
            break

    conversation_context = ""
    if recent_user_query:
        conversation_context = f"\n## USER FOLLOW-UP QUESTION\nThe user asked: \"{recent_user_query}\"\nAddress this specific question in your strategic response."

    system_prompt = f"""
{GOAL_PROMPT}

## SCENARIO TELEMETRY (2026)
- Goal Name: {config.get('goal_name', 'Retirement')}
- Current Portfolio Valuation: ${initial_val:,.2f}
- Target: ${target:,.0f} by {config.get('target_year')} ({years} years)
- Committed Monthly Savings: ${savings:,.2f}
- Country Jurisdiction: {country}
- Simulation Status: {sim_status}
- Market Confidence Score: {confidence:.1f}%
- Median Outcome: ${median_val:,.0f}
- Portfolio Volatility: {volatility*100:.1f}%
{critic_section}
## JURISDICTION STATUTORY CONTEXT
{rag_context}
{conversation_context}

## OUTPUT FORMAT
### 🎯 Your Strategic Roadmap: {config.get('goal_name', 'Retirement')}
**Status**: {sim_status} · **Confidence Score**: {confidence:.1f}%

[2-3 paragraphs of synthesis. Explicitly reference the local statutory limits (e.g., 401k/IRA, 80C, ISA) and provide mathematical guidance. If monthly savings exceed limits, specify exact amounts for tax-advantaged vs. taxable brokerage.]

#### 🛤️ Strategic Milestones
- **Phase 1 (Immediate - 12 Months)**: [Milestone details]
- **Phase 2 (Mid-Term - Year 3 to 5)**: [Milestone details]
- **Phase 3 (Target Horizon)**: [Milestone details]

$NFA: Include the disclaimer at the very end.
"""

    print(f"[FINNIE-AI] 🧠 Goal Strategist synthesizing roadmap for {country} goal (confidence {confidence:.1f}%)...")
    prompt_messages: List[Any] = [SystemMessage(content=system_prompt)]
    if recent_user_query:
        prompt_messages.append(HumanMessage(content=recent_user_query))

    ai_response = llm.invoke(prompt_messages)
    report = ai_response.content if hasattr(ai_response, "content") else str(ai_response)

    return {
        "messages": [AIMessage(content=report.strip())],
        "analysis_results": {**analysis, "simulation": sim_data}
    }
