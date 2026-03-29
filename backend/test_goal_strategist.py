import asyncio
import os
import sys
from pathlib import Path

# Path setup
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from src.models.state import FinnieState
from src.agents.goal_strategist import goal_strategist_node

def test_strategist():
    print("--- Testing Goal Strategist LLM Synthesis ---")
    
    # Mock state
    state: FinnieState = {
        "messages": [],
        "user_id": "test_user",
        "portfolio_data": [],
        "analysis_results": {"volatility": 15.0},
        "goal_configuration": {
            "goal_name": "Retirement",
            "target_amount": 2000000.0,
            "target_year": 2040,
            "monthly_savings": 50000.0,
            "country": "IN"
        }
    }
    
    try:
        result = goal_strategist_node(state)
        print("\n--- Synthesis Result ---")
        for msg in result.get("messages", []):
            print(msg.content)
            
        print("\n--- Simulation Data ---")
        sim = result.get("analysis_results", {}).get("simulation", {})
        print(f"Confidence: {sim.get('confidence_score')}%")
        print(f"Median: {sim.get('final_median')}")
    except Exception as e:
        print(f"Error during node execution: {e}")

if __name__ == "__main__":
    test_strategist()
