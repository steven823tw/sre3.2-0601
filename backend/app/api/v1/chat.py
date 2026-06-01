"""Chat API endpoint.

Provides the AI Agent chat interface that performs intent recognition
and returns structured operation recommendations.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send chat message",
    description=(
        "Process a natural language message through the AI Agent. "
        "Returns detected intent and recommended operation steps."
    ),
)
async def send_message(data: ChatRequest) -> ChatResponse:
    """Process a user message and return structured recommendations.

    The chat service performs rule-based intent recognition and maps
    the detected intent to atomic operations from the registry.
    """
    return chat_service.process_message(
        message=data.message,
        conversation_id=data.conversation_id,
    )
