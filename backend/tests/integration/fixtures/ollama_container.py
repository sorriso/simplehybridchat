"""
Path: backend/tests/integration/fixtures/ollama_container.py
Version: 19
"""

import pytest
import logging
import time
from typing import Generator
from testcontainers.core.container import DockerContainer

logger = logging.getLogger(__name__)


class OllamaContainer(DockerContainer):
    """
    Ollama container for testing
    
    Runs Ollama with a small model (tinyllama 1.1B) for fast tests
    """
    
    def __init__(
        self,
        image: str = "ollama/ollama:latest",
        model: str = "tinyllama",
        **kwargs
    ):
        """
        Initialize Ollama container
        
        Args:
            image: Docker image (default: ollama/ollama:latest)
            model: Model to pull (default: tinyllama)
            **kwargs: Additional container arguments
        """
        super().__init__(image, **kwargs)
        self.model = model
        self.port = 11434
        
        # Start Ollama server explicitly
        # Image has ENTRYPOINT ["ollama"], so just pass "serve" as arg
        self.with_command("serve")
        
        # Expose Ollama API port
        self.with_exposed_ports(self.port)
    
    def start(self):
        """Start container and wait for Ollama to be ready"""
        super().start()
        
        # Wait for Ollama API to be ready
        logger.info("Waiting for Ollama to start...")
        self.wait_until_ready()
        
        return self
    
    def wait_until_ready(self, timeout: int = 60):
        """
        Wait until Ollama API is responding
        
        Checks from inside the container using exec.
        Polls /api/tags endpoint until success or timeout.
        
        Args:
            timeout: Maximum seconds to wait (default: 60)
            
        Raises:
            TimeoutError: If Ollama doesn't respond within timeout
        """
        import time
        
        start_time = time.time()
        attempt = 0
        
        logger.info("Waiting for Ollama to be ready...")
        
        while time.time() - start_time < timeout:
            attempt += 1
            elapsed = time.time() - start_time
            
            try:
                # Use ollama ps to check if server is responding
                # This is the most reliable way since ollama CLI is guaranteed to be present
                result = self.exec("ollama ps")
                
                logger.debug(f"Attempt {attempt} ({elapsed:.1f}s): exit_code={result.exit_code}")
                
                if result.exit_code == 0:
                    logger.info(f"✓ Ollama API ready after {elapsed:.1f}s")
                    return
                
                # Log output for debugging
                if result.output:
                    logger.debug(f"  Output: {result.output[:100]}")
                    
            except Exception as e:
                logger.debug(f"Attempt {attempt} ({elapsed:.1f}s): Exception: {e}")
            
            time.sleep(2)
        
        logger.error(f"✗ Ollama did not become ready within {timeout}s")
        logger.error(f"  Total attempts: {attempt}")
        
        raise TimeoutError(f"Ollama did not become ready within {timeout}s after {attempt} attempts")
    
    def get_connection_url(self) -> str:
        """Get Ollama API URL"""
        host = self.get_container_host_ip()
        port = self.get_exposed_port(self.port)
        return f"http://{host}:{port}"
    
    def get_container_ip(self) -> str:
        """
        Get the container's internal IP address in the Docker network
        
        This is the IP that other containers can use to communicate with this container.
        Uses docker inspect to get the actual container IP.
        
        Returns:
            str: Container's internal IP address (e.g., "172.17.0.4")
        """
        import subprocess
        
        container_id = self.get_wrapped_container().id
        
        try:
            # Get container IP using docker inspect
            result = subprocess.run(
                ["docker", "inspect", container_id, 
                 "--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            container_ip = result.stdout.strip()
            
            if not container_ip:
                logger.warning("Could not get container IP, falling back to host IP")
                return self.get_container_host_ip()
            
            return container_ip
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get container IP: {e}")
            return self.get_container_host_ip()
    
    def get_internal_url(self) -> str:
        """
        Get Ollama API URL using container's internal IP
        
        Use this URL when accessing Ollama from other containers in the same Docker network.
        For access from the host, use get_connection_url() instead.
        
        Returns:
            str: URL like "http://172.17.0.4:11434"
        """
        container_ip = self.get_container_ip()
        return f"http://{container_ip}:{self.port}"
    
    def pull_model(self) -> None:
        """Pull the specified model using ollama CLI inside container"""
        logger.info(f"Pulling model {self.model} in Ollama container...")
        
        try:
            # Use docker exec to pull model inside container
            result = self.exec(f"ollama pull {self.model}")
            
            if result.exit_code != 0:
                logger.error(f"Failed to pull model: {result.output}")
                raise Exception(f"Model pull failed with exit code {result.exit_code}")
            
            logger.info(f"Model {self.model} pulled successfully")
            
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            raise



@pytest.fixture(scope="session")
def ollama_container_session() -> Generator[OllamaContainer, None, None]:
    """
    Session-scoped Ollama container
    
    Starts once per test session, pulls tinyllama model.
    Use this for fast tests that can share the same model.
    
    Yields:
        OllamaContainer instance
    """
    import time
    
    logger.info("Starting Ollama container (session scope)...")
    
    container = OllamaContainer(model="tinyllama")
    container.start()
    
    # Get both URLs
    host_url = container.get_connection_url()  # For host access
    internal_url = container.get_internal_url()  # For container-to-container
    
    logger.info("Ollama container started and ready")
    logger.info(f"Host URL: {host_url}")
    logger.info(f"Internal URL: {internal_url}")
    print(f"\n🔗 Ollama URLs:", flush=True)
    print(f"   From host:       {host_url}", flush=True)
    print(f"   From containers: {internal_url}\n", flush=True)
    
    # Pull model once for all tests
    container.pull_model()
    
    logger.info("Ollama container ready (session scope)")
    
    # Test connection to ensure Ollama is accessible
    internal_url = container.get_internal_url()
    logger.info(f"Testing connection to Ollama at {internal_url}...")
    
    try:
        import subprocess
        import time
        
        # Give Ollama a moment after pull
        time.sleep(2)
        
        # Try to list models using curl (should work from any container)
        # We use subprocess because httpx might have issues with container networking
        result = subprocess.run(
            ["curl", "-s", "-m", "5", f"{internal_url}/api/tags"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "tinyllama" in result.stdout:
            logger.info("✓ Ollama connection test PASSED")
            print(f"✓ Ollama connection test PASSED - {internal_url}\n", flush=True)
        else:
            logger.warning(f"⚠ Ollama connection test FAILED: {result.stderr}")
            print(f"⚠ Ollama might not be accessible at {internal_url}\n", flush=True)
            print(f"   Error: {result.stderr}\n", flush=True)
    
    except Exception as e:
        logger.warning(f"⚠ Could not test Ollama connection: {e}")
        print(f"⚠ Connection test error: {e}\n", flush=True)
    
    # =============================================================================
    # MANUAL TESTING PAUSE - Comment out after testing
    # =============================================================================
    # Get real container info
    wrapped_container = container.get_wrapped_container()
    container_id = wrapped_container.id[:12]
    
    # Get URLs
    host_url = container.get_connection_url()  # For testing from host
    internal_url = container.get_internal_url()  # For app-to-ollama communication
    
    # Parse internal URL for display
    container_ip = container.get_container_ip()
    host = container.get_container_host_ip()
    mapped_port = container.get_exposed_port(container.port)
    
    print("\n" + "="*80, flush=True)
    print("🎯 OLLAMA READY FOR MANUAL TESTING", flush=True)
    print("="*80, flush=True)
    print(f"Container ID:     {container_id}", flush=True)
    print(f"Container IP:     {container_ip} (internal Docker network)", flush=True)
    print(f"Internal Port:    {container.port}", flush=True)
    print("", flush=True)
    print(f"URL for tests from HOST:", flush=True)
    print(f"  {host_url}", flush=True)
    print("", flush=True)
    print(f"URL for app (container-to-container):", flush=True)
    print(f"  {internal_url} ← USED BY TESTS", flush=True)
    print("", flush=True)
    print(f"Model: tinyllama", flush=True)
    print("", flush=True)
    print("Test commands (from host):", flush=True)
    print(f"  curl {host_url}/api/tags", flush=True)
    print(f"  curl {host_url}/api/generate -d '{{\"model\": \"tinyllama\", \"prompt\": \"Hello\", \"stream\": false}}'", flush=True)
    print("", flush=True)
    print(f"Test from inside container:", flush=True)
    print(f"  docker exec {container_id} ollama ps", flush=True)
    print(f"  docker exec {container_id} ollama list", flush=True)
    print("", flush=True)
    print(f"Interactive mode:", flush=True)
    print(f"  docker exec -it {container_id} ollama run tinyllama", flush=True)
    print("", flush=True)
    print("⏸️  PAUSING FOR 10 MINUTES (600s)...", flush=True)
    print("   Press Ctrl+C to skip and continue with tests", flush=True)
    print("="*80 + "\n", flush=True)
    
    #time.sleep(600)  # ⚠️ COMMENT THIS LINE AFTER MANUAL TESTING
    
    print("\n" + "="*80, flush=True)
    print("▶️  CONTINUING WITH TESTS...", flush=True)
    print("="*80 + "\n", flush=True)
    # =============================================================================
    
    yield container
    
    logger.info("Stopping Ollama container (session scope)...")
    container.stop()
    logger.info("Ollama container stopped (session scope)")


@pytest.fixture(scope="function")
def ollama_container_function() -> Generator[OllamaContainer, None, None]:
    """
    Function-scoped Ollama container
    
    Starts fresh for each test. Slower but provides isolation.
    Use this when tests need isolated LLM state.
    
    Yields:
        OllamaContainer instance
    """
    logger.info("Starting Ollama container (function scope)...")
    
    container = OllamaContainer(model="tinyllama")
    container.start()
    
    # Display connection info
    host = container.get_container_host_ip()
    mapped_port = container.get_exposed_port(container.port)
    url = f"http://{host}:{mapped_port}"
    
    logger.info("Ollama container started and ready")
    logger.info(f"Connection URL: {url}")
    
    # Pull model
    container.pull_model()
    
    logger.info("Ollama container ready (function scope)")
    
    yield container
    
    logger.info("Stopping Ollama container (function scope)...")
    container.stop()
    logger.info("Ollama container stopped (function scope)")


@pytest.fixture
def ollama_config(ollama_container_session) -> dict:
    """
    Ollama configuration for tests
    
    Returns dict with connection details for setting env vars.
    Uses the container's internal URL for container-to-container communication.
    
    Usage:
        def test_something(ollama_config):
            os.environ.update(ollama_config)
            # Now get_llm() will use this Ollama instance
    """
    # Use internal URL for container-to-container communication
    # This is the IP that the FastAPI app (running in another container) can reach
    internal_url = ollama_container_session.get_internal_url()
    
    # Log configuration for debugging
    logger.info(f"Configuring tests with Ollama at: {internal_url}")
    
    return {
        "LLM_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": internal_url,
        "OLLAMA_MODEL": ollama_container_session.model,
        "OLLAMA_TIMEOUT": "30"  # Shorter timeout for tests (30s instead of 300s)
    }