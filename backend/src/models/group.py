"""
Path: backend/src/models/group.py
Version: 1

Conversation group models for API requests/responses
Groups are used to organize conversations in the sidebar
"""

from typing import List
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel, BaseRequestModel


class GroupBase(BaseModel):
    """Base group fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Group name")


class GroupCreate(GroupBase):
    """Group creation request"""
    pass


class GroupUpdate(BaseModel):
    """Group update request (all fields optional)"""
    name: str | None = Field(None, min_length=1, max_length=100)


class GroupResponse(CamelCaseModel):
    """
    Group response (no sensitive data)
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - owner_id → ownerId
    - conversation_ids → conversationIds
    - created_at → createdAt
    """
    id: str
    name: str
    owner_id: str
    conversation_ids: List[str] = Field(default_factory=list)
    created_at: datetime


class GroupInDB(GroupBase):
    """Group as stored in database"""
    owner_id: str
    conversation_ids: List[str] = Field(default_factory=list)
    created_at: datetime


class AddConversationRequest(BaseRequestModel):
    """
    Request to add conversation to group
    
    Inherits from BaseRequestModel to accept camelCase from frontend:
    - Frontend sends: {"conversationId": "conv-123"}
    - Backend receives: request.conversation_id
    """
    conversation_id: str = Field(..., description="Conversation ID to add")


class RemoveConversationRequest(BaseRequestModel):
    """
    Request to remove conversation from group (optional, can use URL param)
    
    This is optional since conversation_id is in URL path.
    Kept for consistency with other request models.
    """
    pass