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
from datetime import datetime, timezone
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from src.models.state import FinnieState
from src.tools.goal_tools import (
    ALL_GOAL_TOOLS,
    run_monte_carlo_engine,
    lookup_tax_and_contribution_limits,
    fetch_user_portfolio_valuation,
    fetch_user_liabilities_and_cashflow,
)
from src.utils.simulations import calculate_free_cashflow

GOAL_PROMPT = """
You are Finnie's **Autonomous Strategic Wealth Advisor** (Financial GPS).
You have been provided with deterministic Monte Carlo simulation data (10,000 paths),
monthly cash flow solvency telemetry, debt amortization models, and verified statutory tax guidelines for the user's jurisdiction.

Your core mission:
1. Provide a holistic balance sheet roadmap: Analyze the user's cash flow, debt liabilities, and portfolio investments together.
2. If the user carries outstanding debt liabilities, YOU MUST EXPLICITLY ADDRESS THEM AND PROVIDE ACTIONABLE ACCELERATION OPTIONS:
   - Detail their individual loan balances, interest rates (APR), and monthly payment drag.
   - Provide concrete options to accelerate debt elimination:
     * Option 1: Mathematical Debt Avalanche (Highest APR first) to minimize total interest paid.
     * Option 2: Cash Flow Optimization (Trimming discretionary spend / deploying net surplus) to shorten the debt-free timeline.
     * Option 3: Debt Rollover Compounding (Auto-step-up: rolling former debt payments directly into target goal investments).
   - Highlight the projected Debt-Free Year and cumulative interest saved.
   - Contrast borrowing costs (APR) with expected market returns (>10% APR debt prioritized before non-matched equity investing).
3. Explain the **Confidence Score** (e.g., 82% means the goal is achieved in 8,200 out of 10,000 simulated market scenarios).
4. Ground your investment strategy in the **Jurisdiction Tax Rules** (e.g., 401(k), IRA, Section 80C, ISA allowances).
5. If monthly contributions exceed statutory limits, advise the user on how to split contributions into taxable brokerage or diversified index vehicles.
6. Provide actionable **Strategic Milestones** with target timeframes that combine debt payoff and wealth accumulation.

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
    current_year = datetime.now(timezone.utc).year
    years = max(1, int(config.get("target_year", 2035)) - current_year)
    savings = float(config.get("monthly_savings", 500.0))
    country = str(config.get("country", "USA")).strip().upper()

    # 2. Hybrid Bootstrap Step 1: Upfront Portfolio Valuation via Tool (Scoped to Country)
    portfolio_res = fetch_user_portfolio_valuation.invoke({"user_id": user_id, "country": country})
    initial_val = float(portfolio_res.get("total_valuation", 0.0))
    asset_count = int(portfolio_res.get("asset_count", 0))
    holdings_list = portfolio_res.get("holdings", [])

    # Step 1b: Fetch Cashflow Profile & Liabilities (Merging form inputs with database records)
    liabilities_input = config.get("liabilities") or []
    cashflow_res = fetch_user_liabilities_and_cashflow.invoke({
        "user_id": user_id,
        "country": country,
        "committed_savings": savings
    })
    active_liabilities = liabilities_input if liabilities_input else cashflow_res.get("liabilities", [])

    # Merge form inputs with DB profile
    db_profile = cashflow_res.get("cashflow_profile") or {}
    take_home = float(config.get("monthly_take_home") or db_profile.get("monthly_take_home") or 0.0)
    fixed_costs = float(config.get("fixed_living_costs") or db_profile.get("fixed_living_costs") or 0.0)
    discretionary = float(config.get("monthly_discretionary_spend") or db_profile.get("monthly_discretionary_spend") or 0.0)

    cf_metrics = calculate_free_cashflow(
        monthly_take_home=take_home,
        fixed_living_costs=fixed_costs,
        monthly_discretionary_spend=discretionary,
        liabilities=active_liabilities,
        committed_savings=savings
    )
    free_cashflow = float(cf_metrics.get("free_cash_flow", 0.0))
    solvency_status = "SOLVENT" if cf_metrics.get("is_solvent") else "DEFICIT"
    net_margin = float(cf_metrics.get("net_cash_flow_margin", 0.0))
    total_monthly_debt = float(cf_metrics.get("total_monthly_debt_service", 0.0))
    total_debt_balance = sum(float(l.get("current_balance", 0.0)) for l in active_liabilities)

    expected_return = 0.08
    volatility = float(analysis.get("volatility", 15.0)) / 100.0

    if asset_count == 0:
        portfolio_telemetry = (
            f"- User Portfolio Status ({country}): No regional stock holdings linked ($0.00 initial balance).\n"
            "- Volatility Assumption: 15.0% broad-market benchmark standard deviation (e.g. S&P 500 equity index baseline), "
            "used purely for modeling future monthly savings.\n"
            "- CRITICAL TRUTH INVARIANT: The user has NO stock portfolio loaded in the system. NEVER tell the user 'as per your stock profile' "
            "or 'based on your stock variation'. If discussing volatility, explicitly state that since no individual stocks are linked, "
            "the simulation applies a standard 15.0% broad-market equity index assumption for future projected savings."
        )
    else:
        tickers = ", ".join(h.get("ticker", "") for h in holdings_list[:5])
        portfolio_telemetry = (
            f"- User Portfolio Status ({country}): {asset_count} regional asset(s) linked ({tickers}).\n"
            f"- Current Portfolio Valuation: ${initial_val:,.2f}.\n"
            f"- Portfolio Volatility: {volatility*100:.1f}% derived from active holdings."
        )

    # Cashflow & Liabilities Telemetry
    if active_liabilities:
        loans_breakdown = "\n".join(
            f"  • {l.get('lender_name') or l.get('liability_type', 'Loan')} ({l.get('liability_type', 'Loan')}): Balance ${float(l.get('current_balance', 0)):,.0f} | APR {float(l.get('interest_rate_apr', 0)):.1f}% | Monthly Payment ${float(l.get('monthly_payment', 0)):,.0f}/mo | Term: {int(l.get('remaining_months', 0))} mos"
            for l in active_liabilities
        )
        cashflow_telemetry = (
            f"- Monthly Take-Home Pay: ${take_home:,.2f}/mo\n"
            f"- Fixed Living Expenses: ${fixed_costs:,.2f}/mo\n"
            f"- Discretionary Spend: ${discretionary:,.2f}/mo\n"
            f"- Available Free Cash Flow: ${free_cashflow:,.2f}/mo\n"
            f"- Committed Monthly Goal Savings: ${savings:,.2f}/mo\n"
            f"- Total Monthly Debt Obligations: ${total_monthly_debt:,.2f}/mo across {len(active_liabilities)} account(s)\n"
            f"- Net Solvency Margin: ${net_margin:,.2f}/mo (Status: {solvency_status})\n"
            f"- Total Outstanding Debt Liabilities: {len(active_liabilities)} account(s) totaling ${total_debt_balance:,.2f}\n"
            f"- Active Debt Accounts Breakdown:\n{loans_breakdown}"
        )
    else:
        cashflow_telemetry = (
            f"- Monthly Take-Home Pay: ${take_home:,.2f}/mo\n"
            f"- Fixed Living Expenses: ${fixed_costs:,.2f}/mo\n"
            f"- Discretionary Spend: ${discretionary:,.2f}/mo\n"
            f"- Available Free Cash Flow: ${free_cashflow:,.2f}/mo\n"
            f"- Committed Monthly Goal Savings: ${savings:,.2f}/mo\n"
            f"- Net Solvency Margin: ${net_margin:,.2f}/mo (Status: {solvency_status})\n"
            f"- Active Debt Liabilities: None reported ($0 debt drag, fully unencumbered cash flow)."
        )

    # 3. Hybrid Bootstrap Step 2: Deterministic Cashflow & Net Worth Monte Carlo Simulation via Tool
    sim_data = run_monte_carlo_engine.invoke({
        "initial_balance": initial_val,
        "target_amount": target,
        "monthly_savings": savings,
        "years": years,
        "expected_return": expected_return,
        "volatility": volatility,
        "liabilities": active_liabilities,
        "auto_step_up": True
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
    debt_free_yr = sim_data.get("debt_free_year")
    interest_saved = float(sim_data.get("total_interest_saved", 0.0))

    if active_liabilities and debt_free_yr:
        cashflow_telemetry += (
            f"\n- Projected Debt-Free Year: {debt_free_yr}\n"
            f"- Estimated Lifetime Interest Saved: ${interest_saved:,.2f}"
        )

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
## CRITIC AUDITOR FEEDBACK (MANDATORY REVISION)
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
{cashflow_telemetry}
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
3. NO FULL ROADMAP OVERVIEW: Do NOT output "### Strategic Roadmap:" or full multi-phase milestones (Phase 1, Phase 2, Phase 3) unless the user specifically asks for milestone breakdowns.
4. NO REPETITIVE DISCLAIMERS: If a baseline roadmap has not yet been generated, answer their financial question directly first, then append a brief 1-line note: "Note: You can generate your full 10,000-scenario Monte Carlo simulation anytime using the 'Generate Roadmap' button on the left." Do NOT repeat the full form configuration parameters on every turn.
5. CONCISE & EMPIRICAL: Keep the response conversational, focused (1-2 crisp paragraphs or bullet points), and grounded in exact financial math and statutory rules.
6. HONEST PORTFOLIO RECOGNITION: If the user has 0 linked stock holdings, NEVER claim they have an existing stock profile or stock variation. State that 15% is a standard broad-market benchmark assumption for projected savings.
7. HOLISTIC BALANCE SHEET & DEBT GUIDANCE: If the user asks about debt, monthly cash flow, savings rate, or liabilities, leverage the live cash flow telemetry and liabilities list to provide exact debt amortization or avalanche strategy guidance.
8. PROFESSIONAL TYPOGRAPHY (NO EMOJIS): Do NOT use emojis anywhere in your output. Maintain a clean, professional financial tone.
9. Always end with the $NFA disclaimer.
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
### Strategic Roadmap: {config.get('goal_name', 'Retirement')}
**Status**: {sim_status} · **Confidence Score**: {confidence:.1f}%

[2-3 paragraphs of strategic synthesis. Explicitly reference local statutory limits (e.g., 401k/IRA, 80C, ISA) and provide mathematical guidance. If monthly savings exceed limits, specify exact amounts for tax-advantaged vs. taxable brokerage.]

#### Balance Sheet & Debt Drag Assessment
[Comprehensive assessment of the user's cash flow, monthly net disposable income, and outstanding debt obligations.
- If liabilities exist:
  * Detail each outstanding loan (Lender/Name, Balance, APR %, Monthly Payment).
  * Calculate total monthly debt servicing load and total outstanding liability balance.
  * Contrast borrowing costs (APR) with expected market returns. Apply the Debt Avalanche rule: recommend aggressively paying down high-interest liabilities (>10% APR) before expanding non-matched equity investing.
  * State projected debt freedom timeframe and cumulative interest savings.
  
  ##### Actionable Pathways to Accelerate Debt Elimination & Reach Target Faster
  Provide 3 concrete, comparative strategic options tailored to the user's numbers:
  1. **Option 1: Mathematical Debt Avalanche (Highest APR First)** — Target the highest-interest loan while maintaining minimums on others to eliminate total interest bleed.
  2. **Option 2: Cash Flow Optimization (Discretionary Trimming)** — Detail how reallocating a portion of monthly discretionary spend or surplus cash flow toward extra principal cuts months/years off the debt-free date.
  3. **Option 3: Post-Debt Rollover Compounding (Auto-Step-Up Multiplier)** — Direct 100% of freed-up monthly loan payments straight into the target goal investment portfolio once debts are eliminated, massively boosting final wealth.
- If zero liabilities exist:
  * Explicitly note that the balance sheet is free of high-interest debt, enabling 100% of discretionary surplus to compound directly toward the target.]

#### Strategic Milestones
- **Phase 1 (Immediate - 12 Months)**: [Emergency fund baseline, statutory matching capture, high-interest debt payoff prioritization via Debt Avalanche.]
- **Phase 2 (Mid-Term - Year 3 to 5)**: [Debt-free milestone achievement (if liabilities exist), statutory limit maximization (401k/IRA/80C), expanding core equity allocations.]
- **Phase 3 (Target Horizon - Year {years})**: [Final wealth accumulation: Reinvesting former debt payments directly into target goal compounding, rebalancing for capital preservation as target year nears.]

PROFESSIONAL FORMATTING REQUIREMENT:
Do NOT use emojis (such as 🎯, 🚀, 💡, 💳, 📈, 💰, etc.) anywhere in your output. Use clean, professional headings and standard Markdown.

$NFA: Include the disclaimer at the very end.
"""

        system_prompt = f"""
{GOAL_PROMPT}

## SCENARIO TELEMETRY (2026)
- Goal Name: {config.get('goal_name', 'Retirement')}
{portfolio_telemetry}
{cashflow_telemetry}
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
        "analysis_results": {
            **analysis, 
            "simulation": sim_data,
            "cashflow": cashflow_res,
            "liabilities": active_liabilities
        }
    }
