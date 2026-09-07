
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class FinnieState(TypedDict):
    """
    The shared state for the Finnie AI LangGraph.
    This acts as the 'memory' passed between the Supervisor and Workers.
    """

    # The history of the conversation, appended to rather than overwritten  
    messages: Annotated[list[AnyMessage], add_messages]

    # Context injected by agents as they fetch data
    market_context: Optional[dict]

    # Determines the next routing behavior (e.g., 'FINANCIAL_QA' or 'FINISH')
    next_step: Optional[str]

    # The user's active holdings (injected from SQLite)
    # Format: [{"ticker": "AAPL", "shares": 10}, ...]
    portfolio_data: Optional[list[dict]]

    # Structured results from analysis (Beta, Volatility, etc.)
    # Format: {"beta": 1.2, "volatility": 15.4, "diversification_score": 7}
    analysis_results: Optional[dict]

    # Persistent goal configuration for the Goal Strategist
    # Format: {"target_amount": 1000000, "target_year": 2035, "monthly_savings": 500, "country": "USA"}
    goal_configuration: Optional[dict]


    # The unique request ID tied to LangSmith traces and system logs
    trace_id: Optional[str]

    # Country scope for Portfolio Analyst ("US", "IN", "ALL", etc.)
    # When set, the analyst filters holdings and benchmark to this country only.
    analysis_country: Optional[str]

    # Authenticated user tenant ID
    user_id: Optional[str]
