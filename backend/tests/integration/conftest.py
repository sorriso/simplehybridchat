# path: backend/tests/integration/conftest.py
# version: 1 - Import integration fixtures

"""
Integration test fixtures
Imports fixtures for ArangoDB, MinIO, and Ollama containers
"""

# Import fixtures from project
from tests.integration.fixtures.arango_container import *
from tests.integration.fixtures.minio_container import *
from tests.integration.fixtures.ollama_container import *