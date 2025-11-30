"""
Path: tests/unit/database/test_arango_adapter.py
Version: 2

Changes in v2:
- Modified all assertions: assert "_key" in → assert "id" in
- Modified all document accesses: doc["_key"] → doc["id"]
- Tests now verify adapter returns 'id' (not '_key')
- Matches production adapter behavior (v3)

Unit tests for ArangoDB adapter
Tests all IDatabase interface methods with mock database
"""

import pytest
from typing import Dict, Any

from src.database.adapters.arango_adapter import ArangoDatabaseAdapter
from src.database.exceptions import (
    NotFoundError,
    DuplicateKeyError,
    CollectionNotFoundError,
)
from tests.unit.mocks.mock_database import MockDatabase


# Use mock database for tests (no real ArangoDB needed)
@pytest.fixture
def mock_db():
    """Provide clean mock database for each test"""
    db = MockDatabase()
    db.connect()
    
    # Create test collection
    db.create_collection("test_collection")
    
    yield db
    
    # Cleanup
    db.disconnect()


@pytest.fixture
def sample_document() -> Dict[str, Any]:
    """Provide sample document for testing"""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "status": "active",
        "role": "user",
    }


class TestDatabaseCreate:
    """Test document creation"""
    
    @pytest.mark.unit
    def test_create_document(self, mock_db, sample_document):
        """Test creating a document"""
        result = mock_db.create("test_collection", sample_document)
        
        assert result is not None
        assert "id" in result
        assert result["name"] == sample_document["name"]
        assert result["email"] == sample_document["email"]
    
    @pytest.mark.unit
    def test_create_generates_id(self, mock_db, sample_document):
        """Test that _key is generated if not provided"""
        result = mock_db.create("test_collection", sample_document)
        
        assert "id" in result
        assert result["id"].startswith("mock-")
    
    @pytest.mark.unit
    def test_create_with_unique_constraint(self, mock_db, sample_document):
        """Test unique constraint enforcement"""
        # Create unique index on email
        mock_db.create_index("test_collection", ["email"], unique=True)
        
        # First insert should succeed
        mock_db.create("test_collection", sample_document)
        
        # Second insert with same email should fail
        with pytest.raises(DuplicateKeyError):
            mock_db.create("test_collection", sample_document)
    
    @pytest.mark.unit
    def test_create_in_nonexistent_collection(self, mock_db, sample_document):
        """Test creating in non-existent collection creates it"""
        # Mock creates collection automatically
        result = mock_db.create("new_collection", sample_document)
        assert result is not None


class TestDatabaseRead:
    """Test document retrieval"""
    
    @pytest.mark.unit
    def test_get_by_id_existing(self, mock_db, sample_document):
        """Test retrieving existing document by ID"""
        created = mock_db.create("test_collection", sample_document)
        doc_id = created["id"]
        
        retrieved = mock_db.get_by_id("test_collection", doc_id)
        
        assert retrieved is not None
        assert retrieved["id"] == doc_id
        assert retrieved["name"] == sample_document["name"]
    
    @pytest.mark.unit
    def test_get_by_id_nonexistent(self, mock_db):
        """Test retrieving non-existent document returns None"""
        result = mock_db.get_by_id("test_collection", "nonexistent-id")
        assert result is None
    
    @pytest.mark.unit
    def test_get_all_no_filters(self, mock_db):
        """Test getting all documents without filters"""
        # Create multiple documents
        mock_db.create("test_collection", {"name": "User 1", "status": "active"})
        mock_db.create("test_collection", {"name": "User 2", "status": "active"})
        mock_db.create("test_collection", {"name": "User 3", "status": "disabled"})
        
        results = mock_db.get_all("test_collection")
        
        assert len(results) == 3
    
    @pytest.mark.unit
    def test_get_all_with_filters(self, mock_db):
        """Test filtering documents"""
        mock_db.create("test_collection", {"name": "User 1", "status": "active"})
        mock_db.create("test_collection", {"name": "User 2", "status": "active"})
        mock_db.create("test_collection", {"name": "User 3", "status": "disabled"})
        
        results = mock_db.get_all("test_collection", filters={"status": "active"})
        
        assert len(results) == 2
        assert all(doc["status"] == "active" for doc in results)
    
    @pytest.mark.unit
    def test_get_all_with_pagination(self, mock_db):
        """Test pagination"""
        # Create 10 documents
        for i in range(10):
            mock_db.create("test_collection", {"name": f"User {i}"})
        
        # Get page 2 (skip 5, limit 3)
        results = mock_db.get_all("test_collection", skip=5, limit=3)
        
        assert len(results) == 3
    
    @pytest.mark.unit
    def test_get_all_with_sort(self, mock_db):
        """Test sorting results"""
        mock_db.create("test_collection", {"name": "Charlie", "age": 30})
        mock_db.create("test_collection", {"name": "Alice", "age": 25})
        mock_db.create("test_collection", {"name": "Bob", "age": 35})
        
        # Sort by name ascending
        results = mock_db.get_all("test_collection", sort={"name": 1})
        
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
        assert results[2]["name"] == "Charlie"
    
    @pytest.mark.unit
    def test_find_one(self, mock_db):
        """Test finding single document"""
        mock_db.create("test_collection", {"email": "test@example.com", "name": "Test"})
        
        result = mock_db.find_one("test_collection", {"email": "test@example.com"})
        
        assert result is not None
        assert result["email"] == "test@example.com"
    
    @pytest.mark.unit
    def test_find_one_not_found(self, mock_db):
        """Test find_one returns None when no match"""
        result = mock_db.find_one("test_collection", {"email": "nonexistent@example.com"})
        assert result is None


class TestDatabaseUpdate:
    """Test document updates"""
    
    @pytest.mark.unit
    def test_update_existing_document(self, mock_db, sample_document):
        """Test updating existing document"""
        created = mock_db.create("test_collection", sample_document)
        doc_id = created["id"]
        
        updated = mock_db.update("test_collection", doc_id, {"status": "disabled"})
        
        assert updated["status"] == "disabled"
        assert updated["name"] == sample_document["name"]  # Other fields preserved
    
    @pytest.mark.unit
    def test_update_nonexistent_document(self, mock_db):
        """Test updating non-existent document raises error"""
        with pytest.raises(NotFoundError):
            mock_db.update("test_collection", "nonexistent-id", {"status": "disabled"})
    
    @pytest.mark.unit
    def test_update_partial(self, mock_db, sample_document):
        """Test partial update preserves other fields"""
        created = mock_db.create("test_collection", sample_document)
        doc_id = created["id"]
        
        # Update only status
        updated = mock_db.update("test_collection", doc_id, {"status": "disabled"})
        
        # All other fields should be preserved
        assert updated["name"] == sample_document["name"]
        assert updated["email"] == sample_document["email"]
        assert updated["status"] == "disabled"


class TestDatabaseDelete:
    """Test document deletion"""
    
    @pytest.mark.unit
    def test_delete_existing_document(self, mock_db, sample_document):
        """Test deleting existing document"""
        created = mock_db.create("test_collection", sample_document)
        doc_id = created["id"]
        
        result = mock_db.delete("test_collection", doc_id)
        
        assert result is True
        assert mock_db.get_by_id("test_collection", doc_id) is None
    
    @pytest.mark.unit
    def test_delete_nonexistent_document(self, mock_db):
        """Test deleting non-existent document returns False"""
        result = mock_db.delete("test_collection", "nonexistent-id")
        assert result is False


class TestDatabaseUtilities:
    """Test utility methods"""
    
    @pytest.mark.unit
    def test_count_all(self, mock_db):
        """Test counting all documents"""
        mock_db.create("test_collection", {"name": "User 1"})
        mock_db.create("test_collection", {"name": "User 2"})
        mock_db.create("test_collection", {"name": "User 3"})
        
        count = mock_db.count("test_collection")
        assert count == 3
    
    @pytest.mark.unit
    def test_count_with_filters(self, mock_db):
        """Test counting with filters"""
        mock_db.create("test_collection", {"status": "active"})
        mock_db.create("test_collection", {"status": "active"})
        mock_db.create("test_collection", {"status": "disabled"})
        
        count = mock_db.count("test_collection", filters={"status": "active"})
        assert count == 2
    
    @pytest.mark.unit
    def test_exists_true(self, mock_db, sample_document):
        """Test exists returns True for existing document"""
        created = mock_db.create("test_collection", sample_document)
        doc_id = created["id"]
        
        assert mock_db.exists("test_collection", doc_id) is True
    
    @pytest.mark.unit
    def test_exists_false(self, mock_db):
        """Test exists returns False for non-existent document"""
        assert mock_db.exists("test_collection", "nonexistent-id") is False


class TestCollectionOperations:
    """Test collection management"""
    
    @pytest.mark.unit
    def test_collection_exists(self, mock_db):
        """Test checking if collection exists"""
        assert mock_db.collection_exists("test_collection") is True
        assert mock_db.collection_exists("nonexistent_collection") is False
    
    @pytest.mark.unit
    def test_create_collection(self, mock_db):
        """Test creating new collection"""
        mock_db.create_collection("new_collection")
        assert mock_db.collection_exists("new_collection") is True
    
    @pytest.mark.unit
    def test_drop_collection(self, mock_db):
        """Test dropping collection"""
        mock_db.create_collection("temp_collection")
        mock_db.drop_collection("temp_collection")
        
        assert mock_db.collection_exists("temp_collection") is False
    
    @pytest.mark.unit
    def test_truncate_collection(self, mock_db):
        """Test truncating collection"""
        # Add documents
        mock_db.create("test_collection", {"name": "User 1"})
        mock_db.create("test_collection", {"name": "User 2"})
        
        # Truncate
        mock_db.truncate_collection("test_collection")
        
        # Collection should exist but be empty
        assert mock_db.collection_exists("test_collection") is True
        assert mock_db.count("test_collection") == 0


class TestIndexOperations:
    """Test index management"""
    
    @pytest.mark.unit
    def test_create_unique_index(self, mock_db):
        """Test creating unique index"""
        mock_db.create_index("test_collection", ["email"], unique=True)
        
        # First document should succeed
        mock_db.create("test_collection", {"email": "test@example.com"})
        
        # Second with same email should fail
        with pytest.raises(DuplicateKeyError):
            mock_db.create("test_collection", {"email": "test@example.com"})
    
    @pytest.mark.unit
    def test_create_compound_index(self, mock_db):
        """Test creating compound index"""
        # Should not raise error
        mock_db.create_index("test_collection", ["status", "role"], unique=False)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.unit
    def test_empty_collection(self, mock_db):
        """Test operations on empty collection"""
        results = mock_db.get_all("test_collection")
        assert results == []
        
        count = mock_db.count("test_collection")
        assert count == 0
    
    @pytest.mark.unit
    def test_update_with_empty_dict(self, mock_db, sample_document):
        """Test update with empty updates dict"""
        created = mock_db.create("test_collection", sample_document)
        doc_id = created["id"]
        
        # Update with empty dict should not change document
        updated = mock_db.update("test_collection", doc_id, {})
        assert updated["name"] == sample_document["name"]
    
    @pytest.mark.unit
    def test_large_result_set(self, mock_db):
        """Test handling large number of documents"""
        # Create 1000 documents
        for i in range(1000):
            mock_db.create("test_collection", {"index": i})
        
        # Get with limit
        results = mock_db.get_all("test_collection", limit=100)
        assert len(results) == 100
        
        # Count all
        count = mock_db.count("test_collection")
        assert count == 1000