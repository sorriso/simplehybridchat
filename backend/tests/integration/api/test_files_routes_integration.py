"""
Path: backend/tests/integration/api/test_files_routes_integration.py
Version: 2.0

Changes in v2.0:
- FRONTEND COMPATIBILITY: Updated auth_headers fixtures to use new login format
- Changed response.json()["data"]["accessToken"] → response.json()["token"]

Integration tests for files API with MinIO
"""

import pytest
from datetime import datetime
from io import BytesIO
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
    if not db.collection_exists("files"):
        db.create_collection("files")
    
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
    """Get authentication headers"""
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_headers(client, other_user):
    """Get authentication headers for other user"""
    response = client.post("/api/auth/login", json={
        "email": "other@example.com",
        "password": "otherpass"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestFileUpload:
    """Test file upload endpoint"""
    
    def test_upload_pdf_success(self, client, auth_headers, minio_container_function):
        """Test successful PDF upload"""
        # Create fake PDF
        file_content = b"%PDF-1.4 fake pdf content"
        file = ("document.pdf", BytesIO(file_content), "application/pdf")
        
        response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "document.pdf"
        assert data["type"] == "application/pdf"
        assert "url" in data
        assert "id" in data
    
    def test_upload_text_success(self, client, auth_headers, minio_container_function):
        """Test successful text file upload"""
        file_content = b"This is a test file"
        file = ("test.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "test.txt"
        assert data["size"] == len(file_content)
    
    def test_upload_image_success(self, client, auth_headers, minio_container_function):
        """Test successful image upload"""
        # Fake PNG header
        file_content = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        file = ("image.png", BytesIO(file_content), "image/png")
        
        response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "image.png"
        assert data["type"] == "image/png"
    
    def test_upload_invalid_type(self, client, auth_headers):
        """Test upload with invalid file type"""
        file_content = b"malicious executable"
        file = ("malware.exe", BytesIO(file_content), "application/octet-stream")
        
        response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_file_too_large(self, client, auth_headers):
        """Test upload with file too large"""
        # Create 11MB file
        file_content = b"x" * (11 * 1024 * 1024)
        file = ("huge.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        
        assert response.status_code == 413
        assert "too large" in response.json()["detail"]
    
    def test_upload_unauthenticated(self, client):
        """Test upload without authentication"""
        file_content = b"test content"
        file = ("test.txt", BytesIO(file_content), "text/plain")
        
        response = client.post(
            "/api/files/upload",
            files={"file": file}
        )
        
        assert response.status_code == 401


class TestFileList:
    """Test file listing endpoint"""
    
    def test_list_files_empty(self, client, auth_headers):
        """Test list files when user has no files"""
        response = client.get("/api/files", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_files_with_uploads(self, client, auth_headers, minio_container_function):
        """Test list files after uploading"""
        # Upload files
        file1 = ("doc1.txt", BytesIO(b"content1"), "text/plain")
        file2 = ("doc2.pdf", BytesIO(b"%PDF content"), "application/pdf")
        
        client.post("/api/files/upload", files={"file": file1}, headers=auth_headers)
        client.post("/api/files/upload", files={"file": file2}, headers=auth_headers)
        
        # List files
        response = client.get("/api/files", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        
        # Check files have URLs
        assert all("url" in f for f in data)
        assert all("name" in f for f in data)
    
    def test_list_files_only_own(self, client, auth_headers, other_headers, minio_container_function):
        """Test users only see their own files"""
        # User 1 uploads
        file1 = ("user1.txt", BytesIO(b"user1 content"), "text/plain")
        client.post("/api/files/upload", files={"file": file1}, headers=auth_headers)
        
        # User 2 uploads
        file2 = ("user2.txt", BytesIO(b"user2 content"), "text/plain")
        client.post("/api/files/upload", files={"file": file2}, headers=other_headers)
        
        # User 1 lists - should see only their file
        response = client.get("/api/files", headers=auth_headers)
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "user1.txt"


class TestFileDelete:
    """Test file deletion endpoint"""
    
    def test_delete_file_success(self, client, auth_headers, minio_container_function):
        """Test successful file deletion"""
        # Upload file
        file = ("delete_me.txt", BytesIO(b"delete this"), "text/plain")
        upload_response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # Delete file
        response = client.delete(f"/api/files/{file_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify file is gone
        list_response = client.get("/api/files", headers=auth_headers)
        files = list_response.json()["data"]
        assert not any(f["id"] == file_id for f in files)
    
    def test_delete_file_not_found(self, client, auth_headers, minio_container_function):
        """Test delete nonexistent file"""
        response = client.delete("/api/files/nonexistent", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_delete_file_not_owner(self, client, auth_headers, other_headers, minio_container_function):
        """Test delete file owned by another user"""
        # User 1 uploads
        file = ("private.txt", BytesIO(b"private"), "text/plain")
        upload_response = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        file_id = upload_response.json()["data"]["id"]
        
        # User 2 tries to delete
        response = client.delete(f"/api/files/{file_id}", headers=other_headers)
        
        assert response.status_code == 403
        assert "not file owner" in response.json()["detail"]
    
    def test_delete_unauthenticated(self, client):
        """Test delete without authentication"""
        response = client.delete("/api/files/some-id")
        
        assert response.status_code == 401


class TestFileEndToEnd:
    """Test complete file lifecycle"""
    
    def test_upload_list_delete_flow(self, client, auth_headers, minio_container_function):
        """Test complete workflow: upload â†’ list â†’ delete"""
        # 1. Upload file
        file = ("lifecycle.txt", BytesIO(b"test lifecycle"), "text/plain")
        upload_resp = client.post(
            "/api/files/upload",
            files={"file": file},
            headers=auth_headers
        )
        assert upload_resp.status_code == 201
        file_id = upload_resp.json()["data"]["id"]
        
        # 2. List files - should see the uploaded file
        list_resp = client.get("/api/files", headers=auth_headers)
        assert list_resp.status_code == 200
        files = list_resp.json()["data"]
        assert len(files) == 1
        assert files[0]["id"] == file_id
        
        # 3. Delete file
        delete_resp = client.delete(f"/api/files/{file_id}", headers=auth_headers)
        assert delete_resp.status_code == 204
        
        # 4. List again - should be empty
        list_resp2 = client.get("/api/files", headers=auth_headers)
        files2 = list_resp2.json()["data"]
        assert len(files2) == 0