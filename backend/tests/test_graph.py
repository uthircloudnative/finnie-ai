import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# This line ensures Python can find our 'src' folder when running from the 'scripts' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.graph import finnie_app

def run_test(user_input: str):
    print(f"\n--- TESTING QUERY: '{user_input}' ---")
    
    # 1. We create a fake starting state (POJO) containing one human message
    initial_state = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    # 2. We invoke the compiled LangGraph application
    final_state = finnie_app.invoke(initial_state)
    
    # 3. Print out the results!
    print(f"Final Next Step Decision: {final_state.get('next_step')}")
    
    # Grab the very last message in the state's memory
    last_message = final_state["messages"][-1]
    
    # Check if the last message is an AI response (meaning a worker actually answered)
    if last_message.type == "ai":
        print(f"\n🤖 FINNIE SAYS:\n{last_message.content}\n")
    else:
        print(f"\n[No answer generated. Awaiting implementation for {final_state.get('next_step')}]\n")

if __name__ == "__main__":
    # Test 1: Educational query -> Should route to FINANCIAL_QA
    run_test("Can you explain what an Index Fund is?")
    
    # Test 2: Real-time news query -> Should route to MARKET_INSIGHTS
    run_test("What is the latest news on Apple stock today?")

    # Test 3: Casual greeting -> Should route to FINISH
    run_test("Hello Finnie!")
