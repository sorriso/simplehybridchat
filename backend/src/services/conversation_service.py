"""
Path: src/services/conversation_service.py
Version: 1

Conversation management service
Handles conversation CRUD operations with ownership and sharing logic
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from src.models.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ShareConversationRequest,
    UnshareConversationRequest
)
from src.repositories.conversation_repository import ConversationRepository
from src.database.interface import IDatabase


class ConversationService:
    """
    Conversation management service
    
    Permissions:
    - create_conversation: all authenticated users
    - get_conversation: owner or shared access
    - list_conversations: owner's conversations
    - update_conversation: owner only
    - delete_conversation: owner only
    - share/unshare: owner only
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize service with repository"""
        self.conversation_repo = ConversationRepository(db=db)
    
    def _enrich_conversation(self, conv: Dict[str, Any]) -> ConversationResponse:
        """
        Enrich conversation with calculated fields
        
        Args:
            conv: Conversation dict from DB
            
        Returns:
            ConversationResponse with messageCount and isShared
        """
        # TODO: Calculate messageCount from messages collection
        conv["message_count"] = 0
        
        # Calculate isShared
        conv["is_shared"] = len(conv.get("shared_with_group_ids", [])) > 0
        
        return ConversationResponse(**conv)
    
    def _check_access(
        self,
        conversation: Dict[str, Any],
        current_user: Dict[str, Any],
        require_owner: bool = False
    ) -> None:
        """
        Check if user has access to conversation
        
        Args:
            conversation: Conversation dict
            current_user: Current user dict
            require_owner: If True, only owner has access
            
        Raises:
            HTTPException 403: If access denied
        """
        is_owner = conversation.get("owner_id") == current_user["id"]
        
        if require_owner:
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only conversation owner can perform this action"
                )
        else:
            # Check shared access
            user_groups = current_user.get("group_ids", [])
            shared_groups = conversation.get("shared_with_group_ids", [])
            has_shared_access = any(gid in shared_groups for gid in user_groups)
            
            if not (is_owner or has_shared_access):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
    
    def create_conversation(
        self,
        conversation_data: ConversationCreate,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """Create new conversation"""
        # Prepare data
        db_data = conversation_data.model_dump()
        db_data["owner_id"] = current_user["id"]
        db_data["shared_with_group_ids"] = []
        db_data["created_at"] = datetime.utcnow()
        db_data["updated_at"] = datetime.utcnow()
        
        # TODO: Validate group_id exists if provided
        
        # Create conversation
        conversation = self.conversation_repo.create(db_data)
        
        return self._enrich_conversation(conversation)
    
    def get_conversation(
        self,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """Get conversation by ID"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check access (owner or shared)
        self._check_access(conversation, current_user, require_owner=False)
        
        return self._enrich_conversation(conversation)
    
    def list_conversations(
        self,
        current_user: Dict[str, Any]
    ) -> List[ConversationResponse]:
        """List user's own conversations"""
        conversations = self.conversation_repo.get_by_owner(current_user["id"])
        
        return [self._enrich_conversation(conv) for conv in conversations]
    
    def list_shared_conversations(
        self,
        current_user: Dict[str, Any]
    ) -> List[ConversationResponse]:
        """List conversations shared with user"""
        user_groups = current_user.get("group_ids", [])
        conversations = self.conversation_repo.get_shared_with_user(user_groups)
        
        return [self._enrich_conversation(conv) for conv in conversations]
    
    def update_conversation(
        self,
        conversation_id: str,
        updates: ConversationUpdate,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """Update conversation (owner only)"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check owner access
        self._check_access(conversation, current_user, require_owner=True)
        
        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        
        # Handle undefined -> null for group_id
        if "group_id" in update_data:
            # Frontend sends undefined which becomes None
            # We need to allow None to "ungroup" conversation
            conversation["group_id"] = update_data["group_id"]
        
        if "title" in update_data:
            conversation["title"] = update_data["title"]
        
        conversation["updated_at"] = datetime.utcnow()
        
        # Save
        updated = self.conversation_repo.update(conversation_id, conversation)
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return self._enrich_conversation(updated)
    
    def delete_conversation(
        self,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> bool:
        """Delete conversation (owner only)"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check owner access
        self._check_access(conversation, current_user, require_owner=True)
        
        # TODO: Delete all associated messages
        
        # Delete conversation
        deleted = self.conversation_repo.delete(conversation_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return True
    
    def share_conversation(
        self,
        conversation_id: str,
        share_data: ShareConversationRequest,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """Share conversation with groups (owner only)"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check owner access
        self._check_access(conversation, current_user, require_owner=True)
        
        # TODO: Validate that all group_ids exist
        
        # Replace shared groups
        self.conversation_repo.set_shared_groups(conversation_id, share_data.group_ids)
        
        # Get updated conversation
        updated = self.conversation_repo.get_by_id(conversation_id)
        
        return self._enrich_conversation(updated)
    
    def unshare_conversation(
        self,
        conversation_id: str,
        unshare_data: UnshareConversationRequest,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """Unshare conversation from groups (owner only)"""
        conversation = self.conversation_repo.get_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check owner access
        self._check_access(conversation, current_user, require_owner=True)
        
        # Remove groups from shared list
        current_shared = conversation.get("shared_with_group_ids", [])
        new_shared = [gid for gid in current_shared if gid not in unshare_data.group_ids]
        
        self.conversation_repo.set_shared_groups(conversation_id, new_shared)
        
        # Get updated conversation
        updated = self.conversation_repo.get_by_id(conversation_id)
        
        return self._enrich_conversation(updated)