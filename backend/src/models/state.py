
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
