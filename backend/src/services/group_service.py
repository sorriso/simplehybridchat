"""
Path: backend/src/services/group_service.py
Version: 2

Changes in v2:
- CRITICAL FIX: list_groups() ALWAYS returns list [] never None
- Backend contract: list endpoints MUST return arrays, not None/null

Service for conversation groups (sidebar organization)
Handles business logic and permissions for group operations
"""

from typing import List, Dict, Any
from fastapi import HTTPException, status

from src.repositories.group_repository import GroupRepository
from src.repositories.conversation_repository import ConversationRepository
from src.database.interface import IDatabase


class GroupService:
    """
    Service for conversation group operations
    
    Handles:
    - Owner-only access control
    - Synchronization between groups and conversations
    - Cleanup when deleting groups
    
    IMPORTANT: All list-returning methods MUST return [] (empty list),
    never None. This is API contract enforcement.
    """
    
    def __init__(self, db: IDatabase = None):
        """Initialize service with repositories"""
        self.group_repo = GroupRepository(db=db)
        self.conversation_repo = ConversationRepository(db=db)
    
    def _check_owner(self, group: Dict[str, Any], current_user: Dict[str, Any]) -> None:
        """
        Check if user is owner of group
        
        Args:
            group: Group document
            current_user: Current user dict
            
        Raises:
            HTTPException 403: If user is not owner
        """
        if group.get("owner_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: not group owner"
            )
    
    def create_group(
        self,
        data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new group
        
        Args:
            data: Group data (name)
            current_user: Current user dict
            
        Returns:
            Created group
        """
        return self.group_repo.create(data, current_user["id"])
    
    def get_group(
        self,
        group_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get group by ID
        
        Args:
            group_id: Group ID
            current_user: Current user dict
            
        Returns:
            Group document
            
        Raises:
            HTTPException 404: Group not found
            HTTPException 403: Not owner
        """
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )
        
        self._check_owner(group, current_user)
        return group
    
    def list_groups(self, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        List all groups for current user
        
        Args:
            current_user: Current user dict
            
        Returns:
            List of groups (ALWAYS a list, never None)
            Returns empty list [] if no groups found
            
        CRITICAL: This method MUST return [] not None.
        Frontend expects {"groups": []} not {"groups": null}
        """
        groups = self.group_repo.get_by_owner(current_user["id"])
        
        # CRITICAL SAFETY: Repository should already guarantee [],
        # but we double-check here for absolute certainty
        if groups is None:
            return []
        
        if not isinstance(groups, list):
            return []
        
        return groups
    
    def update_group(
        self,
        group_id: str,
        data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update group
        
        Args:
            group_id: Group ID
            data: Update data (name)
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: Group not found
            HTTPException 403: Not owner
        """
        # Check access
        group = self.get_group(group_id, current_user)
        
        # Update
        return self.group_repo.update(group_id, data)
    
    def delete_group(
        self,
        group_id: str,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete group
        
        Important: Sets conversation.group_id = null for all conversations in group.
        Conversations are NOT deleted.
        
        Args:
            group_id: Group ID
            current_user: Current user dict
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException 404: Group not found
            HTTPException 403: Not owner
        """
        # Check access
        group = self.get_group(group_id, current_user)
        
        # Set group_id = null for all conversations in this group
        conversation_ids = group.get("conversation_ids", [])
        for conv_id in conversation_ids:
            try:
                self.conversation_repo.update(conv_id, {"group_id": None})
            except Exception:
                # Continue even if conversation not found
                pass
        
        # Delete group
        return self.group_repo.delete(group_id)
    
    def add_conversation_to_group(
        self,
        group_id: str,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add conversation to group
        
        Synchronizes:
        1. Adds conversation_id to group.conversation_ids
        2. Sets conversation.group_id = group_id
        
        Args:
            group_id: Group ID
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: Group or conversation not found
            HTTPException 403: Not owner of group or conversation
        """
        # Check group access
        group = self.get_group(group_id, current_user)
        
        # Check conversation exists and user owns it
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        if conversation.get("owner_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: not conversation owner"
            )
        
        # Synchronize: Add to group AND set conversation.group_id
        updated_group = self.group_repo.add_conversation(group_id, conversation_id)
        self.conversation_repo.update(conversation_id, {"group_id": group_id})
        
        return updated_group
    
    def remove_conversation_from_group(
        self,
        group_id: str,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Remove conversation from group
        
        Synchronizes:
        1. Removes conversation_id from group.conversation_ids
        2. Sets conversation.group_id = null
        
        Args:
            group_id: Group ID
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Returns:
            Updated group
            
        Raises:
            HTTPException 404: Group not found
            HTTPException 403: Not owner
        """
        # Check group access
        group = self.get_group(group_id, current_user)
        
        # Synchronize: Remove from group AND set conversation.group_id = null
        updated_group = self.group_repo.remove_conversation(group_id, conversation_id)
        
        # Update conversation (continue even if not found)
        try:
            self.conversation_repo.update(conversation_id, {"group_id": None})
        except Exception:
            pass
        
        return updated_group