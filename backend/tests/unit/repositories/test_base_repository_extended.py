"""
Path: backend/tests/unit/repositories/test_base_repository_extended.py
Version: 1.4

Changes in v1.4:
- FIXED: BaseRepository.get_all() calls db.find_many() - mock find_many not get_all
- FIXED: get_paginated() calls get_all() + count() - mock both find_many and count

Tests for BaseRepository exception branches and edge cases.
Coverage target: 68% → 95%
"""

import pytest
from unittest.mock import MagicMock

from src.repositories.base import BaseRepository
from src.database.exceptions import DatabaseException, NotFoundError


class TestBaseRepositoryCreateExceptions:
    """Test create() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_create_database_exception_raises(self, repository, mock_db):
        """Test create raises DatabaseException on failure"""
        mock_db.create.side_effect = DatabaseException("Connection failed")
        
        with pytest.raises(DatabaseException) as exc_info:
            repository.create({"name": "Test"})
        
        assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_create_success(self, repository, mock_db):
        """Test successful document creation"""
        mock_db.create.return_value = {"id": "doc-1", "name": "Test"}
        
        result = repository.create({"name": "Test"})
        
        assert result["id"] == "doc-1"
        mock_db.create.assert_called_once_with("test_collection", {"name": "Test"})


class TestBaseRepositoryBulkCreateExceptions:
    """Test bulk_create() exception handling"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_bulk_create_continues_on_single_failure(self, repository, mock_db):
        """Test bulk_create continues when one document fails"""
        mock_db.create.side_effect = [
            {"id": "doc-1", "name": "Doc 1"},
            DatabaseException("Duplicate key"),
            {"id": "doc-3", "name": "Doc 3"}
        ]
        
        documents = [
            {"name": "Doc 1"},
            {"name": "Doc 2"},
            {"name": "Doc 3"}
        ]
        
        results = repository.bulk_create(documents)
        
        assert len(results) == 2
        assert results[0]["id"] == "doc-1"
        assert results[1]["id"] == "doc-3"
    
    @pytest.mark.unit
    def test_bulk_create_all_fail(self, repository, mock_db):
        """Test bulk_create when all documents fail"""
        mock_db.create.side_effect = DatabaseException("DB unavailable")
        
        documents = [{"name": f"Doc {i}"} for i in range(3)]
        
        results = repository.bulk_create(documents)
        
        assert results == []
    
    @pytest.mark.unit
    def test_bulk_create_empty_list(self, repository, mock_db):
        """Test bulk_create with empty list"""
        results = repository.bulk_create([])
        
        assert results == []
        mock_db.create.assert_not_called()


class TestBaseRepositoryGetByIdExceptions:
    """Test get_by_id() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_get_by_id_not_found_returns_none(self, repository, mock_db):
        """Test get_by_id returns None when not found"""
        mock_db.get_by_id.return_value = None
        
        result = repository.get_by_id("nonexistent")
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_by_id_success(self, repository, mock_db):
        """Test get_by_id returns document on success"""
        mock_db.get_by_id.return_value = {"id": "doc-123", "name": "Test"}
        
        result = repository.get_by_id("doc-123")
        
        assert result["id"] == "doc-123"
        assert result["name"] == "Test"


class TestBaseRepositoryGetAllExceptions:
    """Test get_all() exception branches - uses db.find_many()"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_get_all_success(self, repository, mock_db):
        """Test get_all returns documents from find_many"""
        # BaseRepository.get_all() calls self.db.find_many()
        mock_db.find_many.return_value = [{"id": "1"}, {"id": "2"}]
        
        result = repository.get_all()
        
        assert len(result) == 2
        assert result[0]["id"] == "1"
    
    @pytest.mark.unit
    def test_get_all_with_all_parameters(self, repository, mock_db):
        """Test get_all with filters, skip, limit, sort"""
        mock_db.find_many.return_value = [{"id": "1"}, {"id": "2"}]
        
        result = repository.get_all(
            filters={"status": "active"},
            skip=10,
            limit=5,
            sort={"created_at": -1}
        )
        
        assert len(result) == 2
        mock_db.find_many.assert_called_once_with(
            "test_collection",
            filters={"status": "active"},
            skip=10,
            limit=5,
            sort={"created_at": -1}
        )
    
    @pytest.mark.unit
    def test_get_all_exception_returns_empty(self, repository, mock_db):
        """Test get_all returns empty list on DatabaseException"""
        mock_db.find_many.side_effect = DatabaseException("Query failed")
        
        result = repository.get_all()
        
        assert result == []


class TestBaseRepositoryFindOneExceptions:
    """Test find_one() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_find_one_not_found_returns_none(self, repository, mock_db):
        """Test find_one returns None when not found"""
        mock_db.find_one.return_value = None
        
        result = repository.find_one({"email": "nonexistent@example.com"})
        
        assert result is None
    
    @pytest.mark.unit
    def test_find_one_success(self, repository, mock_db):
        """Test find_one returns document on success"""
        mock_db.find_one.return_value = {"id": "1", "email": "test@example.com"}
        
        result = repository.find_one({"email": "test@example.com"})
        
        assert result["email"] == "test@example.com"


class TestBaseRepositoryCountExceptions:
    """Test count() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_count_success(self, repository, mock_db):
        """Test count returns number"""
        mock_db.count.return_value = 42
        
        result = repository.count()
        
        assert result == 42
    
    @pytest.mark.unit
    def test_count_with_filters(self, repository, mock_db):
        """Test count with filters"""
        mock_db.count.return_value = 10
        
        result = repository.count(filters={"status": "active"})
        
        assert result == 10
        mock_db.count.assert_called_once_with("test_collection", {"status": "active"})


class TestBaseRepositoryExistsExceptions:
    """Test exists() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_exists_true(self, repository, mock_db):
        """Test exists returns True when document exists"""
        mock_db.exists.return_value = True
        
        result = repository.exists("doc-123")
        
        assert result is True
    
    @pytest.mark.unit
    def test_exists_false(self, repository, mock_db):
        """Test exists returns False when document doesn't exist"""
        mock_db.exists.return_value = False
        
        result = repository.exists("nonexistent")
        
        assert result is False


class TestBaseRepositoryUpdateExceptions:
    """Test update() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_update_not_found_raises(self, repository, mock_db):
        """Test update raises NotFoundError when document not found"""
        mock_db.update.side_effect = NotFoundError("Document not found")
        
        with pytest.raises(NotFoundError):
            repository.update("nonexistent", {"status": "active"})
    
    @pytest.mark.unit
    def test_update_database_exception_raises(self, repository, mock_db):
        """Test update raises DatabaseException on failure"""
        mock_db.update.side_effect = DatabaseException("Update failed")
        
        with pytest.raises(DatabaseException):
            repository.update("doc-123", {"status": "active"})
    
    @pytest.mark.unit
    def test_update_success(self, repository, mock_db):
        """Test update returns updated document"""
        mock_db.update.return_value = {"id": "doc-123", "status": "active"}
        
        result = repository.update("doc-123", {"status": "active"})
        
        assert result["status"] == "active"


class TestBaseRepositoryDeleteExceptions:
    """Test delete() exception branches"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_delete_returns_false_when_not_found(self, repository, mock_db):
        """Test delete returns False when document not found"""
        mock_db.delete.return_value = False
        
        result = repository.delete("nonexistent")
        
        assert result is False
    
    @pytest.mark.unit
    def test_delete_success(self, repository, mock_db):
        """Test delete returns True on success"""
        mock_db.delete.return_value = True
        
        result = repository.delete("doc-123")
        
        assert result is True


class TestBaseRepositoryPaginatedExceptions:
    """Test get_paginated() - calls get_all() which uses find_many(), plus count()"""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_db):
        return BaseRepository(mock_db, collection="test_collection")
    
    @pytest.mark.unit
    def test_get_paginated_first_page(self, repository, mock_db):
        """Test get_paginated first page calculation"""
        # get_paginated calls get_all (which uses find_many) and count
        mock_db.find_many.return_value = [{"id": f"doc-{i}"} for i in range(10)]
        mock_db.count.return_value = 100
        
        items, total = repository.get_paginated(page=1, per_page=10)
        
        assert len(items) == 10
        assert total == 100
        
        # Verify skip=0 for page 1
        call_args = mock_db.find_many.call_args
        assert call_args[1]["skip"] == 0
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.unit
    def test_get_paginated_middle_page(self, repository, mock_db):
        """Test get_paginated middle page skip calculation"""
        mock_db.find_many.return_value = [{"id": f"doc-{i}"} for i in range(10)]
        mock_db.count.return_value = 100
        
        items, total = repository.get_paginated(page=5, per_page=10)
        
        # skip = (page - 1) * per_page = (5-1) * 10 = 40
        call_args = mock_db.find_many.call_args
        assert call_args[1]["skip"] == 40
    
    @pytest.mark.unit
    def test_get_paginated_with_filters_and_sort(self, repository, mock_db):
        """Test get_paginated passes filters and sort"""
        mock_db.find_many.return_value = [{"id": "1", "status": "active"}]
        mock_db.count.return_value = 50
        
        items, total = repository.get_paginated(
            page=2,
            per_page=20,
            filters={"status": "active"},
            sort={"created_at": -1}
        )
        
        find_many_args = mock_db.find_many.call_args
        assert find_many_args[1]["filters"] == {"status": "active"}
        assert find_many_args[1]["sort"] == {"created_at": -1}
        
        # count is called with same filters
        mock_db.count.assert_called_with("test_collection", {"status": "active"})
    
    @pytest.mark.unit
    def test_get_paginated_empty_results(self, repository, mock_db):
        """Test get_paginated with no results"""
        mock_db.find_many.return_value = []
        mock_db.count.return_value = 0
        
        items, total = repository.get_paginated(page=1, per_page=10)
        
        assert items == []
        assert total == 0


class TestBaseRepositoryInitialization:
    """Test BaseRepository initialization"""
    
    @pytest.mark.unit
    def test_init_with_provided_db(self):
        """Test initialization with provided database"""
        mock_db = MagicMock()
        
        repo = BaseRepository(mock_db, collection="users")
        
        assert repo.db == mock_db
        assert repo.collection == "users"