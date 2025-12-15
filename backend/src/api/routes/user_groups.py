"""
Path: backend/src/api/routes/user_groups.py
Version: 5

Changes in v5:
- UPDATED: Documentation for list_user_groups endpoint
- Users can now see groups they are member of (not just managers/root)
- Enables conversation sharing for all users

Changes in v4:
- FIX: create_group passes {"name": data.name} dict instead of data.name string
- FIX: update_group passes {"name": data.name} dict instead of data.name string
- Reason: Service v4 expects dict parameter, not string
- Matches TypeError fix in stack trace (line 106)

Changes in v2:
- Full implementation with service and repository

API routes for user groups (user management, not conversation groups)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_database, UserFromRequest
from src.services.user_group_service import UserGroupService
from src.models.user_group import (
    UserGroupCreate,
    UserGroupUpdate,
    UserGroupStatusUpdate,
    UserGroupResponse,
    AddUserToGroupRequest,
    AssignManagerRequest
)
from src.models.responses import SuccessResponse

router = APIRouter(prefix="/user-groups", tags=["User Groups"])


# Response models
class SingleUserGroupResponse(SuccessResponse):
    """Single user group response wrapper"""
    data: UserGroupResponse


class UserGroupListResponse(SuccessResponse):
    """User group list response wrapper"""
    data: List[UserGroupResponse]


@router.get(
    "",
    response_model=UserGroupListResponse,
    summary="List user groups"
)
async def list_user_groups(
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Get all user groups based on permissions
    
    - User: sees only groups they are member of
    - Manager: sees only groups they manage
    - Root: sees all groups
    """
    service = UserGroupService(db=db)
    groups = service.list_groups(current_user)
    
    return UserGroupListResponse(
        data=[UserGroupResponse(**group) for group in groups]
    )


@router.get(
    "/{group_id}",
    response_model=SingleUserGroupResponse,
    summary="Get user group by ID"
)
async def get_user_group(
    group_id: str,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Get specific user group by ID
    
    Only managers of the group or root can access.
    """
    service = UserGroupService(db=db)
    group = service.get_group(group_id, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


@router.post(
    "",
    response_model=SingleUserGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user group"
)
async def create_user_group(
    data: UserGroupCreate,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Create new user group (root only)
    
    Groups start with no members or managers.
    """
    service = UserGroupService(db=db)
    group = service.create_group({"name": data.name}, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


@router.put(
    "/{group_id}",
    response_model=SingleUserGroupResponse,
    summary="Update user group"
)
async def update_user_group(
    group_id: str,
    data: UserGroupUpdate,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Update user group name (root only)
    """
    service = UserGroupService(db=db)
    group = service.update_group(group_id, {"name": data.name}, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


@router.put(
    "/{group_id}/status",
    response_model=SingleUserGroupResponse,
    summary="Toggle group status"
)
async def toggle_group_status(
    group_id: str,
    data: UserGroupStatusUpdate,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Activate/deactivate group
    
    - Manager: can toggle groups they manage
    - Root: can toggle any group
    """
    service = UserGroupService(db=db)
    group = service.toggle_status(group_id, data.status, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


# ============================================================================
# Member Management
# ============================================================================

@router.post(
    "/{group_id}/members",
    response_model=SingleUserGroupResponse,
    summary="Add member to group"
)
async def add_member_to_group(
    group_id: str,
    data: AddUserToGroupRequest,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Add user to group
    
    - Manager: can add to groups they manage
    - Root: can add to any group
    """
    service = UserGroupService(db=db)
    group = service.add_member(group_id, data.user_id, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


@router.delete(
    "/{group_id}/members/{user_id}",
    response_model=SingleUserGroupResponse,
    summary="Remove member from group"
)
async def remove_member_from_group(
    group_id: str,
    user_id: str,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Remove user from group
    
    - Manager: can remove from groups they manage
    - Root: can remove from any group
    """
    service = UserGroupService(db=db)
    group = service.remove_member(group_id, user_id, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


# ============================================================================
# Manager Management (Root only)
# ============================================================================

@router.post(
    "/{group_id}/managers",
    response_model=SingleUserGroupResponse,
    summary="Assign manager to group"
)
async def assign_manager_to_group(
    group_id: str,
    data: AssignManagerRequest,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Assign manager to group (root only)
    
    User must have manager or root role.
    """
    service = UserGroupService(db=db)
    group = service.assign_manager(group_id, data.user_id, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))


@router.delete(
    "/{group_id}/managers/{user_id}",
    response_model=SingleUserGroupResponse,
    summary="Remove manager from group"
)
async def remove_manager_from_group(
    group_id: str,
    user_id: str,
    current_user: UserFromRequest,
    db=Depends(get_database)
):
    """
    Remove manager from group (root only)
    """
    service = UserGroupService(db=db)
    group = service.remove_manager(group_id, user_id, current_user)
    
    return SingleUserGroupResponse(data=UserGroupResponse(**group))