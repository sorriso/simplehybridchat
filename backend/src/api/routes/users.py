"""
Path: src/api/routes/users.py
Version: 2

User management endpoints

Changes in v2:
- Fixed list_users call: status -> status_filter parameter name
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from src.models.user import UserCreate, UserUpdate, UserResponse
from src.models.responses import SuccessResponse, EmptyResponse, PaginatedResponse
from src.services.user_service import UserService
from src.api.deps import get_database, UserFromRequest


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=SuccessResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Create new user (root only)
    
    Creates a new user account. Only root users can create users.
    
    - **name**: User full name
    - **email**: Valid email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **role**: User role (user/manager/root, default: user)
    - **status**: User status (active/disabled, default: active)
    
    Requires root permission.
    """
    user_service = UserService(db=db)
    user = user_service.create_user(user_data, current_user)
    
    return SuccessResponse(
        data=user,
        message="User created successfully"
    )


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    current_user: UserFromRequest,
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of users to return"),
    role: Optional[str] = Query(None, pattern="^(user|manager|root)$", description="Filter by role"),
    status: Optional[str] = Query(None, pattern="^(active|disabled)$", description="Filter by status"),
    db = Depends(get_database)
) -> PaginatedResponse[UserResponse]:
    """
    List users (manager+ only)
    
    Returns paginated list of users. Managers and root can list all users.
    
    - **skip**: Number of users to skip (for pagination)
    - **limit**: Maximum number of users to return (max 500)
    - **role**: Optional filter by role (user/manager/root)
    - **status**: Optional filter by status (active/disabled)
    
    Requires manager or root permission.
    """
    user_service = UserService(db=db)
    
    # Get users
    users = user_service.list_users(
        current_user=current_user,
        skip=skip,
        limit=limit,
        role=role,
        status_filter=status
    )
    
    # Get total count
    from src.repositories.user_repository import UserRepository
    user_repo = UserRepository(db=db)
    
    if role:
        total = user_repo.count_by_role(role)
    elif status:
        total = user_repo.count_by_status(status)
    else:
        total = user_repo.count()
    
    return PaginatedResponse.create(
        data=users,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit
    )


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Get user by ID
    
    Returns user details. Users can only view their own profile,
    managers and root can view all users.
    
    - **user_id**: User ID
    
    Requires authentication. Users can only see themselves, managers+ can see all.
    """
    user_service = UserService(db=db)
    user = user_service.get_user(user_id, current_user)
    
    return SuccessResponse(data=user)


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: str,
    updates: UserUpdate,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SuccessResponse[UserResponse]:
    """
    Update user
    
    Updates user information. Users can update their own name/email/password.
    Managers and root can update all fields including role and status.
    
    - **user_id**: User ID
    - **name**: New name (optional)
    - **email**: New email (optional, must be unique)
    - **password**: New password (optional)
    - **role**: New role (optional, managers+ only)
    - **status**: New status (optional, managers+ only)
    
    Requires authentication. Users can update themselves, managers+ can update anyone.
    """
    user_service = UserService(db=db)
    user = user_service.update_user(user_id, updates, current_user)
    
    return SuccessResponse(
        data=user,
        message="User updated successfully"
    )


@router.delete("/{user_id}", response_model=EmptyResponse)
async def delete_user(
    user_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> EmptyResponse:
    """
    Delete user (root only)
    
    Permanently deletes a user account. Only root users can delete users.
    Cannot delete yourself.
    
    - **user_id**: User ID
    
    Requires root permission.
    """
    user_service = UserService(db=db)
    user_service.delete_user(user_id, current_user)
    
    return EmptyResponse(message="User deleted successfully")