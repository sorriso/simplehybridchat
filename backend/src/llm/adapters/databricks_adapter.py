"""
Path: backend/src/llm/adapters/databricks_adapter.py
Version: 1

Databricks LLM adapter implementation
Provides streaming chat completion using Databricks Foundation Models API
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


class DatabricksAdapter(ILLM):
    """
    Databricks LLM adapter
    
    Implements ILLM interface for Databricks Foundation Models.
    Supports DBRX, Llama, and other models via OpenAI-compatible API.
    
    Configuration (from settings):
        - DATABRICKS_API_KEY: API key or personal access token
        - DATABRICKS_BASE_URL: Workspace URL (e.g., "https://<workspace>.cloud.databricks.com")
        - DATABRICKS_MODEL: Model serving endpoint name
        - DATABRICKS_MAX_TOKENS: Default max tokens
        - DATABRICKS_TEMPERATURE: Default temperature
        - LLM_TIMEOUT: Request timeout in seconds
    
    Example:
        adapter = DatabricksAdapter()
        adapter.connect()
        
        messages = [{"role": "user", "content": "Hello!"}]
        async for chunk in adapter.stream_chat(messages):
            print(chunk, end="")
    """
    
    def __init__(self):
        """Initialize Databricks adapter with configuration"""
        self.api_key = settings.DATABRICKS_API_KEY
        self.base_url = settings.DATABRICKS_BASE_URL
        self.model = settings.DATABRICKS_MODEL
        self.max_tokens = settings.DATABRICKS_MAX_TOKENS
        self.temperature = settings.DATABRICKS_TEMPERATURE
        self.timeout = settings.LLM_TIMEOUT
        
        self.client: Optional[httpx.AsyncClient] = None
        self._connected = False
    
    def connect(self) -> None:
        """
        Establish connection to Databricks API
        
        Validates configuration and prepares HTTP client.
        
        Raises:
            AuthenticationError: If API key or base URL is missing
            ConnectionError: If connection cannot be established
        """
        if not self.api_key:
            raise AuthenticationError(
                "DATABRICKS_API_KEY not configured. "
                "Set DATABRICKS_API_KEY environment variable."
            )
        
        if not self.base_url:
            raise AuthenticationError(
                "DATABRICKS_BASE_URL not configured. "
                "Set DATABRICKS_BASE_URL environment variable."
            )
        
        try:
            # Initialize async HTTP client
            # Databricks uses OpenAI-compatible format
            self.client = httpx.AsyncClient(
                base_url=f"{self.base_url}/serving-endpoints/{self.model}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
            self._connected = True
            logger.info(f"Databricks adapter connected (model: {self.model})")
            
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Databricks client: {str(e)}")
    
    def disconnect(self) -> None:
        """Close connection to Databricks API"""
        if self.client:
            self._connected = False
            logger.info("Databricks adapter disconnected")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from Databricks
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (prepended to messages)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Max tokens in response (None = use default)
            **kwargs: Additional Databricks-specific parameters
        
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
            # Make streaming request to invocations endpoint
            async with self.client.stream(
                "POST",
                "/invocations",
                json=payload,
            ) as response:
                
                # Check response status
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise ModelNotFoundError(f"Model endpoint not found: {self.model}")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code == 400:
                    error_text = await response.aread()
                    if b"context_length_exceeded" in error_text or b"token limit" in error_text.lower():
                        raise ContextLengthError("Context length exceeded")
                    raise InvalidRequestError(f"Bad request: {error_text.decode()}")
                elif response.status_code >= 500:
                    raise StreamingError(f"Databricks server error: {response.status_code}")
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
                        
                        # Extract content from chunk (OpenAI-compatible format)
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
        return "databricks"
    
    def validate_config(self) -> bool:
        """
        Validate Databricks configuration
        
        Returns:
            True if configuration is valid
        
        Raises:
            InvalidRequestError: If configuration is invalid
        """
        errors = []
        
        if not self.api_key:
            errors.append("DATABRICKS_API_KEY is required")
        
        if not self.base_url:
            errors.append("DATABRICKS_BASE_URL is required")
        
        if not self.model:
            errors.append("DATABRICKS_MODEL is required")
        
        if self.temperature < 0 or self.temperature > 2:
            errors.append(f"DATABRICKS_TEMPERATURE must be between 0 and 2, got {self.temperature}")
        
        if self.max_tokens <= 0:
            errors.append(f"DATABRICKS_MAX_TOKENS must be positive, got {self.max_tokens}")
        
        if self.timeout <= 0:
            errors.append(f"LLM_TIMEOUT must be positive, got {self.timeout}")
        
        if errors:
            raise InvalidRequestError(
                "Databricks configuration validation failed:\n" +
                "\n".join(f"  - {error}" for error in errors)
            )
        
        return True