"""
Path: backend/src/repositories/group_repository.py
Version: 7

Changes in v7:
- ADDED: get_groups_containing_conversation() method
- Returns list of groups containing specified conversation_id
- Filters in Python since DB doesn't support array contains queries

Changes in v6:
- FIX: Conditional import of get_database to avoid import errors in tests

Changes in v5:
- FIX: delete() now returns bool (True if deleted, False if not found)

Changes in v4:
- Fixed create() to re-fetch the document after creation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    """
    Repository for conversation_groups collection
    
    Handles CRUD operations for conversation groups used to organize
    the sidebar. These are different from user_groups (admin feature).
    """
    
    def __init__(self, db=None):
        """
        Initialize repository with collection name
        
        Args:
            db: Database instance (optional, uses factory if not provided)
        """
        if db is None:
            from src.database.factory import get_database
            db = get_database()
        super().__init__(db=db, collection="conversation_groups")
    
    def create(self, data: Dict[str, Any], owner_id: str) -> Dict[str, Any]:
        """
        Create new group
        
        FIXED v4: Re-fetch document after creation to ensure we return it
        
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
        
        # Create the document
        result = super().create(group_data)
        
        # If result is None or doesn't have an id, something went wrong
        if not result or not result.get("id"):
            raise RuntimeError("Failed to create group: BaseRepository.create returned None or invalid result")
        
        # Re-fetch the document to ensure we have the complete object
        created_group = self.get_by_id(result["id"])
        
        if not created_group:
            raise RuntimeError(f"Group was created but cannot be retrieved: {result['id']}")
        
        return created_group
    
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
            List of group documents
        """
        return super().get_all(filters={"owner_id": owner_id})
    
    def update(self, group_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update group
        
        Args:
            group_id: Group ID
            data: Update data (name)
            
        Returns:
            Updated group document
            
        Raises:
            NotFoundError: If group not found
        """
        return super().update(group_id, data)
    
    def delete(self, group_id: str) -> bool:
        """
        Delete group
        
        Args:
            group_id: Group ID
            
        Returns:
            True if deleted, False if not found
        """
        return super().delete(group_id)
    
    def add_conversation(
        self,
        group_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Add conversation to group
        
        Args:
            group_id: Group ID
            conversation_id: Conversation ID to add
            
        Returns:
            Updated group document
            
        Raises:
            NotFoundError: If group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            from src.database.exceptions import NotFoundError
            raise NotFoundError(f"Group {group_id} not found")
        
        # Add conversation if not already in group
        if conversation_id not in group.get("conversation_ids", []):
            conversation_ids = group.get("conversation_ids", [])
            conversation_ids.append(conversation_id)
            return self.update(group_id, {"conversation_ids": conversation_ids})
        
        return group
    
    def remove_conversation(
        self,
        group_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Remove conversation from group
        
        Args:
            group_id: Group ID
            conversation_id: Conversation ID to remove
            
        Returns:
            Updated group document
            
        Raises:
            NotFoundError: If group not found
        """
        group = self.get_by_id(group_id)
        if not group:
            from src.database.exceptions import NotFoundError
            raise NotFoundError(f"Group {group_id} not found")
        
        # Remove conversation if in group
        if conversation_id in group.get("conversation_ids", []):
            conversation_ids = group.get("conversation_ids", [])
            conversation_ids.remove(conversation_id)
            return self.update(group_id, {"conversation_ids": conversation_ids})
        
        return group
    
    def get_groups_containing_conversation(
        self,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all groups containing a specific conversation
        
        Args:
            conversation_id: Conversation ID to search for
            
        Returns:
            List of group documents containing this conversation
            
        Example:
            groups = repo.get_groups_containing_conversation("conv-123")
            # Returns all groups where "conv-123" is in conversation_ids
        """
        all_groups = self.get_all()
        
        # Filter groups that contain this conversation
        matching_groups = [
            group for group in all_groups
            if conversation_id in group.get("conversation_ids", [])
        ]
        
        return matching_groups