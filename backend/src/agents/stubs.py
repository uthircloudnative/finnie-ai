from src.models.state import FinnieState
from langchain_core.messages import AIMessage

def market_insights_node(state: FinnieState) -> dict:
    """Placeholder for the Market Insights agent."""
    return {"messages": [AIMessage(content="I'm still learning how to read live market news! This feature is coming very soon to help you track your stocks.")]}

def goal_strategist_node(state: FinnieState) -> dict:
    """Placeholder for the Goal Strategist agent."""
    return {"messages": [AIMessage(content="Retirement planning and goal setting are in my training manual, but I'm not quite ready to calculate your roadmap yet. Stay tuned!")]}
