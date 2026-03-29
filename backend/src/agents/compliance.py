from src.models.state import FinnieState
from langchain_core.messages import AIMessage

def compliance_guardian_node(state: FinnieState) -> dict:
    """
    A post-processor node that ensures all AI messages 
    related to analysis include the $NFA disclaimer.
    """
    print("--- ENTERING COMPLIANCE GUARDIAN NODE ---")
    
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    
    if last_message.type == "ai":
        disclaimer = "\n\n---\n**Disclaimer:** I am an AI, not a financial advisor. This is **Not Financial Advice ($NFA)**. Always consult a certified professional before making investment decisions."
        
        # Only append if not already present
        if "$NFA" not in last_message.content:
            new_content = last_message.content + disclaimer
            new_msg = AIMessage(content=new_content, id=last_message.id)
            # Replace the last message in history
            # In LangGraph with add_messages, we return the NEW message
            # and it will be appended. To 'replace', we need careful strategy,
            # but for simplicity, we just append a specialized 'compliance' message 
            # or modify the existing one if the state allows it.
            # Actually, LangGraph's add_messages will append.
            # To 'edit' the last message, we return it with the SAME ID.
            return {"messages": [new_msg]}
            
    return {}
