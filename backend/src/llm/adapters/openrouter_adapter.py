"""
Path: backend/src/llm/adapters/openrouter_adapter.py
Version: 1

OpenRouter LLM adapter implementation
Provides streaming chat completion using OpenRouter unified API
"""

import logging
from typing import AsyncGenerator, Dict, List, Optional, Any
import httpx

from src.core.config import settings
from src.llm.interface import ILLM
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

logger = logging.getLogger(__name__)


class OpenRouterAdapter(ILLM):
    """
    OpenRouter LLM adapter
    
    Implements ILLM interface for OpenRouter unified API.
    Provides access to multiple model providers through single API.
    
    Configuration (from settings):
        - OPENROUTER_API_KEY: API key
        - OPENROUTER_MODEL: Model name (e.g., "openai/gpt-4", "anthropic/claude-3-opus")
        - OPENROUTER_MAX_TOKENS: Default max tokens
        - OPENROUTER_TEMPERATURE: Default temperature
        - LLM_TIMEOUT: Request timeout in seconds
    
    Example:
        adapter = OpenRouterAdapter()
        adapter.connect()
        
        messages = [{"role": "user", "content": "Hello!"}]
        async for chunk in adapter.stream_chat(messages):
            print(chunk, end="")
    """
    
    def __init__(self):
        """Initialize OpenRouter adapter with configuration"""
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1"
        self.max_tokens = settings.OPENROUTER_MAX_TOKENS
        self.temperature = settings.OPENROUTER_TEMPERATURE
        self.timeout = settings.LLM_TIMEOUT
        
        self.client: Optional[httpx.AsyncClient] = None
        self._connected = False
    
    def connect(self) -> None:
        """
        Establish connection to OpenRouter API
        
        Validates configuration and prepares HTTP client.
        
        Raises:
            AuthenticationError: If API key is missing or invalid
            ConnectionError: If connection cannot be established
        """
        if not self.api_key:
            raise AuthenticationError(
                "OPENROUTER_API_KEY not configured. "
                "Set OPENROUTER_API_KEY environment variable."
            )
        
        try:
            # Initialize async HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/simplehybridchat",
                    "X-Title": "SimpleHybridChat",
                },
                timeout=self.timeout,
            )
            self._connected = True
            logger.info(f"OpenRouter adapter connected (model: {self.model})")
            
        except Exception as e:
            raise ConnectionError(f"Failed to initialize OpenRouter client: {str(e)}")
    
    def disconnect(self) -> None:
        """Close connection to OpenRouter API"""
        if self.client:
            self._connected = False
            logger.info("OpenRouter adapter disconnected")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (prepended to messages)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Max tokens in response (None = use default)
            **kwargs: Additional OpenRouter-specific parameters
        
        Yields:
            String chunks as they arrive from API
        
        Raises:
            StreamingError: If streaming fails
            ModelNotFoundError: If model doesn't exist
            RateLimitError: If rate limit exceeded
            InvalidRequestError: If request is malformed
            ContextLengthError: If context too long
            TimeoutError: If request times out
            AuthenticationError: If API key invalid
        """
        if not self._connected or not self.client:
            raise ConnectionError("Adapter not connected. Call connect() first.")
        
        if not messages:
            raise InvalidRequestError("Messages list cannot be empty")
        
        # Build messages list with optional system prompt
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        # Prepare request payload (OpenAI-compatible format)
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        else:
            payload["max_tokens"] = self.max_tokens
        
        try:
            # Make streaming request
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                
                # Check response status
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise ModelNotFoundError(f"Model not found: {self.model}")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code == 400:
                    error_text = await response.aread()
                    if b"context_length_exceeded" in error_text:
                        raise ContextLengthError("Context length exceeded")
                    raise InvalidRequestError(f"Bad request: {error_text.decode()}")
                elif response.status_code >= 500:
                    raise StreamingError(f"OpenRouter server error: {response.status_code}")
                elif response.status_code != 200:
                    raise StreamingError(f"Unexpected status: {response.status_code}")
                
                # Stream response chunks
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if not line.startswith("data: "):
                        continue
                    
                    data = line[6:]  # Remove "data: " prefix
                    
                    if data == "[DONE]":
                        break
                    
                    try:
                        import json
                        chunk_data = json.loads(data)
                        
                        # Extract content from chunk
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            choice = chunk_data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                if content:
                                    yield content
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse chunk: {data}")
                        continue
        
        except httpx.TimeoutException:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        
        except httpx.RequestError as e:
            raise StreamingError(f"Request error: {str(e)}")
        
        except (AuthenticationError, ModelNotFoundError, RateLimitError, 
                InvalidRequestError, ContextLengthError, TimeoutError):
            # Re-raise our custom exceptions
            raise
        
        except Exception as e:
            raise StreamingError(f"Unexpected error during streaming: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get configured model name"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "openrouter"
    
    def validate_config(self) -> bool:
        """
        Validate OpenRouter configuration
        
        Returns:
            True if configuration is valid
        
        Raises:
            InvalidRequestError: If configuration is invalid
        """
        errors = []
        
        if not self.api_key:
            errors.append("OPENROUTER_API_KEY is required")
        
        if not self.model:
            errors.append("OPENROUTER_MODEL is required")
        
        if self.temperature < 0 or self.temperature > 2:
            errors.append(f"OPENROUTER_TEMPERATURE must be between 0 and 2, got {self.temperature}")
        
        if self.max_tokens <= 0:
            errors.append(f"OPENROUTER_MAX_TOKENS must be positive, got {self.max_tokens}")
        
        if self.timeout <= 0:
            errors.append(f"LLM_TIMEOUT must be positive, got {self.timeout}")
        
        if errors:
            raise InvalidRequestError(
                "OpenRouter configuration validation failed:\n" +
                "\n".join(f"  - {error}" for error in errors)
            )
        
        return True