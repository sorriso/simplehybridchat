"""
Path: backend/src/models/conversation.py
Version: 7

Changes in v7:
- CRITICAL FIX: ShareConversationRequest uses group_ids instead of user_ids
- CRITICAL FIX: UnshareConversationRequest uses group_ids instead of user_ids
- REMOVED: permission field from ShareConversationRequest (not used in backend)
- Reason: Conversation sharing uses user_groups, not direct user_ids
- Frontend sends groupIds, backend converts to group_ids

Changes in v6:
- ADDED: shared_with_group_ids and is_shared to ConversationResponse

Changes in v5:
- CRITICAL FIX: ConversationCreate now inherits BaseRequestModel (accepts camelCase from frontend)
- CRITICAL FIX: ConversationUpdate now inherits BaseRequestModel
- This allows frontend to send {title, groupId} instead of {title, group_id}

Conversation models and schemas for API requests/responses
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel, BaseRequestModel


class ConversationCreate(BaseRequestModel):
    """
    Conversation creation request
    
    Accepts camelCase from frontend (groupId) and converts to snake_case (group_id)
    """
    title: str = Field(default="New Conversation", min_length=1, max_length=200)
    group_id: Optional[str] = Field(default=None, description="Group ID (null if not grouped)")


class ConversationUpdate(BaseRequestModel):
    """
    Conversation update request (all fields optional)
    
    Accepts camelCase from frontend (groupId) and converts to snake_case (group_id)
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    group_id: Optional[str] = None


class ConversationResponse(CamelCaseModel):
    """
    Conversation response (output)
    
    Converts snake_case to camelCase for frontend:
    - group_id → groupId
    - owner_id → ownerId
    - created_at → createdAt
    - updated_at → updatedAt
    - message_count → messageCount
    - shared_with_group_ids → sharedWithGroupIds
    - is_shared → isShared
    """
    id: str
    title: str
    group_id: Optional[str] = None
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0
    shared_with_group_ids: List[str] = Field(default_factory=list)
    is_shared: bool = False


class ConversationListResponse(BaseModel):
    """List of conversations"""
    conversations: List[ConversationResponse]


class ConversationDetailResponse(BaseModel):
    """Single conversation with details"""
    conversation: ConversationResponse


class ShareConversationRequest(BaseRequestModel):
    """
    Request to share conversation with user groups
    
    Accepts camelCase from frontend (groupIds) and converts to snake_case (group_ids)
    """
    group_ids: List[str] = Field(..., min_items=1, description="List of group IDs to share with")


class UnshareConversationRequest(BaseRequestModel):
    """
    Request to unshare conversation from user groups
    
    Accepts camelCase from frontend (groupIds) and converts to snake_case (group_ids)
    """
    group_ids: List[str] = Field(..., min_items=1, description="List of group IDs to unshare from")


class ConversationShareInfo(CamelCaseModel):
    """Information about conversation sharing"""
    user_id: str
    permission: str
    shared_at: datetime
    shared_by: str