import asyncio
import os
from dotenv import load_dotenv

# Load ENV before imports
load_dotenv()

from src.agents.market_insights import market_insights_node
from langchain_core.messages import HumanMessage

async def test_cache():
    print("--- TESTING MARKET INSIGHTS CACHE ---")
    state = {
        "messages": [HumanMessage(content="What's the news?")],
        "portfolio_data": [
            {"ticker": "AAPL", "country": "US", "exchange": "NASDAQ"},
            {"ticker": "NVDA", "country": "US", "exchange": "NASDAQ"}
        ]
    }
    
    print("\n[Step 1] First Call (API Hit)...")
    result1 = await market_insights_node(state)
    print(f"Finnie Response 1:\n{result1['messages'][-1].content[:200]}...")

    print("\n[Step 2] Second Call (Cache Hit)...")
    result2 = await market_insights_node(state)
    print(f"Finnie Response 2:\n{result2['messages'][-1].content[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_cache())
