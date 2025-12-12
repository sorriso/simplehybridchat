"""
Path: backend/src/repositories/conversation_repository.py
Version: 3

Changes in v3:
- ADDED: update() method to properly update conversation fields
- Fixes message_count not updating after chat messages
- Uses db.update() to persist changes to database

Changes in v2:
- Fixed __init__: collection_name Ã¢â€ â€™ collection
- Fixed all methods: self.collection_name Ã¢â€ â€™ self.collection
- Added factory pattern for db initialization

Repository for managing conversations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    """
    Repository for managing conversations
    
    Provides CRUD operations and queries for conversations.
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
        super().__init__(db=db, collection="conversations")
    
    def update(self, conversation_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update conversation fields
        
        Args:
            conversation_id: Conversation ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated conversation or None if not found
        """
        # Get existing conversation
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Update fields
        for key, value in updates.items():
            conversation[key] = value
        
        # Save back to database
        self.db.update(self.collection, conversation_id, conversation)
        
        return conversation
    
    def get_by_owner(self, owner_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations owned by a user
        
        Args:
            owner_id: Owner user ID
            
        Returns:
            List of conversations sorted by updatedAt DESC
        """
        conversations = self.db.get_all(
            self.collection,
            filters={"owner_id": owner_id},
            sort={"updated_at": -1}
        )
        return conversations
    
    def get_shared_with_user(self, user_group_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get conversations shared with user's groups
        
        Args:
            user_group_ids: List of group IDs user belongs to
            
        Returns:
            List of shared conversations
        """
        if not user_group_ids:
            return []
        
        # Get all conversations
        all_conversations = self.db.get_all(self.collection)
        
        # Filter conversations where shared_with_group_ids intersects with user_group_ids
        shared = []
        for conv in all_conversations:
            shared_groups = conv.get("shared_with_group_ids", [])
            if any(gid in shared_groups for gid in user_group_ids):
                shared.append(conv)
        
        # Sort by updated_at DESC
        shared.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=True)
        
        return shared
    
    def get_by_group(self, group_id: str) -> List[Dict[str, Any]]:
        """
        Get conversations in a specific group
        
        Args:
            group_id: Group ID
            
        Returns:
            List of conversations
        """
        return self.db.get_all(
            self.collection,
            filters={"group_id": group_id},
            sort={"updated_at": -1}
        )
    
    def add_shared_group(self, conversation_id: str, group_id: str) -> bool:
        """
        Add a group to conversation's shared list
        
        Args:
            conversation_id: Conversation ID
            group_id: Group ID to add
            
        Returns:
            True if successful
        """
        conv = self.get_by_id(conversation_id)
        if not conv:
            return False
        
        shared_groups = conv.get("shared_with_group_ids", [])
        if group_id not in shared_groups:
            shared_groups.append(group_id)
            conv["shared_with_group_ids"] = shared_groups
            conv["updated_at"] = datetime.utcnow()
            self.update(conversation_id, conv)
        
        return True
    
    def remove_shared_group(self, conversation_id: str, group_id: str) -> bool:
        """
        Remove a group from conversation's shared list
        
        Args:
            conversation_id: Conversation ID
            group_id: Group ID to remove
            
        Returns:
            True if successful
        """
        conv = self.get_by_id(conversation_id)
        if not conv:
            return False
        
        shared_groups = conv.get("shared_with_group_ids", [])
        if group_id in shared_groups:
            shared_groups.remove(group_id)
            conv["shared_with_group_ids"] = shared_groups
            conv["updated_at"] = datetime.utcnow()
            self.update(conversation_id, conv)
        
        return True
    
    def set_shared_groups(self, conversation_id: str, group_ids: List[str]) -> bool:
        """
        Set the complete list of shared groups (replaces existing)
        
        Args:
            conversation_id: Conversation ID
            group_ids: List of group IDs
            
        Returns:
            True if successful
        """
        conv = self.get_by_id(conversation_id)
        if not conv:
            return False
        
        conv["shared_with_group_ids"] = group_ids
        conv["updated_at"] = datetime.utcnow()
        self.update(conversation_id, conv)
        
        return True