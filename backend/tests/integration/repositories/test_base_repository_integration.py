"""
Path: tests/integration/repositories/test_base_repository_integration.py
Version: 3

Changes in v3:
- Fixed item["_key"] → item["id"] (line 268)
- Fixed bulk_create assertion: "_key" → "id" (line 174)

Changes in v2:
- Modified all document accesses: doc["_key"] → doc["id"]
- Modified all assertions: "_key" → "id"
- Tests now verify integration with real adapter

Integration tests for BaseRepository with real ArangoDB
"""

import pytest
from src.repositories.base import BaseRepository
from src.database.exceptions import NotFoundError


@pytest.mark.integration
@pytest.mark.integration_slow
class TestBaseRepositoryIntegrationFunctionScope:
    """Test BaseRepository with fresh ArangoDB container per test"""
    
    def test_create_and_retrieve(self, arango_container_function):
        """Test creating and retrieving document"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create user
        user = repo.create({
            "name": "John Doe",
            "email": "john@example.com",
            "status": "active"
        })
        
        # Retrieve user
        retrieved = repo.get_by_id(user["id"])
        
        assert retrieved is not None
        assert retrieved["name"] == "John Doe"
        assert retrieved["email"] == "john@example.com"
    
    def test_update_document(self, arango_container_function):
        """Test updating document"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create user
        user = repo.create({
            "name": "Jane Doe",
            "email": "jane@example.com",
            "status": "pending"
        })
        user_id = user["id"]
        
        # Update status
        updated = repo.update(user_id, {
            "status": "active",
            "verified": True
        })
        
        assert updated["status"] == "active"
        assert updated["verified"] is True
        assert updated["name"] == "Jane Doe"  # Preserved
    
    def test_delete_document(self, arango_container_function):
        """Test deleting document"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create user
        user = repo.create({"name": "To Delete"})
        user_id = user["id"]
        
        # Delete
        assert repo.exists(user_id) is True
        deleted = repo.delete(user_id)
        
        assert deleted is True
        assert repo.exists(user_id) is False
    
    def test_find_one_with_filters(self, arango_container_function):
        """Test finding document with filters"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create users
        repo.create({
            "name": "User 1",
            "email": "user1@example.com",
            "status": "active"
        })
        repo.create({
            "name": "User 2",
            "email": "user2@example.com",
            "status": "inactive"
        })
        
        # Find by email
        found = repo.find_one({"email": "user1@example.com"})
        
        assert found is not None
        assert found["name"] == "User 1"
        assert found["status"] == "active"
    
    def test_get_all_with_filters(self, arango_container_function):
        """Test filtering documents"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create users with different statuses
        for i in range(5):
            status = "active" if i % 2 == 0 else "inactive"
            repo.create({
                "name": f"User {i}",
                "status": status
            })
        
        # Get active users only
        active_users = repo.get_all(filters={"status": "active"})
        
        assert len(active_users) == 3  # 0, 2, 4 are active
        assert all(u["status"] == "active" for u in active_users)
    
    def test_pagination(self, arango_container_function):
        """Test pagination with get_paginated"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create 25 users
        for i in range(25):
            repo.create({"name": f"User {i}", "index": i})
        
        # Get page 2 (items 11-20)
        items, total = repo.get_paginated(page=2, per_page=10)
        
        assert len(items) == 10
        assert total == 25
        
        # Get last page (partial)
        items, total = repo.get_paginated(page=3, per_page=10)
        
        assert len(items) == 5  # Only 5 items on last page
        assert total == 25
    
    def test_bulk_create(self, arango_container_function):
        """Test bulk creating documents"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Bulk create
        users = [
            {"name": "User 1", "email": "user1@example.com"},
            {"name": "User 2", "email": "user2@example.com"},
            {"name": "User 3", "email": "user3@example.com"}
        ]
        
        created = repo.bulk_create(users)
        
        assert len(created) == 3
        assert all("id" in user for user in created)
        
        # Verify all exist
        total = repo.count()
        assert total == 3
    
    def test_count_with_filters(self, arango_container_function):
        """Test counting with filters"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        # Create users
        for i in range(10):
            repo.create({
                "name": f"User {i}",
                "status": "active" if i < 7 else "inactive"
            })
        
        # Count all
        total = repo.count()
        assert total == 10
        
        # Count active
        active_count = repo.count(filters={"status": "active"})
        assert active_count == 7
    
    def test_update_nonexistent_raises_error(self, arango_container_function):
        """Test updating non-existent document raises NotFoundError"""
        db = arango_container_function
        db.create_collection("test_users")
        
        repo = BaseRepository(db, collection="test_users")
        
        with pytest.raises(NotFoundError):
            repo.update("nonexistent-id", {"status": "active"})


@pytest.mark.integration
@pytest.mark.integration_fast
class TestBaseRepositoryIntegrationModuleScope:
    """Test BaseRepository with shared ArangoDB container"""
    
    def test_sorting_descending(self, clean_database_module):
        """Test sorting in descending order"""
        db = clean_database_module
        db.create_collection("test_items")
        
        repo = BaseRepository(db, collection="test_items")
        
        # Create items with different ages
        repo.create({"name": "Item A", "age": 30})
        repo.create({"name": "Item B", "age": 25})
        repo.create({"name": "Item C", "age": 35})
        
        # Sort by age descending
        items = repo.get_all(sort={"age": -1})
        
        assert items[0]["age"] == 35
        assert items[1]["age"] == 30
        assert items[2]["age"] == 25
    
    def test_find_many_with_pagination(self, clean_database_module):
        """Test find_many with pagination"""
        db = clean_database_module
        db.create_collection("test_items")
        
        repo = BaseRepository(db, collection="test_items")
        
        # Create items
        for i in range(20):
            status = "published" if i < 15 else "draft"
            repo.create({"title": f"Item {i}", "status": status})
        
        # Find published items, page 2
        items = repo.find_many(
            filters={"status": "published"},
            skip=10,
            limit=5
        )
        
        assert len(items) == 5
        assert all(item["status"] == "published" for item in items)
    
    def test_exists_method(self, clean_database_module):
        """Test exists method"""
        db = clean_database_module
        db.create_collection("test_items")
        
        repo = BaseRepository(db, collection="test_items")
        
        # Create item
        item = repo.create({"name": "Test Item"})
        item_id = item["id"]
        
        # Should exist
        assert repo.exists(item_id) is True
        
        # Delete and check
        repo.delete(item_id)
        assert repo.exists(item_id) is False


@pytest.mark.integration
@pytest.mark.integration_slow
class TestBaseRepositoryComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_user_repository_pattern(self, arango_container_function):
        """Test typical user repository usage pattern"""
        db = arango_container_function
        db.create_collection("users")
        
        # Create index on email (unique)
        db.create_index("users", ["email"], unique=True)
        
        repo = BaseRepository(db, collection="users")
        
        # Register user
        user = repo.create({
            "name": "Alice Smith",
            "email": "alice@example.com",
            "status": "pending",
            "role": "user"
        })
        user_id = user["id"]
        
        # Activate user
        repo.update(user_id, {"status": "active"})
        
        # Find by email
        found = repo.find_one({"email": "alice@example.com"})
        assert found["status"] == "active"
        
        # Get all active users
        active_users = repo.get_all(filters={"status": "active"})
        assert len(active_users) == 1
        
        # Cleanup
        repo.delete(user_id)
    
    def test_pagination_with_filters_and_sort(self, arango_container_function):
        """Test combining pagination, filters, and sorting"""
        db = arango_container_function
        db.create_collection("products")
        
        repo = BaseRepository(db, collection="products")
        
        # Create products
        for i in range(50):
            category = "electronics" if i < 30 else "books"
            repo.create({
                "name": f"Product {i}",
                "category": category,
                "price": 10 + i,
                "stock": 100 - i
            })
        
        # Get page 2 of electronics, sorted by price desc
        items, total = repo.get_paginated(
            page=2,
            per_page=10,
            filters={"category": "electronics"},
            sort={"price": -1}
        )
        
        assert len(items) == 10
        assert total == 30
        assert all(item["category"] == "electronics" for item in items)
        
        # Verify sorted (descending)
        for i in range(len(items) - 1):
            assert items[i]["price"] >= items[i + 1]["price"]