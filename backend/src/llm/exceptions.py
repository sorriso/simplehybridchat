"""
Path: backend/src/llm/exceptions.py
Version: 1

LLM-specific exceptions for error handling
All LLM adapters should raise these exceptions for consistent error handling
"""


class LLMException(Exception):
    """
    Base exception for all LLM operations
    
    All LLM-related errors should inherit from this exception
    to allow catching all LLM errors with a single except clause.
    
    Example:
        try:
            async for chunk in llm.stream_chat(messages):
                print(chunk)
        except LLMException as e:
            logger.error(f"LLM error: {e}")
    """
    pass


class ConnectionError(LLMException):
    """
    LLM provider connection error
    
    Raised when unable to establish or maintain connection to LLM provider.
    
    Example:
        try:
            llm.connect()
        except ConnectionError:
            logger.critical("Cannot connect to LLM provider")
            raise
    """
    pass


class StreamingError(LLMException):
    """
    Error during streaming response
    
    Raised when streaming is interrupted or fails.
    
    Example:
        try:
            async for chunk in llm.stream_chat(messages):
                yield chunk
        except StreamingError as e:
            logger.error(f"Streaming interrupted: {e}")
            yield "[ERROR]"
    """
    pass


class ModelNotFoundError(LLMException):
    """
    Requested model not available
    
    Raised when specified model doesn't exist or isn't accessible.
    
    Example:
        try:
            llm.stream_chat(messages, model="gpt-99")
        except ModelNotFoundError:
            return {"error": "Model not found"}
    """
    pass


class RateLimitError(LLMException):
    """
    Rate limit exceeded
    
    Raised when API rate limits are hit.
    Should be handled with retry logic or user notification.
    
    Example:
        try:
            async for chunk in llm.stream_chat(messages):
                yield chunk
        except RateLimitError:
            logger.warning("Rate limit hit, waiting...")
            time.sleep(60)
    """
    pass


class InvalidRequestError(LLMException):
    """
    Invalid request parameters
    
    Raised when request parameters are malformed or invalid.
    
    Example:
        try:
            llm.stream_chat([])  # Empty messages
        except InvalidRequestError as e:
            return {"error": f"Invalid request: {e}"}
    """
    pass


class TimeoutError(LLMException):
    """
    LLM operation timeout
    
    Raised when operation exceeds configured timeout limit.
    
    Example:
        try:
            async for chunk in llm.stream_chat(messages, timeout=30):
                yield chunk
        except TimeoutError:
            return {"error": "Request timed out"}
    """
    pass


class ContextLengthError(LLMException):
    """
    Context length exceeded
    
    Raised when input messages exceed model's context window.
    
    Example:
        try:
            async for chunk in llm.stream_chat(very_long_messages):
                yield chunk
        except ContextLengthError:
            return {"error": "Message too long for model"}
    """
    pass


class AuthenticationError(LLMException):
    """
    Authentication failed
    
    Raised when API key or credentials are invalid.
    
    Example:
        try:
            llm.connect()
        except AuthenticationError:
            logger.error("Invalid API key")
            raise
    """
    pass