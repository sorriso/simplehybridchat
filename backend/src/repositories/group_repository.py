"""
Path: backend/src/repositories/group_repository.py
Version: 4

Changes in v4:
- CRITICAL FIX: get_by_owner() ALWAYS returns list [] never None
- CRITICAL FIX: get_groups_containing_conversation() ALWAYS returns list [] never None
- Backend must ALWAYS return empty arrays, not None/null

Changes in v3:
- Fixed exception name: DocumentNotFoundError → NotFoundError (correct exception in src.database.exceptions)

Repository for conversation groups (sidebar organization)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    """
    Repository for conversation_groups collection
    
    Handles CRUD operations for conversation groups used to organize
    the sidebar. These are different from user_groups (admin feature).
    
    IMPORTANT: All list-returning methods MUST return [] (empty list),
    never None or null. This is the backend's responsibility to ensure
    frontend doesn't need undefined checks.
    """
    
    def __init__(self, db=None):
        """
        Initialize repository with collection name
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        from src.database.factory import get_database
        if db is None:
            db = get_database()
        super().__init__(db=db, collection="conversation_groups")
    
    def create(self, data: Dict[str, Any], owner_id: str) -> Dict[str, Any]:
        """
        Create new group
        
        Args:
            data: Group data (name)
            owner_id: Owner user ID
            
        Returns:
            Created group document with id
        """
        group_data = {
            **data,
            "owner_id": owner_id,
            "conversation_ids": [],
            "created_at": datetime.utcnow()
        }
        return super().create(group_data)
    
    def get_by_id(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get group by ID
        
        Args:
            group_id: Group ID
            
        Returns:
            Group document or None if not found
        """
        return super().get_by_id(group_id)
    
    def get_by_owner(self, owner_id: str) -> List[Dict[str, Any]]:
        """
        Get all groups for a user
        
        Args:
            owner_id: Owner user ID
            
        Returns:
            List of group documents (ALWAYS a list, never None)
            Returns empty list [] if no groups found
        """
        result = super().get_all(filters={"owner_id": owner_id})
        
        # CRITICAL: Ensure we ALWAYS return a list, never None
        if result is None:
            return []
        
        # Ensure result is actually a list
        if not isinstance(result, list):
            return []
        
        return result
    
    def update(self, group_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update group
        
        Args:
            group_id: Group ID
            data: Update data (name)
            
        Returns:
            Updated group document
            
        Raises:
            NotFoundError: Group not found
        """
        return super().update(group_id, data)
    
    def delete(self, group_id: str) -> bool:
        """
        Delete group
        
        Args:
            group_id: Group ID
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: Group not found
        """
        return super().delete(group_id)
    
    def add_conversation(self, group_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Add conversation to group
        
        Args:
            group_id: Group ID
            conversation_id: Conversation ID
            
        Returns:
            Updated group document
            
        Raises:
            NotFoundError: Group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            from src.database.exceptions import NotFoundError
            raise NotFoundError(f"Group {group_id} not found")
        
        conversation_ids = group.get("conversation_ids", [])
        
        # Add conversation ID if not already present
        if conversation_id not in conversation_ids:
            conversation_ids.append(conversation_id)
            return self.update(group_id, {"conversation_ids": conversation_ids})
        
        return group
    
    def remove_conversation(self, group_id: str, conversation_id: str) -> Dict[str, Any]:
        """
        Remove conversation from group
        
        Args:
            group_id: Group ID
            conversation_id: Conversation ID
            
        Returns:
            Updated group document
            
        Raises:
            NotFoundError: Group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            from src.database.exceptions import NotFoundError
            raise NotFoundError(f"Group {group_id} not found")
        
        conversation_ids = group.get("conversation_ids", [])
        
        # Remove conversation ID if present
        if conversation_id in conversation_ids:
            conversation_ids.remove(conversation_id)
            return self.update(group_id, {"conversation_ids": conversation_ids})
        
        return group
    
    def get_groups_containing_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all groups containing a specific conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of group documents containing this conversation
            (ALWAYS a list, never None)
            Returns empty list [] if no groups found
        """
        # Get all groups and filter manually
        all_groups = super().get_all()
        
        # CRITICAL: Ensure we ALWAYS return a list, never None
        if all_groups is None:
            return []
        
        if not isinstance(all_groups, list):
            return []
        
        # Filter groups containing this conversation
        return [
            group for group in all_groups
            if conversation_id in group.get("conversation_ids", [])
        ]