"""
Path: backend/src/services/message_service.py
Version: 2

Changes in v2:
- ADDED: Debug logging for access checks
- Shows user_id, owner_id, user_groups, shared_groups
- Helps diagnose 403 Forbidden issues

Message management service
Handles message operations for conversations
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from src.models.message import MessageCreate, MessageResponse
from src.repositories.message_repository import MessageRepository
from src.repositories.conversation_repository import ConversationRepository
from src.database.interface import IDatabase

logger = logging.getLogger(__name__)


class MessageService:
    """
    Message management service
    
    Provides operations for conversation messages.
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize service with repositories"""
        self.message_repo = MessageRepository(db=db)
        self.conversation_repo = ConversationRepository(db=db)
    
    def _check_conversation_access(
        self,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if user has access to conversation
        
        Args:
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Returns:
            Conversation dict if access granted
            
        Raises:
            HTTPException 404: Conversation not found
            HTTPException 403: Access denied
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # DEBUG: Log access check details
        user_id = current_user["id"]
        owner_id = conversation.get("owner_id")
        user_groups = current_user.get("group_ids", [])
        shared_groups = conversation.get("shared_with_group_ids", [])
        
        logger.debug(f"[ACCESS CHECK] conversation_id={conversation_id}")
        logger.debug(f"[ACCESS CHECK] user_id={user_id}, owner_id={owner_id}")
        logger.debug(f"[ACCESS CHECK] user_groups={user_groups}")
        logger.debug(f"[ACCESS CHECK] shared_groups={shared_groups}")
        
        # Check access
        is_owner = owner_id == user_id
        has_shared_access = any(gid in shared_groups for gid in user_groups)
        
        logger.debug(f"[ACCESS CHECK] is_owner={is_owner}, has_shared_access={has_shared_access}")
        
        if not (is_owner or has_shared_access):
            logger.warning(f"[ACCESS DENIED] user {user_id} cannot access conversation {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
        
        logger.debug(f"[ACCESS GRANTED] user {user_id} can access conversation {conversation_id}")
        return conversation
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> List[MessageResponse]:
        """
        Get all messages for a conversation
        
        Args:
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Returns:
            List of messages sorted by timestamp ASC
            
        Raises:
            HTTPException 403: Access denied
            HTTPException 404: Conversation not found
        """
        # Check access
        self._check_conversation_access(conversation_id, current_user)
        
        # Get messages
        messages = self.message_repo.get_by_conversation(conversation_id)
        
        return [MessageResponse(**msg) for msg in messages]
    
    def create_message(
        self,
        message_data: MessageCreate,
        current_user: Dict[str, Any]
    ) -> MessageResponse:
        """
        Create a new message in a conversation
        
        Args:
            message_data: Message creation data
            current_user: Current user dict
            
        Returns:
            Created message
            
        Raises:
            HTTPException 403: Access denied or not owner
            HTTPException 404: Conversation not found
        """
        # Check access and ownership
        conversation = self._check_conversation_access(
            message_data.conversation_id,
            current_user
        )
        
        # Only owner can add messages (users in shared groups have read-only access)
        if conversation.get("owner_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only conversation owner can add messages"
            )
        
        # Create message
        message = self.message_repo.create_message(
            conversation_id=message_data.conversation_id,
            role=message_data.role,
            content=message_data.content
        )
        
        return MessageResponse(**message)
    
    def get_message_count(self, conversation_id: str) -> int:
        """
        Get message count for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Count of messages
        """
        return self.message_repo.count_by_conversation(conversation_id)