"""
Path: backend/src/llm/adapters/ollama_adapter.py
Version: 2.0

Changes in v2.0:
- Enhanced debugging for model pulling with detailed logs
- Added post-pull verification to ensure model is actually installed
- Added 2-second wait after pull for Ollama to finalize
- Added comprehensive statistics collection (tokens, duration, performance)
- Added get_stats() method to retrieve last generation statistics
- Improved error messages and troubleshooting information

Ollama adapter for local LLM inference
Uses Ollama API for running models locally
"""

import logging
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass, asdict
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


@dataclass
class OllamaStats:
    """Statistics from Ollama generation"""
    # Token counts
    prompt_tokens: int = 0      # Input tokens (prompt_eval_count)
    completion_tokens: int = 0  # Output tokens (eval_count)
    total_tokens: int = 0       # Total tokens
    
    # Duration in nanoseconds (Ollama format)
    total_duration_ns: int = 0       # Total time
    load_duration_ns: int = 0        # Model load time
    prompt_eval_duration_ns: int = 0 # Prompt evaluation time
    eval_duration_ns: int = 0        # Generation time
    
    # Derived metrics (in seconds for convenience)
    total_duration_s: float = 0.0
    tokens_per_second: float = 0.0
    
    # Model info
    model: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


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
        self._last_stats: Optional[OllamaStats] = None
        
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
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get statistics from last generation
        
        Returns:
            Dictionary with token counts, durations, and performance metrics
            None if no generation has occurred yet
            
        Example:
            {
                'prompt_tokens': 15,
                'completion_tokens': 42,
                'total_tokens': 57,
                'total_duration_s': 2.5,
                'tokens_per_second': 16.8,
                'model': 'tinyllama'
            }
        """
        if self._last_stats:
            return self._last_stats.to_dict()
        return None
    
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
            
        Note:
            After generation completes, statistics are available via get_stats()
        """
        if not self.client:
            raise ConnectionError("Not connected to Ollama")
        
        # Reset stats for this generation
        self._last_stats = None
        
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
                        
                        # Check if done and collect stats
                        if data.get("done", False):
                            self._collect_stats(data)
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse Ollama response line: {line[:100]}")
                        continue
                    
        except ModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise StreamingError(f"Ollama streaming failed: {str(e)}")
    
    def _collect_stats(self, final_data: Dict[str, Any]) -> None:
        """
        Collect statistics from final Ollama response
        
        Args:
            final_data: Final response data with 'done': True
        """
        try:
            stats = OllamaStats(model=self.model)
            
            # Token counts
            stats.prompt_tokens = final_data.get("prompt_eval_count", 0)
            stats.completion_tokens = final_data.get("eval_count", 0)
            stats.total_tokens = stats.prompt_tokens + stats.completion_tokens
            
            # Durations (nanoseconds)
            stats.total_duration_ns = final_data.get("total_duration", 0)
            stats.load_duration_ns = final_data.get("load_duration", 0)
            stats.prompt_eval_duration_ns = final_data.get("prompt_eval_duration", 0)
            stats.eval_duration_ns = final_data.get("eval_duration", 0)
            
            # Convert to seconds
            stats.total_duration_s = stats.total_duration_ns / 1_000_000_000
            
            # Calculate tokens per second
            if stats.eval_duration_ns > 0:
                stats.tokens_per_second = (
                    stats.completion_tokens / (stats.eval_duration_ns / 1_000_000_000)
                )
            
            self._last_stats = stats
            
            # Log summary
            logger.info(
                f"Generation complete: {stats.completion_tokens} tokens in "
                f"{stats.total_duration_s:.2f}s ({stats.tokens_per_second:.1f} tok/s)"
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect stats: {e}")
    
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
            logger.debug(f"[DEBUG] Listing models from: {self.base_url}/api/tags")
            
            response = await self.client.get("/api/tags")
            
            logger.debug(f"[DEBUG] List response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"[DEBUG] List failed with status {response.status_code}: {error_text}")
                raise LLMException(f"Failed to list models: {response.status_code}")
            
            data = response.json()
            logger.debug(f"[DEBUG] List response data: {data}")
            
            models = [model["name"] for model in data.get("models", [])]
            logger.info(f"[DEBUG] Available models: {models}")
            
            return models
            
        except Exception as e:
            logger.error(f"[DEBUG] List exception: {type(e).__name__}: {e}")
            raise LLMException(f"Failed to list models: {str(e)}")
    
    async def pull_model(self, model_name: str) -> None:
        """
        Pull/download a model from Ollama registry
        
        Args:
            model_name: Name of model to pull (e.g., "tinyllama")
            
        Raises:
            LLMException: If pull fails
            
        Note:
            After pulling, the method verifies the model is actually installed
            by checking it appears in list_models()
        """
        if not self.client:
            raise ConnectionError("Not connected to Ollama")
        
        try:
            logger.info(f"[DEBUG] Starting pull for model: {model_name}")
            logger.info(f"[DEBUG] Ollama URL: {self.base_url}")
            logger.info(f"[DEBUG] Pull endpoint: {self.base_url}/api/pull")
            
            # Pull request
            pull_data = {"name": model_name, "stream": True}
            logger.debug(f"[DEBUG] Pull request data: {pull_data}")
            
            async with self.client.stream(
                "POST",
                "/api/pull",
                json=pull_data
            ) as response:
                
                logger.info(f"[DEBUG] Pull response status: {response.status_code}")
                logger.debug(f"[DEBUG] Pull response headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_msg = error_text.decode()
                    logger.error(f"[DEBUG] Pull failed with status {response.status_code}")
                    logger.error(f"[DEBUG] Error body: {error_msg}")
                    raise LLMException(f"Failed to pull model: {response.status_code} - {error_msg}")
                
                # Log progress
                logger.info(f"[DEBUG] Streaming pull progress...")
                async for line in response.aiter_lines():
                    if line.strip():
                        import json
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                logger.info(f"Pull progress: {data['status']}")
                            if "error" in data:
                                logger.error(f"[DEBUG] Pull error in stream: {data['error']}")
                                raise LLMException(f"Pull error: {data['error']}")
                        except json.JSONDecodeError:
                            logger.debug(f"[DEBUG] Non-JSON line: {line[:100]}")
            
            logger.info(f"[DEBUG] Pull stream completed successfully")
            
            # CRITICAL: Wait for Ollama to finalize the model
            logger.info(f"[DEBUG] Waiting 2 seconds for Ollama to finalize model...")
            await asyncio.sleep(2)
            
            # Verify model is actually installed
            logger.info(f"[DEBUG] Verifying model installation...")
            try:
                models = await self.list_models()
                logger.info(f"[DEBUG] Models after pull: {models}")
                
                # Check if model is in the list (may have :latest suffix)
                model_found = any(
                    model_name in model or model in model_name 
                    for model in models
                )
                
                if not model_found:
                    logger.error(f"[DEBUG] Model '{model_name}' NOT FOUND after pull!")
                    logger.error(f"[DEBUG] Available models: {models}")
                    logger.error(f"[DEBUG] This indicates a problem with Ollama storage/persistence")
                    raise LLMException(
                        f"Model '{model_name}' was pulled but not found in model list. "
                        f"Available models: {models}. "
                        f"Check Ollama volume persistence and permissions."
                    )
                
                logger.info(f"[DEBUG] ✓ Model '{model_name}' verified in model list")
                
            except LLMException:
                raise
            except Exception as e:
                logger.error(f"[DEBUG] Failed to verify model: {type(e).__name__}: {e}")
                raise LLMException(f"Failed to verify model after pull: {str(e)}")
            
            logger.info(f"Model {model_name} pulled and verified successfully")
            
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"[DEBUG] Pull exception: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
            raise LLMException(f"Failed to pull model: {str(e)}")