"""
Path: src/services/user_service.py
Version: 6

User management service
Handles user CRUD operations with role-based permissions

Changes in v6:
- ARCHITECTURE: Removed _map_db_to_response() - adapter now does DB-to-Service mapping  
- ARCHITECTURE: Removed _get_user_id() - only use current_user["id"] (middleware format)
- Simplified all methods - direct use of objects with 'id' from adapter
- All UserResponse creations now use **user directly (adapter returns with 'id')

Changes in v5:
- Added _get_user_id() helper (REMOVED in v6)
- Fixed unit tests compatibility (REMOVED in v6)

Changes in v4:
- Fixed all current_user["_key"] -> current_user["id"] (3 occurrences)
- Added "Permission denied: " prefix to all 403 error messages
- Changed delete_yourself from 400 to 403 for consistency

Changes in v3:
- Fixed get_current_user_profile to fetch user from DB instead of using middleware user dict
- Middleware user only has 'id' and 'role', need full user from DB with '_key'

Changes in v2:
- Modified __init__ to accept optional db parameter (aligned with AuthService)
- Added IDatabase import for type hints

Changes in v1:
- Added _map_db_to_response() helper to fix _key -> id mapping
- Added created_at default when missing
- Added fastapi.status import (fix AttributeError)
- Fixed list_users() to use get_all() instead of list()
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from src.models.user import UserCreate, UserUpdate, UserResponse
from src.repositories.user_repository import UserRepository
from src.database.interface import IDatabase
from src.core.permissions import check_permission




class UserService:
    """
    User management service
    
    Provides CRUD operations for users with role-based access control.
    
    Permissions:
    - create_user: root only
    - get_user: self or manager+
    - list_users: manager+
    - update_user: self (basic fields) or manager+ (role/status)
    - delete_user: root only (cannot delete self)
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """
        Initialize service with repository
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        self.user_repo = UserRepository(db=db)
    
    def create_user(
        self,
        user_data: UserCreate,
        current_user: Dict[str, Any]
    ) -> UserResponse:
        """
        Create new user (root only)
        
        Args:
            user_data: User creation data
            current_user: Current authenticated user
            
        Returns:
            Created user
            
        Raises:
            HTTPException 403: If not root
            HTTPException 409: If email already exists
        """
        # Permission check: root only
        if not check_permission(current_user, "root"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only root users can create users"
            )
        
        # Create user
        from src.core.security import hash_password
        
        user_dict = user_data.model_dump()
        user_dict["password_hash"] = hash_password(user_data.password)
        del user_dict["password"]
        
        created_user = self.user_repo.create_with_validation(user_dict)
        
        return UserResponse(**created_user)
    
    def get_user(
        self,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> UserResponse:
        """
        Get user by ID
        
        Args:
            user_id: User ID to get
            current_user: Current authenticated user
            
        Returns:
            User data
            
        Raises:
            HTTPException 403: If not authorized
            HTTPException 404: If user not found
        """
        # Permission check: self or manager+
        is_self = current_user["id"] == user_id
        is_manager_or_above = check_permission(current_user, "manager")
        
        if not is_self and not is_manager_or_above:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: not authorized to view this user"
            )
        
        # Get user
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user)
    
    def list_users(
        self,
        current_user: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[UserResponse]:
        """
        List users with pagination and filters (manager+ only)
        
        Args:
            current_user: Current authenticated user
            skip: Number of users to skip
            limit: Maximum number of users to return
            role: Filter by role
            status_filter: Filter by status
            
        Returns:
            List of users
            
        Raises:
            HTTPException 403: If not manager+
        """
        # Permission check: manager+
        if not check_permission(current_user, "manager"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only managers can list users"
            )
        
        # Build filters
        filters = {}
        if role:
            filters["role"] = role
        if status_filter:
            filters["status"] = status_filter
        
        # Get users - FIXED: use get_all() instead of list()
        try:
            if filters:
                users = self.user_repo.get_all(
                    filters=filters,
                    skip=skip,
                    limit=limit
                )
            else:
                users = self.user_repo.get_all(
                    skip=skip,
                    limit=limit
                )
            
            return [UserResponse(**user) for user in users]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing users: {str(e)}"
            )
    
    def update_user(
        self,
        user_id: str,
        user_data: UserUpdate,
        current_user: Dict[str, Any]
    ) -> UserResponse:
        """
        Update user
        
        Permissions:
        - Self: Can update name, email, password
        - Manager+: Can update role, status
        
        Args:
            user_id: User ID to update
            user_data: Update data
            current_user: Current authenticated user
            
        Returns:
            Updated user
            
        Raises:
            HTTPException 403: If not authorized
            HTTPException 404: If user not found
        """
        # Get existing user
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions
        is_self = current_user["id"] == user_id
        is_manager_or_above = check_permission(current_user, "manager")
        
        # Prepare updates
        updates = user_data.model_dump(exclude_unset=True)
        
        # Check if trying to update privileged fields
        privileged_fields = {"role", "status"}
        updating_privileged = any(field in updates for field in privileged_fields)
        
        if updating_privileged and not is_manager_or_above:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only managers can update role and status"
            )
        
        # If not self and not manager, deny
        if not is_self and not is_manager_or_above:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: not authorized to update this user"
            )
        
        # Handle password update
        if "password" in updates:
            from src.core.security import hash_password
            updates["password_hash"] = hash_password(updates["password"])
            del updates["password"]
        
        # Update user
        updated_user = self.user_repo.update_with_validation(
            user_id,
            updates
        )
        
        return UserResponse(**updated_user)
    
    def delete_user(
        self,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete user (root only, cannot delete self)
        
        Args:
            user_id: User ID to delete
            current_user: Current authenticated user
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException 400: If trying to delete self
            HTTPException 403: If not root
            HTTPException 404: If user not found
        """
        # Permission check: root only
        if not check_permission(current_user, "root"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only root users can delete users"
            )
        
        # Cannot delete self
        if current_user["id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: cannot delete yourself"
            )
        
        # Delete user
        deleted = self.user_repo.delete(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return True
    
    def get_current_user_profile(
        self,
        current_user: Dict[str, Any]
    ) -> UserResponse:
        """
        Get current user's profile
        
        Args:
            current_user: Current authenticated user (from middleware, has 'id' and 'role')
            
        Returns:
            Current user data (fetched from database)
        """
        # Get full user data from database using id
        try:
            user_id = current_user["id"]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user in token"
            )
        
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user)