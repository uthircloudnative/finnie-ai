"""
Chat API Models
===============
Pydantic request/response schemas for the /chat endpoint.
Keeps the API contract explicit and type-safe at the boundary layer.
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming payload from the frontend or any API client."""

    message: str = Field(
        ...,
        description="The user's raw message to send to Finnie.",
        min_length=1,
        examples=["What is an Index Fund?"],
    )


class ChatResponse(BaseModel):
    """Outgoing payload returned by the /chat endpoint."""

    reply: str = Field(
        ...,
        description="Finnie's generated response to the user's message.",
    )
