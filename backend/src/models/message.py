"""
Path: backend/src/models/message.py
Version: 4

Changes in v4:
- Added optional LLM metadata fields for assistant messages:
  - llm_full_prompt: Complete prompt sent to LLM (includes preferences, RAG context)
  - llm_raw_response: Raw response from LLM before processing
  - llm_stats: LLM generation statistics (tokens, duration, performance)
- Fields are stored in DB but not exposed in API responses yet

Changes in v3:
- CRITICAL FIX: Changed MessageResponse.timestamp -> created_at
- Changed MessageInDB.timestamp -> created_at  
- Matches field name used in chat_service.py (created_at)
- Fixes Pydantic validation error when loading messages from DB

Message models and schemas for API requests/responses
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel


class MessageBase(BaseModel):
    """Base message fields"""
    role: str = Field(..., pattern="^(user|assistant)$", description="Message role: user or assistant")
    content: str = Field(..., min_length=1, description="Message content")


class MessageCreate(MessageBase):
    """Message creation request"""
    conversation_id: str = Field(..., description="Conversation ID")


class MessageResponse(CamelCaseModel):
    """
    Message response
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - conversation_id Ã¢â€ â€™ conversationId
    """
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime


class MessageInDB(MessageBase):
    """Message as stored in database"""
    conversation_id: str
    created_at: datetime
    
    # Optional LLM metadata (for assistant messages only)
    llm_full_prompt: Optional[str] = Field(None, description="Full prompt sent to LLM (with preferences, RAG)")
    llm_raw_response: Optional[str] = Field(None, description="Raw response from LLM")
    llm_stats: Optional[Dict[str, Any]] = Field(None, description="LLM generation statistics")