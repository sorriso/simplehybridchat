"""
Path: backend/tests/integration/database/test_database_integration.py
Version: 3

Changes in v3:
- Fixed pagination test: u["_key"] â†’ u["id"] (lines 184-185)

Changes in v2:
- Modified all assertions: assert "_key" in â†’ assert "id" in
- Modified all document accesses: doc["_key"] â†’ doc["id"]
- Tests now verify database returns 'id' (adapter behavior)

Database integration tests with real ArangoDB
Tests database adapter with actual Docker container

Run with:
    pytest tests/integration/database/ -v -m integration
    pytest tests/integration/database/ -v -m integration_slow  # Function scope only
    pytest tests/integration/database/ -v -m integration_fast  # Module scope only
"""

import pytest
from typing import Dict, Any

from src.database.adapters.arango_adapter import ArangoDatabaseAdapter
from src.database.exceptions import NotFoundError, DuplicateKeyError


# ============================================================================
# FUNCTION SCOPE TESTS - Fresh container per test (complete isolation)
# ============================================================================

class TestDatabaseIntegrationFunctionScope:
    """
    Integration tests with function scope
    
    Each test gets a fresh ArangoDB container.
    Slower but guarantees complete isolation.
    """
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_create_and_retrieve_document(self, arango_container_function):
        """Test creating and retrieving document in real ArangoDB"""
        db = arango_container_function
        
        # Create collection
        db.create_collection("test_users")
        
        # Create document
        user_data = {
            "name": "Integration Test User",
            "email": "integration@test.com",
            "role": "user",
            "status": "active"
        }
        
        created_user = db.create("test_users", user_data)
        
        # Verify creation
        assert created_user is not None
        assert "id" in created_user
        assert created_user["name"] == user_data["name"]
        assert created_user["email"] == user_data["email"]
        
        # Retrieve by ID
        user_id = created_user["id"]
        retrieved_user = db.get_by_id("test_users", user_id)
        
        assert retrieved_user is not None
        assert retrieved_user["id"] == user_id
        assert retrieved_user["name"] == user_data["name"]
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_update_document(self, arango_container_function):
        """Test updating document in real ArangoDB"""
        db = arango_container_function
        
        # Create collection and document
        db.create_collection("test_users")
        user = db.create("test_users", {
            "name": "Original Name",
            "status": "pending"
        })
        
        # Update document
        updated_user = db.update("test_users", user["id"], {
            "status": "active",
            "verified": True
        })
        
        # Verify update
        assert updated_user["status"] == "active"
        assert updated_user["verified"] is True
        assert updated_user["name"] == "Original Name"  # Preserved
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_delete_document(self, arango_container_function):
        """Test deleting document from real ArangoDB"""
        db = arango_container_function
        
        # Create collection and document
        db.create_collection("test_users")
        user = db.create("test_users", {"name": "To Delete"})
        user_id = user["id"]
        
        # Verify exists
        assert db.exists("test_users", user_id) is True
        
        # Delete
        deleted = db.delete("test_users", user_id)
        assert deleted is True
        
        # Verify deleted
        assert db.exists("test_users", user_id) is False
        assert db.get_by_id("test_users", user_id) is None
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_unique_constraint(self, arango_container_function):
        """Test unique index enforcement in real ArangoDB"""
        db = arango_container_function
        
        # Create collection
        db.create_collection("test_users")
        
        # Create unique index on email
        db.create_index("test_users", ["email"], unique=True)
        
        # First insert succeeds
        db.create("test_users", {
            "name": "User 1",
            "email": "unique@test.com"
        })
        
        # Second insert with same email should fail
        with pytest.raises(Exception):  # ArangoDB raises error on duplicate
            db.create("test_users", {
                "name": "User 2",
                "email": "unique@test.com"
            })
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_query_with_filters(self, arango_container_function):
        """Test querying with filters in real ArangoDB"""
        db = arango_container_function
        
        # Create collection
        db.create_collection("test_users")
        
        # Insert multiple documents
        db.create("test_users", {"name": "Active User 1", "status": "active"})
        db.create("test_users", {"name": "Active User 2", "status": "active"})
        db.create("test_users", {"name": "Inactive User", "status": "inactive"})
        
        # Query active users
        active_users = db.get_all("test_users", filters={"status": "active"})
        
        assert len(active_users) == 2
        assert all(user["status"] == "active" for user in active_users)
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_pagination(self, arango_container_function):
        """Test pagination in real ArangoDB"""
        db = arango_container_function
        
        # Create collection
        db.create_collection("test_users")
        
        # Insert 10 documents
        for i in range(10):
            db.create("test_users", {"name": f"User {i}", "index": i})
        
        # Get first page (5 items)
        page1 = db.get_all("test_users", skip=0, limit=5)
        assert len(page1) == 5
        
        # Get second page
        page2 = db.get_all("test_users", skip=5, limit=5)
        assert len(page2) == 5
        
        # Verify different results
        page1_keys = {u["id"] for u in page1}
        page2_keys = {u["id"] for u in page2}
        assert page1_keys.isdisjoint(page2_keys)  # No overlap
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_sorting(self, arango_container_function):
        """Test sorting in real ArangoDB"""
        db = arango_container_function
        
        # Create collection
        db.create_collection("test_users")
        
        # Insert documents
        db.create("test_users", {"name": "Charlie", "age": 30})
        db.create("test_users", {"name": "Alice", "age": 25})
        db.create("test_users", {"name": "Bob", "age": 35})
        
        # Sort by name ascending
        sorted_users = db.get_all("test_users", sort={"name": 1})
        
        assert sorted_users[0]["name"] == "Alice"
        assert sorted_users[1]["name"] == "Bob"
        assert sorted_users[2]["name"] == "Charlie"
        
        # Sort by age descending
        sorted_by_age = db.get_all("test_users", sort={"age": -1})
        
        assert sorted_by_age[0]["age"] == 35
        assert sorted_by_age[1]["age"] == 30
        assert sorted_by_age[2]["age"] == 25


# ============================================================================
# MODULE SCOPE TESTS - Shared container (faster, must clean up)
# ============================================================================

class TestDatabaseIntegrationModuleScope:
    """
    Integration tests with module scope
    
    All tests share one ArangoDB container.
    Faster but requires cleanup between tests.
    """
    
    @pytest.mark.integration
    @pytest.mark.integration_fast
    def test_count_documents(self, clean_database_module):
        """Test counting documents in real ArangoDB"""
        db = clean_database_module
        
        # Create collection
        db.create_collection("test_items")
        
        # Insert documents
        db.create("test_items", {"type": "A"})
        db.create("test_items", {"type": "A"})
        db.create("test_items", {"type": "B"})
        
        # Count all
        total = db.count("test_items")
        assert total == 3
        
        # Count with filter
        type_a_count = db.count("test_items", filters={"type": "A"})
        assert type_a_count == 2
    
    @pytest.mark.integration
    @pytest.mark.integration_fast
    def test_find_one(self, clean_database_module):
        """Test find_one in real ArangoDB"""
        db = clean_database_module
        
        # Create collection
        db.create_collection("test_items")
        
        # Insert documents
        db.create("test_items", {"email": "test@example.com", "name": "Test"})
        
        # Find by email
        found = db.find_one("test_items", {"email": "test@example.com"})
        
        assert found is not None
        assert found["email"] == "test@example.com"
        assert found["name"] == "Test"
    
    @pytest.mark.integration
    @pytest.mark.integration_fast
    def test_collection_operations(self, clean_database_module):
        """Test collection management in real ArangoDB"""
        db = clean_database_module
        
        # Collection shouldn't exist
        assert db.collection_exists("temp_collection") is False
        
        # Create collection
        db.create_collection("temp_collection")
        assert db.collection_exists("temp_collection") is True
        
        # Truncate
        db.create("temp_collection", {"data": "test"})
        db.truncate_collection("temp_collection")
        assert db.count("temp_collection") == 0
        
        # Drop
        db.drop_collection("temp_collection")
        assert db.collection_exists("temp_collection") is False
    
    @pytest.mark.integration
    @pytest.mark.integration_fast
    def test_complex_query(self, clean_database_module):
        """Test complex query with filters, sort, and pagination"""
        db = clean_database_module
        
        # Create collection
        db.create_collection("test_products")
        
        # Insert products
        products = [
            {"name": "Product A", "category": "electronics", "price": 100},
            {"name": "Product B", "category": "electronics", "price": 200},
            {"name": "Product C", "category": "books", "price": 15},
            {"name": "Product D", "category": "electronics", "price": 150},
            {"name": "Product E", "category": "books", "price": 25},
        ]
        
        for product in products:
            db.create("test_products", product)
        
        # Query: electronics, sorted by price desc, limit 2
        results = db.get_all(
            "test_products",
            filters={"category": "electronics"},
            sort={"price": -1},
            limit=2
        )
        
        assert len(results) == 2
        assert results[0]["price"] == 200  # Highest
        assert results[1]["price"] == 150  # Second highest


# ============================================================================
# PATTERN TESTS - Bottom-up (DB Ã¢â€ â€™ API) and Top-down (API Ã¢â€ â€™ DB)
# ============================================================================

class TestDatabasePatterns:
    """
    Test integration patterns for API testing
    
    These tests demonstrate how to test API endpoints with database:
    - Bottom-up: Inject data in DB, read via API
    - Top-down: Write via API, verify in DB
    """
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_pattern_bottom_up_inject_db_read_api(self, arango_container_function):
        """
        Pattern 1: Bottom-up testing
        
        1. Inject data directly in database
        2. Read via API/service layer
        3. Verify API returns correct data from DB
        
        Use case: Testing read operations, data retrieval logic
        """
        db = arango_container_function
        
        # Create collection
        db.create_collection("users")
        
        # 1. INJECT: Create data directly in DB
        db.create("users", {
            "name": "DB Injected User",
            "email": "injected@test.com",
            "status": "active"
        })
        
        # 2. READ: Get via database layer (simulates API reading from DB)
        users = db.get_all("users", filters={"status": "active"})
        
        # 3. VERIFY: Data is correctly retrieved
        assert len(users) == 1
        assert users[0]["name"] == "DB Injected User"
        assert users[0]["email"] == "injected@test.com"
        
        # In real API test, you would call:
        # response = client.get("/api/users?status=active")
        # assert response.json()[0]["name"] == "DB Injected User"
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_pattern_top_down_write_api_verify_db(self, arango_container_function):
        """
        Pattern 2: Top-down testing
        
        1. Create data via API/service layer
        2. Verify directly in database
        3. Check data is correctly persisted
        
        Use case: Testing write operations, data persistence
        """
        db = arango_container_function
        
        # Create collection
        db.create_collection("users")
        
        # 1. WRITE: Create via database layer (simulates API writing to DB)
        # In real API test, you would call:
        # response = client.post("/api/users", json={...})
        created_user = db.create("users", {
            "name": "API Created User",
            "email": "created@test.com",
            "role": "user"
        })
        
        # 2. VERIFY: Check directly in database
        user_in_db = db.find_one("users", {"email": "created@test.com"})
        
        assert user_in_db is not None
        assert user_in_db["name"] == "API Created User"
        assert user_in_db["role"] == "user"
        assert "id" in user_in_db
    
    @pytest.mark.integration
    @pytest.mark.integration_slow
    def test_pattern_full_cycle_create_update_delete(self, arango_container_function):
        """
        Pattern 3: Full lifecycle testing
        
        Tests complete CRUD cycle with database verification at each step
        """
        db = arango_container_function
        
        # Setup
        db.create_collection("users")
        
        # 1. CREATE via API (simulated)
        user = db.create("users", {
            "name": "Lifecycle User",
            "email": "lifecycle@test.com",
            "status": "pending"
        })
        user_id = user["id"]
        
        # Verify in DB
        assert db.exists("users", user_id) is True
        
        # 2. UPDATE via API (simulated)
        db.update("users", user_id, {"status": "active"})
        
        # Verify in DB
        updated = db.get_by_id("users", user_id)
        assert updated["status"] == "active"
        
        # 3. DELETE via API (simulated)
        db.delete("users", user_id)
        
        # Verify in DB
        assert db.exists("users", user_id) is False


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestDatabaseErrorHandling:
    """Test error handling with real ArangoDB"""
    
    @pytest.mark.integration
    @pytest.mark.integration_fast
    def test_update_nonexistent_document(self, clean_database_module):
        """Test updating non-existent document raises error"""
        db = clean_database_module
        
        db.create_collection("test_items")
        
        # Try to update non-existent document
        with pytest.raises(NotFoundError):
            db.update("test_items", "nonexistent-id", {"field": "value"})
    
    @pytest.mark.integration
    @pytest.mark.integration_fast
    def test_query_nonexistent_collection(self, clean_database_module):
        """Test querying non-existent collection raises error"""
        db = clean_database_module
        
        # Try to query non-existent collection
        with pytest.raises(Exception):  # CollectionNotFoundError
            db.get_all("nonexistent_collection")