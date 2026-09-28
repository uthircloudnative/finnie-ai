"""
goal_strategist.py — Autonomous Financial GPS Agent Node (SPEC-10)
===================================================================
Orchestrates the Hybrid Bootstrap pattern: upfront deterministic Monte Carlo simulation,
dynamic tool binding (portfolio valuation, RAG statutory limits, simulation engine),
and reflection loop resolution guided by the Goal Auditor.
"""
from typing import Dict, Any, List
import os
import time
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
    asset_count = int(portfolio_res.get("asset_count", 0))
    holdings_list = portfolio_res.get("holdings", [])

    expected_return = 0.08
    volatility = float(analysis.get("volatility", 15.0)) / 100.0

    if asset_count == 0:
        portfolio_telemetry = (
            "- User Portfolio Status: No stock holdings linked ($0.00 initial balance).\n"
            "- Volatility Assumption: 15.0% broad-market benchmark standard deviation (e.g. S&P 500 equity index baseline), "
            "used purely for modeling future monthly savings.\n"
            "- CRITICAL TRUTH INVARIANT: The user has NO stock portfolio loaded in the system. NEVER tell the user 'as per your stock profile' "
            "or 'based on your stock variation'. If discussing volatility, explicitly state that since no individual stocks are linked, "
            "the simulation applies a standard 15.0% broad-market equity index assumption for future projected savings."
        )
    else:
        tickers = ", ".join(h.get("ticker", "") for h in holdings_list[:5])
        portfolio_telemetry = (
            f"- User Portfolio Status: {asset_count} asset(s) linked ({tickers}).\n"
            f"- Current Portfolio Valuation: ${initial_val:,.2f}.\n"
            f"- Portfolio Volatility: {volatility*100:.1f}% derived from active holdings."
        )

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

    is_refinement = bool(config.get("is_refinement"))
    has_baseline = bool(config.get("has_baseline"))

    if is_refinement:
        system_prompt = f"""
You are Finnie's **Autonomous Interactive Wealth Copilot & Financial GPS**.
The user is conversing with you directly in the Ask Finnie Strategy drawer.

CURRENT GOAL STATE:
- Goal: {config.get('goal_name', 'Retirement')}
{portfolio_telemetry}
- Target: ${target:,.0f} by {config.get('target_year')} ({years} years)
- Monthly Contribution: ${savings:,.2f}
- Jurisdiction: {country}
- Monte Carlo Confidence Score: {confidence:.1f}% (Median Path: ${median_val:,.0f})
- Baseline Roadmap Status: {"Generated & Active" if has_baseline else "Pending User Click on 'Generate Roadmap'"}

STATUTORY TAX GUIDELINES:
{rag_context}

CRITICAL RULES FOR CHAT INTERACTIONS:
1. ANSWER THE SPECIFIC QUESTION: Directly address the user's latest inquiry: "{recent_user_query}".
2. DO NOT REPEAT OLD ANSWERS: Treat previous questions and answers in this thread as read-only history. Do NOT repeat or paraphrase previous answers.
3. NO FULL ROADMAP OVERVIEW: Do NOT output "### 🎯 Your Strategic Roadmap:" or full multi-phase milestones (Phase 1, Phase 2, Phase 3) unless the user specifically asks for milestone breakdowns.
4. NO REPETITIVE DISCLAIMERS: If a baseline roadmap has not yet been generated, answer their financial question directly first, then append a brief 1-line note: "💡 You can generate your full 10,000-scenario Monte Carlo simulation anytime using the 'Generate Roadmap' button on the left." Do NOT repeat the full form configuration parameters on every turn.
5. CONCISE & EMPIRICAL: Keep the response conversational, focused (1-2 crisp paragraphs or bullet points), and grounded in exact financial math and statutory rules.
6. HONEST PORTFOLIO RECOGNITION: If the user has 0 linked stock holdings, NEVER claim they have an existing stock profile or stock variation. State that 15% is a standard broad-market benchmark assumption for projected savings.
7. Always end with the $NFA disclaimer.
"""
        prompt_messages: List[Any] = [SystemMessage(content=system_prompt)]

        # Extract prior dialogue turns (up to 8 messages) so LLM has read-only multi-turn context
        dialogue_history: List[Any] = []
        for m in history_messages:
            content = m.content if hasattr(m, "content") else str(m)
            msg_type = getattr(m, "type", "")
            if msg_type == "human" or (isinstance(m, dict) and m.get("role") == "user"):
                dialogue_history.append(HumanMessage(content=content))
            elif msg_type == "ai" or (isinstance(m, dict) and m.get("role") == "assistant"):
                dialogue_history.append(AIMessage(content=content))

        if dialogue_history and isinstance(dialogue_history[-1], HumanMessage) and dialogue_history[-1].content == recent_user_query:
            prompt_messages.extend(dialogue_history[-8:])
        else:
            prompt_messages.extend(dialogue_history[-8:])
            if recent_user_query:
                prompt_messages.append(HumanMessage(content=recent_user_query))
    else:
        output_format_instruction = f"""
## OUTPUT FORMAT (FULL ROADMAP SYNTHESIS)
### 🎯 Your Strategic Roadmap: {config.get('goal_name', 'Retirement')}
**Status**: {sim_status} · **Confidence Score**: {confidence:.1f}%

[2-3 paragraphs of synthesis. Explicitly reference the local statutory limits (e.g., 401k/IRA, 80C, ISA) and provide mathematical guidance. If monthly savings exceed limits, specify exact amounts for tax-advantaged vs. taxable brokerage.]

#### 🛤️ Strategic Milestones
- **Phase 1 (Immediate - 12 Months)**: [Milestone details]
- **Phase 2 (Mid-Term - Year 3 to 5)**: [Milestone details]
- **Phase 3 (Target Horizon)**: [Milestone details]

$NFA: Include the disclaimer at the very end.
"""

        system_prompt = f"""
{GOAL_PROMPT}

## SCENARIO TELEMETRY (2026)
- Goal Name: {config.get('goal_name', 'Retirement')}
{portfolio_telemetry}
- Target: ${target:,.0f} by {config.get('target_year')} ({years} years)
- Committed Monthly Savings: ${savings:,.2f}
- Country Jurisdiction: {country}
- Simulation Status: {sim_status}
- Market Confidence Score: {confidence:.1f}%
- Median Outcome: ${median_val:,.0f}
{critic_section}
## JURISDICTION STATUTORY CONTEXT
{rag_context}
{conversation_context}

{output_format_instruction}
"""
        prompt_messages = [SystemMessage(content=system_prompt)]
        if recent_user_query:
            prompt_messages.append(HumanMessage(content=recent_user_query))

    print(f"[FINNIE-AI] 🎲 [DETERMINISTIC ENGINE] Monte Carlo 10,000 scenarios ({years}y horizon) -> Confidence: {confidence:.1f}% | Median: ${median_val:,.0f} (0 LLM calls)")
    print(f"[FINNIE-AI] 📚 [DETERMINISTIC RAG] Statutory limits lookup for '{country}' complete (0 LLM calls)")

    ai_response = llm.invoke(prompt_messages)
    report = ai_response.content if hasattr(ai_response, "content") else str(ai_response)

    return {
        "messages": [AIMessage(content=report.strip())],
        "analysis_results": {**analysis, "simulation": sim_data}
    }
