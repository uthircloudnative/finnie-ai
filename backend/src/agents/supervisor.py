import os
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from typing import Literal
from src.models.state import FinnieState

# 1. THE BLUEPRINT (Data Structure for the LLM)
class RoutingDecision(BaseModel):
    """
    The choice of which agent to route the user's message to.
    """

    next_step: Literal["FINANCIAL_QA", "MARKET_INSIGHTS", 
    "PORTFOLIO_ANALYST", "GOAL_STRATEGIST", "FINISH"] = Field(
        description="The next agent to route to. Use FINISH if the user's request is completely fulfilled or if it's a casual greeting."
    )

def supervisor_node(state: FinnieState) -> dict:
    """
    The orchestrator that reads the chat history and decides who should act next.
    """

    user_message = state["messages"][-1].content
    print(f"\n[FINNIE-AI] 🔍 Supervisor reading user query: '{user_message}'")

    # Read vendor config from .env
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")

    # Force the LLM to output exactly our RoutingDecision blueprint
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0)

    structured_llm = llm.with_structured_output(RoutingDecision)
 
    system_prompt = (
        "You are Finnie, the Supervisor Agent for a financial advisory system.\n"
        "Your job is to route the user's query to the correct specialized worker.\n\n"
        "Workers available:\n"
        "- FINANCIAL_QA: For general financial definitions, investment theory (e.g., 'What is an ETF?').\n"
        "- MARKET_INSIGHTS: For live news, stock sentiment, and current market trends (e.g., 'What's happening with $NVDA?' or 'How is the market today?').\n"
        "- PORTFOLIO_ANALYST: For personal portfolio risk, diversification, and Beta analysis.\n"
        "- GOAL_STRATEGIST: For retirement or specific financial goal planning.\n"
        "- FINISH: Use this for casual greetings or if you can answer directly without a worker.\n"
    )

    # EXPLANATION: How `messages` works:
    messages = [
        # 1. The SystemMessage provides the invisible "instructions" to the AI on how to behave.
        SystemMessage(content=system_prompt),
        
        # 2. The * (asterisk) is called "unpacking". We are taking the entire existing history 
        # of the conversation out of our POJO State and expanding it into this new list.
        # This way, the LLM reads its instructions first, and then reads the whole chat history.
        *state["messages"]
    ]

    # EXPLANATION: How `invoke` works:
    # .invoke() actively sends the conversation list over the internet to the AI.
    # Because we used `with_structured_output`, the variable `result` is NOT a text string! 
    # `result` is a fully populated `RoutingDecision` Python object (our blueprint).
    result = structured_llm.invoke(messages)

    print(f"[FINNIE-AI] 🎯 Decision: Routing to {result.next_step}")

    # EXPLANATION: How `return` works:
    # The LangGraph rule is: Nodes must return a dictionary containing the pieces 
    # of the State POJO they want to update. 
    # Here, we update the `next_step` variable in the State so the Graph knows who to call next.
    return {"next_step": result.next_step}









    