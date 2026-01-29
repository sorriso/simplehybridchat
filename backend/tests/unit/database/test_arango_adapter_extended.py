"""
Path: backend/tests/unit/database/test_arango_adapter_extended.py
Version: 1.2

Changes in v1.2:
- FIXED: create mock must return {'_key': ..., 'new': {...}} structure
- FIXED: get_by_id returns None on not found (doesn't raise)
- FIXED: count mock must return iterator (not list) for next()

Extended tests for ArangoDatabaseAdapter exception branches.
Coverage target: 70% → 90%
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from src.database.adapters.arango_adapter import ArangoDatabaseAdapter
from src.database.exceptions import (
    DatabaseException,
    NotFoundError,
    DuplicateKeyError,
    CollectionNotFoundError,
    ConnectionError,
)


class TestArangoAdapterConnection:
    """Test connect/disconnect edge cases"""
    
    @pytest.fixture
    def mock_arango_client(self):
        """Mock ArangoDB client"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            yield client, mock_db
    
    @pytest.mark.unit
    def test_connect_success(self, mock_arango_client):
        """Test successful connection"""
        client, mock_db = mock_arango_client
        
        adapter = ArangoDatabaseAdapter()
        adapter.connect()
        
        assert adapter._connected is True
        assert adapter._db is not None
    
    @pytest.mark.unit
    def test_connect_already_connected(self, mock_arango_client):
        """Test connect when already connected"""
        client, mock_db = mock_arango_client
        
        adapter = ArangoDatabaseAdapter()
        adapter.connect()
        adapter.connect()  # Should not raise
        
        assert adapter._connected is True
    
    @pytest.mark.unit
    def test_disconnect_clears_connection(self, mock_arango_client):
        """Test disconnect clears connection"""
        client, mock_db = mock_arango_client
        
        adapter = ArangoDatabaseAdapter()
        adapter.connect()
        adapter.disconnect()
        
        assert adapter._connected is False


class TestArangoAdapterCollection:
    """Test collection operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_collection_exists_true(self, adapter):
        """Test collection_exists returns True"""
        adapter._db.has_collection.return_value = True
        
        result = adapter.collection_exists('test_collection')
        
        assert result is True
    
    @pytest.mark.unit
    def test_collection_exists_false(self, adapter):
        """Test collection_exists returns False"""
        adapter._db.has_collection.return_value = False
        
        result = adapter.collection_exists('test_collection')
        
        assert result is False


class TestArangoAdapterCreate:
    """Test create operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_create_success(self, adapter):
        """Test successful document creation"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        
        # insert returns {'_key': ..., 'new': {...}} when return_new=True
        mock_collection.insert.return_value = {
            '_key': 'doc-123',
            'new': {
                '_key': 'doc-123',
                '_id': 'test/doc-123',
                '_rev': 'abc123',
                'name': 'Test'
            }
        }
        
        result = adapter.create('test_collection', {'name': 'Test'})
        
        # _map_to_service converts _key to id and removes _id, _rev
        assert result['id'] == 'doc-123'
        assert result['name'] == 'Test'
        assert '_key' not in result
        assert '_id' not in result
        assert '_rev' not in result
    
    @pytest.mark.unit
    def test_create_duplicate_key_error(self, adapter):
        """Test create with duplicate key"""
        from arango.exceptions import DocumentInsertError
        
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        
        error = DocumentInsertError(
            resp=MagicMock(error_code=1210, error_message='unique constraint violated'),
            request=MagicMock()
        )
        mock_collection.insert.side_effect = error
        
        with pytest.raises(DuplicateKeyError):
            adapter.create('test_collection', {'_key': 'existing'})


class TestArangoAdapterGetById:
    """Test get_by_id operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_get_by_id_success(self, adapter):
        """Test successful document retrieval"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.get.return_value = {
            '_key': 'doc-123',
            '_id': 'test/doc-123',
            '_rev': 'abc',
            'name': 'Test'
        }
        
        result = adapter.get_by_id('test_collection', 'doc-123')
        
        assert result['id'] == 'doc-123'
        assert result['name'] == 'Test'
    
    @pytest.mark.unit
    def test_get_by_id_not_found(self, adapter):
        """Test get_by_id returns None when document not found"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.get.return_value = None
        
        # get_by_id returns None (doesn't raise NotFoundError)
        result = adapter.get_by_id('test_collection', 'nonexistent')
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_by_id_error_returns_none(self, adapter):
        """Test get_by_id returns None on error"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.get.side_effect = Exception("Get failed")
        
        # Returns None on error (logged as warning)
        result = adapter.get_by_id('test_collection', 'doc-123')
        
        assert result is None


class TestArangoAdapterGetAll:
    """Test get_all operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_get_all_success(self, adapter):
        """Test get_all returns documents"""
        adapter._db.aql.execute.return_value = iter([
            {'_key': 'doc-1', 'name': 'Doc 1'},
            {'_key': 'doc-2', 'name': 'Doc 2'}
        ])
        
        result = adapter.get_all('test_collection')
        
        assert len(result) == 2
        assert result[0]['id'] == 'doc-1'
    
    @pytest.mark.unit
    def test_get_all_with_filters(self, adapter):
        """Test get_all with filters"""
        adapter._db.aql.execute.return_value = iter([
            {'_key': 'doc-1', 'status': 'active'}
        ])
        
        result = adapter.get_all('test_collection', filters={'status': 'active'})
        
        assert len(result) == 1


class TestArangoAdapterUpdate:
    """Test update operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_update_success(self, adapter):
        """Test successful document update"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.return_value = True
        
        # update returns {'_key': ..., 'new': {...}} when return_new=True
        mock_collection.update.return_value = {
            '_key': 'doc-123',
            'new': {
                '_key': 'doc-123',
                '_id': 'test/doc-123',
                '_rev': 'def456',
                'name': 'Updated'
            }
        }
        
        result = adapter.update('test_collection', 'doc-123', {'name': 'Updated'})
        
        assert result['name'] == 'Updated'
        assert result['id'] == 'doc-123'
    
    @pytest.mark.unit
    def test_update_not_found(self, adapter):
        """Test update when document not found"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.return_value = False
        
        with pytest.raises(NotFoundError):
            adapter.update('test_collection', 'nonexistent', {'name': 'Updated'})


class TestArangoAdapterDelete:
    """Test delete operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_delete_success(self, adapter):
        """Test successful document deletion"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.return_value = True
        
        result = adapter.delete('test_collection', 'doc-123')
        
        assert result is True
        mock_collection.delete.assert_called_once()
    
    @pytest.mark.unit
    def test_delete_not_found(self, adapter):
        """Test delete when document not found"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.return_value = False
        
        result = adapter.delete('test_collection', 'nonexistent')
        
        assert result is False


class TestArangoAdapterCount:
    """Test count operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_count_no_filters(self, adapter):
        """Test count without filters - must return iterator for next()"""
        # count uses next(cursor, 0) so mock must be an iterator
        adapter._db.aql.execute.return_value = iter([42])
        
        result = adapter.count('test_collection')
        
        assert result == 42
    
    @pytest.mark.unit
    def test_count_with_filters(self, adapter):
        """Test count with filters"""
        adapter._db.aql.execute.return_value = iter([10])
        
        result = adapter.count('test_collection', filters={'status': 'active'})
        
        assert result == 10
    
    @pytest.mark.unit
    def test_count_error_returns_zero(self, adapter):
        """Test count returns 0 on error"""
        adapter._db.aql.execute.side_effect = Exception("Count failed")
        
        result = adapter.count('test_collection')
        
        assert result == 0


class TestArangoAdapterExists:
    """Test exists operations"""
    
    @pytest.fixture
    def adapter(self):
        """Provide connected adapter with mock database"""
        with patch('src.database.adapters.arango_adapter.ArangoClient') as mock:
            client = MagicMock()
            mock.return_value = client
            
            mock_db = MagicMock()
            client.db.return_value = mock_db
            mock_db.version.return_value = {'version': '3.11.0'}
            
            adapter = ArangoDatabaseAdapter()
            adapter.connect()
            yield adapter
    
    @pytest.mark.unit
    def test_exists_true(self, adapter):
        """Test exists returns True"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.return_value = True
        
        result = adapter.exists('test_collection', 'doc-123')
        
        assert result is True
    
    @pytest.mark.unit
    def test_exists_false(self, adapter):
        """Test exists returns False"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.return_value = False
        
        result = adapter.exists('test_collection', 'nonexistent')
        
        assert result is False
    
    @pytest.mark.unit
    def test_exists_error_returns_false(self, adapter):
        """Test exists returns False on error"""
        mock_collection = MagicMock()
        adapter._db.has_collection.return_value = True
        adapter._db.collection.return_value = mock_collection
        mock_collection.has.side_effect = Exception("Check failed")
        
        result = adapter.exists('test_collection', 'doc-123')
        
        assert result is False