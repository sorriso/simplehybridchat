"""
Path: backend/src/models/group.py
Version: 2

Changes in v2:
- CRITICAL FIX: GroupCreate now inherits from BaseRequestModel to accept camelCase
- Frontend sends { name: "..." } which is now properly received

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


class GroupCreate(BaseRequestModel):
    """
    Group creation request
    
    FIXED v2: Inherits from BaseRequestModel to accept camelCase from frontend
    Frontend sends: { "name": "Group Name" }
    Backend receives: GroupCreate(name="Group Name")
    """
    name: str = Field(..., min_length=1, max_length=100, description="Group name")


class GroupUpdate(BaseRequestModel):
    """
    Group update request (all fields optional)
    
    Inherits from BaseRequestModel to accept camelCase from frontend
    """
    name: str | None = Field(None, min_length=1, max_length=100)


class GroupResponse(CamelCaseModel):
    """
    Group response (no sensitive data)
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - owner_id â†’ ownerId
    - conversation_ids â†’ conversationIds
    - created_at â†’ createdAt
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