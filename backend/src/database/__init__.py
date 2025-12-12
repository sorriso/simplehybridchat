"""
Path: backend/src/database/__init__.py
Version: 1.0

Database abstraction layer - Reusable block
Provides database-agnostic interface for data persistence
"""

from src.database.interface import IDatabase
from src.database.factory import get_database
from src.database.exceptions import (
    DatabaseException,
    NotFoundError,
    DuplicateKeyError,
    ConnectionError,
)

__all__ = [
    "IDatabase",
    "get_database",
    "DatabaseException",
    "NotFoundError",
    "DuplicateKeyError",
    "ConnectionError",
]