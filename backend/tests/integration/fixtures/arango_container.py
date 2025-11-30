"""
Path: tests/integration/fixtures/arango_container.py
Version: 4 - IP retry fix for empty container IP

Changes in v4:
- Added retry mechanism for container IP retrieval (fixes empty IP issue)
- Container.reload() to refresh network info before getting IP
- 10 retry attempts with 0.5s delay between attempts

Changes in v3:
- Fixed container-to-container networking (uses container IP instead of localhost)
- Fixed port access (uses internal port 8529 instead of mapped port)
- Fixed regex pattern for ArangoDB 3.12+ logs
- Fixed database creation (connects to _system first)

ArangoDB testcontainer fixtures
Provides isolated ArangoDB containers for integration testing

Fixtures available:
- arango_container_function: Fresh container per test (scope=function)
- arango_container_module: Shared container per test module (scope=module)

Compatible with testcontainers 4.13.3+ and devcontainer environments
"""

import pytest
import logging
import time
import os
from typing import Generator
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from src.core.config import settings
from src.database.factory import get_database, reset_database
from src.database.adapters.arango_adapter import ArangoDatabaseAdapter

logger = logging.getLogger(__name__)


class ArangoContainer(DockerContainer):
    """
    ArangoDB testcontainer
    
    Provides isolated ArangoDB instance for testing.
    Automatically starts container and waits for readiness.
    
    Compatible with testcontainers 4.13.3+
    
    Example:
        with ArangoContainer() as arango:
            host = arango.get_host()
            port = arango.get_port()
            # Use database...
    """
    
    def __init__(
        self,
        image: str = "arangodb:latest",
        root_password: str = "test-password"
    ):
        """
        Initialize ArangoDB container
        
        Args:
            image: Docker image to use
            root_password: Root password for ArangoDB
        """
        super().__init__(image)
        self.root_password = root_password
        self.port = 8529
        
        # Configure container
        self.with_exposed_ports(self.port)
        self.with_env("ARANGO_ROOT_PASSWORD", root_password)
        self.with_env("ARANGO_NO_AUTH", "0")
    
    def start(self):
        """Start container and wait for ArangoDB to be ready"""
        super().start()
        
        # Wait for ArangoDB ready message
        wait_for_logs(
            container=self,
            predicate=r"ArangoDB.*is ready for business",
            timeout=60
        )
        
        # Additional delay to ensure port is ready
        time.sleep(2)
        
        logger.info("ArangoDB container started and ready")
        return self
    
    def get_host(self) -> str:
        """
        Get container host
        
        Returns the container's IP address for container-to-container communication.
        This is required when tests run inside a devcontainer.
        """
        max_attempts = 10
        retry_delay = 0.5
        
        for attempt in range(max_attempts):
            try:
                # Get container's actual IP address
                wrapped = self.get_wrapped_container()
                
                # Refresh container info
                wrapped.reload()
                
                container_ip = wrapped.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                
                # Check if IP is not empty
                if container_ip:
                    logger.info(f"Using container IP: {container_ip}")
                    return container_ip
                
                # IP is empty, retry
                logger.debug(f"Container IP empty, attempt {attempt + 1}/{max_attempts}")
                time.sleep(retry_delay)
                
            except Exception as e:
                logger.debug(f"Error getting container IP (attempt {attempt + 1}): {e}")
                time.sleep(retry_delay)
        
        # All attempts failed
        logger.error("Could not get container IP after retries")
        
        # Fallback: use gateway IP (may not work in devcontainer)
        fallback = self.get_container_host_ip()
        logger.warning(f"Using fallback host: {fallback}")
        return fallback
    
    def get_port(self) -> int:
        """
        Get port for ArangoDB
        
        Returns internal port (8529) for container-to-container communication.
        """
        return self.port  # Always 8529 for container-to-container
    
    def get_connection_url(self) -> str:
        """Get full connection URL"""
        return f"http://{self.get_host()}:{self.get_port()}"


def _configure_database_adapter(container: ArangoContainer) -> ArangoDatabaseAdapter:
    """
    Configure database adapter to use testcontainer
    
    Args:
        container: Running ArangoDB container
        
    Returns:
        Configured adapter connected to container
    """
    from arango import ArangoClient
    
    # Get connection info
    host = container.get_host()
    port = container.get_port()
    password = container.root_password
    test_db_name = settings.ARANGO_DATABASE
    
    url = f"http://{host}:{port}"
    logger.info(f"Configuring adapter for {url}")
    
    # Connect to _system database first to create test database
    client = ArangoClient(hosts=url)
    sys_db = client.db("_system", username="root", password=password)
    
    # Create test database if not exists
    try:
        sys_db.create_database(test_db_name)
        logger.info(f"Created test database: {test_db_name}")
    except Exception as e:
        logger.info(f"Test database already exists: {test_db_name}")
    
    # Configure settings to point to test database
    settings.ARANGO_HOST = host
    settings.ARANGO_PORT = port
    settings.ARANGO_PASSWORD = password
    settings.ARANGO_DATABASE = test_db_name
    
    # Reset database singleton
    reset_database()
    
    # Create and connect adapter
    adapter = ArangoDatabaseAdapter()
    adapter.connect()
    
    logger.info(f"Database adapter ready: {url}/{test_db_name}")
    
    return adapter


def _cleanup_database(adapter: ArangoDatabaseAdapter) -> None:
    """
    Clean up test database - drop all collections
    
    Args:
        adapter: Connected database adapter
    """
    try:
        # Get all collections
        collections = adapter._db.collections()
        
        # Drop all non-system collections
        for col in collections:
            if not col['name'].startswith('_'):
                try:
                    adapter.drop_collection(col['name'])
                    logger.debug(f"Dropped collection: {col['name']}")
                except Exception as e:
                    logger.warning(f"Failed to drop collection {col['name']}: {e}")
        
        logger.info("Database cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning database: {e}")


# ============================================================================
# FUNCTION SCOPE FIXTURE - Fresh container per test
# ============================================================================

@pytest.fixture(scope="function")
def arango_container_function() -> Generator[ArangoDatabaseAdapter, None, None]:
    """
    ArangoDB container with function scope
    
    Creates a fresh ArangoDB container for EACH test.
    Provides complete isolation between tests.
    Slower but guarantees no side effects.
    
    Use when:
    - Tests modify data and you need complete isolation
    - Testing data integrity, constraints, indexes
    - Each test needs clean database state
    
    Yields:
        ArangoDatabaseAdapter connected to container
        
    Example:
        @pytest.mark.integration
        def test_user_creation(arango_container_function):
            db = arango_container_function
            
            # Fresh database, no data
            user = db.create("users", {"name": "Test"})
            assert user["name"] == "Test"
    """
    logger.info("Starting ArangoDB container (function scope)...")
    
    # Start container
    container = ArangoContainer()
    container.start()
    
    try:
        # Configure adapter
        adapter = _configure_database_adapter(container)
        
        logger.info("ArangoDB container ready (function scope)")
        yield adapter
        
    finally:
        # Cleanup
        logger.info("Stopping ArangoDB container (function scope)...")
        try:
            adapter.disconnect()
        except:
            pass
        
        container.stop()
        logger.info("ArangoDB container stopped (function scope)")


# ============================================================================
# MODULE SCOPE FIXTURE - Shared container per test file
# ============================================================================

@pytest.fixture(scope="module")
def arango_container_module() -> Generator[ArangoDatabaseAdapter, None, None]:
    """
    ArangoDB container with module scope
    
    Creates ONE ArangoDB container shared by ALL tests in the module.
    Faster but tests must clean up their data.
    
    Use when:
    - Running many tests that don't conflict
    - Speed is important
    - Tests use different collections
    
    Yields:
        ArangoDatabaseAdapter connected to container
        
    Example:
        @pytest.mark.integration
        def test_read_operations(arango_container_module):
            db = arango_container_module
            # Container shared across all tests in file
            users = db.get_all("users")
    """
    logger.info("Starting ArangoDB container (module scope)...")
    
    # Start container
    container = ArangoContainer()
    container.start()
    
    try:
        # Configure adapter
        adapter = _configure_database_adapter(container)
        
        logger.info("ArangoDB container ready (module scope)")
        yield adapter
        
    finally:
        # Cleanup
        logger.info("Stopping ArangoDB container (module scope)...")
        try:
            adapter.disconnect()
        except:
            pass
        
        container.stop()
        logger.info("ArangoDB container stopped (module scope)")


# ============================================================================
# CLEANUP FIXTURES - Reset database between tests
# ============================================================================

@pytest.fixture
def clean_database_function(arango_container_function) -> Generator[ArangoDatabaseAdapter, None, None]:
    """
    Clean database before each test (function scope)
    
    Drops all collections before test runs.
    Use with arango_container_function for complete isolation.
    
    Yields:
        Clean ArangoDatabaseAdapter
        
    Example:
        def test_with_clean_db(clean_database_function):
            db = clean_database_function
            # Database is empty, no collections
            db.create_collection("users")
            assert db.count("users") == 0
    """
    adapter = arango_container_function
    _cleanup_database(adapter)
    yield adapter


@pytest.fixture
def clean_database_module(arango_container_module) -> Generator[ArangoDatabaseAdapter, None, None]:
    """
    Clean database before each test (module scope)
    
    Drops all collections before test runs.
    Use with arango_container_module when you need clean state
    but want to reuse container.
    
    Yields:
        Clean ArangoDatabaseAdapter
        
    Example:
        def test_with_clean_shared_db(clean_database_module):
            db = clean_database_module
            # Database cleaned, but container reused
            db.create_collection("users")
            db.create("users", {"name": "Test"})
    """
    adapter = arango_container_module
    _cleanup_database(adapter)
    yield adapter