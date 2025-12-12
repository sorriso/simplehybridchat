# path: backend/tests/conftest.py
# version: 8 - Removed ollama imports (now in integration/conftest.py)

import os
import sys
import pytest
import signal
import logging
from typing import List

logger = logging.getLogger(__name__)


# =============================================================================
# LLM PROVIDER SETUP - Ollama for integration tests
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_llm_provider():
    """
    Configure LLM provider for tests
    
    Uses Ollama by default (via ollama_container fixture in integration tests).
    Can be overridden with OPENROUTER_API_KEY env var for OpenRouter tests.
    """
    # Check if OpenRouter token is available
    if os.getenv("OPENROUTER_API_KEY"):
        logger.info("OpenRouter API key found - will use OpenRouter for tests")
    else:
        logger.info("No OpenRouter API key - will use Ollama for tests")
    
    yield


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "docker: Tests requiring Docker")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "openrouter: Tests requiring OpenRouter API key")
    
    # Display configuration
    print("\n" + "="*80)
    print("PYTEST CONFIGURATION")
    print("="*80)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Test paths: {config.getini('testpaths')}")
    print("="*80 + "\n")


# =============================================================================
# SESSION-LEVEL CLEANUP
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def cleanup_on_exit():
    """
    Ensure cleanup happens on session exit, even on interrupt.
    
    This fixture runs automatically for every test session.
    """
    # Setup: register signal handlers
    original_sigint = signal.signal(signal.SIGINT, signal.default_int_handler)
    original_sigterm = signal.signal(signal.SIGTERM, signal.default_int_handler)
    
    yield
    
    # Teardown: restore signal handlers and cleanup
    signal.signal(signal.SIGINT, original_sigint)
    signal.signal(signal.SIGTERM, original_sigterm)
    
    # Run cleanup
    _cleanup_all_containers()


def _cleanup_all_containers():
    """
    Cleanup all testcontainers.
    
    This is called at the end of the test session.
    """
    print("\n" + "="*80)
    print("SESSION CLEANUP - Removing testcontainers")
    print("="*80)
    
    try:
        import docker
        client = docker.from_env()
        
        # Find containers with testcontainer label
        filters = {"label": "testcontainer=true"}
        containers = client.containers.list(all=True, filters=filters)
        
        if not containers:
            print("✓ No testcontainers found")
            print("="*80 + "\n")
            return
        
        print(f"Found {len(containers)} container(s) to clean up:")
        
        removed = 0
        failed = 0
        
        for container in containers:
            try:
                name = container.name
                short_id = container.short_id
                status = container.status
                
                print(f"  [{short_id}] {name} ({status})... ", end="")
                
                # Force stop if running
                if status == 'running':
                    container.stop(timeout=5)
                
                # Remove with volumes
                container.remove(force=True, v=True)
                print("✓ Removed")
                removed += 1
                
            except Exception as e:
                print(f"✗ Failed: {e}")
                failed += 1
        
        print(f"\nSummary: {removed} removed, {failed} failed")
        
    except ImportError:
        print("⚠ Docker package not installed, skipping container cleanup")
    except Exception as e:
        print(f"⚠ Error during cleanup: {e}")
    
    print("="*80 + "\n")


# =============================================================================
# TEST COLLECTION HOOKS
# =============================================================================

def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection.
    
    This adds markers automatically based on test location.
    """
    for item in items:
        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.docker)
        
        # Auto-mark unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# =============================================================================
# REPORTING HOOKS
# =============================================================================

def pytest_sessionstart(session):
    """Hook called at the start of test session."""
    print("\n" + "="*80)
    print("TEST SESSION STARTING")
    print("="*80 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """
    Hook called at the end of test session.
    
    Ensures final cleanup happens.
    """
    _cleanup_all_containers()
    
    print("\n" + "="*80)
    print("TEST SESSION FINISHED")
    print(f"Exit status: {exitstatus}")
    print("="*80 + "\n")


# =============================================================================
# TEST EXECUTION HOOKS
# =============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make test results available in fixtures.
    
    This allows fixtures to check if a test passed/failed.
    """
    outcome = yield
    rep = outcome.get_result()
    
    # Store test result in item for use in fixtures
    setattr(item, f"rep_{rep.when}", rep)


# =============================================================================
# DOCKER HELPERS
# =============================================================================

def is_docker_available() -> bool:
    """Check if Docker is available."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_available():
    """
    Session-scoped fixture that checks Docker availability.
    
    Skip tests that require Docker if it's not available.
    """
    if not is_docker_available():
        pytest.skip("Docker is not available")
    return True


# =============================================================================
# RESOURCE MONITORING (Optional)
# =============================================================================

@pytest.fixture(scope="function", autouse=False)
def monitor_resources(request):
    """
    Optional fixture to monitor resource usage during tests.
    
    Usage: Add @pytest.mark.usefixtures("monitor_resources") to test.
    """
    try:
        import docker
        client = docker.from_env()
        
        # Get initial stats
        filters = {"label": "testcontainer=true"}
        containers = client.containers.list(filters=filters)
        
        print(f"\n[RESOURCES] Test: {request.node.name}")
        print(f"[RESOURCES] Active containers: {len(containers)}")
        
        for container in containers:
            stats = container.stats(stream=False)
            memory_usage = stats.get('memory_stats', {}).get('usage', 0)
            memory_mb = memory_usage / (1024 * 1024)
            print(f"[RESOURCES]   - {container.name}: {memory_mb:.1f} MB")
        
    except Exception as e:
        print(f"[RESOURCES] Warning: Could not get stats: {e}")
    
    yield
    
    # Can add post-test resource monitoring here if needed