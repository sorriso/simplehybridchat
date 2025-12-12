"""
Path: backend/src/repositories/message_repository.py
Version: 3

Changes in v3:
- FIX: Conditional import of get_database to avoid import errors in tests
- Only import when db is None, allows tests with MockDatabase

Changes in v2:
- Fixed __init__: collection_name to collection
- Fixed all methods: self.collection_name to self.collection
- Added factory pattern for db initialization

Repository for managing messages
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.base import BaseRepository


class MessageRepository(BaseRepository):
    """
    Repository for managing messages
    
    Provides CRUD operations and queries for messages.
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
        super().__init__(db=db, collection="messages")
    
    def get_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation
        
        Args:
            conversation_id: Conversation ID
            skip: Number to skip (pagination)
            limit: Max results
            
        Returns:
            List of messages sorted by created_at ASC (chronological order)
        """
        messages = self.db.get_all(
            self.collection,
            filters={"conversation_id": conversation_id},
            skip=skip,
            limit=limit,
            sort={"created_at": 1}  # Ascending order (oldest first)
        )
        return messages
    
    def count_by_conversation(self, conversation_id: str) -> int:
        """
        Count messages in a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Count of messages
        """
        messages = self.db.get_all(
            self.collection,
            filters={"conversation_id": conversation_id}
        )
        return len(messages)
    
    def delete_by_conversation(self, conversation_id: str) -> int:
        """
        Delete all messages in a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Count of deleted messages
        """
        messages = self.get_by_conversation(conversation_id, limit=10000)
        deleted_count = 0
        
        for message in messages:
            if self.db.delete(self.collection, message["id"]):
                deleted_count += 1
        
        return deleted_count
    
    def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Create a new message
        
        Args:
            conversation_id: Conversation ID
            role: Message role ("user" or "assistant")
            content: Message content
            
        Returns:
            Created message dict
        """
        message_data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow()
        }
        
        return self.create(message_data)