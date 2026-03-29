"""
goal_strategist.py — The LangGraph node for target-based goal planning
======================================================================
Combines Monte Carlo math with RAG-based tax and regulatory rules.
"""
from typing import Dict, Any
import os
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage
from src.models.state import FinnieState
from src.utils.simulations import run_monte_carlo
from src.utils.vector_store import VectorStoreManager

# Mock/Expert prompts for goal synthesis
GOAL_PROMPT = """
You are Finnie's **Strategic Wealth Advisor**. You have been given a financial goal and 10,000 Monte Carlo simulation results.

Your job:
1.  Explain the **Confidence Score** (e.g. 82% means you win in 8,200 out of 10,000 futures).
2.  Use the **RAG Context** to identify any legal or tax hurdles (like contribution limits).
3.  Provide 2-3 specific **Strategic Milestones** to improve the outcome.

Maintain a professional, encouraging, yet mathematically-grounded tone.
Always include the $NFA disclaimer.
"""


def goal_strategist_node(state: FinnieState) -> Dict[str, Any]:
    """
    Orchestrates the 'Financial GPS' logic.
    Inputs: Goal config + Portfolio Risk
    Outputs: Simulation data + Strategic Roadmap report
    """
    config = state.get("goal_configuration")
    analysis = state.get("analysis_results") or {}
    
    if not config:
        return {
            "messages": [AIMessage(content="I'm ready to build your roadmap! Please set your Target Amount, Year, and Country in the 'Goal Configurator' form to begin.")]
        }

    # 1. Prepare Simulation Inputs
    target = config.get("target_amount", 1000000.0)
    years = max(1, config.get("target_year", 2035) - 2024) # Simplified timeline
    savings = config.get("monthly_savings", 500.0)
    country = config.get("country", "USA")
    
    # Use Portfolio Analyst risk metrics as the baseline
    # Default to 8% return and 15% volatility if portfolio is empty
    initial_val = sum(h.get("shares", 0) * 100 for h in state.get("portfolio_data", [])) # Mock price $100
    expected_return = 0.08 
    volatility = analysis.get("volatility", 15.0) / 100.0 # Convert from percentage

    # 2. Run the Math Engine (Monte Carlo)
    sim_data = run_monte_carlo(
        initial_balance=initial_val,
        target_amount=target,
        monthly_savings=savings,
        years=years,
        expected_return=expected_return,
        volatility=volatility
    )

    # 3. RAG Validation (Country Rules)
    # Filter by user's selected country to apply local tax/regulatory context
    vector_store = VectorStoreManager(collection_name="goal_rules")
    rag_context = ""
    try:
        search_query = f"Financial contribution limits and tax rules for {country} retirement goals"
        # Use our custom .search() to apply the metadata filter correctly
        results = vector_store.search(search_query, k=3, target_country=country)
        rag_context = "\n\n".join([r.page_content for r in results])
    except Exception as e:
        print(f"[FINNIE-AI] RAG Error in Goal Strategist: {e}")
        rag_context = "No specific local rules found. Proceeding with standard global assumptions."

    # 4. Synthesize the Strategic Roadmap (LLM Report)
    confidence = sim_data["confidence_score"]
    
    # ── LLM Setup ──
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0.2)

    # ── Instruction Prompt ──
    # We pass the raw scenario data and the legal rules to the LLM for reasoning
    system_prompt = f"""
{GOAL_PROMPT}

## SCENARIO DATA (2026)
- Goal: {config.get('goal_name')}
- Target: ${target:,.0f} by {config.get('target_year')}
- Monthly Savings: ${savings}
- Country: {country}
- Market Confidence Score: {confidence}%
- Median Outcome: ${sim_data['final_median']:,.0f}
- Portfolio Volatility: {volatility*100:.1f}%

## RAG REGULATORY CONTEXT
{rag_context}

## OUTPUT FORMAT
Your report MUST follow this structure:
### 🎯 Your Strategic Roadmap: [Goal Name]
[Brief Status: ON TRACK, CAUTION, or AT RISK]

[2-3 paragraphs of synthesis. Explicitly mention the local tax rules found in RAG context (e.g. 80C, 401k limits) and how they impact the goal.]

#### 🛤️ Strategic Milestones
- [Milestone 1]
- [Milestone 2]
- [Milestone 3]

$NFA: Include the disclaimer at the very end.
"""
    
    print(f"[FINNIE-AI] 🧠 Synthesizing Strategic Roadmap for {country} goal...")
    ai_response = llm.invoke([SystemMessage(content=system_prompt)])
    report = ai_response.content

    # 5. Return the report + the raw simulation data for the UI charts
    return {
        "messages": [AIMessage(content=report.strip())],
        "analysis_results": {**analysis, "simulation": sim_data} # Feed the UI charts
    }
