"""
Path: backend/tests/unit/services/test_chat_service.py
Version: 6.0

Changes in v6.0:
- Add verification of LLM metadata fields in created messages:
  - llm_full_prompt stored in both user and assistant messages
  - llm_raw_response stored in assistant messages
  - llm_stats stored in assistant messages (from LLM.get_stats())
- Mock LLM.get_stats() to return statistics dict
- Verify create() calls include new optional fields

Changes in v5.2:
- Use patch for SettingsService to properly mock it before service creation
- Remove manual assignment of mock_settings_service (doesn't work reliably)
- Simplify tests to focus on actual behavior verification
- Tests now verify that user settings are properly retrieved and applied

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
        """Test successful chat streaming with default settings"""
        with patch('src.services.chat_service.SettingsService') as MockSettingsService:
            # Mock SettingsService to return empty customization
            mock_settings_instance = MagicMock()
            mock_settings_instance.get_settings.return_value = {
                "prompt_customization": "",
                "theme": "light",
                "language": "en"
            }
            MockSettingsService.return_value = mock_settings_instance
            
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
            
            # Mock LLM with stats
            mock_llm = MagicMock()
            mock_llm.get_stats.return_value = {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
                "total_duration_s": 0.5,
                "tokens_per_second": 10.0,
                "model": "tinyllama"
            }
            
            async def mock_stream(*args, **kwargs):
                # Verify system prompt is default (no customization)
                system_prompt = kwargs.get("system_prompt")
                assert "helpful AI assistant" in system_prompt
                assert "preferences" not in system_prompt  # No customization
                
                for chunk in ["Hi", " ", "there", "!"]:
                    yield chunk
            
            mock_llm.stream_chat = mock_stream
            
            # Create service (SettingsService is now mocked)
            service = ChatService(db=MagicMock())
            service.conversation_repo = mock_conv_repo
            service.message_repo = mock_msg_repo
            service._llm = mock_llm
            
            current_user = {"id": "user-1", "group_ids": []}
            
            # Stream chat
            chunks = []
            async for chunk in service.stream_chat("Hello", "conv-1", current_user):
                chunks.append(chunk)
            
            # Verify chunks
            assert chunks == ["Hi", " ", "there", "!"]
            
            # Verify settings were retrieved
            mock_settings_instance.get_settings.assert_called_once_with("user-1")
            
            # Verify messages created with LLM metadata
            assert mock_msg_repo.create.call_count == 2
            
            # Check user message has llm_full_prompt
            user_msg_call = mock_msg_repo.create.call_args_list[0]
            user_msg_data = user_msg_call[0][0]
            assert user_msg_data["role"] == "user"
            assert user_msg_data["content"] == "Hello"
            assert "llm_full_prompt" in user_msg_data
            assert "helpful AI assistant" in user_msg_data["llm_full_prompt"]
            
            # Check assistant message has full LLM metadata
            assistant_msg_call = mock_msg_repo.create.call_args_list[1]
            assistant_msg_data = assistant_msg_call[0][0]
            assert assistant_msg_data["role"] == "assistant"
            assert assistant_msg_data["content"] == "Hi there!"
            assert "llm_full_prompt" in assistant_msg_data
            assert "llm_raw_response" in assistant_msg_data
            assert assistant_msg_data["llm_raw_response"] == "Hi there!"
            assert "llm_stats" in assistant_msg_data
            assert assistant_msg_data["llm_stats"]["prompt_tokens"] == 10
            assert assistant_msg_data["llm_stats"]["completion_tokens"] == 5
            
            # Verify LLM stats were retrieved
            mock_llm.get_stats.assert_called_once()
            
            # Verify conversation updated
            mock_conv_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_chat_with_request_customization(self):
        """Test that request prompt_customization is used"""
        with patch('src.services.chat_service.SettingsService') as MockSettingsService:
            # Mock SettingsService with empty customization
            mock_settings_instance = MagicMock()
            mock_settings_instance.get_settings.return_value = {
                "prompt_customization": "",
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
            mock_llm.get_stats.return_value = {"prompt_tokens": 12, "completion_tokens": 3}
            
            async def mock_stream(*args, **kwargs):
                # Verify system prompt includes request customization
                system_prompt = kwargs.get("system_prompt")
                assert "Be brief" in system_prompt
                yield "OK"
            
            mock_llm.stream_chat = mock_stream
            
            service = ChatService(db=MagicMock())
            service.conversation_repo = mock_conv_repo
            service.message_repo = mock_msg_repo
            service._llm = mock_llm
            
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
            mock_settings_instance.get_settings.assert_called_once_with("user-1")
    
    @pytest.mark.asyncio
    async def test_stream_chat_with_db_customization(self):
        """Test that DB prompt_customization is used when no request customization"""
        with patch('src.services.chat_service.SettingsService') as MockSettingsService:
            # Mock SettingsService with DB customization
            mock_settings_instance = MagicMock()
            mock_settings_instance.get_settings.return_value = {
                "prompt_customization": "Always be polite",
                "theme": "dark",
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
                assert "Always be polite" in system_prompt
                yield "Certainly"
            
            mock_llm.stream_chat = mock_stream
            
            service = ChatService(db=MagicMock())
            service.conversation_repo = mock_conv_repo
            service.message_repo = mock_msg_repo
            service._llm = mock_llm
            
            current_user = {"id": "user-1", "group_ids": []}
            
            chunks = []
            async for chunk in service.stream_chat("Hello", "conv-1", current_user):
                chunks.append(chunk)
            
            assert chunks == ["Certainly"]
            mock_settings_instance.get_settings.assert_called_once_with("user-1")
    
    @pytest.mark.asyncio
    async def test_stream_chat_request_overrides_db(self):
        """Test request prompt_customization takes priority over DB"""
        with patch('src.services.chat_service.SettingsService') as MockSettingsService:
            # Mock SettingsService with DB customization
            mock_settings_instance = MagicMock()
            mock_settings_instance.get_settings.return_value = {
                "prompt_customization": "DB prompt (should be ignored)",
                "theme": "dark",
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
            mock_llm.get_stats.return_value = {"prompt_tokens": 20, "completion_tokens": 2}
            
            async def mock_stream(*args, **kwargs):
                # Verify system prompt uses REQUEST customization, not DB
                system_prompt = kwargs.get("system_prompt")
                assert "Request prompt" in system_prompt
                assert "DB prompt" not in system_prompt
                yield "OK"
            
            mock_llm.stream_chat = mock_stream
            
            service = ChatService(db=MagicMock())
            service.conversation_repo = mock_conv_repo
            service.message_repo = mock_msg_repo
            service._llm = mock_llm
            
            current_user = {"id": "user-1", "group_ids": []}
            
            chunks = []
            async for chunk in service.stream_chat(
                "Hello",
                "conv-1",
                current_user,
                prompt_customization="Request prompt (priority)"
            ):
                chunks.append(chunk)
            
            assert chunks == ["OK"]
            mock_settings_instance.get_settings.assert_called_once_with("user-1")