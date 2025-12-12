"""
Path: backend/tests/integration/api/test_user_settings_routes_integration.py
Version: 1.0

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
    if not db.collection_exists("user_settings"):
        db.create_collection("user_settings")
    
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
        """Test get settings returns defaults when no settings exist"""
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should return defaults
        assert data["promptCustomization"] == ""
        assert data["theme"] == "light"
        assert data["language"] == "en"
    
    def test_get_settings_returns_stored_settings(self, client, auth_headers, arango_container_function):
        """Test get settings returns stored values"""
        # First, update settings
        update_response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "promptCustomization": "Be concise",
                "theme": "dark",
                "language": "fr"
            }
        )
        assert update_response.status_code == 200
        
        # Get settings
        response = client.get("/api/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should return stored values
        assert data["promptCustomization"] == "Be concise"
        assert data["theme"] == "dark"
        assert data["language"] == "fr"
    
    def test_get_settings_unauthenticated(self, client):
        """Test get settings without authentication"""
        response = client.get("/api/settings")
        
        assert response.status_code == 401


class TestUpdateSettings:
    """Test PUT /api/settings endpoint"""
    
    def test_update_settings_full(self, client, auth_headers):
        """Test update all settings fields"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "promptCustomization": "Be detailed",
                "theme": "dark",
                "language": "es"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Verify all fields updated
        assert data["promptCustomization"] == "Be detailed"
        assert data["theme"] == "dark"
        assert data["language"] == "es"
    
    def test_update_settings_partial(self, client, auth_headers):
        """Test partial update (only some fields)"""
        # First, set initial settings
        client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "promptCustomization": "Initial",
                "theme": "dark",
                "language": "fr"
            }
        )
        
        # Update only theme
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "light"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Only theme should change, others unchanged
        assert data["promptCustomization"] == "Initial"
        assert data["theme"] == "light"
        assert data["language"] == "fr"
    
    def test_update_settings_empty_prompt(self, client, auth_headers):
        """Test setting empty prompt_customization"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"promptCustomization": ""}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["promptCustomization"] == ""
    
    def test_update_settings_invalid_theme(self, client, auth_headers):
        """Test update with invalid theme value"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "invalid"}
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_update_settings_invalid_language(self, client, auth_headers):
        """Test update with invalid language value"""
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"language": "xx"}
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_update_settings_unauthenticated(self, client):
        """Test update without authentication"""
        response = client.put(
            "/api/settings",
            json={"theme": "dark"}
        )
        
        assert response.status_code == 401


class TestSettingsPersistence:
    """Test settings persistence across requests"""
    
    def test_settings_persist_across_requests(self, client, auth_headers):
        """Test settings are persisted and retrieved correctly"""
        # 1. Update settings
        update_resp = client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "promptCustomization": "Test persistence",
                "theme": "dark",
                "language": "de"
            }
        )
        assert update_resp.status_code == 200
        
        # 2. Get settings - should be same
        get_resp = client.get("/api/settings", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()["data"]
        
        assert data["promptCustomization"] == "Test persistence"
        assert data["theme"] == "dark"
        assert data["language"] == "de"
        
        # 3. Update partially
        update2_resp = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"language": "en"}
        )
        assert update2_resp.status_code == 200
        
        # 4. Get again - should have new language but keep others
        get2_resp = client.get("/api/settings", headers=auth_headers)
        data2 = get2_resp.json()["data"]
        
        assert data2["promptCustomization"] == "Test persistence"
        assert data2["theme"] == "dark"
        assert data2["language"] == "en"  # Updated
    
    def test_multiple_updates_overwrite_correctly(self, client, auth_headers):
        """Test multiple updates work correctly"""
        # Update 1
        client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "dark"}
        )
        
        # Update 2
        client.put(
            "/api/settings",
            headers=auth_headers,
            json={"theme": "light"}
        )
        
        # Get final state
        response = client.get("/api/settings", headers=auth_headers)
        data = response.json()["data"]
        
        # Should have latest value
        assert data["theme"] == "light"


class TestSettingsValidation:
    """Test input validation"""
    
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
        """Test prompt_customization accepts long text"""
        long_prompt = "Be very detailed and comprehensive. " * 50
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"promptCustomization": long_prompt}
        )
        assert response.status_code == 200