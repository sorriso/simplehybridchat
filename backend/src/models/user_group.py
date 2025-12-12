"""
Path: backend/src/models/user_group.py
Version: 2

Changes in v2:
- FIX: Removed Config class from UserGroupResponse
- Reason: Pydantic v1 style Config was overriding CamelCaseModel's model_config
- CamelCaseModel already provides populate_by_name=True for accepting snake_case input
- from_attributes=True was not needed (we pass dicts, not ORM objects)

User group models for organizing users (not conversation groups)
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel


class UserGroupBase(BaseModel):
    """Base user group fields"""
    name: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="active", pattern="^(active|disabled)$")


class UserGroupCreate(UserGroupBase):
    """User group creation request"""
    pass


class UserGroupUpdate(BaseModel):
    """User group update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class UserGroupStatusUpdate(BaseModel):
    """User group status update"""
    status: str = Field(..., pattern="^(active|disabled)$")


class UserGroupResponse(CamelCaseModel):
    """User group response (camelCase for frontend)"""
    id: str
    name: str
    status: str
    created_at: datetime
    manager_ids: List[str] = Field(default_factory=list)
    member_ids: List[str] = Field(default_factory=list)


class AddUserToGroupRequest(BaseModel):
    """Request to add user to group"""
    user_id: str = Field(..., alias="userId")
    
    class Config:
        populate_by_name = True


class AssignManagerRequest(BaseModel):
    """Request to assign manager to group"""
    user_id: str = Field(..., alias="userId")
    
    class Config:
        populate_by_name = True