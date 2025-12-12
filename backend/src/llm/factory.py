"""
Path: backend/src/llm/factory.py
Version: 1

LLM factory pattern implementation
Provides single point to get LLM instance based on configuration
"""

from typing import Optional
import logging

from src.core.config import settings
from src.llm.interface import ILLM
from src.llm.exceptions import LLMException, InvalidRequestError

logger = logging.getLogger(__name__)

# Singleton instance
_llm_instance: Optional[ILLM] = None


def get_llm() -> ILLM:
    """
    Factory function to get LLM instance based on configuration
    
    Returns appropriate LLM adapter based on settings.LLM_PROVIDER:
        - "openai": OpenAI GPT models
        - "claude": Anthropic Claude models
        - "gemini": Google Gemini models
        - "databricks": Databricks DBRX/Llama models
        - "openrouter": OpenRouter unified API
        - "ollama": Local Ollama models
    
    Returns:
        ILLM implementation (singleton)
        
    Raises:
        ValueError: If LLM_PROVIDER is not supported
        LLMException: If connection fails
        
    Example:
        # In service
        from src.llm.factory import get_llm
        
        llm = get_llm()
        async for chunk in llm.stream_chat(messages):
            yield chunk
        
    Note:
        This returns a singleton instance. The LLM connection
        is established on first call and reused for subsequent calls.
        
        To change LLM implementation, simply update LLM_PROVIDER
        in configuration - no code changes needed.
    """
    global _llm_instance
    
    if _llm_instance is None:
        logger.info(f"Initializing LLM adapter: {settings.LLM_PROVIDER}")
        
        # Import and instantiate appropriate adapter
        if settings.LLM_PROVIDER == "openai":
            from src.llm.adapters.openai_adapter import OpenAIAdapter
            _llm_instance = OpenAIAdapter()
            
        elif settings.LLM_PROVIDER == "claude":
            # Future implementation
            try:
                from src.llm.adapters.claude_adapter import ClaudeAdapter
                _llm_instance = ClaudeAdapter()
            except ImportError:
                raise LLMException(
                    "Claude adapter not implemented yet. "
                    "Set LLM_PROVIDER=openai in configuration."
                )
            
        elif settings.LLM_PROVIDER == "gemini":
            # Future implementation
            try:
                from src.llm.adapters.gemini_adapter import GeminiAdapter
                _llm_instance = GeminiAdapter()
            except ImportError:
                raise LLMException(
                    "Gemini adapter not implemented yet. "
                    "Set LLM_PROVIDER=openai in configuration."
                )
            
        elif settings.LLM_PROVIDER == "databricks":
            # Future implementation
            try:
                from src.llm.adapters.databricks_adapter import DatabricksAdapter
                _llm_instance = DatabricksAdapter()
            except ImportError:
                raise LLMException(
                    "Databricks adapter not implemented yet. "
                    "Set LLM_PROVIDER=openai in configuration."
                )
            
        elif settings.LLM_PROVIDER == "openrouter":
            # Future implementation
            try:
                from src.llm.adapters.openrouter_adapter import OpenRouterAdapter
                _llm_instance = OpenRouterAdapter()
            except ImportError:
                raise LLMException(
                    "OpenRouter adapter not implemented yet. "
                    "Set LLM_PROVIDER=openai in configuration."
                )
            
        elif settings.LLM_PROVIDER == "ollama":
            # Future implementation
            try:
                from src.llm.adapters.ollama_adapter import OllamaAdapter
                _llm_instance = OllamaAdapter()
            except ImportError:
                raise LLMException(
                    "Ollama adapter not implemented yet. "
                    "Set LLM_PROVIDER=openai in configuration."
                )
            
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}. "
                f"Supported types: openai, claude, gemini, databricks, openrouter, ollama"
            )
        
        # Validate configuration before connecting
        try:
            _llm_instance.validate_config()
            logger.info(f"LLM configuration validated: {settings.LLM_PROVIDER}")
        except InvalidRequestError as e:
            logger.error(f"Invalid LLM configuration: {e}")
            _llm_instance = None
            raise
        
        # Establish connection
        try:
            _llm_instance.connect()
            logger.info(
                f"LLM connection established: {settings.LLM_PROVIDER} "
                f"(model: {_llm_instance.get_model_name()})"
            )
        except Exception as e:
            logger.error(f"Failed to connect to LLM provider: {e}")
            _llm_instance = None
            raise LLMException(f"LLM connection failed: {str(e)}")
    
    return _llm_instance


def reset_llm() -> None:
    """
    Reset LLM singleton instance
    
    Useful for testing or forcing reconnection.
    Closes existing connection and clears singleton.
    
    Example:
        # In tests
        from src.llm.factory import reset_llm
        
        def teardown():
            reset_llm()  # Clean state between tests
    """
    global _llm_instance
    
    if _llm_instance is not None:
        try:
            _llm_instance.disconnect()
            logger.info("LLM connection closed")
        except Exception as e:
            logger.warning(f"Error disconnecting LLM: {e}")
        finally:
            _llm_instance = None


def get_llm_type() -> str:
    """
    Get configured LLM provider type
    
    Returns:
        LLM provider string (openai, claude, gemini, etc.)
        
    Example:
        llm_type = get_llm_type()
        if llm_type == "openai":
            # OpenAI-specific logic
            pass
    """
    return settings.LLM_PROVIDER


def is_connected() -> bool:
    """
    Check if LLM is connected
    
    Returns:
        True if LLM instance exists and is connected
        
    Example:
        if not is_connected():
            logger.warning("LLM not connected")
            llm = get_llm()  # Reconnect
    """
    return _llm_instance is not None


def get_available_providers() -> list[str]:
    """
    Get list of supported LLM providers
    
    Returns:
        List of provider names that can be configured
        
    Example:
        providers = get_available_providers()
        print(f"Available providers: {', '.join(providers)}")
    """
    return ["openai", "claude", "gemini", "databricks", "openrouter", "ollama"]


def get_provider_status() -> dict[str, bool]:
    """
    Check which providers are implemented
    
    Returns:
        Dict mapping provider names to implementation status
        
    Example:
        status = get_provider_status()
        for provider, implemented in status.items():
            print(f"{provider}: {'✓' if implemented else '✗'}")
    """
    status = {}
    
    for provider in get_available_providers():
        try:
            if provider == "openai":
                from src.llm.adapters.openai_adapter import OpenAIAdapter
                status[provider] = True
            elif provider == "claude":
                from src.llm.adapters.claude_adapter import ClaudeAdapter
                status[provider] = True
            elif provider == "gemini":
                from src.llm.adapters.gemini_adapter import GeminiAdapter
                status[provider] = True
            elif provider == "databricks":
                from src.llm.adapters.databricks_adapter import DatabricksAdapter
                status[provider] = True
            elif provider == "openrouter":
                from src.llm.adapters.openrouter_adapter import OpenRouterAdapter
                status[provider] = True
            elif provider == "ollama":
                from src.llm.adapters.ollama_adapter import OllamaAdapter
                status[provider] = True
            else:
                status[provider] = False
        except ImportError:
            status[provider] = False
    
    return status