"""
Path: backend/tests/unit/storage/test_factory.py
Version: 1.0

Unit tests for storage factory pattern.

Tests cover:
- get_storage() singleton behavior
- Different STORAGE_TYPE configurations (minio, azure, gcs)
- Connection error handling
- reset_storage() cleanup
- get_storage_type() and is_connected() helpers
"""

import pytest
from unittest.mock import patch, MagicMock

from src.storage.factory import (
    get_storage,
    reset_storage,
    get_storage_type,
    is_connected
)
from src.storage.exceptions import StorageException


class TestGetStorage:
    """Test get_storage factory function"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        reset_storage()
        yield
        reset_storage()
    
    @pytest.mark.unit
    def test_get_storage_minio(self):
        """Test getting MinIO adapter"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                storage = get_storage()
                
                MockAdapter.assert_called_once()
                mock_instance.connect.assert_called_once()
                assert storage == mock_instance
    
    @pytest.mark.unit
    def test_get_storage_singleton(self):
        """Test singleton pattern - same instance returned"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                storage1 = get_storage()
                storage2 = get_storage()
                
                # Should only create adapter once
                assert MockAdapter.call_count == 1
                assert storage1 is storage2
    
    @pytest.mark.unit
    def test_get_storage_azure_not_implemented(self):
        """Test Azure adapter raises when not implemented"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "azure"
            
            with pytest.raises(StorageException) as exc_info:
                get_storage()
            
            assert "Azure Blob adapter not implemented" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_storage_gcs_not_implemented(self):
        """Test GCS adapter raises when not implemented"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "gcs"
            
            with pytest.raises(StorageException) as exc_info:
                get_storage()
            
            assert "Google Cloud Storage adapter not implemented" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_storage_unsupported_type(self):
        """Test unsupported STORAGE_TYPE raises ValueError"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "unsupported_storage"
            
            with pytest.raises(ValueError) as exc_info:
                get_storage()
            
            assert "Unsupported STORAGE_TYPE" in str(exc_info.value)
            assert "unsupported_storage" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_storage_connection_failure(self):
        """Test connection failure is handled properly"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                mock_instance.connect.side_effect = Exception("Connection refused")
                MockAdapter.return_value = mock_instance
                
                with pytest.raises(StorageException) as exc_info:
                    get_storage()
                
                assert "connection failed" in str(exc_info.value).lower()


class TestResetStorage:
    """Test reset_storage function"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        reset_storage()
        yield
        reset_storage()
    
    @pytest.mark.unit
    def test_reset_storage_clears_singleton(self):
        """Test reset clears singleton instance"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                # Get storage to create singleton
                get_storage()
                assert is_connected() is True
                
                # Reset
                reset_storage()
                assert is_connected() is False
                
                # Disconnect should have been called
                mock_instance.disconnect.assert_called_once()
    
    @pytest.mark.unit
    def test_reset_storage_handles_disconnect_error(self):
        """Test reset handles disconnect errors gracefully"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                mock_instance.disconnect.side_effect = Exception("Disconnect failed")
                MockAdapter.return_value = mock_instance
                
                # Get storage
                get_storage()
                
                # Reset should not raise even if disconnect fails
                reset_storage()  # Should not raise
                assert is_connected() is False
    
    @pytest.mark.unit
    def test_reset_storage_when_not_connected(self):
        """Test reset when no connection exists"""
        # Should not raise when nothing to reset
        reset_storage()
        assert is_connected() is False


class TestGetStorageType:
    """Test get_storage_type helper function"""
    
    @pytest.mark.unit
    def test_get_storage_type_minio(self):
        """Test getting minio type"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            result = get_storage_type()
            
            assert result == "minio"
    
    @pytest.mark.unit
    def test_get_storage_type_azure(self):
        """Test getting azure type"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "azure"
            
            result = get_storage_type()
            
            assert result == "azure"
    
    @pytest.mark.unit
    def test_get_storage_type_gcs(self):
        """Test getting gcs type"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "gcs"
            
            result = get_storage_type()
            
            assert result == "gcs"


class TestIsConnected:
    """Test is_connected helper function"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        reset_storage()
        yield
        reset_storage()
    
    @pytest.mark.unit
    def test_is_connected_false_when_not_initialized(self):
        """Test is_connected returns False before initialization"""
        assert is_connected() is False
    
    @pytest.mark.unit
    def test_is_connected_true_after_get_storage(self):
        """Test is_connected returns True after get_storage"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                get_storage()
                
                assert is_connected() is True
    
    @pytest.mark.unit
    def test_is_connected_false_after_reset(self):
        """Test is_connected returns False after reset"""
        with patch('src.storage.factory.settings') as mock_settings:
            mock_settings.STORAGE_TYPE = "minio"
            
            with patch('src.storage.adapters.minio_adapter.MinIOStorageAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                get_storage()
                assert is_connected() is True
                
                reset_storage()
                assert is_connected() is False