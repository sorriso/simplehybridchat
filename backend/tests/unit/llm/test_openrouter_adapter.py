"""
Path: backend/tests/unit/llm/test_openrouter_adapter.py
Version: 1

Unit tests for OpenRouter adapter
Tests adapter behavior with mocked HTTP responses
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.llm.adapters.openrouter_adapter import OpenRouterAdapter
from src.llm.exceptions import (
    ConnectionError,
    StreamingError,
    ModelNotFoundError,
    RateLimitError,
    InvalidRequestError,
    TimeoutError,
    AuthenticationError,
)


class TestOpenRouterAdapterInitialization:
    """Test OpenRouter adapter initialization"""
    
    def test_adapter_initialization(self):
        """Test adapter initializes with settings"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            
            assert adapter.api_key == "test-key"
            assert adapter.model == "openai/gpt-4"
            assert adapter.base_url == "https://openrouter.ai/api/v1"
            assert adapter.max_tokens == 2000
            assert adapter.temperature == 0.7
            assert adapter.timeout == 60


class TestOpenRouterAdapterConnection:
    """Test OpenRouter adapter connection management"""
    
    def test_connect_without_api_key_raises_error(self):
        """Test connect fails without API key"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = None
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            
            with pytest.raises(AuthenticationError) as exc_info:
                adapter.connect()
            
            assert "OPENROUTER_API_KEY not configured" in str(exc_info.value)
    
    def test_connect_success(self):
        """Test successful connection"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            adapter.connect()
            
            assert adapter._connected is True
            assert adapter.client is not None
    
    def test_disconnect(self):
        """Test disconnect clears connection state"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            adapter.connect()
            adapter.disconnect()
            
            assert adapter._connected is False


class TestOpenRouterAdapterValidation:
    """Test OpenRouter adapter configuration validation"""
    
    def test_validate_config_success(self):
        """Test validation passes with valid config"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            result = adapter.validate_config()
            assert result is True
    
    def test_validate_config_missing_api_key(self):
        """Test validation fails without API key"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = None
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            
            with pytest.raises(InvalidRequestError) as exc_info:
                adapter.validate_config()
            
            assert "OPENROUTER_API_KEY is required" in str(exc_info.value)


class TestOpenRouterAdapterMetadata:
    """Test OpenRouter adapter metadata methods"""
    
    def test_get_model_name(self):
        """Test get_model_name returns configured model"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "anthropic/claude-3-opus"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            assert adapter.get_model_name() == "anthropic/claude-3-opus"
    
    def test_get_provider_name(self):
        """Test get_provider_name returns 'openrouter'"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            assert adapter.get_provider_name() == "openrouter"


class TestOpenRouterAdapterStreamChat:
    """Test OpenRouter adapter stream_chat method"""
    
    @pytest.mark.asyncio
    async def test_stream_chat_not_connected_raises_error(self):
        """Test stream_chat fails if not connected"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(ConnectionError):
                async for _ in adapter.stream_chat(messages):
                    pass
    
    @pytest.mark.asyncio
    async def test_stream_chat_empty_messages_raises_error(self):
        """Test stream_chat fails with empty messages"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            adapter.connect()
            
            with pytest.raises(InvalidRequestError):
                async for _ in adapter.stream_chat([]):
                    pass
    
    @pytest.mark.asyncio
    async def test_stream_chat_success(self):
        """Test successful streaming response"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            adapter.connect()
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            
            async def mock_aiter_lines():
                lines = [
                    'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                    'data: {"choices":[{"delta":{"content":" world"}}]}',
                    'data: [DONE]',
                ]
                for line in lines:
                    yield line
            
            mock_response.aiter_lines = mock_aiter_lines
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            adapter.client.stream = MagicMock(return_value=mock_stream_context)
            
            messages = [{"role": "user", "content": "Hi"}]
            chunks = []
            
            async for chunk in adapter.stream_chat(messages):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " world"]
    
    @pytest.mark.asyncio
    async def test_stream_chat_handles_401_error(self):
        """Test stream_chat raises AuthenticationError on 401"""
        with patch("src.llm.adapters.openrouter_adapter.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "openai/gpt-4"
            mock_settings.OPENROUTER_MAX_TOKENS = 2000
            mock_settings.OPENROUTER_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenRouterAdapter()
            adapter.connect()
            
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            adapter.client.stream = MagicMock(return_value=mock_stream_context)
            
            messages = [{"role": "user", "content": "Hi"}]
            
            with pytest.raises(AuthenticationError):
                async for _ in adapter.stream_chat(messages):
                    pass