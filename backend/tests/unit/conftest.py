"""
Path: backend/tests/unit/conftest.py
Version: 1.0

Unit test fixtures and mocks
"""

import pytest
from unittest.mock import MagicMock

from tests.unit.mock_database import MockDatabase


@pytest.fixture
def mock_database():
    """
    Mock database for unit tests
    
    Returns a MockDatabase instance that simulates ArangoDB behavior
    without requiring actual database connection.
    """
    return MockDatabase()