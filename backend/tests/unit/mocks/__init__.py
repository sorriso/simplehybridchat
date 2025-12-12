"""
Path: backend/tests/unit/mocks/__init__.py
Version: 1.0

Mock objects for unit testing
Provides in-memory implementations for testing without external dependencies
"""

from tests.unit.mocks.mock_database import MockDatabase

__all__ = [
    "MockDatabase",
]