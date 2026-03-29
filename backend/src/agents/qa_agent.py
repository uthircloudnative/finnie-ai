import os
from langchain.chat_models import init_chat_model

from langchain_core.messages import SystemMessage
from src.models.state import FinnieState
from src.utils.vector_store import VectorStoreManager

def financial_qa_node(state: FinnieState) -> dict:
    """
    The Financial Q&A Worker.
    Retrieves educational context from ChromaDB and answers the user's question.
    """
    user_message = state["messages"][-1].content
    print(f"\n[FINNIE-AI] 📚 Q&A Agent starting research for: '{user_message}'")
    
    # 1. RETRIEVE FACTS: Connect to ChromaDB
    print(f"[FINNIE-AI] 🔍 Searching educational_kb vector store...")
    db = VectorStoreManager(collection_name="educational_kb")
    
    # We pass target_country="USA" to use the metadata filtering we planned!
    docs = db.search(query=user_message, k=3, target_country="USA")
    
    # Squash the chunks into a single giant string
    context_text = "\n\n".join([doc.page_content for doc in docs])
    print(f"[FINNIE-AI] 📖 Found {len(docs)} relevant knowledge chunks.")

    # 2. INSTRUCT THE LLM: 
    # Notice we inject the `context_text` directly into the System Prompt!
    system_prompt = (
        "You are Finnie, a beginner-friendly financial educator. "
        "Answer the user's question using ONLY the provided context below. "
        "Do not make up information. If the answer is not in the context, say 'I don't have enough facts on that.'\n\n"
        f"CONTEXT:\n{context_text}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"] # Include the chat history
    ]
    
    # 3. GENERATE ANSWER: Notice we do NOT use structured_output here. We want a normal text string back!
    # Read vendor config from .env
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    
    # Initialize the LLM
    print(f"[FINNIE-AI] 🧠 Generating grounded answer via LLM...")
    llm = init_chat_model(model=model_name, model_provider=provider, temperature=0)
    ai_msg = llm.invoke(messages)
    
    # 4. UPDATE STATE: We append the AI's response to the conversation history.
    return {"messages": [ai_msg]}
