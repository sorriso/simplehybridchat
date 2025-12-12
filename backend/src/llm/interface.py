"""
Path: backend/src/llm/interface.py
Version: 1

Abstract LLM interface defining contract for all LLM adapters
This interface ensures LLM implementation can be swapped without changing application code
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional


class ILLM(ABC):
    """
    Abstract interface for LLM operations
    
    All LLM adapters must implement this interface to ensure
    consistent behavior across different LLM providers.
    
    Implementations:
        - OpenAIAdapter: OpenAI GPT models
        - ClaudeAdapter: Anthropic Claude models
        - GeminiAdapter: Google Gemini models
        - DatabricksAdapter: Databricks DBRX/Llama models
        - OpenRouterAdapter: OpenRouter unified API
        - OllamaAdapter: Local Ollama models
    
    Usage:
        llm = get_llm()  # Returns configured adapter
        async for chunk in llm.stream_chat(messages):
            print(chunk, end="")
    """
    
    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to LLM provider
        
        Called once during initialization by factory.
        Should validate API keys, check connectivity, etc.
        
        Raises:
            ConnectionError: If connection cannot be established
            AuthenticationError: If credentials are invalid
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to LLM provider
        
        Should cleanup resources, close connections, etc.
        Called during application shutdown.
        """
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "user", "content": "Hello"}]
            system_prompt: Optional system prompt to guide model behavior
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response (None = model default)
            **kwargs: Provider-specific parameters
            
        Yields:
            String chunks of the response as they arrive
            
        Raises:
            StreamingError: If streaming fails or is interrupted
            ModelNotFoundError: If specified model doesn't exist
            RateLimitError: If rate limit is exceeded
            InvalidRequestError: If request parameters are invalid
            ContextLengthError: If messages exceed context window
            TimeoutError: If request times out
            
        Example:
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello!"}
            ]
            
            async for chunk in llm.stream_chat(messages):
                print(chunk, end="", flush=True)
                
        Note:
            The generator must yield text chunks only.
            Special markers like [DONE] should NOT be yielded.
            Error handling should raise appropriate exceptions.
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the configured model name
        
        Returns:
            Model identifier (e.g., "gpt-4", "claude-3-opus", "gemini-pro")
            
        Example:
            model = llm.get_model_name()
            logger.info(f"Using model: {model}")
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the LLM provider name
        
        Returns:
            Provider name (e.g., "openai", "claude", "gemini")
            
        Example:
            provider = llm.get_provider_name()
            logger.info(f"Using provider: {provider}")
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate provider configuration
        
        Checks if all required configuration values are present and valid.
        Does not make API calls, just validates local configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            InvalidRequestError: If configuration is invalid
            
        Example:
            if llm.validate_config():
                llm.connect()
        """
        pass
    
    # Future extension points for memory and RAG
    
    def enrich_messages_with_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Enrich messages with user memory (future implementation)
        
        This is a placeholder for future memory integration (e.g., mem0).
        Default implementation returns messages unchanged.
        
        Args:
            messages: Original message list
            user_id: User identifier for memory lookup
            conversation_id: Conversation identifier for context
            
        Returns:
            Enriched message list with memory context
            
        Example:
            # Future implementation
            enriched = llm.enrich_messages_with_memory(messages, user_id, conv_id)
            async for chunk in llm.stream_chat(enriched):
                yield chunk
        """
        return messages
    
    def enrich_messages_with_rag(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Enrich messages with RAG context (future implementation)
        
        This is a placeholder for future RAG integration (vectors, graphs).
        Default implementation returns messages unchanged.
        
        Args:
            messages: Original message list
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            Enriched message list with RAG context
            
        Example:
            # Future implementation
            enriched = llm.enrich_messages_with_rag(messages, user_id, conv_id)
            async for chunk in llm.stream_chat(enriched):
                yield chunk
        """
        return messages
    
    def get_system_prompt(self, user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """
        Build system prompt with user preferences (future implementation)
        
        This is a placeholder for incorporating user settings into system prompt.
        Default implementation returns empty string.
        
        Args:
            user_preferences: User settings dict with prompt customization
            
        Returns:
            System prompt string
            
        Example:
            # Future implementation
            system_prompt = llm.get_system_prompt(user_settings)
            async for chunk in llm.stream_chat(messages, system_prompt=system_prompt):
                yield chunk
        """
        return ""