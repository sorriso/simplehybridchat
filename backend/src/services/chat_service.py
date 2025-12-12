"""
Path: backend/src/services/chat_service.py
Version: 3

Changes in v3:
- Add validate_conversation_access() public method
- Call this before streaming to raise HTTP exceptions early (before SSE starts)
- Fixes issue where 404/403 were caught in stream generator and returned as 200

Changes in v2:
- Lazy-load LLM via @property instead of in __init__
- This allows ChatService to be imported without LLM being configured
- LLM is only initialized on first actual use

Chat streaming service
Handles chat streaming with conversation context and message persistence
"""

import logging
from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime
from fastapi import HTTPException, status

from src.llm.factory import get_llm
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.database.interface import IDatabase

logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat streaming service
    
    Handles:
    1. Conversation access verification
    2. User message persistence
    3. LLM streaming with context
    4. Assistant message persistence
    5. Conversation metadata updates
    
    Permissions:
    - stream_chat: owner or shared access to conversation
    """
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize service with repositories"""
        self.conversation_repo = ConversationRepository(db=db)
        self.message_repo = MessageRepository(db=db)
        self._llm = None  # Lazy-loaded
    
    @property
    def llm(self):
        """Lazy-load LLM on first access"""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm
    
    def _check_conversation_access(
        self,
        conversation: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> None:
        """
        Check if user has access to conversation
        
        Args:
            conversation: Conversation dict from DB
            current_user: Current user dict
            
        Raises:
            HTTPException 403: If access denied
        """
        is_owner = conversation.get("owner_id") == current_user["id"]
        
        # Check shared access
        user_groups = current_user.get("group_ids", [])
        shared_groups = conversation.get("shared_with_group_ids", [])
        has_shared_access = any(gid in shared_groups for gid in user_groups)
        
        if not (is_owner or has_shared_access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
    
    def validate_conversation_access(
        self,
        conversation_id: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate conversation exists and user has access
        
        This should be called BEFORE starting SSE streaming to ensure
        HTTP exceptions (404, 403) are raised before the response starts.
        
        Args:
            conversation_id: Conversation ID
            current_user: Current user dict
            
        Returns:
            Conversation document
            
        Raises:
            HTTPException 404: Conversation not found
            HTTPException 403: Access denied
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        self._check_conversation_access(conversation, current_user)
        return conversation
    
    def _build_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = 20
    ) -> list[Dict[str, str]]:
        """
        Build conversation context from message history
        
        Args:
            conversation_id: Conversation ID
            max_messages: Maximum number of historical messages to include
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        # Get recent messages from conversation
        messages = self.message_repo.get_by_conversation(
            conversation_id,
            limit=max_messages
        )
        
        # Convert to LLM format
        context = []
        for msg in messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context
    
    def _get_system_prompt(
        self,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Build system prompt with user customization
        
        Args:
            user_settings: User settings dict with prompt_customization
            
        Returns:
            System prompt string or None
        """
        base_prompt = "You are a helpful AI assistant."
        
        if user_settings and user_settings.get("prompt_customization"):
            customization = user_settings["prompt_customization"]
            return f"{base_prompt}\n\nUser preferences: {customization}"
        
        return base_prompt
    
    async def stream_chat(
        self,
        message: str,
        conversation_id: str,
        current_user: Dict[str, Any],
        prompt_customization: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response
        
        IMPORTANT: validate_conversation_access() must be called BEFORE this method
        to ensure HTTP exceptions are raised before SSE streaming starts.
        
        Flow:
        1. Save user message
        2. Build context with conversation history
        3. Stream from LLM
        4. Accumulate response
        5. Save assistant message
        6. Update conversation metadata
        
        Args:
            message: User message content
            conversation_id: Conversation ID (already validated)
            current_user: Current user dict
            prompt_customization: Optional prompt customization from request
            
        Yields:
            Text chunks from LLM
            
        Raises:
            HTTPException 500: Streaming error
        """
        # 1. Save user message
        user_message = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": message,
            "created_at": datetime.utcnow()
        }
        user_msg_doc = self.message_repo.create(user_message)
        logger.info(f"Saved user message: {user_msg_doc['id']}")
        
        # 2. Build context
        context = self._build_conversation_context(conversation_id)
        
        # Add current message to context
        context.append({"role": "user", "content": message})
        
        # 3. Build system prompt
        user_settings = {"prompt_customization": prompt_customization} if prompt_customization else None
        system_prompt = self._get_system_prompt(user_settings)
        
        # 4. Stream from LLM and accumulate response
        full_response = []
        
        try:
            async for chunk in self.llm.stream_chat(
                messages=context,
                system_prompt=system_prompt
            ):
                full_response.append(chunk)
                yield chunk
                
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Streaming error: {str(e)}"
            )
        
        # 5. Save assistant message
        assistant_content = "".join(full_response)
        assistant_message = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_content,
            "created_at": datetime.utcnow()
        }
        assistant_msg_doc = self.message_repo.create(assistant_message)
        logger.info(f"Saved assistant message: {assistant_msg_doc['id']}")
        
        # 6. Update conversation metadata
        # Count messages in conversation
        message_count = self.message_repo.count_by_conversation(conversation_id)
        
        self.conversation_repo.update(
            conversation_id,
            {
                "updated_at": datetime.utcnow(),
                "message_count": message_count
            }
        )
        logger.info(f"Updated conversation {conversation_id} (messages: {message_count})")