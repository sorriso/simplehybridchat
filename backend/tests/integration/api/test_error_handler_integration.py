"""
Path: backend/tests/integration/api/test_error_handler_integration.py
Version: 3

Integration tests for error handler middleware with FastAPI
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.middleware.error_handler import register_exception_handlers
from src.database.exceptions import NotFoundError, DuplicateKeyError
from src.storage.exceptions import FileNotFoundError as StorageFileNotFoundError


@pytest.fixture
def app():
    """Create FastAPI app with error handlers"""
    app = FastAPI()
    register_exception_handlers(app)
    
    # Add test endpoints
    @app.get("/test/not-found")
    def test_not_found():
        raise NotFoundError("Document not found")
    
    @app.get("/test/duplicate")
    def test_duplicate():
        raise DuplicateKeyError("Duplicate key error")
    
    @app.get("/test/storage-not-found")
    def test_storage_not_found():
        raise StorageFileNotFoundError("File not found")
    
    @app.get("/test/http-404")
    def test_http_404():
        raise HTTPException(status_code=404, detail="Resource not found")
    
    @app.get("/test/http-401")
    def test_http_401():
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    @app.get("/test/generic-error")
    def test_generic_error():
        raise Exception("Something went wrong")
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.integration
class TestErrorHandlerIntegration:
    """Test error handler with real FastAPI app"""
    
    def test_database_not_found_error(self, client):
        """Test NotFoundError handling"""
        response = client.get("/test/not-found")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "NOT_FOUND"
        assert "not found" in data["error"].lower()
    
    def test_database_duplicate_key_error(self, client):
        """Test DuplicateKeyError handling"""
        response = client.get("/test/duplicate")
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "DUPLICATE_KEY"
        assert "duplicate" in data["error"].lower()
    
    def test_storage_file_not_found_error(self, client):
        """Test storage FileNotFoundError handling"""
        response = client.get("/test/storage-not-found")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "FILE_NOT_FOUND"
        assert "not found" in data["error"].lower()
    
    def test_http_404_exception(self, client):
        """Test HTTP 404 exception"""
        response = client.get("/test/http-404")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "NOT_FOUND"
        assert data["error"] == "Resource not found"
    
    def test_http_401_exception(self, client):
        """Test HTTP 401 exception"""
        response = client.get("/test/http-401")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "UNAUTHORIZED"
        assert data["error"] == "Unauthorized"
    
    def test_generic_exception(self, client):
        """Test generic exception handling"""
        response = client.get("/test/generic-error")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "INTERNAL_ERROR"
        assert data["error"] == "Internal server error"
        # Should NOT expose internal error details
        assert "Something went wrong" not in data["error"]
    
    def test_validation_error(self, client, app):
        """Test validation error handling"""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            age: int
        
        @app.post("/test/validation")
        def test_validation(data: TestModel):
            return data
        
        # Send invalid data
        response = client.post("/test/validation", json={
            "name": "John",
            "age": "not-a-number"  # Invalid type
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["code"] == "VALIDATION_ERROR"
        assert "Validation failed" in data["error"]
        assert "details" in data
    
    def test_error_response_format_consistency(self, client):
        """Test that all errors have consistent format"""
        endpoints = [
            "/test/not-found",
            "/test/duplicate",
            "/test/storage-not-found",
            "/test/http-404",
            "/test/generic-error"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            
            # All errors should have these fields
            assert "success" in data
            assert "error" in data
            assert "code" in data
            
            # success should always be False
            assert data["success"] is False
            
            # error and code should be strings
            assert isinstance(data["error"], str)
            assert isinstance(data["code"], str)