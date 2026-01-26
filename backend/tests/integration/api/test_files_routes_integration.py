"""
Path: backend/tests/integration/api/test_files_routes_integration.py
Version: 4.4

Changes in v4.4:
- FIX: Added conversation_groups collection in client fixture
- Needed by group creation tests (projects replaced by groups)

Changes in v4.3:
- FIX: Replace /api/projects with /api/groups (groups are equivalent to projects)
- Remove "description" field from group creation (not in GroupCreate model)

Changes in v4.2:
- Added missing fixtures: client, test_user, admin_user, auth_headers, admin_headers, other_user_headers
- Fixtures use arango_container_function and minio_container_function auto-imported via conftest

Changes in v4.1:
- Fixed import: removed tests.integration.conftest import
- Fixtures arango_container_function and minio_container_function are auto-imported via conftest.py

Integration tests for file upload routes with contextual scopes.

Tests:
- Upload files with different scopes (system/user_global/user_project)
- List files with filters (scope, project, search)
- Download files with access control
- Delete files with cascade
- Permission checks (system upload requires admin)
- Duplicate detection via checksums
"""

import pytest
from io import BytesIO
from datetime import datetime
from fastapi.testclient import TestClient

from src.core.security import hash_password


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
        "password_hash": hash_password("testpass"),
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
        "password_hash": hash_password("adminpass"),
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
        "password_hash": hash_password("otherpass"),
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
        "password": "testpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(client, other_user):
    """Get authentication headers for other user"""
    response = client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password": "otherpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestFileUpload:
    """Tests for file upload with contextual scopes"""
    
    def test_upload_file_user_global(self, client: TestClient, auth_headers: dict):
        """Test uploading file with user_global scope"""
        # Create test file
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
        assert data["project_id"] is None
        assert "checksums" in data
        assert "md5" in data["checksums"]
        assert "sha256" in data["checksums"]
        assert "simhash" in data["checksums"]
        assert data["processing_status"]["global_status"] == "pending"
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
        assert data["project_id"] == project_id
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
        assert "admin or manager" in response.json()["detail"].lower()
    
    def test_upload_file_system_as_admin(self, client: TestClient, admin_headers: dict):
        """Test that admin can upload system files"""
        file_content = b"System file content"
        file = ("system.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=system",
            files={"file": file},
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        
        assert data["scope"] == "system"
        assert data["project_id"] is None
    
    def test_upload_file_user_project_without_project_id_fails(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that user_project scope requires project_id"""
        file_content = b"Project file"
        file = ("test.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=user_project",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "project_id required" in response.json()["detail"].lower()
    
    def test_upload_file_duplicate_detection(self, client: TestClient, auth_headers: dict):
        """Test duplicate detection via SHA256 checksum"""
        file_content = b"Duplicate content test"
        file1 = ("file1.txt", BytesIO(file_content), "text/plain")
        
        # Upload first file
        response1 = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file1},
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Upload duplicate
        file2 = ("file2.txt", BytesIO(file_content), "text/plain")
        response2 = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file2},
            headers=auth_headers
        )
        
        assert response2.status_code == 201
        data2 = response2.json()["data"]
        assert data2.get("duplicate_detected") is True
    
    def test_upload_file_too_large_fails(self, client: TestClient, auth_headers: dict):
        """Test that files larger than 50MB are rejected"""
        # Create 51MB file
        large_content = b"x" * (51 * 1024 * 1024)
        file = ("large.txt", BytesIO(large_content), "text/plain")
        
        response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()
    
    def test_upload_file_invalid_type_fails(self, client: TestClient, auth_headers: dict):
        """Test that invalid file types are rejected"""
        file_content = b"executable content"
        file = ("test.exe", BytesIO(file_content), "application/x-msdownload")
        
        response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()


class TestFileList:
    """Tests for file listing with filters"""
    
    def test_list_files_all(self, client: TestClient, auth_headers: dict):
        """Test listing all accessible files"""
        # Upload test files
        file1 = ("file1.txt", BytesIO(b"Content 1"), "text/plain")
        file2 = ("file2.txt", BytesIO(b"Content 2"), "text/plain")
        
        client.post("/api/files/upload?scope=user_global", files={"file": file1}, headers=auth_headers)
        client.post("/api/files/upload?scope=user_global", files={"file": file2}, headers=auth_headers)
        
        response = client.get("/api/files", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 2
        assert all(f["url"] is not None for f in data)
    
    def test_list_files_filter_by_scope(self, client: TestClient, auth_headers: dict):
        """Test filtering files by scope"""
        # Upload files with different scopes
        file1 = ("global.txt", BytesIO(b"Global"), "text/plain")
        client.post("/api/files/upload?scope=user_global", files={"file": file1}, headers=auth_headers)
        
        # Create project and upload project file
        project_response = client.post(
            "/api/groups",
            json={"name": "Filter Test"},
            headers=auth_headers
        )
        project_id = project_response.json()["data"]["id"]
        
        file2 = ("project.txt", BytesIO(b"Project"), "text/plain")
        client.post(
            f"/api/files/upload?scope=user_project&project_id={project_id}",
            files={"file": file2},
            headers=auth_headers
        )
        
        # Filter by user_global
        response = client.get("/api/files?scope=user_global", headers=auth_headers)
        assert response.status_code == 200
        global_files = response.json()["data"]
        assert all(f["scope"] == "user_global" for f in global_files)
        
        # Filter by user_project
        response = client.get("/api/files?scope=user_project", headers=auth_headers)
        assert response.status_code == 200
        project_files = response.json()["data"]
        assert all(f["scope"] == "user_project" for f in project_files)
    
    def test_list_files_filter_by_project(self, client: TestClient, auth_headers: dict):
        """Test filtering files by project_id"""
        # Create two projects
        project1 = client.post(
            "/api/groups",
            json={"name": "Project 1"},
            headers=auth_headers
        ).json()["data"]["id"]
        
        project2 = client.post(
            "/api/groups",
            json={"name": "Project 2"},
            headers=auth_headers
        ).json()["data"]["id"]
        
        # Upload files to different projects
        file1 = ("p1.txt", BytesIO(b"P1"), "text/plain")
        client.post(
            f"/api/files/upload?scope=user_project&project_id={project1}",
            files={"file": file1},
            headers=auth_headers
        )
        
        file2 = ("p2.txt", BytesIO(b"P2"), "text/plain")
        client.post(
            f"/api/files/upload?scope=user_project&project_id={project2}",
            files={"file": file2},
            headers=auth_headers
        )
        
        # Filter by project1
        response = client.get(f"/api/files?project_id={project1}", headers=auth_headers)
        assert response.status_code == 200
        files = response.json()["data"]
        assert all(f["project_id"] == project1 for f in files if f["scope"] == "user_project")
    
    def test_list_files_search(self, client: TestClient, auth_headers: dict):
        """Test searching files by partial name match"""
        # Upload files with different names
        file1 = ("report_january.pdf", BytesIO(b"Jan"), "application/pdf")
        file2 = ("report_february.pdf", BytesIO(b"Feb"), "application/pdf")
        file3 = ("summary.txt", BytesIO(b"Sum"), "text/plain")
        
        client.post("/api/files/upload?scope=user_global", files={"file": file1}, headers=auth_headers)
        client.post("/api/files/upload?scope=user_global", files={"file": file2}, headers=auth_headers)
        client.post("/api/files/upload?scope=user_global", files={"file": file3}, headers=auth_headers)
        
        # Search for "report"
        response = client.get("/api/files?search=report", headers=auth_headers)
        assert response.status_code == 200
        files = response.json()["data"]
        assert all("report" in f["name"].lower() for f in files)
        assert len([f for f in files if "report" in f["name"].lower()]) >= 2
    
    def test_list_files_alphabetical_order(self, client: TestClient, auth_headers: dict):
        """Test that files are returned in alphabetical order"""
        # Upload files in random order
        files = [
            ("zebra.txt", b"Z"),
            ("alpha.txt", b"A"),
            ("beta.txt", b"B")
        ]
        
        for name, content in files:
            file = (name, BytesIO(content), "text/plain")
            client.post("/api/files/upload?scope=user_global", files={"file": file}, headers=auth_headers)
        
        response = client.get("/api/files", headers=auth_headers)
        assert response.status_code == 200
        file_names = [f["name"] for f in response.json()["data"]]
        
        # Find our test files
        test_files = [name for name in file_names if name in ["zebra.txt", "alpha.txt", "beta.txt"]]
        assert test_files == sorted(test_files)
    
    def test_list_project_files_endpoint(self, client: TestClient, auth_headers: dict):
        """Test dedicated project files endpoint"""
        # Create project
        project_response = client.post(
            "/api/groups",
            json={"name": "Endpoint Test"},
            headers=auth_headers
        )
        project_id = project_response.json()["data"]["id"]
        
        # Upload project file
        file = ("project_doc.pdf", BytesIO(b"Doc"), "application/pdf")
        client.post(
            f"/api/files/upload?scope=user_project&project_id={project_id}",
            files={"file": file},
            headers=auth_headers
        )
        
        # Use dedicated endpoint
        response = client.get(f"/api/files/projects/{project_id}", headers=auth_headers)
        
        assert response.status_code == 200
        files = response.json()["data"]
        assert len(files) >= 1
        assert any(f["project_id"] == project_id for f in files)


class TestFileDownload:
    """Tests for file download with access control"""
    
    def test_download_file_success(self, client: TestClient, auth_headers: dict):
        """Test downloading file"""
        file_content = b"Test content for download"
        file = ("download_test.txt", BytesIO(file_content), "text/plain")
        
        # Upload file
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Download file
        response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.content == file_content
        assert response.headers["content-type"] == "text/plain"
        assert "attachment" in response.headers.get("content-disposition", "")
    
    def test_download_file_access_denied(self, client: TestClient, auth_headers: dict, other_user_headers: dict):
        """Test that users cannot download other users' files"""
        file_content = b"Private content"
        file = ("private.txt", BytesIO(file_content), "text/plain")
        
        # Upload file as user1
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Try to download as user2
        response = client.get(f"/api/files/{file_id}/download", headers=other_user_headers)
        
        assert response.status_code == 403
    
    def test_download_system_file_any_user(self, client: TestClient, admin_headers: dict, auth_headers: dict):
        """Test that any user can download system files"""
        file_content = b"Public system file"
        file = ("system_public.txt", BytesIO(file_content), "text/plain")
        
        # Upload as admin with system scope
        upload_response = client.post(
            "/api/files/upload?scope=system",
            files={"file": file},
            headers=admin_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Download as regular user
        response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.content == file_content


class TestFileDelete:
    """Tests for file deletion with cascade"""
    
    def test_delete_file_success(self, client: TestClient, auth_headers: dict):
        """Test deleting file"""
        file_content = b"File to delete"
        file = ("delete_test.txt", BytesIO(file_content), "text/plain")
        
        # Upload file
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Delete file
        response = client.delete(f"/api/files/{file_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify file is deleted
        get_response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_file_not_owner_fails(self, client: TestClient, auth_headers: dict, other_user_headers: dict):
        """Test that non-owner cannot delete file"""
        file_content = b"Protected file"
        file = ("protected.txt", BytesIO(file_content), "text/plain")
        
        # Upload as user1
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Try to delete as user2
        response = client.delete(f"/api/files/{file_id}", headers=other_user_headers)
        assert response.status_code == 403
    
    def test_delete_file_admin_can_delete_any(self, client: TestClient, auth_headers: dict, admin_headers: dict):
        """Test that admin can delete any file"""
        file_content = b"User file"
        file = ("user_file.txt", BytesIO(file_content), "text/plain")
        
        # Upload as regular user
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Delete as admin
        response = client.delete(f"/api/files/{file_id}", headers=admin_headers)
        assert response.status_code == 204


class TestFileInfo:
    """Tests for file metadata retrieval"""
    
    def test_get_file_info_success(self, client: TestClient, auth_headers: dict):
        """Test getting file metadata"""
        file_content = b"Info test content"
        file = ("info_test.txt", BytesIO(file_content), "text/plain")
        
        # Upload file
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Get file info
        response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == file_id
        assert data["name"] == "info_test.txt"
        assert "processing_status" in data
        assert "checksums" in data
        assert "url" in data
    
    def test_get_file_info_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting info for non-existent file"""
        response = client.get("/api/files/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_file_info_access_denied(self, client: TestClient, auth_headers: dict, other_user_headers: dict):
        """Test that users cannot access other users' file info"""
        file_content = b"Private info"
        file = ("private_info.txt", BytesIO(file_content), "text/plain")
        
        # Upload as user1
        upload_response = client.post(
            "/api/files/upload?scope=user_global",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Try to get info as user2
        response = client.get(f"/api/files/{file_id}", headers=other_user_headers)
        assert response.status_code == 403