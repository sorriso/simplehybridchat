"""
Path: backend/tests/integration/fixtures/minio_container.py
Version: 1

MinIO testcontainer fixtures
Provides isolated MinIO containers for integration testing

Fixtures available:
- minio_container_function: Fresh container per test (scope=function)
- minio_container_module: Shared container per test module (scope=module)

Compatible with testcontainers 4.13.3+ and devcontainer environments
"""

import pytest
import logging
import time
from typing import Generator
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from src.core.config import settings
from src.storage.factory import get_storage, reset_storage
from src.storage.adapters.minio_adapter import MinIOStorageAdapter

logger = logging.getLogger(__name__)


class MinIOContainer(DockerContainer):
    """
    MinIO testcontainer
    
    Provides isolated MinIO instance for testing.
    Automatically starts container and waits for readiness.
    
    Compatible with testcontainers 4.13.3+
    """
    
    def __init__(
        self,
        image: str = "minio/minio:latest",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin"
    ):
        """
        Initialize MinIO container
        
        Args:
            image: Docker image to use
            access_key: MinIO root access key
            secret_key: MinIO root secret key
        """
        super().__init__(image)
        self.access_key = access_key
        self.secret_key = secret_key
        self.api_port = 9000
        self.console_port = 9001
        
        # Configure container
        self.with_exposed_ports(self.api_port, self.console_port)
        self.with_env("MINIO_ROOT_USER", access_key)
        self.with_env("MINIO_ROOT_PASSWORD", secret_key)
        
        # MinIO server command
        self.with_command("server /data --console-address :9001")
    
    def start(self):
        """Start container and wait for MinIO to be ready"""
        super().start()
        
        # Wait for MinIO ready message
        wait_for_logs(
            container=self,
            predicate=r"API:.*http",
            timeout=60
        )
        
        # Additional delay to ensure API is ready
        time.sleep(3)
        
        logger.info("MinIO container started and ready")
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
        Get port for MinIO API
        
        Returns internal port (9000) for container-to-container communication.
        """
        return self.api_port  # Always 9000 for container-to-container
    
    def get_connection_url(self) -> str:
        """Get full connection URL"""
        return f"{self.get_host()}:{self.get_port()}"


def _configure_storage_adapter(container: MinIOContainer) -> MinIOStorageAdapter:
    """
    Configure storage adapter to use testcontainer
    
    Args:
        container: Running MinIO container
        
    Returns:
        Configured adapter connected to container
    """
    # Get connection info
    host = container.get_host()
    port = container.get_port()
    access_key = container.access_key
    secret_key = container.secret_key
    
    url = f"{host}:{port}"
    logger.info(f"Configuring adapter for {url}")
    
    # Configure settings to point to test MinIO
    settings.MINIO_HOST = host
    settings.MINIO_PORT = port
    settings.MINIO_ACCESS_KEY = access_key
    settings.MINIO_SECRET_KEY = secret_key
    settings.MINIO_SECURE = False
    
    # Reset storage singleton
    reset_storage()
    
    # Create and connect adapter
    adapter = MinIOStorageAdapter()
    adapter.connect()
    
    logger.info(f"Storage adapter ready: {url}")
    
    return adapter


def _cleanup_storage(adapter: MinIOStorageAdapter) -> None:
    """
    Clean up test storage - delete all buckets
    
    Args:
        adapter: Connected storage adapter
    """
    try:
        # Get all buckets
        buckets = adapter.list_buckets()
        
        # Delete all buckets (force delete with contents)
        for bucket in buckets:
            try:
                adapter.delete_bucket(bucket, force=True)
                logger.debug(f"Deleted bucket: {bucket}")
            except Exception as e:
                logger.warning(f"Failed to delete bucket {bucket}: {e}")
        
        logger.info("Storage cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning storage: {e}")


# ============================================================================
# FUNCTION SCOPE FIXTURE - Fresh container per test
# ============================================================================

@pytest.fixture(scope="function")
def minio_container_function() -> Generator[MinIOStorageAdapter, None, None]:
    """
    MinIO container with function scope
    
    Creates a fresh MinIO container for EACH test.
    Provides complete isolation between tests.
    Slower but guarantees no side effects.
    
    Use when:
    - Tests modify data and you need complete isolation
    - Testing file operations, buckets, permissions
    - Each test needs clean storage state
    
    Yields:
        MinIOStorageAdapter connected to container
    """
    logger.info("Starting MinIO container (function scope)...")
    
    # Start container
    container = MinIOContainer()
    container.start()
    
    try:
        # Configure adapter
        adapter = _configure_storage_adapter(container)
        
        logger.info("MinIO container ready (function scope)")
        yield adapter
        
    finally:
        # Cleanup
        logger.info("Stopping MinIO container (function scope)...")
        try:
            adapter.disconnect()
        except:
            pass
        
        container.stop()
        logger.info("MinIO container stopped (function scope)")


# ============================================================================
# MODULE SCOPE FIXTURE - Shared container per test file
# ============================================================================

@pytest.fixture(scope="module")
def minio_container_module() -> Generator[MinIOStorageAdapter, None, None]:
    """
    MinIO container with module scope
    
    Creates ONE MinIO container shared by ALL tests in the module.
    Faster but tests must clean up their data.
    
    Use when:
    - Running many tests that don't conflict
    - Speed is important
    - Tests use different buckets
    
    Yields:
        MinIOStorageAdapter connected to container
    """
    logger.info("Starting MinIO container (module scope)...")
    
    # Start container
    container = MinIOContainer()
    container.start()
    
    try:
        # Configure adapter
        adapter = _configure_storage_adapter(container)
        
        logger.info("MinIO container ready (module scope)")
        yield adapter
        
    finally:
        # Cleanup
        logger.info("Stopping MinIO container (module scope)...")
        try:
            adapter.disconnect()
        except:
            pass
        
        container.stop()
        logger.info("MinIO container stopped (module scope)")


# ============================================================================
# CLEANUP FIXTURES - Reset storage between tests
# ============================================================================

@pytest.fixture
def clean_storage_function(minio_container_function) -> Generator[MinIOStorageAdapter, None, None]:
    """
    Clean storage before each test (function scope)
    
    Deletes all buckets before test runs.
    Use with minio_container_function for complete isolation.
    
    Yields:
        Clean MinIOStorageAdapter
    """
    adapter = minio_container_function
    _cleanup_storage(adapter)
    yield adapter


@pytest.fixture
def clean_storage_module(minio_container_module) -> Generator[MinIOStorageAdapter, None, None]:
    """
    Clean storage before each test (module scope)
    
    Deletes all buckets before test runs.
    Use with minio_container_module when you need clean state
    but want to reuse container.
    
    Yields:
        Clean MinIOStorageAdapter
    """
    adapter = minio_container_module
    _cleanup_storage(adapter)
    yield adapter