"""
Path: backend/tests/unit/services/test_chat_service.py
Version: 4

Changes in v4:
- Fix tests for new architecture where validation is separate from streaming
- test_stream_chat_conversation_not_found: Use validate_conversation_access() instead
- test_stream_chat_access_denied: Use validate_conversation_access() instead
- test_stream_chat_success: Use service._llm instead of service.llm (property has no setter)
- test_stream_chat_with_customization: Use service._llm instead of service.llm

Changes in v3:
- Added pytest fixture to mock get_llm for all tests

Changes in v2:
- Mock get_llm before importing ChatService to avoid adapter initialization

Unit tests for chat service
Tests chat streaming logic with mocked dependencies
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from fastapi import HTTPException

from src.services.chat_service import ChatService


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock get_llm for all tests in this module"""
    with patch('src.services.chat_service.get_llm') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


class TestChatServiceAccessControl:
    """Test conversation access control"""
    
    def test_check_conversation_access_owner(self):
        """Test owner has access"""
        service = ChatService(db=MagicMock())
        
        conversation = {"owner_id": "user-1", "shared_with_group_ids": []}
        current_user = {"id": "user-1", "group_ids": []}
        
        # Should not raise
        service._check_conversation_access(conversation, current_user)
    
    def test_check_conversation_access_shared(self):
        """Test user with shared group access"""
        service = ChatService(db=MagicMock())
        
        conversation = {"owner_id": "user-1", "shared_with_group_ids": ["group-1"]}
        current_user = {"id": "user-2", "group_ids": ["group-1"]}
        
        # Should not raise
        service._check_conversation_access(conversation, current_user)
    
    def test_check_conversation_access_denied(self):
        """Test access denied for non-owner without shared access"""
        service = ChatService(db=MagicMock())
        
        conversation = {"owner_id": "user-1", "shared_with_group_ids": []}
        current_user = {"id": "user-2", "group_ids": []}
        
        with pytest.raises(HTTPException) as exc_info:
            service._check_conversation_access(conversation, current_user)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail


class TestChatServiceContextBuilding:
    """Test conversation context building"""
    
    def test_build_conversation_context(self):
        """Test building context from message history"""
        mock_repo = MagicMock()
        mock_repo.get_by_conversation.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        
        service = ChatService(db=MagicMock())
        service.message_repo = mock_repo
        
        context = service._build_conversation_context("conv-1")
        
        assert len(context) == 2
        assert context[0] == {"role": "user", "content": "Hello"}
        assert context[1] == {"role": "assistant", "content": "Hi there!"}
        mock_repo.get_by_conversation.assert_called_once_with("conv-1", limit=20)
    
    def test_build_conversation_context_empty(self):
        """Test building context with no messages"""
        mock_repo = MagicMock()
        mock_repo.get_by_conversation.return_value = []
        
        service = ChatService(db=MagicMock())
        service.message_repo = mock_repo
        
        context = service._build_conversation_context("conv-1")
        
        assert context == []


class TestChatServiceSystemPrompt:
    """Test system prompt building"""
    
    def test_get_system_prompt_default(self):
        """Test default system prompt without customization"""
        service = ChatService(db=MagicMock())
        
        prompt = service._get_system_prompt()
        
        assert "helpful AI assistant" in prompt
    
    def test_get_system_prompt_with_customization(self):
        """Test system prompt with user customization"""
        service = ChatService(db=MagicMock())
        
        user_settings = {"prompt_customization": "Be concise"}
        prompt = service._get_system_prompt(user_settings)
        
        assert "helpful AI assistant" in prompt
        assert "Be concise" in prompt
    
    def test_get_system_prompt_with_empty_customization(self):
        """Test system prompt with empty customization"""
        service = ChatService(db=MagicMock())
        
        user_settings = {"prompt_customization": ""}
        prompt = service._get_system_prompt(user_settings)
        
        assert "helpful AI assistant" in prompt


class TestChatServiceStreaming:
    """Test chat streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_stream_chat_conversation_not_found(self):
        """Test validation fails when conversation not found"""
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = None
        
        service = ChatService(db=MagicMock())
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-1", "group_ids": []}
        
        # Use validate_conversation_access instead of stream_chat
        # Validation now happens before streaming starts
        with pytest.raises(HTTPException) as exc_info:
            service.validate_conversation_access("conv-1", current_user)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_stream_chat_access_denied(self):
        """Test validation fails when access denied"""
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = {
            "id": "conv-1",
            "owner_id": "user-1",
            "shared_with_group_ids": []
        }
        
        service = ChatService(db=MagicMock())
        service.conversation_repo = mock_conv_repo
        
        current_user = {"id": "user-2", "group_ids": []}
        
        # Use validate_conversation_access instead of stream_chat
        # Validation now happens before streaming starts
        with pytest.raises(HTTPException) as exc_info:
            service.validate_conversation_access("conv-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_stream_chat_success(self):
        """Test successful chat streaming"""
        # Mock conversation repository
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = {
            "id": "conv-1",
            "owner_id": "user-1",
            "shared_with_group_ids": []
        }
        
        # Mock message repository
        mock_msg_repo = MagicMock()
        mock_msg_repo.create.side_effect = [
            {"id": "msg-user", "conversation_id": "conv-1", "role": "user", "content": "Hello"},
            {"id": "msg-assistant", "conversation_id": "conv-1", "role": "assistant", "content": "Hi there!"}
        ]
        mock_msg_repo.get_by_conversation.return_value = []
        mock_msg_repo.count_by_conversation.return_value = 2
        
        # Mock LLM
        mock_llm = MagicMock()
        
        async def mock_stream(*args, **kwargs):
            for chunk in ["Hi", " ", "there", "!"]:
                yield chunk
        
        mock_llm.stream_chat = mock_stream
        
        # Create service
        service = ChatService(db=MagicMock())
        service.conversation_repo = mock_conv_repo
        service.message_repo = mock_msg_repo
        service._llm = mock_llm  # Use _llm directly (llm property has no setter)
        
        current_user = {"id": "user-1", "group_ids": []}
        
        # Stream chat
        chunks = []
        async for chunk in service.stream_chat("Hello", "conv-1", current_user):
            chunks.append(chunk)
        
        # Verify chunks
        assert chunks == ["Hi", " ", "there", "!"]
        
        # Verify messages created
        assert mock_msg_repo.create.call_count == 2
        
        # Verify conversation updated
        mock_conv_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_chat_with_customization(self):
        """Test chat streaming with prompt customization"""
        mock_conv_repo = MagicMock()
        mock_conv_repo.get_by_id.return_value = {
            "id": "conv-1",
            "owner_id": "user-1",
            "shared_with_group_ids": []
        }
        
        mock_msg_repo = MagicMock()
        mock_msg_repo.create.return_value = {"id": "msg-1"}
        mock_msg_repo.get_by_conversation.return_value = []
        mock_msg_repo.count_by_conversation.return_value = 2
        
        mock_llm = MagicMock()
        
        async def mock_stream(*args, **kwargs):
            # Verify system prompt includes customization
            system_prompt = kwargs.get("system_prompt")
            assert "Be brief" in system_prompt
            yield "OK"
        
        mock_llm.stream_chat = mock_stream
        
        service = ChatService(db=MagicMock())
        service.conversation_repo = mock_conv_repo
        service.message_repo = mock_msg_repo
        service._llm = mock_llm  # Use _llm directly (llm property has no setter)
        
        current_user = {"id": "user-1", "group_ids": []}
        
        chunks = []
        async for chunk in service.stream_chat(
            "Hello",
            "conv-1",
            current_user,
            prompt_customization="Be brief"
        ):
            chunks.append(chunk)
        
        assert chunks == ["OK"]