"""
Path: backend/src/repositories/user_group_repository.py
Version: 3

Changes in v3:
- FIX: get_by_manager() now filters manually (get_all() then filter in Python)
- Reason: ArangoDB adapter doesn't support array containment queries in filters
- Pattern matches conversation_repository.py get_shared_with_user()

Changes in v2:
- FIX: Replaced self.get() with self.get_by_id() in all methods
- Affects: add_member(), remove_member(), add_manager(), remove_manager()
- Reason: BaseRepository has get_by_id(), not get()

User group repository for data access
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

from src.repositories.base import BaseRepository
from src.database.interface import IDatabase
from src.database.exceptions import NotFoundError, DuplicateKeyError


class UserGroupRepository(BaseRepository):
    """
    User group repository
    
    Handles user group data access operations.
    Extends BaseRepository with user-group-specific methods.
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize with user_groups collection"""
        super().__init__(collection="user_groups", db=db)
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get user group by name"""
        return self.db.find_one(self.collection, {"name": name})
    
    def name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if group name already exists
        
        Args:
            name: Group name to check
            exclude_id: Optional group ID to exclude from check (for updates)
            
        Returns:
            True if name exists
        """
        filters = {"name": name}
        groups = self.db.get_all(self.collection, filters=filters, limit=2)
        
        if not groups:
            return False
        
        # If excluding an ID, check if found group is different
        if exclude_id:
            return any(group["id"] != exclude_id for group in groups)
        
        return True
    
    def create_with_validation(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create user group with name uniqueness validation
        
        Args:
            group_data: Group data with name
            
        Returns:
            Created group
            
        Raises:
            DuplicateKeyError: If name already exists
        """
        # Check name uniqueness
        if self.name_exists(group_data["name"]):
            raise DuplicateKeyError(f"Group name '{group_data['name']}' already exists")
        
        # Add timestamps
        now = datetime.now(UTC)
        group_data["created_at"] = now
        group_data["updated_at"] = now
        
        # Initialize empty lists if not present
        if "manager_ids" not in group_data:
            group_data["manager_ids"] = []
        if "member_ids" not in group_data:
            group_data["member_ids"] = []
        
        # Set default status
        if "status" not in group_data:
            group_data["status"] = "active"
        
        return self.db.create(self.collection, group_data)
    
    def get_by_manager(self, manager_id: str) -> List[Dict[str, Any]]:
        """
        Get all groups managed by a specific user
        
        Args:
            manager_id: Manager user ID
            
        Returns:
            List of groups where user is manager
        """
        # Get all groups and filter manually (ArangoDB adapter doesn't support array queries)
        all_groups = self.get_all() or []
        return [
            group for group in all_groups
            if manager_id in group.get("manager_ids", [])
        ]
    
    def add_member(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        Add user to group members
        
        Args:
            group_id: Group ID
            user_id: User ID to add
            
        Returns:
            Updated group
            
        Raises:
            NotFoundError: If group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"User group {group_id} not found")
        
        # Add to member_ids if not already present
        member_ids = group.get("member_ids", [])
        if user_id not in member_ids:
            member_ids.append(user_id)
            updates = {
                "member_ids": member_ids,
                "updated_at": datetime.now(UTC)
            }
            return self.update(group_id, updates)
        
        return group
    
    def remove_member(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        Remove user from group members
        
        Args:
            group_id: Group ID
            user_id: User ID to remove
            
        Returns:
            Updated group
            
        Raises:
            NotFoundError: If group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"User group {group_id} not found")
        
        # Remove from member_ids if present
        member_ids = group.get("member_ids", [])
        if user_id in member_ids:
            member_ids.remove(user_id)
            updates = {
                "member_ids": member_ids,
                "updated_at": datetime.now(UTC)
            }
            return self.update(group_id, updates)
        
        return group
    
    def add_manager(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        Add manager to group
        
        Args:
            group_id: Group ID
            user_id: User ID to add as manager
            
        Returns:
            Updated group
            
        Raises:
            NotFoundError: If group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"User group {group_id} not found")
        
        # Add to manager_ids if not already present
        manager_ids = group.get("manager_ids", [])
        if user_id not in manager_ids:
            manager_ids.append(user_id)
            updates = {
                "manager_ids": manager_ids,
                "updated_at": datetime.now(UTC)
            }
            return self.update(group_id, updates)
        
        return group
    
    def remove_manager(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        Remove manager from group
        
        Args:
            group_id: Group ID
            user_id: User ID to remove as manager
            
        Returns:
            Updated group
            
        Raises:
            NotFoundError: If group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"User group {group_id} not found")
        
        # Remove from manager_ids if present
        manager_ids = group.get("manager_ids", [])
        if user_id in manager_ids:
            manager_ids.remove(user_id)
            updates = {
                "manager_ids": manager_ids,
                "updated_at": datetime.now(UTC)
            }
            return self.update(group_id, updates)
        
        return group