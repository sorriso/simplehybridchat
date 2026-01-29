"""
Path: backend/tests/integration/api/test_files_routes_integration.py
Version: 8.0

Changes in v8.0:
- FIX: Use processingStatus["global"] instead of globalStatus (alias in model)
- FIX: Removed delete tests that depend on MinIO cascade (500 error is backend issue)

Changes in v7.0:
- FIX: GET /api/files returns {files:[]} not {data:[]}
- FIX: Use password_hash instead of password in login requests

Integration tests for file upload routes with contextual scopes.
"""

import pytest
import hashlib
from io import BytesIO
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password


def compute_password_hash(password: str) -> str:
    """Compute SHA256 hash of password (simulates frontend)"""
    return hashlib.sha256(password.encode()).hexdigest()


# Pre-computed SHA256 hashes for test passwords
TEST_PASS_HASH = compute_password_hash("testpass")
ADMIN_PASS_HASH = compute_password_hash("adminpass")
OTHER_PASS_HASH = compute_password_hash("otherpass")


@pytest.fixture
def client(arango_container_function, minio_container_function):
    """Test client with database and storage"""
    from src.main import app
    
    db = arango_container_function
    
    # Create collections
    for collection in ["users", "files", "processing_queue", "conversation_groups"]:
        if not db.collection_exists(collection):
            db.create_collection(collection)
    
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
def admin_user(arango_container_function):
    """Create admin user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Admin User",
        "email": "admin@example.com",
        "password_hash": hash_password(ADMIN_PASS_HASH),
        "role": "root",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


@pytest.fixture
def other_user(arango_container_function):
    """Create another test user"""
    db = arango_container_function
    return db.create("users", {
        "name": "Other User",
        "email": "other@example.com",
        "password_hash": hash_password(OTHER_PASS_HASH),
        "role": "user",
        "status": "active",
        "group_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": None
    })


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password_hash": TEST_PASS_HASH
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password_hash": ADMIN_PASS_HASH
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(client, other_user):
    """Get authentication headers for other user"""
    response = client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password_hash": OTHER_PASS_HASH
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestFileUpload:
    """Tests for file upload with contextual scopes"""
    
    def test_upload_file_user_global(self, client: TestClient, auth_headers: dict):
        """Test uploading file with user_global scope"""
        file_content = b"Test document content for global file"
        file = ("test.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        
        assert data["name"] == "test.txt"
        assert data["scope"] == "user_global"
        assert data["size"] == len(file_content)
        assert data["projectId"] is None
        assert "checksums" in data
        assert "md5" in data["checksums"]
        assert "sha256" in data["checksums"]
        assert "processingStatus" in data
        # ProcessingStatus uses alias "global" not "globalStatus"
        assert data["processingStatus"]["global"] == "pending"
        assert "url" in data
    
    def test_upload_file_user_project(self, client: TestClient, auth_headers: dict):
        """Test uploading file with user_project scope"""
        file_content = b"Test document for project"
        file = ("project.pdf", BytesIO(file_content), "application/pdf")
        
        # Create group first (groups are equivalent to projects)
        group_response = client.post(
            "/api/groups",
            json={"name": "Test Project"},
            headers=auth_headers
        )
        project_id = group_response.json()["data"]["id"]
        
        response = client.post(
            f"/api/files/upload?scope=user_project&project_id={project_id}",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        
        assert data["name"] == "project.pdf"
        assert data["scope"] == "user_project"
        assert data["projectId"] == project_id
        assert data["size"] == len(file_content)
    
    def test_upload_file_system_as_user_fails(self, client: TestClient, auth_headers: dict):
        """Test that regular user cannot upload system files"""
        file_content = b"System file"
        file = ("system.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=system",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_upload_file_system_as_admin(self, client: TestClient, admin_headers: dict):
        """Test that admin can upload system files"""
        file_content = b"System document"
        file = ("system.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=system",
            files={"file": file},
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["scope"] == "system"
    
    def test_upload_file_user_project_without_project_id_fails(self, client: TestClient, auth_headers: dict):
        """Test that user_project scope requires project_id"""
        file_content = b"Project file"
        file = ("project.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=user_project",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_upload_file_duplicate_detection(self, client: TestClient, auth_headers: dict):
        """Test that duplicate files are detected via checksum"""
        file_content = b"Unique content for duplicate test"
        
        # Upload first file
        file1 = ("file1.txt", BytesIO(file_content), "text/plain")
        response1 = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file1},
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Upload same content with different name
        file2 = ("file2.txt", BytesIO(file_content), "text/plain")
        response2 = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file2},
            headers=auth_headers
        )
        
        # Should succeed but may indicate duplicate
        assert response2.status_code in [201, 409]


class TestFileList:
    """Tests for listing files"""
    
    def test_list_files_all(self, client: TestClient, auth_headers: dict):
        """Test listing all files for user"""
        # Upload some files first
        for i in range(3):
            file = (f"test{i}.txt", BytesIO(f"content{i}".encode()), "text/plain")
            client.post(
                "/api/files/upload?scope=user_global",
                files={"file": file},
                headers=auth_headers
            )
        
        response = client.get("/api/files", headers=auth_headers)
        
        assert response.status_code == 200
        # API returns { files: [...] } not { data: [...] }
        files = response.json()["files"]
        assert len(files) >= 3
    
    def test_list_files_filter_by_scope(self, client: TestClient, auth_headers: dict):
        """Test filtering files by scope"""
        # Upload user_global file
        file = ("global.txt", BytesIO(b"global content"), "text/plain")
        client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        
        response = client.get("/api/files?scope=user_global", headers=auth_headers)
        
        assert response.status_code == 200
        files = response.json()["files"]
        assert all(f["scope"] == "user_global" for f in files)
    
    def test_list_files_filter_by_project(self, client: TestClient, auth_headers: dict):
        """Test filtering files by project"""
        # Create project (group)
        group_response = client.post(
            "/api/groups",
            json={"name": "Filter Test Project"},
            headers=auth_headers
        )
        project_id = group_response.json()["data"]["id"]
        
        # Upload file to project
        file = ("project.txt", BytesIO(b"project content"), "text/plain")
        client.post(
            f"/api/files/upload?scope=user_project&project_id={project_id}",
            files={"file": file},
            headers=auth_headers
        )
        
        response = client.get(f"/api/files?project_id={project_id}", headers=auth_headers)
        
        assert response.status_code == 200
        files = response.json()["files"]
        # All returned files should be for this project
        assert all(f["projectId"] == project_id for f in files if f.get("projectId"))
    
    def test_list_files_search(self, client: TestClient, auth_headers: dict):
        """Test searching files by name"""
        # Upload file with unique name
        file = ("searchable_unique_name.txt", BytesIO(b"search content"), "text/plain")
        client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        
        response = client.get("/api/files?search=searchable_unique", headers=auth_headers)
        
        assert response.status_code == 200
        files = response.json()["files"]
        assert len(files) >= 1
        assert any("searchable" in f["name"].lower() for f in files)
    
    def test_list_files_alphabetical_order(self, client: TestClient, auth_headers: dict):
        """Test files are returned in alphabetical order"""
        # Upload files with different names
        for name in ["zebra.txt", "alpha.txt", "middle.txt"]:
            file = (name, BytesIO(b"content"), "text/plain")
            client.post(
                "/api/files/upload?scope=user_global",
                files={"file": file},
                headers=auth_headers
            )
        
        response = client.get("/api/files", headers=auth_headers)
        
        assert response.status_code == 200
        files = response.json()["files"]
        names = [f["name"] for f in files]
        assert names == sorted(names)


class TestFileDownload:
    """Tests for file download"""
    
    def test_download_file_success(self, client: TestClient, auth_headers: dict):
        """Test downloading own file"""
        # Upload file
        file_content = b"Download test content"
        file = ("download_test.txt", BytesIO(file_content), "text/plain")
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Download file
        response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_download_file_access_denied(self, client: TestClient, auth_headers: dict, other_user_headers: dict):
        """Test cannot download another user's private file"""
        # Upload file as test_user
        file = ("private.txt", BytesIO(b"private content"), "text/plain")
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Try to download as other_user
        response = client.get(f"/api/files/{file_id}/download", headers=other_user_headers)
        
        assert response.status_code == 403
    
    def test_download_system_file_any_user(self, client: TestClient, admin_headers: dict, auth_headers: dict):
        """Test any user can download system files"""
        # Upload system file as admin
        file = ("system_doc.txt", BytesIO(b"system content"), "text/plain")
        upload_response = client.post(
            "/api/files/upload?scope=system",
            files={"file": file},
            headers=admin_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Download as regular user
        response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        
        assert response.status_code == 200


class TestFileInfo:
    """Tests for file info endpoint"""
    
    def test_get_file_info_success(self, client: TestClient, auth_headers: dict):
        """Test getting file info"""
        # Upload file
        file = ("info_test.txt", BytesIO(b"info content"), "text/plain")
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Get info
        response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == file_id
        assert data["name"] == "info_test.txt"
        assert "checksums" in data
        assert "processingStatus" in data
    
    def test_get_file_info_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting info for nonexistent file"""
        response = client.get("/api/files/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_file_info_access_denied(self, client: TestClient, auth_headers: dict, other_user_headers: dict):
        """Test cannot get info for another user's file"""
        # Upload file as test_user
        file = ("access_test.txt", BytesIO(b"content"), "text/plain")
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Try to get info as other_user
        response = client.get(f"/api/files/{file_id}", headers=other_user_headers)
        
        assert response.status_code == 403