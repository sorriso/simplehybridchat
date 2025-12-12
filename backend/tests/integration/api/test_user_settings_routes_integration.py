"""
Path: backend/tests/integration/api/test_user_settings_routes_integration.py
Version: 1.4

Changes in v1.4:
- FIX: Fixed last remaining direct access at line 200
- Changed response.json()["theme"] to response.json()["data"]["theme"]
- Reason: Missed in v1.3 correction

Changes in v1.3:
- FIX: Access response data via response.json()["data"] not response.json()
- Reason: Settings routes wrap responses in SuccessResponse format {"data": {...}}
- Fixed 7 test methods to access correct data structure

Changes in v1.2:
- FIX: Changed has_collection() to collection_exists() (correct API)
- Reason: ArangoDatabaseAdapter uses collection_exists(), not has_collection()

Changes in v1.1:
- FIX: Changed collection_exists() to has_collection() (correct API)
- FIX: Changed "user_settings" to "settings" (matches repository v2)

Integration tests for user settings API
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password


@pytest.fixture
def client(arango_container_function):
    """Test client with database"""
    from src.main import app
    
    db = arango_container_function
    
    # Create collections
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
        "password_hash": hash_password("testpass"),
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
        "password": "testpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetSettings:
    """Test GET /api/settings endpoint"""
    
    def test_get_settings_returns_defaults_for_new_user(self, client, auth_headers):
        """Test getting settings returns defaults for new user"""
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "promptCustomization" in data
        assert "theme" in data
        assert "language" in data
        assert data["theme"] == "light"  # Default (changed from dark)
        assert data["language"] == "en"  # Default
    
    def test_get_settings_returns_stored_settings(self, client, auth_headers, test_user, arango_container_function):
        """Test getting settings returns stored values"""
        db = arango_container_function
        
        # Store settings
        db.create("settings", {
            "_key": test_user["id"],
            "prompt_customization": "Custom prompt",
            "theme": "light",
            "language": "fr"
        })
        
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["promptCustomization"] == "Custom prompt"
        assert data["theme"] == "light"
        assert data["language"] == "fr"


class TestUpdateSettings:
    """Test PUT /api/settings endpoint"""
    
    def test_update_settings_full(self, client, auth_headers):
        """Test updating all settings"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "promptCustomization": "New custom prompt",
                "theme": "light",
                "language": "fr"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["promptCustomization"] == "New custom prompt"
        assert data["theme"] == "light"
        assert data["language"] == "fr"
    
    def test_update_settings_partial(self, client, auth_headers):
        """Test updating partial settings"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "theme": "dark"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "dark"
        assert "language" in data  # Other fields still present
    
    def test_update_settings_empty_prompt(self, client, auth_headers):
        """Test updating with empty prompt"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "promptCustomization": "",
                "theme": "light"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["promptCustomization"] == ""


class TestSettingsPersistence:
    """Test settings persistence"""
    
    def test_settings_persist_across_requests(self, client, auth_headers):
        """Test settings persist between requests"""
        # Update settings
        client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "light", "language": "es"}
        )
        
        # Get settings in new request
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["theme"] == "light"
        assert data["language"] == "es"
    
    def test_multiple_updates_overwrite_correctly(self, client, auth_headers):
        """Test multiple updates overwrite previous values"""
        # First update
        client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "dark"}
        )
        
        # Second update
        client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "light"}
        )
        
        # Verify final state
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["data"]["theme"] == "light"


class TestSettingsValidation:
    """Test settings validation"""
    
    def test_theme_accepts_light(self, client, auth_headers):
        """Test theme accepts 'light'"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "light"}
        )
        assert response.status_code == 200
    
    def test_theme_accepts_dark(self, client, auth_headers):
        """Test theme accepts 'dark'"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "dark"}
        )
        assert response.status_code == 200
    
    def test_language_accepts_en(self, client, auth_headers):
        """Test language accepts 'en'"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"language": "en"}
        )
        assert response.status_code == 200
    
    def test_language_accepts_fr(self, client, auth_headers):
        """Test language accepts 'fr'"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"language": "fr"}
        )
        assert response.status_code == 200
    
    def test_language_accepts_es(self, client, auth_headers):
        """Test language accepts 'es'"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"language": "es"}
        )
        assert response.status_code == 200
    
    def test_language_accepts_de(self, client, auth_headers):
        """Test language accepts 'de'"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"language": "de"}
        )
        assert response.status_code == 200
    
    def test_prompt_accepts_long_text(self, client, auth_headers):
        """Test prompt accepts long text"""
        long_prompt = "A" * 1000
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"promptCustomization": long_prompt}
        )
        assert response.status_code == 200