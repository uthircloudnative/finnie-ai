from langgraph.graph import START, END, StateGraph
from src.models.state import FinnieState
from src.agents.supervisor import supervisor_node
from src.agents.qa_agent import financial_qa_node
from src.agents.portfolio_analyst import portfolio_analyst_node
from src.agents.compliance import compliance_guardian_node
from src.agents.stubs import market_insights_node, goal_strategist_node


# 1. Initialize the Graph Builder
workflow = StateGraph(FinnieState)

# 2. Add our "Nodes" (The Worker Functions)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("financial_qa", financial_qa_node)
workflow.add_node("portfolio_analyst", portfolio_analyst_node)
workflow.add_node("market_insights", market_insights_node)
workflow.add_node("goal_strategist", goal_strategist_node)
workflow.add_node("compliance", compliance_guardian_node)

# 3. Define the Router Logic
def route_decision(state: FinnieState) -> str:
    """
    Reads the 'next_step' variable to decide which edge to take.
    """
    step = state.get("next_step")
    if step == "FINANCIAL_QA":
        return "financial_qa"
    elif step == "PORTFOLIO_ANALYST":
        return "portfolio_analyst"
    elif step == "MARKET_INSIGHTS":
        return "market_insights"
    elif step == "GOAL_STRATEGIST":
        return "goal_strategist"
    elif step == "FINISH":
        return "compliance"  # Always go through compliance!
    else:
        return "compliance"

def start_node(state: FinnieState) -> str:
    """
    Decides whether to go to the supervisor or directly to a worker.
    """
    # If the API already knows where to go (next_step is set), bypass supervisor
    if state.get("next_step"):
        return route_decision(state)
    return "supervisor"

# 4. Wiring the Edges (The Flow)
# Conditional START: Maps string names returned by start_node to actual node IDs
workflow.add_conditional_edges(
    START,
    start_node,
    {
        "supervisor": "supervisor",
        "financial_qa": "financial_qa",
        "portfolio_analyst": "portfolio_analyst",
        "market_insights": "market_insights",
        "goal_strategist": "goal_strategist",
        "compliance": "compliance"
    }
)

workflow.add_conditional_edges(
    "supervisor",
    route_decision, 
    {
        "financial_qa": "financial_qa",
        "portfolio_analyst": "portfolio_analyst",
        "market_insights": "market_insights",
        "goal_strategist": "goal_strategist",
        "compliance": "compliance"
    }
)

# After workers finish, they MUST go through compliance!
workflow.add_edge("financial_qa", "compliance")
workflow.add_edge("portfolio_analyst", "compliance")
workflow.add_edge("market_insights", "compliance")
workflow.add_edge("goal_strategist", "compliance")

# The only way to reach the end is via the Compliance Guardian
workflow.add_edge("compliance", END)

# 5. Compile the graph
finnie_app = workflow.compile()
