"""
Path: backend/src/services/chat_service.py
Version: 6

Changes in v6:
- Store COMPLETE context in llm_full_prompt as structured JSON:
  - system: system prompt with user preferences
  - context: conversation history messages sent to LLM
  - current_message: the user's current message
- Enables full traceability of what was sent to LLM
- Prepares for RAG integration (will be added to system or context)

Changes in v5:
- Store LLM metadata in messages:
  - llm_full_prompt: Complete system prompt with preferences/RAG context
  - llm_raw_response: Full raw response from LLM
  - llm_stats: Generation statistics (tokens, duration, tokens/sec)

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
from src.services.settings_service import SettingsService
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
        self.settings_service = SettingsService(db=db)
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
        prompt_customization: Optional[str] = None
    ) -> Optional[str]:
        """
        Build system prompt with user customization
        
        Args:
            prompt_customization: Combined user prompt customization
            
        Returns:
            System prompt string
        """
        base_prompt = "You are a helpful AI assistant."
        
        if prompt_customization:
            return f"{base_prompt}\n\nUser preferences: {prompt_customization}"
        
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
        1. Retrieve user settings from database
        2. Combine DB prompt_customization with request prompt_customization
        3. Save user message
        4. Build context with conversation history
        5. Stream from LLM with combined prompt
        6. Accumulate response
        7. Save assistant message
        8. Update conversation metadata
        
        Args:
            message: User message content
            conversation_id: Conversation ID (already validated)
            current_user: Current user dict
            prompt_customization: Optional prompt customization from request (overrides DB)
            
        Yields:
            Text chunks from LLM
            
        Raises:
            HTTPException 500: Streaming error
        """
        # 1. Retrieve user settings from database
        user_settings = self.settings_service.get_settings(current_user["id"])
        db_prompt_customization = user_settings.get("prompt_customization", "")
        
        # 2. Combine prompts: request takes priority over DB
        combined_prompt = prompt_customization if prompt_customization else db_prompt_customization
        
        if combined_prompt:
            logger.info(f"Using prompt customization for user {current_user['id']}: "
                       f"{'request' if prompt_customization else 'database'}")
        
        # 5. Build system prompt with combined customization
        system_prompt = self._get_system_prompt(combined_prompt)
        
        # 4. Build context
        context = self._build_conversation_context(conversation_id)
        
        # Build complete prompt context for traceability
        llm_full_context = {
            "system": system_prompt,
            "context": context,  # Conversation history
            "current_message": message
        }
        
        # 3. Save user message with complete context
        user_message = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": message,
            "created_at": datetime.utcnow(),
            "llm_full_prompt": llm_full_context  # Store complete context as JSON
        }
        user_msg_doc = self.message_repo.create(user_message)
        logger.info(f"Saved user message: {user_msg_doc['id']}")
        
        # Add current message to context for LLM call
        context.append({"role": "user", "content": message})
        
        # 6. Stream from LLM and accumulate response
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
        
        # 7. Save assistant message with raw response and stats
        assistant_content = "".join(full_response)
        
        # Get LLM stats if available
        llm_stats = None
        if hasattr(self.llm, 'get_stats'):
            llm_stats = self.llm.get_stats()
        
        assistant_message = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_content,
            "created_at": datetime.utcnow(),
            "llm_full_prompt": llm_full_context,  # Same complete context used for generation
            "llm_raw_response": assistant_content,  # Store raw response
            "llm_stats": llm_stats  # Store generation statistics
        }
        assistant_msg_doc = self.message_repo.create(assistant_message)
        logger.info(f"Saved assistant message: {assistant_msg_doc['id']}")
        
        # Log stats if available
        if llm_stats:
            logger.info(f"LLM stats: {llm_stats}")
        
        # 8. Update conversation metadata
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