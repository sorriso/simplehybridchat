"""
Path: backend/src/models/chat.py
Version: 1

Chat models and schemas for streaming API requests/responses
"""

from typing import Optional
from pydantic import BaseModel, Field

from src.models.base import BaseRequestModel


class ChatRequest(BaseRequestModel):
    """
    Chat streaming request
    
    Inherits from BaseRequestModel to accept camelCase from frontend:
    - conversationId → conversation_id
    - promptCustomization → prompt_customization
    """
    message: str = Field(..., min_length=1, max_length=50000, description="User message content")
    conversation_id: str = Field(..., description="Conversation ID for context")
    prompt_customization: Optional[str] = Field(
        None,
        max_length=5000,
        description="Optional user-specific prompt customization from settings"
    )


class ChatStreamEvent(BaseModel):
    """
    Server-Sent Event for chat streaming
    
    Not used directly in API (streaming returns raw text chunks),
    but documents the expected streaming format.
    """
    content: str = Field(..., description="Text chunk from LLM")
    
    def to_sse(self) -> str:
        """
        Convert to SSE format
        
        Returns:
            SSE-formatted string: "data: {content}\n\n"
        """
        return f"data: {self.content}\n\n"