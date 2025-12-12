"""
Path: backend/tests/unit/llm/test_openai_adapter.py
Version: 1

Unit tests for OpenAI adapter
Tests adapter behavior with mocked HTTP responses
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.llm.adapters.openai_adapter import OpenAIAdapter
from src.llm.exceptions import (
    ConnectionError,
    StreamingError,
    ModelNotFoundError,
    RateLimitError,
    InvalidRequestError,
    TimeoutError,
    ContextLengthError,
    AuthenticationError,
)


class TestOpenAIAdapterInitialization:
    """Test OpenAI adapter initialization"""
    
    def test_adapter_initialization(self):
        """Test adapter initializes with settings"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            assert adapter.api_key == "test-key"
            assert adapter.model == "gpt-4"
            assert adapter.base_url == "https://api.openai.com/v1"
            assert adapter.max_tokens == 2000
            assert adapter.temperature == 0.7
            assert adapter.timeout == 60
    
    def test_adapter_initialization_with_custom_base_url(self):
        """Test adapter uses custom base URL when provided"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = "https://custom.openai.com"
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            assert adapter.base_url == "https://custom.openai.com"


class TestOpenAIAdapterConnection:
    """Test OpenAI adapter connection management"""
    
    def test_connect_without_api_key_raises_error(self):
        """Test connect fails without API key"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            with pytest.raises(AuthenticationError) as exc_info:
                adapter.connect()
            
            assert "OPENAI_API_KEY not configured" in str(exc_info.value)
    
    def test_connect_success(self):
        """Test successful connection"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            assert adapter._connected is True
            assert adapter.client is not None
    
    def test_disconnect(self):
        """Test disconnect clears connection state"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            assert adapter._connected is True
            
            adapter.disconnect()
            
            assert adapter._connected is False


class TestOpenAIAdapterValidation:
    """Test OpenAI adapter configuration validation"""
    
    def test_validate_config_success(self):
        """Test validation passes with valid config"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            result = adapter.validate_config()
            assert result is True
    
    def test_validate_config_missing_api_key(self):
        """Test validation fails without API key"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            with pytest.raises(InvalidRequestError) as exc_info:
                adapter.validate_config()
            
            assert "OPENAI_API_KEY is required" in str(exc_info.value)
    
    def test_validate_config_invalid_temperature(self):
        """Test validation fails with invalid temperature"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 3.0
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            with pytest.raises(InvalidRequestError) as exc_info:
                adapter.validate_config()
            
            assert "OPENAI_TEMPERATURE must be between 0 and 2" in str(exc_info.value)
    
    def test_validate_config_invalid_max_tokens(self):
        """Test validation fails with invalid max_tokens"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = -100
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            with pytest.raises(InvalidRequestError) as exc_info:
                adapter.validate_config()
            
            assert "OPENAI_MAX_TOKENS must be positive" in str(exc_info.value)


class TestOpenAIAdapterMetadata:
    """Test OpenAI adapter metadata methods"""
    
    def test_get_model_name(self):
        """Test get_model_name returns configured model"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4-turbo"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            assert adapter.get_model_name() == "gpt-4-turbo"
    
    def test_get_provider_name(self):
        """Test get_provider_name returns 'openai'"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            
            assert adapter.get_provider_name() == "openai"


class TestOpenAIAdapterStreamChat:
    """Test OpenAI adapter stream_chat method"""
    
    @pytest.mark.asyncio
    async def test_stream_chat_not_connected_raises_error(self):
        """Test stream_chat fails if not connected"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(ConnectionError) as exc_info:
                async for _ in adapter.stream_chat(messages):
                    pass
            
            assert "Adapter not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_chat_empty_messages_raises_error(self):
        """Test stream_chat fails with empty messages"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            with pytest.raises(InvalidRequestError) as exc_info:
                async for _ in adapter.stream_chat([]):
                    pass
            
            assert "Messages list cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_chat_success(self):
        """Test successful streaming response"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            # Mock streaming response
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
    async def test_stream_chat_with_system_prompt(self):
        """Test streaming with system prompt prepends it to messages"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            # Mock response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            
            async def mock_aiter_lines():
                yield 'data: {"choices":[{"delta":{"content":"response"}}]}'
                yield 'data: [DONE]'
            
            mock_response.aiter_lines = mock_aiter_lines
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            
            # Capture the request payload
            captured_payload = {}
            
            def mock_stream_call(method, url, **kwargs):
                captured_payload.update(kwargs.get('json', {}))
                return mock_stream_context
            
            adapter.client.stream = mock_stream_call
            
            messages = [{"role": "user", "content": "Hello"}]
            system_prompt = "You are helpful"
            
            chunks = []
            async for chunk in adapter.stream_chat(messages, system_prompt=system_prompt):
                chunks.append(chunk)
            
            # Verify system prompt was prepended
            assert captured_payload['messages'][0] == {"role": "system", "content": "You are helpful"}
            assert captured_payload['messages'][1] == {"role": "user", "content": "Hello"}
    
    @pytest.mark.asyncio
    async def test_stream_chat_handles_401_error(self):
        """Test stream_chat raises AuthenticationError on 401"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
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
    
    @pytest.mark.asyncio
    async def test_stream_chat_handles_404_error(self):
        """Test stream_chat raises ModelNotFoundError on 404"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            mock_response = AsyncMock()
            mock_response.status_code = 404
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            
            adapter.client.stream = MagicMock(return_value=mock_stream_context)
            
            messages = [{"role": "user", "content": "Hi"}]
            
            with pytest.raises(ModelNotFoundError):
                async for _ in adapter.stream_chat(messages):
                    pass
    
    @pytest.mark.asyncio
    async def test_stream_chat_handles_429_error(self):
        """Test stream_chat raises RateLimitError on 429"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            mock_response = AsyncMock()
            mock_response.status_code = 429
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            
            adapter.client.stream = MagicMock(return_value=mock_stream_context)
            
            messages = [{"role": "user", "content": "Hi"}]
            
            with pytest.raises(RateLimitError):
                async for _ in adapter.stream_chat(messages):
                    pass
    
    @pytest.mark.asyncio
    async def test_stream_chat_handles_timeout(self):
        """Test stream_chat raises TimeoutError on timeout"""
        with patch("src.llm.adapters.openai_adapter.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_BASE_URL = None
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.LLM_TIMEOUT = 60
            
            adapter = OpenAIAdapter()
            adapter.connect()
            
            # Mock timeout exception
            adapter.client.stream = MagicMock(side_effect=httpx.TimeoutException("timeout"))
            
            messages = [{"role": "user", "content": "Hi"}]
            
            with pytest.raises(TimeoutError):
                async for _ in adapter.stream_chat(messages):
                    pass