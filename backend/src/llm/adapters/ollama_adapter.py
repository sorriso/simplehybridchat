"""
Path: backend/src/llm/adapters/ollama_adapter.py
Version: 1

Ollama adapter for local LLM inference
Uses Ollama API for running models locally
"""

import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
import httpx

from src.llm.interface import ILLM
from src.llm.exceptions import (
    ConnectionError,
    StreamingError,
    ModelNotFoundError,
    InvalidRequestError,
    LLMException
)
from src.core.config import settings

logger = logging.getLogger(__name__)


class OllamaAdapter(ILLM):
    """
    Ollama adapter for local LLM inference
    
    Supports running models locally via Ollama:
    - tinyllama (1.1B) - Fast and small
    - llama2 (7B) - Better quality
    - mistral (7B) - Good performance
    
    Configuration (environment variables):
    - OLLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
    - OLLAMA_MODEL: Model name (default: tinyllama)
    - OLLAMA_TIMEOUT: Request timeout in seconds (default: 300)
    """
    
    def __init__(self):
        """Initialize Ollama adapter"""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.client: Optional[httpx.AsyncClient] = None
        self._connected = False
        
        logger.info(f"Initializing Ollama adapter: {self.base_url}, model: {self.model}")
    
    def validate_config(self) -> None:
        """
        Validate Ollama configuration
        
        Raises:
            InvalidRequestError: If configuration is invalid
        """
        if not self.base_url:
            raise InvalidRequestError("OLLAMA_BASE_URL is required")
        
        if not self.model:
            raise InvalidRequestError("OLLAMA_MODEL is required")
        
        logger.info("Ollama configuration validated")
    
    def connect(self) -> None:
        """
        Establish connection to Ollama server
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            self._connected = True
            logger.info(f"Connected to Ollama: {self.base_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise ConnectionError(f"Ollama connection failed: {str(e)}")
    
    def disconnect(self) -> None:
        """Close connection to Ollama"""
        if self.client:
            # httpx.AsyncClient needs async close, but we'll handle it in __del__
            self._connected = False
            logger.info("Disconnected from Ollama")
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not self._connected:
            self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from Ollama
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (Ollama uses num_predict)
            **kwargs: Additional Ollama-specific parameters
            
        Yields:
            Text chunks as they are generated
            
        Raises:
            StreamingError: If streaming fails
            ModelNotFoundError: If model not found
        """
        if not self.client:
            raise ConnectionError("Not connected to Ollama")
        
        try:
            # Build Ollama chat request
            request_data = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_data["messages"] = [
                    {"role": "system", "content": system_prompt}
                ] + messages
            
            # Add max tokens if specified
            if max_tokens:
                request_data["options"]["num_predict"] = max_tokens
            
            # Stream response
            async with self.client.stream(
                "POST",
                "/api/chat",
                json=request_data
            ) as response:
                
                if response.status_code == 404:
                    raise ModelNotFoundError(f"Model '{self.model}' not found in Ollama")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise StreamingError(
                        f"Ollama streaming failed: {response.status_code} - {error_text.decode()}"
                    )
                
                # Parse streaming response
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        import json
                        data = json.loads(line)
                        
                        # Extract message content
                        if "message" in data and "content" in data["message"]:
                            chunk = data["message"]["content"]
                            if chunk:
                                yield chunk
                        
                        # Check if done
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse Ollama response line: {line[:100]}")
                        continue
                    
        except ModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise StreamingError(f"Ollama streaming failed: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get current model name"""
        return self.model
    
    def get_llm_type(self) -> str:
        """Get LLM provider type"""
        return "ollama"
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return f"Ollama ({self.model})"
    
    async def list_models(self) -> List[str]:
        """
        List available models in Ollama
        
        Returns:
            List of model names
            
        Raises:
            LLMException: If listing fails
        """
        if not self.client:
            raise ConnectionError("Not connected to Ollama")
        
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            raise LLMException(f"Failed to list models: {str(e)}")
    
    async def pull_model(self, model_name: str) -> None:
        """
        Pull/download a model
        
        Args:
            model_name: Name of model to pull (e.g., "tinyllama")
            
        Raises:
            LLMException: If pull fails
        """
        if not self.client:
            raise ConnectionError("Not connected to Ollama")
        
        try:
            logger.info(f"Pulling Ollama model: {model_name}")
            
            async with self.client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name, "stream": True}
            ) as response:
                response.raise_for_status()
                
                # Log progress
                async for line in response.aiter_lines():
                    if line.strip():
                        import json
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                logger.info(f"Pull progress: {data['status']}")
                        except json.JSONDecodeError:
                            pass
            
            logger.info(f"Model {model_name} pulled successfully")
            
        except Exception as e:
            logger.error(f"Failed to pull Ollama model: {e}")
            raise LLMException(f"Failed to pull model: {str(e)}")