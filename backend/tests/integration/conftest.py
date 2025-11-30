"""
Path: tests/integration/conftest.py
Version: 2

Global integration test configuration
Makes fixtures available to all integration tests
"""

import pytest
import logging

# Import database fixtures
from tests.integration.fixtures.arango_container import (
    arango_container_function,
    arango_container_module,
    clean_database_function,
    clean_database_module,
)

# Import storage fixtures
from tests.integration.fixtures.minio_container import (
    minio_container_function,
    minio_container_module,
    clean_storage_function,
    clean_storage_module,
)

# Configure logging for integration tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Make fixtures available
__all__ = [
    # Database fixtures
    "arango_container_function",
    "arango_container_module",
    "clean_database_function",
    "clean_database_module",
    # Storage fixtures
    "minio_container_function",
    "minio_container_module",
    "clean_storage_function",
    "clean_storage_module",
]


# Marker for integration tests
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test requiring Docker"
    )
    config.addinivalue_line(
        "markers",
        "integration_slow: mark test as slow integration test (fresh container per test)"
    )
    config.addinivalue_line(
        "markers",
        "integration_fast: mark test as fast integration test (shared container)"
    )