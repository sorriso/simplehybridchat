"""
Path: backend/src/llm/__init__.py
Version: 1

LLM module for chat streaming with multiple providers
Provides abstraction layer for different LLM providers (OpenAI, Claude, Gemini, etc.)
"""

from src.llm.interface import ILLM
from src.llm.factory import get_llm, reset_llm, get_llm_type, is_connected
from src.llm.exceptions import (
    LLMException,
    ConnectionError,
    StreamingError,
    ModelNotFoundError,
    RateLimitError,
    InvalidRequestError,
    TimeoutError,
)

__all__ = [
    # Interface
    "ILLM",
    # Factory functions
    "get_llm",
    "reset_llm",
    "get_llm_type",
    "is_connected",
    # Exceptions
    "LLMException",
    "ConnectionError",
    "StreamingError",
    "ModelNotFoundError",
    "RateLimitError",
    "InvalidRequestError",
    "TimeoutError",
]