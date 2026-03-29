import asyncio
import os
from dotenv import load_dotenv

# Load ENV before imports
load_dotenv()

from src.agents.portfolio_analyst import portfolio_analyst_node
from langchain_core.messages import HumanMessage

def test_analyst_global():
    print("--- TESTING PORTFOLIO ANALYST GLOBAL FIX ---")
    state = {
        "messages": [HumanMessage(content="Analyze my portfolio performance.")],
        "portfolio_data": [
            {"ticker": "AAPL", "country": "US", "exchange": "NASDAQ"},
            {"ticker": "RELIANCE", "country": "IN", "exchange": "NSE"}
        ]
    }
    
    print("\nExecuting Analyst Node...")
    # The node is sync, so we just call it
    result = portfolio_analyst_node(state)
    
    print("\n--- FINNIE RESPONSE ---")
    print(result['messages'][-1].content)
    
    print("\n--- STRUCTURED RESULTS ---")
    print(result.get("analysis_results"))

if __name__ == "__main__":
    test_analyst_global()
