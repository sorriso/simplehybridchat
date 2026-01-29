"""
Path: backend/tests/unit/database/test_factory.py
Version: 1.0

Unit tests for database factory pattern.

Tests cover:
- get_database() singleton behavior
- Different DB_TYPE configurations (arango, mongo, postgres)
- Connection error handling
- reset_database() cleanup
- get_database_type() and is_connected() helpers
"""

import pytest
from unittest.mock import patch, MagicMock

from src.database.factory import (
    get_database,
    reset_database,
    get_database_type,
    is_connected
)
from src.database.exceptions import DatabaseException


class TestGetDatabase:
    """Test get_database factory function"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        reset_database()
        yield
        reset_database()
    
    @pytest.mark.unit
    def test_get_database_arango(self):
        """Test getting ArangoDB adapter"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                db = get_database()
                
                MockAdapter.assert_called_once()
                mock_instance.connect.assert_called_once()
                assert db == mock_instance
    
    @pytest.mark.unit
    def test_get_database_singleton(self):
        """Test singleton pattern - same instance returned"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                db1 = get_database()
                db2 = get_database()
                
                # Should only create adapter once
                assert MockAdapter.call_count == 1
                assert db1 is db2
    
    @pytest.mark.unit
    def test_get_database_mongo_not_implemented(self):
        """Test MongoDB adapter raises when not implemented"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "mongo"
            
            with pytest.raises(DatabaseException) as exc_info:
                get_database()
            
            assert "MongoDB adapter not implemented" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_database_postgres_not_implemented(self):
        """Test PostgreSQL adapter raises when not implemented"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "postgres"
            
            with pytest.raises(DatabaseException) as exc_info:
                get_database()
            
            assert "PostgreSQL adapter not implemented" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_database_unsupported_type(self):
        """Test unsupported DB_TYPE raises ValueError"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "unsupported_db"
            
            with pytest.raises(ValueError) as exc_info:
                get_database()
            
            assert "Unsupported DB_TYPE" in str(exc_info.value)
            assert "unsupported_db" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_get_database_connection_failure(self):
        """Test connection failure is handled properly"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                mock_instance.connect.side_effect = Exception("Connection refused")
                MockAdapter.return_value = mock_instance
                
                with pytest.raises(DatabaseException) as exc_info:
                    get_database()
                
                assert "connection failed" in str(exc_info.value).lower()


class TestResetDatabase:
    """Test reset_database function"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        reset_database()
        yield
        reset_database()
    
    @pytest.mark.unit
    def test_reset_database_clears_singleton(self):
        """Test reset clears singleton instance"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                # Get database to create singleton
                get_database()
                assert is_connected() is True
                
                # Reset
                reset_database()
                assert is_connected() is False
                
                # Disconnect should have been called
                mock_instance.disconnect.assert_called_once()
    
    @pytest.mark.unit
    def test_reset_database_handles_disconnect_error(self):
        """Test reset handles disconnect errors gracefully"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                mock_instance.disconnect.side_effect = Exception("Disconnect failed")
                MockAdapter.return_value = mock_instance
                
                # Get database
                get_database()
                
                # Reset should not raise even if disconnect fails
                reset_database()  # Should not raise
                assert is_connected() is False
    
    @pytest.mark.unit
    def test_reset_database_when_not_connected(self):
        """Test reset when no connection exists"""
        # Should not raise when nothing to reset
        reset_database()
        assert is_connected() is False


class TestGetDatabaseType:
    """Test get_database_type helper function"""
    
    @pytest.mark.unit
    def test_get_database_type_arango(self):
        """Test getting arango type"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            result = get_database_type()
            
            assert result == "arango"
    
    @pytest.mark.unit
    def test_get_database_type_mongo(self):
        """Test getting mongo type"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "mongo"
            
            result = get_database_type()
            
            assert result == "mongo"
    
    @pytest.mark.unit
    def test_get_database_type_postgres(self):
        """Test getting postgres type"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "postgres"
            
            result = get_database_type()
            
            assert result == "postgres"


class TestIsConnected:
    """Test is_connected helper function"""
    
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before and after each test"""
        reset_database()
        yield
        reset_database()
    
    @pytest.mark.unit
    def test_is_connected_false_when_not_initialized(self):
        """Test is_connected returns False before initialization"""
        assert is_connected() is False
    
    @pytest.mark.unit
    def test_is_connected_true_after_get_database(self):
        """Test is_connected returns True after get_database"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                get_database()
                
                assert is_connected() is True
    
    @pytest.mark.unit
    def test_is_connected_false_after_reset(self):
        """Test is_connected returns False after reset"""
        with patch('src.database.factory.settings') as mock_settings:
            mock_settings.DB_TYPE = "arango"
            
            with patch('src.database.adapters.arango_adapter.ArangoDatabaseAdapter') as MockAdapter:
                mock_instance = MagicMock()
                MockAdapter.return_value = mock_instance
                
                get_database()
                assert is_connected() is True
                
                reset_database()
                assert is_connected() is False