"""
Path: backend/tests/unit/llm/test_interface.py
Version: 1

Unit tests for LLM interface contract
Tests that interface defines correct abstract methods
"""

import pytest
from typing import AsyncGenerator, Dict, List, Optional, Any
from src.llm.interface import ILLM


class MockLLMAdapter(ILLM):
    """Mock LLM adapter for testing interface contract"""
    
    def __init__(self):
        self.connected = False
        self.model_name = "mock-model"
        self.provider_name = "mock-provider"
    
    def connect(self) -> None:
        self.connected = True
    
    def disconnect(self) -> None:
        self.connected = False
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        for word in ["Hello", " ", "World"]:
            yield word
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def get_provider_name(self) -> str:
        return self.provider_name
    
    def validate_config(self) -> bool:
        return True


class TestILLMInterface:
    """Test ILLM interface contract"""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that ILLM interface cannot be instantiated directly"""
        with pytest.raises(TypeError):
            ILLM()
    
    def test_mock_adapter_implements_interface(self):
        """Test that mock adapter properly implements ILLM interface"""
        adapter = MockLLMAdapter()
        assert isinstance(adapter, ILLM)
    
    def test_connect_method_exists(self):
        """Test that connect method is defined"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "connect")
        assert callable(adapter.connect)
    
    def test_disconnect_method_exists(self):
        """Test that disconnect method is defined"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "disconnect")
        assert callable(adapter.disconnect)
    
    def test_stream_chat_method_exists(self):
        """Test that stream_chat method is defined"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "stream_chat")
        assert callable(adapter.stream_chat)
    
    def test_get_model_name_method_exists(self):
        """Test that get_model_name method is defined"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "get_model_name")
        assert callable(adapter.get_model_name)
    
    def test_get_provider_name_method_exists(self):
        """Test that get_provider_name method is defined"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "get_provider_name")
        assert callable(adapter.get_provider_name)
    
    def test_validate_config_method_exists(self):
        """Test that validate_config method is defined"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "validate_config")
        assert callable(adapter.validate_config)
    
    def test_connect_disconnect_behavior(self):
        """Test connect and disconnect change adapter state"""
        adapter = MockLLMAdapter()
        assert not adapter.connected
        
        adapter.connect()
        assert adapter.connected
        
        adapter.disconnect()
        assert not adapter.connected
    
    @pytest.mark.asyncio
    async def test_stream_chat_returns_generator(self):
        """Test stream_chat returns async generator"""
        adapter = MockLLMAdapter()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = adapter.stream_chat(messages)
        assert hasattr(result, '__aiter__')
    
    @pytest.mark.asyncio
    async def test_stream_chat_yields_strings(self):
        """Test stream_chat yields string chunks"""
        adapter = MockLLMAdapter()
        messages = [{"role": "user", "content": "Hello"}]
        
        chunks = []
        async for chunk in adapter.stream_chat(messages):
            chunks.append(chunk)
        
        assert chunks == ["Hello", " ", "World"]
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_get_model_name_returns_string(self):
        """Test get_model_name returns string"""
        adapter = MockLLMAdapter()
        model_name = adapter.get_model_name()
        assert isinstance(model_name, str)
        assert model_name == "mock-model"
    
    def test_get_provider_name_returns_string(self):
        """Test get_provider_name returns string"""
        adapter = MockLLMAdapter()
        provider_name = adapter.get_provider_name()
        assert isinstance(provider_name, str)
        assert provider_name == "mock-provider"
    
    def test_validate_config_returns_bool(self):
        """Test validate_config returns boolean"""
        adapter = MockLLMAdapter()
        result = adapter.validate_config()
        assert isinstance(result, bool)
        assert result is True
    
    def test_enrich_messages_with_memory_method_exists(self):
        """Test that enrich_messages_with_memory placeholder exists"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "enrich_messages_with_memory")
        assert callable(adapter.enrich_messages_with_memory)
    
    def test_enrich_messages_with_rag_method_exists(self):
        """Test that enrich_messages_with_rag placeholder exists"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "enrich_messages_with_rag")
        assert callable(adapter.enrich_messages_with_rag)
    
    def test_get_system_prompt_method_exists(self):
        """Test that get_system_prompt placeholder exists"""
        adapter = MockLLMAdapter()
        assert hasattr(adapter, "get_system_prompt")
        assert callable(adapter.get_system_prompt)
    
    def test_enrich_messages_with_memory_default_passthrough(self):
        """Test that default enrich_messages_with_memory returns unchanged messages"""
        adapter = MockLLMAdapter()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = adapter.enrich_messages_with_memory(messages, "user-1", "conv-1")
        assert result == messages
    
    def test_enrich_messages_with_rag_default_passthrough(self):
        """Test that default enrich_messages_with_rag returns unchanged messages"""
        adapter = MockLLMAdapter()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = adapter.enrich_messages_with_rag(messages, "user-1", "conv-1")
        assert result == messages
    
    def test_get_system_prompt_default_empty(self):
        """Test that default get_system_prompt returns empty string"""
        adapter = MockLLMAdapter()
        
        result = adapter.get_system_prompt()
        assert result == ""
        
        result_with_prefs = adapter.get_system_prompt({"key": "value"})
        assert result_with_prefs == ""


class IncompleteAdapter(ILLM):
    """Adapter missing required methods - should fail to instantiate"""
    pass


class TestInterfaceContractEnforcement:
    """Test that interface contract is properly enforced"""
    
    def test_incomplete_adapter_cannot_be_instantiated(self):
        """Test that adapter missing abstract methods cannot be instantiated"""
        with pytest.raises(TypeError) as exc_info:
            IncompleteAdapter()
        
        error_message = str(exc_info.value)
        assert "Can't instantiate abstract class" in error_message