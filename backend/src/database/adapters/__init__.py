"""
Path: src/database/adapters/__init__.py
Version: 1.0

Database adapters package
Contains concrete implementations of IDatabase interface for different databases
"""

from src.database.adapters.arango_adapter import ArangoDatabaseAdapter

__all__ = [
    "ArangoDatabaseAdapter",
    # Future adapters:
    # "MongoDatabaseAdapter",
    # "PostgresDatabaseAdapter",
]