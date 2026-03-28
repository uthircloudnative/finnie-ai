"""
Finnie AI — FastAPI Application Entry Point
============================================
Run locally with:
    uv run uvicorn main:app --reload --port 8000

Endpoints:
    GET  /health  - Liveness check (no LLM call)
    POST /chat    - Send a message; get Finnie's response
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

# Load .env before importing anything that needs API keys
load_dotenv()

from src.graph import finnie_app  # noqa: E402 (must come after load_dotenv)
from src.models.chat import ChatRequest, ChatResponse  # noqa: E402

# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Finnie AI",
    description="Multi-agent personal finance guide powered by LangGraph.",
    version="0.1.0",
)

# Allow the React dev server (port 5173) to call this API without CORS errors.
# Tighten this list before going to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Ops"])
async def health_check() -> dict:
    """Quick liveness probe — never touches the LLM."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to Finnie and receive her response.

    The Supervisor Agent decides which worker to route to based on the query.
    Currently active workers: Financial Q&A (RAG-grounded).
    """
    # 1. Build the initial LangGraph state
    initial_state = {
        "messages": [HumanMessage(content=request.message)]
    }

    # 2. Run the full agent graph (Supervisor → worker → answer)
    try:
        final_state = finnie_app.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent graph failed: {exc}",
        ) from exc

    # 3. Extract the last message from the conversation history
    messages = final_state.get("messages", [])
    last_message = messages[-1] if messages else None

    # Guard: if no AI message came back (e.g., unimplemented agent stub),
    # raise a clear 500 rather than returning an empty reply.
    if last_message is None or last_message.type != "ai":
        raise HTTPException(
            status_code=500,
            detail=(
                f"Agent routed to '{final_state.get('next_step')}' "
                "but no reply was generated. This worker is not yet implemented."
            ),
        )

    return ChatResponse(reply=last_message.content)
