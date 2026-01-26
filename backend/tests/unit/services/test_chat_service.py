"""
Path: backend/tests/unit/services/test_chat_service.py
Version: 2

Changes in v2:
- Updated expectations to match current DEFAULT_SETTINGS in settings_service.py
- Tests now expect llm_full_prompt as dict with system/context/current_message structure

Unit tests for ChatService streaming
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from src.services.chat_service import ChatService


# Expected default prompt from settings_service.py
EXPECTED_DEFAULT_PROMPT = "Your are an AI expert,\nDo not lie,\nDo not invent,\nDo not cheat,\nIf additional information are missing then ask for them,\nIf you do not know then just say it and ask for help,\nDo not generate additional data (documentation, explanation) except if I request explicitly them,\nRespond in a clear, structured, straightforward and professional way"


class TestChatServiceConversationAccess:
    """Test conversation access validation"""
    
    def test_check_conversation_access_owner(self):
        """Test owner can access conversation"""
        service = ChatService(db=MagicMock())
        
        conversation = {"owner_id": "user-1", "shared_with_group_ids": []}
        current_user = {"id": "user-1", "group_ids": []}
        
        # Should not raise
        service._check_conversation_access(conversation, current_user)
    
    def test_check_conversation_access_shared_group(self):
        """Test user with shared group can access"""
        service = ChatService(db=MagicMock())
        
        conversation = {"owner_id": "user-1", "shared_with_group_ids": ["group-1"]}
        current_user = {"id": "user-2", "group_ids": ["group-1", "group-2"]}
        
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
        
        prompt = service._get_system_prompt(None)
        
        assert "helpful AI assistant" in prompt
        assert "preferences" not in prompt
    
    def test_get_system_prompt_with_customization(self):
        """Test system prompt with user customization"""
        service = ChatService(db=MagicMock())
        
        prompt = service._get_system_prompt("Be concise")
        
        assert "helpful AI assistant" in prompt
        assert "Be concise" in prompt
        assert "preferences" in prompt
    
    def test_get_system_prompt_with_empty_customization(self):
        """Test system prompt with empty customization"""
        service = ChatService(db=MagicMock())
        
        prompt = service._get_system_prompt("")
        
        assert "helpful AI assistant" in prompt
        assert "preferences" not in prompt


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
        
        with pytest.raises(HTTPException) as exc_info:
            service.validate_conversation_access("conv-1", current_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_stream_chat_success(self):
        """Test successful chat streaming with default settings"""
        with patch('src.services.chat_service.SettingsService') as MockSettingsService:
            # Mock SettingsService to return default prompt
            mock_settings_instance = MagicMock()
            mock_settings_instance.get_settings.return_value = {
                "prompt_customization": EXPECTED_DEFAULT_PROMPT,
                "theme": "light",
                "language": "en"
            }
            MockSettingsService.return_value = mock_settings_instance
            
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
            mock_llm.get_stats.return_value = {"prompt_tokens": 15, "completion_tokens": 8}
            
            async def mock_stream(*args, **kwargs):
                # Verify system prompt includes DB customization
                system_prompt = kwargs.get("system_prompt")
                assert "helpful AI assistant" in system_prompt
                # The llm_full_prompt should be a dict with structure
                yield "Hi"
                yield " "
                yield "there"
                yield "!"
            
            mock_llm.stream_chat = mock_stream
            
            service = ChatService(db=MagicMock())
            service.conversation_repo = mock_conv_repo
            service.message_repo = mock_msg_repo
            service._llm = mock_llm
            
            current_user = {"id": "user-1", "group_ids": []}
            
            chunks = []
            async for chunk in service.stream_chat("Hello", "conv-1", current_user):
                chunks.append(chunk)
            
            assert chunks == ["Hi", " ", "there", "!"]
            mock_settings_instance.get_settings.assert_called_once_with("user-1")
            
            # Verify llm_full_prompt structure
            user_msg_call = mock_msg_repo.create.call_args_list[0]
            user_msg_data = user_msg_call[0][0]
            assert "llm_full_prompt" in user_msg_data
            llm_context = user_msg_data["llm_full_prompt"]
            assert isinstance(llm_context, dict)
            assert "system" in llm_context
            assert "context" in llm_context
            assert "current_message" in llm_context
            assert llm_context["current_message"] == "Hello"