"""
Path: backend/src/services/conversation_service.py
Version: 1

Conversation service with business logic
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException, status

from src.repositories.conversation_repository import ConversationRepository
from src.repositories.user_repository import UserRepository
from src.models.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ShareConversationRequest,
    UnshareConversationRequest
)


class ConversationService:
    """
    Service for conversation operations
    """
    
    def __init__(self, db):
        self.conversation_repo = ConversationRepository(db=db)
        self.user_repo = UserRepository(db=db)
    
    # ========================================================================
    # List and Retrieve
    # ========================================================================
    
    def list_conversations(self, current_user: Dict[str, Any]) -> List[ConversationResponse]:
        """
        List all conversations owned by current user
        
        Args:
            current_user: Current user dict
            
        Returns:
            List of ConversationResponse objects
        """
        user_id = current_user["id"]
        conversations = self.conversation_repo.get_by_owner(user_id)
        
        # Convert to response models
        response_list = []
        for conv in conversations:
            # Ensure is_shared field
            shared_groups = conv.get("shared_with_group_ids", [])
            conv["is_shared"] = len(shared_groups) > 0
            
            response_list.append(ConversationResponse(**conv))
        
        return response_list
    
    def list_shared_conversations(self, current_user: Dict[str, Any]) -> List[ConversationResponse]:
        """
        Get conversations shared with current user via user groups
        
        Returns conversations where:
        - owner_id != current_user["id"] AND
        - At least one group in shared_with_group_ids matches user's group_ids
        
        Args:
            current_user: Current user dict with 'id' and 'group_ids'
            
        Returns:
            List of ConversationResponse (read-only access)
        """
        user_id = current_user["id"]
        
        # Get user's group IDs
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return []
        
        user_group_ids = user.get("group_ids", [])
        if not user_group_ids:
            return []
        
        # Use repository method
        shared_conversations = self.conversation_repo.get_shared_with_user(user_group_ids)
        
        # Filter out conversations owned by user (double check)
        filtered = []
        for conv in shared_conversations:
            owner_id = conv.get("owner_id")
            if owner_id != user_id:
                # Mark as shared
                conv["is_shared"] = True
                filtered.append(conv)
        
        # Convert to response models
        return [ConversationResponse(**conv) for conv in filtered]
    
    def get_conversation(
        self, 
        conversation_id: str, 
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """
        Get conversation by ID with permission check
        
        User can access if:
        - They own the conversation OR
        - Conversation is shared with one of their groups
        
        Args:
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Returns:
            ConversationResponse
            
        Raises:
            HTTPException 404: If conversation not found
            HTTPException 403: If user cannot access conversation
        """
        conv = self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_id = current_user["id"]
        owner_id = conv.get("owner_id")
        
        # Check if user owns conversation
        if owner_id == user_id:
            # Add is_shared field
            shared_groups = conv.get("shared_with_group_ids", [])
            conv["is_shared"] = len(shared_groups) > 0
            return ConversationResponse(**conv)
        
        # Check if conversation is shared with user's groups
        user = self.user_repo.get_by_id(user_id)
        if user:
            user_group_ids = user.get("group_ids", [])
            shared_groups = conv.get("shared_with_group_ids", [])
            
            if any(group_id in user_group_ids for group_id in shared_groups):
                conv["is_shared"] = True
                return ConversationResponse(**conv)
        
        # User cannot access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation"
        )
    
    # ========================================================================
    # Create, Update, Delete
    # ========================================================================
    
    def create_conversation(
        self, 
        data: ConversationCreate, 
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """
        Create new conversation
        
        Args:
            data: ConversationCreate model
            current_user: Current user dict
            
        Returns:
            ConversationResponse
        """
        user_id = current_user["id"]
        
        conversation_data = {
            "owner_id": user_id,
            "title": data.title,
            "group_id": data.group_id,
            "shared_with_group_ids": [],
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
        
        conv = self.conversation_repo.create(conversation_data)
        conv["is_shared"] = False
        
        return ConversationResponse(**conv)
    
    def update_conversation(
        self,
        conversation_id: str,
        data: ConversationUpdate,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """
        Update conversation (title, group_id)
        
        Only owner can update
        
        Args:
            conversation_id: Conversation ID
            data: ConversationUpdate model
            current_user: Current user dict
            
        Returns:
            ConversationResponse
            
        Raises:
            HTTPException 404: If conversation not found
            HTTPException 403: If user is not owner
        """
        conv = self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_id = current_user["id"]
        owner_id = conv.get("owner_id")
        
        if owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can update conversation"
            )
        
        # Build update dict from non-None fields
        update_data = {}
        if data.title is not None:
            update_data["title"] = data.title
        if data.group_id is not None:
            update_data["group_id"] = data.group_id
        
        update_data["updated_at"] = datetime.utcnow()
        
        updated_conv = self.conversation_repo.update(conversation_id, update_data)
        
        # Add is_shared field
        shared_groups = updated_conv.get("shared_with_group_ids", [])
        updated_conv["is_shared"] = len(shared_groups) > 0
        
        return ConversationResponse(**updated_conv)
    
    def delete_conversation(
        self,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> None:
        """
        Delete conversation
        
        Only owner can delete
        
        Args:
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Raises:
            HTTPException 404: If conversation not found
            HTTPException 403: If user is not owner
        """
        conv = self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_id = current_user["id"]
        owner_id = conv.get("owner_id")
        
        if owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can delete conversation"
            )
        
        self.conversation_repo.delete(conversation_id)
    
    # ========================================================================
    # Sharing
    # ========================================================================
    
    def share_conversation(
        self,
        conversation_id: str,
        data: ShareConversationRequest,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """
        Share conversation with user groups
        
        Only owner can share
        
        Args:
            conversation_id: Conversation ID
            data: ShareConversationRequest with group_ids
            current_user: Current user dict
            
        Returns:
            ConversationResponse
            
        Raises:
            HTTPException 404: If conversation not found
            HTTPException 403: If user is not owner
        """
        conv = self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_id = current_user["id"]
        owner_id = conv.get("owner_id")
        
        if owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can share conversation"
            )
        
        # Set shared groups (replaces existing)
        self.conversation_repo.set_shared_groups(conversation_id, data.group_ids)
        
        # Get updated conversation
        updated_conv = self.conversation_repo.get_by_id(conversation_id)
        updated_conv["is_shared"] = len(data.group_ids) > 0
        
        return ConversationResponse(**updated_conv)
    
    def unshare_conversation(
        self,
        conversation_id: str,
        data: UnshareConversationRequest,
        current_user: Dict[str, Any]
    ) -> ConversationResponse:
        """
        Unshare conversation from specific user groups
        
        Only owner can unshare
        
        Args:
            conversation_id: Conversation ID
            data: UnshareConversationRequest with group_ids to remove
            current_user: Current user dict
            
        Returns:
            ConversationResponse
            
        Raises:
            HTTPException 404: If conversation not found
            HTTPException 403: If user is not owner
        """
        conv = self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_id = current_user["id"]
        owner_id = conv.get("owner_id")
        
        if owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can unshare conversation"
            )
        
        # Remove specified groups
        current_shared = conv.get("shared_with_group_ids", [])
        new_shared = [gid for gid in current_shared if gid not in data.group_ids]
        
        self.conversation_repo.set_shared_groups(conversation_id, new_shared)
        
        # Get updated conversation
        updated_conv = self.conversation_repo.get_by_id(conversation_id)
        updated_conv["is_shared"] = len(new_shared) > 0
        
        return ConversationResponse(**updated_conv)