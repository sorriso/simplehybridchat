"""
Path: backend/src/services/user_group_service.py
Version: 4

Changes in v4:
- FIX: Corrected check_permission calls - function takes 2 args only (user, required_role)
- FIX: Added delete_group() method that was missing
- Changed all check_permission(user, role, message) to check_permission(user, role) + HTTPException
- All permission checks now use proper pattern: if not check_permission(...): raise HTTPException

Changes in v3:
- FIX: Replaced self.user_repo.get() with self.user_repo.get_by_id() (2 occurrences)

Changes in v2:
- FIX: Replaced self.group_repo.get() with self.group_repo.get_by_id()

Service for user groups (user management, not conversation groups)
Handles business logic and permissions for user group operations
"""

from typing import List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.user_group_repository import UserGroupRepository
from src.repositories.user_repository import UserRepository
from src.database.interface import IDatabase
from src.core.permissions import check_permission


class UserGroupService:
    """
    Service for user group operations
    
    Handles:
    - Permission-based access control (manager vs root)
    - Business logic for group management
    - User membership management
    - Manager assignment
    
    IMPORTANT: All list-returning methods MUST return [] (empty list),
    never None. This is API contract enforcement.
    """
    
    def __init__(self, db: IDatabase):
        """Initialize with database connection"""
        self.db = db
        self.group_repo = UserGroupRepository(db)
        self.user_repo = UserRepository(db)
    
    # ========================================================================
    # List and Get Operations
    # ========================================================================
    
    def list_groups(self, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        List user groups based on permissions
        
        Root: sees all groups
        Manager: sees only groups they manage
        User: forbidden
        
        Args:
            current_user: Current user dict
            
        Returns:
            List of groups (never None)
            
        Raises:
            HTTPException 403: If user lacks manager permission
        """
        # Require at least manager role
        if not check_permission(current_user, "manager"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager or root permission required"
            )
        
        # Root sees all groups
        if check_permission(current_user, "root"):
            return self.group_repo.get_all() or []
        
        # Manager sees only their managed groups
        return self.group_repo.get_by_manager(current_user["id"]) or []
    
    def get_group(
        self,
        group_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get group by ID (with permission check)
        
        Args:
            group_id: Group ID
            current_user: Current user dict
            
        Returns:
            Group document
            
        Raises:
            HTTPException 404: If group not found
            HTTPException 403: If user cannot access group
        """
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User group not found"
            )
        
        # Check if user can manage this group
        self._check_can_manage_group(group, current_user)
        return group
    
    def _check_can_manage_group(
        self,
        group: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> None:
        """
        Check if user can manage this group
        
        Root: can manage all groups
        Manager: can only manage groups they're assigned to
        
        Args:
            group: Group document
            current_user: Current user dict
            
        Raises:
            HTTPException 403: If user cannot manage group
        """
        # Root can manage all groups
        if check_permission(current_user, "root"):
            return
        
        # Managers can only manage their assigned groups
        if check_permission(current_user, "manager"):
            if current_user["id"] in group.get("manager_ids", []):
                return
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a manager of this group"
        )
    
    # ========================================================================
    # Create and Update Operations
    # ========================================================================
    
    def create_group(
        self,
        data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new user group (root only)
        
        Args:
            data: Group data (name, status)
            current_user: Current user dict
            
        Returns:
            Created group
            
        Raises:
            HTTPException 403: If not root
            HTTPException 400: If name already exists
        """
        # Only root can create groups
        if not check_permission(current_user, "root"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only root can create user groups"
            )
        
        try:
            return self.group_repo.create_with_validation(data)
        except Exception as e:
            if "already exists" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            raise
    
    def update_group(
        self,
        group_id: str,
        updates: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update group (name)
        
        Args:
            group_id: Group ID
            updates: Update data
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: If group not found
            HTTPException 403: If user cannot manage group
        """
        group = self.get_group(group_id, current_user)
        
        # Check name uniqueness if updating name
        if "name" in updates and updates["name"] != group["name"]:
            if self.group_repo.name_exists(updates["name"], exclude_id=group_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Group name '{updates['name']}' already exists"
                )
        
        return self.group_repo.update(group_id, updates)
    
    def toggle_status(
        self,
        group_id: str,
        new_status: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Toggle group status (active/disabled)
        
        Args:
            group_id: Group ID
            new_status: New status ("active" or "disabled")
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: If group not found
            HTTPException 403: If user cannot manage group
        """
        group = self.get_group(group_id, current_user)
        
        updates = {"status": new_status}
        return self.group_repo.update(group_id, updates)
    
    def delete_group(
        self,
        group_id: str,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete user group (root only)
        
        Args:
            group_id: Group ID
            current_user: Current user dict
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException 403: If not root
            HTTPException 404: If group not found
        """
        # Only root can delete groups
        if not check_permission(current_user, "root"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only root can delete user groups"
            )
        
        # Check group exists
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User group not found"
            )
        
        return self.group_repo.delete(group_id)
    
    # ========================================================================
    # Member Management
    # ========================================================================
    
    def add_member(
        self,
        group_id: str,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add user to group
        
        Args:
            group_id: Group ID
            user_id: User ID to add
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: If group or user not found
            HTTPException 403: If user cannot manage group
        """
        group = self.get_group(group_id, current_user)
        
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return self.group_repo.add_member(group_id, user_id)
    
    def remove_member(
        self,
        group_id: str,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Remove user from group
        
        Args:
            group_id: Group ID
            user_id: User ID to remove
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: If group not found
            HTTPException 403: If user cannot manage group
        """
        group = self.get_group(group_id, current_user)
        return self.group_repo.remove_member(group_id, user_id)
    
    # ========================================================================
    # Manager Management
    # ========================================================================
    
    def assign_manager(
        self,
        group_id: str,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assign manager to group (root only)
        
        Args:
            group_id: Group ID
            user_id: User ID to assign as manager
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 403: If not root
            HTTPException 404: If group or user not found
            HTTPException 400: If user is not a manager
        """
        # Only root can assign managers
        if not check_permission(current_user, "root"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only root can assign managers"
            )
        
        # Check group exists
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User group not found"
            )
        
        # Verify user exists and is a manager
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.get("role") not in ["manager", "root"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must have manager or root role"
            )
        
        return self.group_repo.add_manager(group_id, user_id)
    
    def remove_manager(
        self,
        group_id: str,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Remove manager from group (root only)
        
        Args:
            group_id: Group ID
            user_id: User ID to remove as manager
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 403: If not root
            HTTPException 404: If group not found
        """
        # Only root can remove managers
        if not check_permission(current_user, "root"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only root can remove managers"
            )
        
        # Check group exists
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User group not found"
            )
        
        return self.group_repo.remove_manager(group_id, user_id)