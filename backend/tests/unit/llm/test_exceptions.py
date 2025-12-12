"""
Path: backend/tests/unit/llm/test_exceptions.py
Version: 1

Unit tests for LLM exceptions
Tests exception hierarchy and behavior
"""

import pytest
from src.llm.exceptions import (
    LLMException,
    ConnectionError,
    StreamingError,
    ModelNotFoundError,
    RateLimitError,
    InvalidRequestError,
    TimeoutError,
    ContextLengthError,
    AuthenticationError,
)


class TestLLMExceptions:
    """Test LLM exception hierarchy"""
    
    def test_llm_exception_base(self):
        """Test base LLMException can be raised"""
        with pytest.raises(LLMException) as exc_info:
            raise LLMException("Test error")
        
        assert str(exc_info.value) == "Test error"
    
    def test_connection_error_inherits_from_llm_exception(self):
        """Test ConnectionError inherits from LLMException"""
        assert issubclass(ConnectionError, LLMException)
        
        with pytest.raises(LLMException):
            raise ConnectionError("Connection failed")
    
    def test_streaming_error_inherits_from_llm_exception(self):
        """Test StreamingError inherits from LLMException"""
        assert issubclass(StreamingError, LLMException)
        
        with pytest.raises(LLMException):
            raise StreamingError("Stream interrupted")
    
    def test_model_not_found_error_inherits_from_llm_exception(self):
        """Test ModelNotFoundError inherits from LLMException"""
        assert issubclass(ModelNotFoundError, LLMException)
        
        with pytest.raises(LLMException):
            raise ModelNotFoundError("Model not available")
    
    def test_rate_limit_error_inherits_from_llm_exception(self):
        """Test RateLimitError inherits from LLMException"""
        assert issubclass(RateLimitError, LLMException)
        
        with pytest.raises(LLMException):
            raise RateLimitError("Rate limit exceeded")
    
    def test_invalid_request_error_inherits_from_llm_exception(self):
        """Test InvalidRequestError inherits from LLMException"""
        assert issubclass(InvalidRequestError, LLMException)
        
        with pytest.raises(LLMException):
            raise InvalidRequestError("Invalid parameters")
    
    def test_timeout_error_inherits_from_llm_exception(self):
        """Test TimeoutError inherits from LLMException"""
        assert issubclass(TimeoutError, LLMException)
        
        with pytest.raises(LLMException):
            raise TimeoutError("Request timed out")
    
    def test_context_length_error_inherits_from_llm_exception(self):
        """Test ContextLengthError inherits from LLMException"""
        assert issubclass(ContextLengthError, LLMException)
        
        with pytest.raises(LLMException):
            raise ContextLengthError("Context too long")
    
    def test_authentication_error_inherits_from_llm_exception(self):
        """Test AuthenticationError inherits from LLMException"""
        assert issubclass(AuthenticationError, LLMException)
        
        with pytest.raises(LLMException):
            raise AuthenticationError("Auth failed")
    
    def test_catch_all_llm_exceptions(self):
        """Test catching all LLM exceptions with base class"""
        exceptions_to_test = [
            ConnectionError("test"),
            StreamingError("test"),
            ModelNotFoundError("test"),
            RateLimitError("test"),
            InvalidRequestError("test"),
            TimeoutError("test"),
            ContextLengthError("test"),
            AuthenticationError("test"),
        ]
        
        for exception in exceptions_to_test:
            with pytest.raises(LLMException):
                raise exception
    
    def test_exception_messages_are_preserved(self):
        """Test exception messages are properly stored"""
        message = "Detailed error message"
        
        exceptions = [
            LLMException(message),
            ConnectionError(message),
            StreamingError(message),
            ModelNotFoundError(message),
            RateLimitError(message),
            InvalidRequestError(message),
            TimeoutError(message),
            ContextLengthError(message),
            AuthenticationError(message),
        ]
        
        for exc in exceptions:
            assert str(exc) == message