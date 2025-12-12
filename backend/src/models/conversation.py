"""
Path: backend/src/models/conversation.py
Version: 4

Changes in v4:
- PROPER FIX: ShareConversationRequest and UnshareConversationRequest now inherit BaseRequestModel
- This is the clean, uniform solution for accepting camelCase from frontend
- Consistent with architecture: BaseRequestModel for inputs, CamelCaseModel for outputs

Changes in v3:
- REVERTED: alias approach was "bidouillage"

Changes in v2:
- ConversationResponse now inherits from CamelCaseModel
- Ensures camelCase serialization for frontend compatibility

Conversation models and schemas for API requests/responses
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel, BaseRequestModel


class ConversationBase(BaseModel):
    """Base conversation fields"""
    title: str = Field(default="New Conversation", min_length=1, max_length=200)
    group_id: Optional[str] = Field(default=None, description="Group ID (null if not grouped)")


class ConversationCreate(ConversationBase):
    """Conversation creation request"""
    pass


class ConversationUpdate(BaseModel):
    """Conversation update request (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    group_id: Optional[str] = None  # undefined in frontend becomes None here


class ConversationResponse(CamelCaseModel):
    """
    Conversation response (no sensitive data)
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - owner_id → ownerId
    - group_id → groupId
    - shared_with_group_ids → sharedWithGroupIds
    - is_shared → isShared
    - message_count → messageCount
    - created_at → createdAt
    - updated_at → updatedAt
    """
    id: str
    title: str
    group_id: Optional[str] = None
    owner_id: str
    shared_with_group_ids: List[str] = Field(default_factory=list)
    is_shared: bool = False
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationInDB(ConversationBase):
    """Conversation as stored in database"""
    owner_id: str
    shared_with_group_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ShareConversationRequest(BaseRequestModel):
    """
    Request to share conversation with groups
    
    Inherits from BaseRequestModel to accept camelCase from frontend:
    - Frontend sends: {"groupIds": ["group-1"]}
    - Backend receives: request.group_ids
    """
    group_ids: List[str] = Field(..., min_length=1, description="List of group IDs to share with")


class UnshareConversationRequest(BaseRequestModel):
    """
    Request to unshare conversation from groups
    
    Inherits from BaseRequestModel to accept camelCase from frontend:
    - Frontend sends: {"groupIds": ["group-1"]}
    - Backend receives: request.group_ids
    """
    group_ids: List[str] = Field(..., min_length=1, description="List of group IDs to unshare from")