"""
Path: backend/src/api/routes/groups.py
Version: 1

API routes for conversation groups (sidebar organization)
"""

from typing import List
from fastapi import APIRouter, Depends, status

from src.api.deps import get_database, UserFromRequest
from src.services.group_service import GroupService
from src.models.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    AddConversationRequest
)
from src.models.responses import SuccessResponse


router = APIRouter(prefix="/groups", tags=["Groups"])


# Response models
class SingleGroupResponse(SuccessResponse):
    """Single group response wrapper"""
    data: GroupResponse


class GroupListResponse(SuccessResponse):
    """Group list response wrapper"""
    data: List[GroupResponse]


@router.get(
    "",
    response_model=GroupListResponse,
    summary="List user's groups"
)
async def list_groups(
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Get all conversation groups for current user
    
    Returns list of groups used to organize conversations in sidebar.
    """
    service = GroupService(db=db)
    groups = service.list_groups(current_user)
    
    return GroupListResponse(
        data=[GroupResponse(**group) for group in groups]
    )


@router.get(
    "/{group_id}",
    response_model=SingleGroupResponse,
    summary="Get group by ID"
)
async def get_group(
    group_id: str,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Get specific group by ID
    
    Only owner can access the group.
    """
    service = GroupService(db=db)
    group = service.get_group(group_id, current_user)
    
    return SingleGroupResponse(data=GroupResponse(**group))


@router.post(
    "",
    response_model=SingleGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new group"
)
async def create_group(
    data: GroupCreate,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Create new conversation group
    
    Groups are used to organize conversations in sidebar.
    Empty group is created, conversations are added separately.
    """
    service = GroupService(db=db)
    group = service.create_group(data.model_dump(), current_user)
    
    return SingleGroupResponse(data=GroupResponse(**group))


@router.put(
    "/{group_id}",
    response_model=SingleGroupResponse,
    summary="Update group"
)
async def update_group(
    group_id: str,
    data: GroupUpdate,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Update group (rename)
    
    Only owner can update the group.
    """
    service = GroupService(db=db)
    
    # Only update provided fields
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    group = service.update_group(group_id, update_data, current_user)
    
    return SingleGroupResponse(data=GroupResponse(**group))


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete group"
)
async def delete_group(
    group_id: str,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Delete conversation group
    
    Important:
    - Conversations are NOT deleted
    - conversation.group_id is set to null for all conversations in group
    - Only owner can delete the group
    """
    service = GroupService(db=db)
    service.delete_group(group_id, current_user)
    
    # 204 No Content - no body returned


@router.post(
    "/{group_id}/conversations",
    response_model=SingleGroupResponse,
    summary="Add conversation to group"
)
async def add_conversation_to_group(
    group_id: str,
    request: AddConversationRequest,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Add conversation to group
    
    Synchronizes:
    1. Adds conversation to group.conversation_ids
    2. Sets conversation.group_id = group_id
    
    Requirements:
    - User must own both the group and the conversation
    - Conversation cannot be in multiple groups (latest wins)
    """
    service = GroupService(db=db)
    group = service.add_conversation_to_group(
        group_id,
        request.conversation_id,
        current_user
    )
    
    return SingleGroupResponse(data=GroupResponse(**group))


@router.delete(
    "/{group_id}/conversations/{conversation_id}",
    response_model=SingleGroupResponse,
    summary="Remove conversation from group"
)
async def remove_conversation_from_group(
    group_id: str,
    conversation_id: str,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Remove conversation from group
    
    Synchronizes:
    1. Removes conversation from group.conversation_ids
    2. Sets conversation.group_id = null
    
    Only owner can remove conversations from group.
    """
    service = GroupService(db=db)
    group = service.remove_conversation_from_group(
        group_id,
        conversation_id,
        current_user
    )
    
    return SingleGroupResponse(data=GroupResponse(**group))