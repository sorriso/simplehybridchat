"""
Path: tebackend/testssts/unit/repositories/test_base_repository.py
Version: 3

Changes in v3:
- Fixed bulk_create assertion: "_key" → "id" (line 70)

Changes in v2:
- Modified all assertions: assert "_key" in → assert "id" in
- Modified all document accesses: doc["_key"] → doc["id"]
- Tests now verify repository returns 'id' from adapter
- Matches MockDatabase v3 behavior

Unit tests for BaseRepository with mock database
"""

import pytest
from src.repositories.base import BaseRepository
from tests.unit.mocks.mock_database import MockDatabase
from src.database.exceptions import NotFoundError


@pytest.fixture
def mock_db():
    """Provide clean mock database"""
    db = MockDatabase()
    db.connect()
    db.create_collection("test_collection")
    yield db
    db.disconnect()


@pytest.fixture
def repository(mock_db):
    """Provide repository instance"""
    return BaseRepository(mock_db, collection="test_collection")


class TestBaseRepositoryCreate:
    """Test create operations"""
    
    @pytest.mark.unit
    def test_create_document(self, repository):
        """Test creating a document"""
        data = {"name": "Test User", "email": "test@example.com"}
        result = repository.create(data)
        
        assert result is not None
        assert "id" in result
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"
    
    @pytest.mark.unit
    def test_create_generates_id(self, repository):
        """Test that _key is generated"""
        result = repository.create({"name": "User"})
        
        assert "id" in result
        assert result["id"].startswith("mock-")
    
    @pytest.mark.unit
    def test_bulk_create(self, repository):
        """Test bulk create"""
        documents = [
            {"name": "User 1"},
            {"name": "User 2"},
            {"name": "User 3"}
        ]
        
        results = repository.bulk_create(documents)
        
        assert len(results) == 3
        assert all("id" in doc for doc in results)


class TestBaseRepositoryRead:
    """Test read operations"""
    
    @pytest.mark.unit
    def test_get_by_id_existing(self, repository):
        """Test getting existing document"""
        created = repository.create({"name": "Test"})
        doc_id = created["id"]
        
        retrieved = repository.get_by_id(doc_id)
        
        assert retrieved is not None
        assert retrieved["id"] == doc_id
        assert retrieved["name"] == "Test"
    
    @pytest.mark.unit
    def test_get_by_id_nonexistent(self, repository):
        """Test getting non-existent document"""
        result = repository.get_by_id("nonexistent-id")
        assert result is None
    
    @pytest.mark.unit
    def test_get_all_no_filters(self, repository):
        """Test getting all documents"""
        repository.create({"name": "User 1"})
        repository.create({"name": "User 2"})
        repository.create({"name": "User 3"})
        
        results = repository.get_all()
        
        assert len(results) == 3
    
    @pytest.mark.unit
    def test_get_all_with_filters(self, repository):
        """Test filtering documents"""
        repository.create({"name": "User 1", "status": "active"})
        repository.create({"name": "User 2", "status": "active"})
        repository.create({"name": "User 3", "status": "inactive"})
        
        results = repository.get_all(filters={"status": "active"})
        
        assert len(results) == 2
        assert all(doc["status"] == "active" for doc in results)
    
    @pytest.mark.unit
    def test_get_all_with_pagination(self, repository):
        """Test pagination"""
        for i in range(10):
            repository.create({"name": f"User {i}"})
        
        # Get page 2 (skip 5, limit 3)
        results = repository.get_all(skip=5, limit=3)
        
        assert len(results) == 3
    
    @pytest.mark.unit
    def test_get_all_with_sort(self, repository):
        """Test sorting"""
        repository.create({"name": "Charlie", "age": 30})
        repository.create({"name": "Alice", "age": 25})
        repository.create({"name": "Bob", "age": 35})
        
        results = repository.get_all(sort={"name": 1})
        
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
        assert results[2]["name"] == "Charlie"
    
    @pytest.mark.unit
    def test_find_one(self, repository):
        """Test finding single document"""
        repository.create({"email": "test@example.com", "name": "Test"})
        
        result = repository.find_one({"email": "test@example.com"})
        
        assert result is not None
        assert result["email"] == "test@example.com"
    
    @pytest.mark.unit
    def test_find_one_not_found(self, repository):
        """Test find_one returns None when not found"""
        result = repository.find_one({"email": "nonexistent@example.com"})
        assert result is None
    
    @pytest.mark.unit
    def test_find_many(self, repository):
        """Test finding multiple documents"""
        repository.create({"status": "active", "name": "User 1"})
        repository.create({"status": "active", "name": "User 2"})
        repository.create({"status": "inactive", "name": "User 3"})
        
        results = repository.find_many({"status": "active"})
        
        assert len(results) == 2
    
    @pytest.mark.unit
    def test_count(self, repository):
        """Test counting documents"""
        repository.create({"status": "active"})
        repository.create({"status": "active"})
        repository.create({"status": "inactive"})
        
        total = repository.count()
        active = repository.count(filters={"status": "active"})
        
        assert total == 3
        assert active == 2
    
    @pytest.mark.unit
    def test_exists(self, repository):
        """Test checking document existence"""
        created = repository.create({"name": "Test"})
        doc_id = created["id"]
        
        assert repository.exists(doc_id) is True
        assert repository.exists("nonexistent") is False


class TestBaseRepositoryUpdate:
    """Test update operations"""
    
    @pytest.mark.unit
    def test_update_document(self, repository):
        """Test updating document"""
        created = repository.create({"name": "Original", "status": "pending"})
        doc_id = created["id"]
        
        updated = repository.update(doc_id, {
            "status": "active",
            "verified": True
        })
        
        assert updated["status"] == "active"
        assert updated["verified"] is True
        assert updated["name"] == "Original"  # Preserved
    
    @pytest.mark.unit
    def test_update_nonexistent(self, repository):
        """Test updating non-existent document"""
        with pytest.raises(NotFoundError):
            repository.update("nonexistent-id", {"status": "active"})
    
    @pytest.mark.unit
    def test_update_partial(self, repository):
        """Test partial update preserves other fields"""
        created = repository.create({
            "name": "User",
            "email": "user@example.com",
            "status": "pending"
        })
        doc_id = created["id"]
        
        updated = repository.update(doc_id, {"status": "active"})
        
        assert updated["name"] == "User"
        assert updated["email"] == "user@example.com"
        assert updated["status"] == "active"


class TestBaseRepositoryDelete:
    """Test delete operations"""
    
    @pytest.mark.unit
    def test_delete_existing(self, repository):
        """Test deleting existing document"""
        created = repository.create({"name": "Test"})
        doc_id = created["id"]
        
        result = repository.delete(doc_id)
        
        assert result is True
        assert repository.get_by_id(doc_id) is None
    
    @pytest.mark.unit
    def test_delete_nonexistent(self, repository):
        """Test deleting non-existent document"""
        result = repository.delete("nonexistent-id")
        assert result is False


class TestBaseRepositoryPagination:
    """Test pagination utilities"""
    
    @pytest.mark.unit
    def test_get_paginated(self, repository):
        """Test paginated results with total count"""
        for i in range(25):
            repository.create({"index": i})
        
        items, total = repository.get_paginated(page=2, per_page=10)
        
        assert len(items) == 10
        assert total == 25
    
    @pytest.mark.unit
    def test_get_paginated_with_filters(self, repository):
        """Test paginated results with filters"""
        for i in range(20):
            status = "active" if i % 2 == 0 else "inactive"
            repository.create({"index": i, "status": status})
        
        items, total = repository.get_paginated(
            page=1,
            per_page=5,
            filters={"status": "active"}
        )
        
        assert len(items) == 5
        assert total == 10  # 10 active items total
    
    @pytest.mark.unit
    def test_get_paginated_last_page(self, repository):
        """Test last page with partial results"""
        for i in range(23):
            repository.create({"index": i})
        
        items, total = repository.get_paginated(page=3, per_page=10)
        
        assert len(items) == 3  # Only 3 items on last page
        assert total == 23