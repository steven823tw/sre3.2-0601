"""Pydantic schemas for Chat API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    conversation_id: int | None = Field(None, description="Existing conversation ID")


class RecommendationStep(BaseModel):
    """A single recommended action step."""
    step: int = Field(..., ge=1, description="Step sequence number")
    action: str = Field(..., description="Atomic operation ID (e.g. 'infra.ping')")
    description: str = Field(..., description="Human-readable description")
    params: dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    risk_level: str = Field(..., description="Risk level: low/medium/high/critical")
    estimated_time_ms: int = Field(..., ge=0, description="Estimated execution time in ms")


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""
    success: bool = True
    conversation_id: int | None = None
    intent: str = Field(..., description="Detected intent")
    recommendations: list[RecommendationStep] = Field(
        default_factory=list, description="Recommended action steps"
    )
    message: str = Field(..., description="AI agent response message")


class ConversationResponse(BaseModel):
    """Response for a conversation with its messages."""
    id: int
    title: str | None
    user: str | None
    message_count: int


class ConversationListResponse(BaseModel):
    """Paginated conversation list."""
    items: list[ConversationResponse]
    total: int
    page: int
    limit: int
