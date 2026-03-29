"""
Chat API Models
===============
Pydantic request/response schemas for the /chat endpoint.
Keeps the API contract explicit and type-safe at the boundary layer.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming payload from the frontend or any API client."""

    message: str = Field(
        ...,
        description="The user's raw message to send to Finnie.",
        min_length=1,
        examples=["What is an Index Fund?"],
    )
    preferred_worker: Optional[str] = Field(
        default=None,
        description="Optional hint to route the message to a specific agent (e.g. 'PORTFOLIO_ANALYST')."
    )
    analysis_context: Optional[dict] = Field(
        default=None,
        description="Optional pre-calculated results (e.g. Beta, Volatility) to provide context."
    )


class ChatResponse(BaseModel):
    """Outgoing payload returned by the /chat endpoint."""

    reply: str = Field(
        ...,
        description="Finnie's generated response to the user's message.",
    )
    analysis_results: Optional[dict] = Field(
        default=None,
        description="Optional structured results from specialized workers (e.g. Portfolio Analyst)."
    )
