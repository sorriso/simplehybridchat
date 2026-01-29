"""
Path: backend/tests/integration/api/test_user_settings_routes_integration.py
Version: 3.0

Changes in v3.0:
- FIX: Use promptCustomization instead of systemPrompt (matches model)
- FIX: Updated default expectations to match settings_service defaults

Changes in v2.0:
- FIX: Use password_hash instead of password in login requests

Integration tests for user settings API
"""

import pytest
import hashlib
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password


def compute_password_hash(password: str) -> str:
    """Compute SHA256 hash of password (simulates frontend)"""
    return hashlib.sha256(password.encode()).hexdigest()


# Pre-computed SHA256 hash
TEST_PASS_HASH = compute_password_hash("testpass")


@pytest.fixture
def client(arango_container_function):
    """Test client with database"""
    from src.main import app
    
    db = arango_container_function
    
    if not db.collection_exists("users"):
        db.create_collection("users")
    if not db.collection_exists("settings"):
        db.create_collection("settings")
    
    yield TestClient(app)


@pytest.fixture
def test_user(arango_container_function):
    """Create test user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": hash_password(TEST_PASS_HASH),
        "role": "user",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password_hash": TEST_PASS_HASH
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetSettings:
    """Test GET /api/settings"""
    
    def test_get_settings_returns_defaults_for_new_user(self, client, auth_headers):
        """Test getting settings for user without existing settings"""
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Check defaults - field is promptCustomization not systemPrompt
        assert data["theme"] in ["light", "dark", "system", "auto"]
        assert data["language"] in ["en", "fr", "es", "de"]
        assert "promptCustomization" in data
    
    def test_get_settings_returns_stored_settings(self, client, auth_headers, test_user, arango_container_function):
        """Test getting previously stored settings"""
        db = arango_container_function
        
        # Store settings directly in DB
        db.create("settings", {
            "user_id": test_user["id"],
            "theme": "dark",
            "language": "fr",
            "prompt_customization": "Custom prompt"
        })
        
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "dark"
        assert data["language"] == "fr"
        assert data["promptCustomization"] == "Custom prompt"


class TestUpdateSettings:
    """Test PUT /api/settings"""
    
    def test_update_settings_full(self, client, auth_headers):
        """Test updating all settings"""
        response = client.put(
            "/api/settings",
            json={
                "theme": "dark",
                "language": "fr",
                "promptCustomization": "Updated prompt"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "dark"
        assert data["language"] == "fr"
        assert data["promptCustomization"] == "Updated prompt"
    
    def test_update_settings_partial(self, client, auth_headers):
        """Test updating only some settings"""
        # First set all settings
        client.put(
            "/api/settings",
            json={"theme": "light", "language": "en", "promptCustomization": "Original"},
            headers=auth_headers
        )
        
        # Then update only theme
        response = client.put(
            "/api/settings",
            json={"theme": "dark"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "dark"
        assert "language" in data
    
    def test_update_settings_empty_prompt(self, client, auth_headers):
        """Test updating with empty prompt customization"""
        response = client.put(
            "/api/settings",
            json={"promptCustomization": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["promptCustomization"] == ""


class TestSettingsPersistence:
    """Test settings persistence"""
    
    def test_settings_persist_across_requests(self, client, auth_headers):
        """Test that settings persist across requests"""
        # Update settings
        client.put(
            "/api/settings",
            json={"theme": "dark", "language": "de"},
            headers=auth_headers
        )
        
        # Get settings
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "dark"
        assert data["language"] == "de"
    
    def test_multiple_updates_overwrite_correctly(self, client, auth_headers):
        """Test that multiple updates overwrite correctly"""
        # First update
        client.put(
            "/api/settings",
            json={"theme": "light"},
            headers=auth_headers
        )
        
        # Second update
        client.put(
            "/api/settings",
            json={"theme": "dark"},
            headers=auth_headers
        )
        
        # Verify latest value
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "dark"


class TestSettingsValidation:
    """Test settings validation"""
    
    def test_theme_accepts_light(self, client, auth_headers):
        """Test theme accepts 'light'"""
        response = client.put(
            "/api/settings",
            json={"theme": "light"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_theme_accepts_dark(self, client, auth_headers):
        """Test theme accepts 'dark'"""
        response = client.put(
            "/api/settings",
            json={"theme": "dark"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_language_accepts_en(self, client, auth_headers):
        """Test language accepts 'en'"""
        response = client.put(
            "/api/settings",
            json={"language": "en"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_language_accepts_fr(self, client, auth_headers):
        """Test language accepts 'fr'"""
        response = client.put(
            "/api/settings",
            json={"language": "fr"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_language_accepts_es(self, client, auth_headers):
        """Test language accepts 'es'"""
        response = client.put(
            "/api/settings",
            json={"language": "es"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_language_accepts_de(self, client, auth_headers):
        """Test language accepts 'de'"""
        response = client.put(
            "/api/settings",
            json={"language": "de"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_prompt_accepts_long_text(self, client, auth_headers):
        """Test prompt customization accepts long text"""
        long_prompt = "A" * 1000
        response = client.put(
            "/api/settings",
            json={"promptCustomization": long_prompt},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["promptCustomization"] == long_prompt