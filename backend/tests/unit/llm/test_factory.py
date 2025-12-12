"""
Path: backend/tests/unit/llm/test_factory.py
Version: 4

Changes in v4:
- Ollama adapter now implemented - updated tests accordingly
- Removed ollama from unimplemented providers list
- Updated provider status expectations

Changes in v3:
- Simplified mocking strategy - removed complex adapter mocking
- Tests now focus on actual factory behavior
- Fixed test expectations for implemented providers (databricks, openrouter)

Unit tests for LLM factory
Tests factory instantiation, singleton pattern, and provider selection
"""

import pytest
from unittest.mock import patch
from src.llm.factory import (
    get_llm,
    reset_llm,
    get_llm_type,
    is_connected,
    get_available_providers,
    get_provider_status,
)
from src.llm.exceptions import LLMException, InvalidRequestError
from src.core.config import settings


class TestLLMFactory:
    """Test LLM factory functions"""
    
    def teardown_method(self):
        """Reset LLM singleton after each test"""
        reset_llm()
    
    def test_is_connected_initially_false(self):
        """Test that is_connected returns False initially"""
        reset_llm()
        assert is_connected() is False
    
    def test_get_llm_type_returns_configured_provider(self):
        """Test that get_llm_type returns the configured provider"""
        assert get_llm_type() == settings.LLM_PROVIDER
    
    def test_get_available_providers_returns_list(self):
        """Test that get_available_providers returns expected list"""
        providers = get_available_providers()
        
        assert isinstance(providers, list)
        assert "openai" in providers
        assert "claude" in providers
        assert "gemini" in providers
        assert "databricks" in providers
        assert "openrouter" in providers
        assert "ollama" in providers
        assert len(providers) == 6
    
    def test_get_provider_status_returns_dict(self):
        """Test that get_provider_status returns dict with provider status"""
        status = get_provider_status()
        
        assert isinstance(status, dict)
        assert "openai" in status
        assert "claude" in status
        assert "gemini" in status
        assert "databricks" in status
        assert "openrouter" in status
        assert "ollama" in status
        
        # All values should be booleans
        assert all(isinstance(v, bool) for v in status.values())
        
        # OpenAI, Databricks, OpenRouter should be implemented
        assert status["openai"] is True
        assert status["databricks"] is True
        assert status["openrouter"] is True
        
        # Ollama is now implemented
        assert status["ollama"] is True
        
        # Claude, Gemini should not be implemented
        assert status["claude"] is False
        assert status["gemini"] is False
    
    def test_get_llm_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError"""
        with patch("src.llm.factory.settings.LLM_PROVIDER", "unsupported"):
            with pytest.raises(ValueError) as exc_info:
                get_llm()
            
            assert "Unsupported LLM_PROVIDER" in str(exc_info.value)
            assert "unsupported" in str(exc_info.value)
    
    def test_get_llm_validation_failure_for_openai(self):
        """Test that validation failure prevents connection for OpenAI"""
        with patch("src.llm.factory.settings.LLM_PROVIDER", "openai"):
            with patch("src.llm.factory.settings.OPENAI_API_KEY", None):
                reset_llm()
                
                with pytest.raises(InvalidRequestError) as exc_info:
                    get_llm()
                
                assert "OPENAI_API_KEY is required" in str(exc_info.value)
    
    def test_get_llm_validation_failure_for_databricks(self):
        """Test that validation failure prevents connection for Databricks"""
        with patch("src.llm.factory.settings.LLM_PROVIDER", "databricks"):
            with patch("src.llm.factory.settings.DATABRICKS_API_KEY", None):
                with patch("src.llm.factory.settings.DATABRICKS_BASE_URL", None):
                    reset_llm()
                    
                    with pytest.raises(InvalidRequestError) as exc_info:
                        get_llm()
                    
                    error_msg = str(exc_info.value).lower()
                    assert "databricks" in error_msg
                    assert "required" in error_msg
    
    def test_reset_llm_when_not_connected(self):
        """Test that reset_llm works when no instance exists"""
        reset_llm()
        assert not is_connected()
        
        # Should not raise exception
        reset_llm()
        assert not is_connected()


class TestProviderSelection:
    """Test provider selection logic"""
    
    def teardown_method(self):
        """Reset LLM singleton after each test"""
        reset_llm()
    
    @pytest.mark.parametrize("provider", [
        "claude",
        "gemini",
    ])
    def test_unimplemented_providers_raise_not_implemented(self, provider):
        """Test that unimplemented providers raise LLMException"""
        with patch("src.llm.factory.settings.LLM_PROVIDER", provider):
            with pytest.raises(LLMException) as exc_info:
                get_llm()
            
            error_message = str(exc_info.value)
            assert "not implemented yet" in error_message.lower()
            assert "Set LLM_PROVIDER=openai" in error_message
    
    @pytest.mark.parametrize("provider", [
        "databricks",
    ])
    def test_implemented_providers_fail_with_config_error(self, provider):
        """Test that implemented providers fail gracefully with config errors"""
        with patch("src.llm.factory.settings.LLM_PROVIDER", provider):
            # These are implemented but will fail validation due to missing config
            reset_llm()
            
            with pytest.raises(InvalidRequestError) as exc_info:
                get_llm()
            
            error_message = str(exc_info.value).lower()
            # Should get validation error, not "not implemented"
            assert "configuration validation failed" in error_message or "required" in error_message
            assert provider in error_message