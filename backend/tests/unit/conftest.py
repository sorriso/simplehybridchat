"""
Path: backend/tests/unit/conftest.py
Version: 2.0

Changes in v2.0:
- FIX: Corrected import path from tests.unit.mock_database to tests.unit.mocks.mock_database
- MockDatabase is in the 'mocks' subdirectory

Unit test fixtures and mocks
"""

import pytest
from unittest.mock import MagicMock

# Correct import path - MockDatabase is in tests/unit/mocks/mock_database.py
from tests.unit.mocks.mock_database import MockDatabase


@pytest.fixture
def mock_database():
    """
    Mock database for unit tests
    
    Returns a MockDatabase instance that simulates ArangoDB behavior
    without requiring actual database connection.
    
    Example:
        def test_something(mock_database):
            mock_database.connect()
            mock_database.create_collection("users")
            # ... test code
    """
    db = MockDatabase()
    db.connect()
    yield db
    db.disconnect()


@pytest.fixture
def mock_db():
    """
    Alias for mock_database fixture
    
    Shorter name commonly used in tests.
    """
    db = MockDatabase()
    db.connect()
    yield db
    db.disconnect()