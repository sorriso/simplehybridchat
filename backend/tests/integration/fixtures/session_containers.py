"""
Path: backend/tests/integration/fixtures/session_containers.py
Version: 1

Session-scoped containers for maximum speed
Shared across ALL tests in the entire test session
"""

import pytest
import logging
from typing import Generator

from tests.integration.fixtures.arango_container import (
    ArangoContainer,
    _configure_database_adapter,
    _cleanup_database
)
from tests.integration.fixtures.minio_container import (
    MinIOContainer,
    _configure_storage_adapter,
    _cleanup_storage
)

logger = logging.getLogger(__name__)


# =============================================================================
# SESSION SCOPE - PartagÃ© par TOUS les tests
# =============================================================================

@pytest.fixture(scope="session")
def arango_container_session():
    """
    ArangoDB container shared across entire test session
    
    FASTEST option but requires cleanup between tests.
    Use with clean_database_session fixture.
    
    âš¡ Speed: ~2s startup for entire session
    """
    logger.info("Starting ArangoDB container (session scope)...")
    
    container = ArangoContainer()
    container.start()
    
    try:
        adapter = _configure_database_adapter(container)
        logger.info("ArangoDB container ready (session scope)")
        yield adapter
        
    finally:
        logger.info("Stopping ArangoDB container (session scope)...")
        try:
            adapter.disconnect()
        except:
            pass
        
        container.stop()
        logger.info("ArangoDB container stopped (session scope)")


@pytest.fixture(scope="session")
def minio_container_session():
    """
    MinIO container shared across entire test session
    
    FASTEST option but requires cleanup between tests.
    Use with clean_storage_session fixture.
    
    âš¡ Speed: ~3s startup for entire session
    """
    logger.info("Starting MinIO container (session scope)...")
    
    container = MinIOContainer()
    container.start()
    
    try:
        adapter = _configure_storage_adapter(container)
        logger.info("MinIO container ready (session scope)")
        yield adapter
        
    finally:
        logger.info("Stopping MinIO container (session scope)...")
        try:
            adapter.disconnect()
        except:
            pass
        
        container.stop()
        logger.info("MinIO container stopped (session scope)")


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture
def clean_database_session(arango_container_session):
    """
    Clean database before each test (session container)
    
    Use when you need clean state but want session-level container.
    
    âš¡ Speed: Very fast, just drops collections
    """
    adapter = arango_container_session
    _cleanup_database(adapter)
    yield adapter


@pytest.fixture
def clean_storage_session(minio_container_session):
    """
    Clean storage before each test (session container)
    
    Use when you need clean state but want session-level container.
    
    âš¡ Speed: Very fast, just deletes buckets
    """
    adapter = minio_container_session
    _cleanup_storage(adapter)
    yield adapter


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
SPEED COMPARISON:
-----------------
Function scope (fresh container per test):
  - Setup time: ~2-3s per test
  - 10 tests = ~25s

Module scope (shared per file):
  - Setup time: ~2-3s per file
  - 10 tests in 3 files = ~9s

Session scope (shared entire session):
  - Setup time: ~2-3s total
  - 10 tests in 3 files = ~3s
  
âš¡ Session scope is ~8x faster than function scope!

USAGE:
------
# For tests that need isolation:
def test_something(clean_database_session):
    db = clean_database_session
    # Clean database, shared container
    
# For read-only tests (no cleanup needed):
def test_readonly(arango_container_session):
    db = arango_container_session
    # No cleanup overhead
    
WHEN TO USE EACH SCOPE:
-----------------------
Session scope:
  âœ“ Read-only tests
  âœ“ Tests with cleanup
  âœ“ Maximum speed
  âœ— Complex state dependencies

Module scope:
  âœ“ Good isolation
  âœ“ Good speed
  âœ“ Balance speed/isolation

Function scope:
  âœ“ Complete isolation
  âœ“ Complex scenarios
  âœ— Slower
"""