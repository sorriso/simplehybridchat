# path: backend/tests/integration/conftest.py
# version: 2.0 - Added password_hash helpers and common fixtures

"""
Integration test fixtures

Changes in v2.0:
- ADDED: compute_password_hash() helper for SHA256 password hashing
- ADDED: Common constants for test passwords (TEST_PASSWORD, TEST_PASSWORD_HASH)
- ADDED: login_user() helper function for obtaining auth tokens
- Imports fixtures for ArangoDB, MinIO, and Ollama containers

All integration tests should use TEST_PASSWORD_HASH when calling /api/auth/login
instead of plaintext passwords, as the backend expects SHA256 hashed passwords.
"""

import hashlib
from typing import Tuple

# Import fixtures from project
from tests.integration.fixtures.arango_container import *
from tests.integration.fixtures.minio_container import *
from tests.integration.fixtures.ollama_container import *


# =============================================================================
# PASSWORD HASH HELPERS
# =============================================================================

def compute_password_hash(password: str) -> str:
    """
    Compute SHA256 hash of password (simulates frontend behavior)
    
    The frontend computes SHA256(password) before sending to backend.
    Backend expects password_hash field with 64-char hex string.
    
    Args:
        password: Plaintext password
        
    Returns:
        64-character hex string (SHA256 hash)
        
    Example:
        >>> compute_password_hash("password123")
        'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'
    """
    return hashlib.sha256(password.encode()).hexdigest()


# =============================================================================
# COMMON TEST CONSTANTS
# =============================================================================

# Standard test password used across integration tests
TEST_PASSWORD = "Password123"
TEST_PASSWORD_HASH = compute_password_hash(TEST_PASSWORD)

# Root user password
ROOT_PASSWORD = "RootPass123"
ROOT_PASSWORD_HASH = compute_password_hash(ROOT_PASSWORD)

# Admin password
ADMIN_PASSWORD = "AdminPass123"
ADMIN_PASSWORD_HASH = compute_password_hash(ADMIN_PASSWORD)

# Other user password
OTHER_PASSWORD = "OtherPass123"
OTHER_PASSWORD_HASH = compute_password_hash(OTHER_PASSWORD)


# =============================================================================
# LOGIN HELPER
# =============================================================================

def login_user(client, email: str, password_hash: str) -> Tuple[str, dict]:
    """
    Login user and return token with headers
    
    Helper function to authenticate a user and get authorization headers.
    Uses password_hash as expected by the backend API.
    
    Args:
        client: TestClient instance
        email: User email
        password_hash: SHA256 hash of password (use compute_password_hash())
        
    Returns:
        Tuple of (token, headers_dict)
        
    Raises:
        AssertionError: If login fails
        
    Example:
        token, headers = login_user(client, "user@example.com", TEST_PASSWORD_HASH)
        response = client.get("/api/protected", headers=headers)
    """
    response = client.post("/api/auth/login", json={
        "email": email,
        "password_hash": password_hash
    })
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    return token, headers


def create_test_user(db, email: str, password_hash: str, role: str = "user", name: str = None):
    """
    Create a test user in database with proper password hash
    
    Args:
        db: Database adapter
        email: User email
        password_hash: SHA256 hash of password
        role: User role (user, manager, root)
        name: User name (defaults to email prefix)
        
    Returns:
        Created user document
    """
    from datetime import datetime
    from src.core.security import hash_password
    
    if name is None:
        name = email.split("@")[0].replace(".", " ").title()
    
    # hash_password() applies bcrypt to the SHA256 hash
    bcrypt_hash = hash_password(password_hash)
    
    return db.create("users", {
        "name": name,
        "email": email,
        "password_hash": bcrypt_hash,
        "role": role,
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })