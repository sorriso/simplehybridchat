"""
Path: backend/src/models/message.py
Version: 3

Changes in v3:
- CRITICAL FIX: Changed MessageResponse.timestamp -> created_at
- Changed MessageInDB.timestamp -> created_at  
- Matches field name used in chat_service.py (created_at)
- Fixes Pydantic validation error when loading messages from DB

Changes in v2:
- MessageResponse now inherits from CamelCaseModel
- Ensures camelCase serialization for frontend compatibility

Message models and schemas for API requests/responses
"""

from typing import Optional
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