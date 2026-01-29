"""
Path: backend/tests/unit/middleware/test_error_handler_unit.py
Version: 1.0

Tests for error handler middleware exception branches.
Coverage target: 78% → 100%
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from src.middleware.error_handler import (
    register_exception_handlers,
    database_exception_handler,
    storage_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from src.database.exceptions import (
    DatabaseException,
    NotFoundError,
    DuplicateKeyError,
    ConnectionError as DBConnectionError,
)
from src.storage.exceptions import (
    StorageException,
    FileNotFoundError as StorageFileNotFoundError,
    BucketNotFoundError,
)


@pytest.fixture
def mock_request():
    """Provide mock request object"""
    request = MagicMock(spec=Request)
    request.url.path = '/api/test'
    request.method = 'GET'
    return request


class TestDatabaseExceptionHandler:
    """Test database exception handler"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found_error_returns_404(self, mock_request):
        """Test NotFoundError returns 404"""
        exc = NotFoundError("Document not found")
        
        response = await database_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_key_error_returns_409(self, mock_request):
        """Test DuplicateKeyError returns 409"""
        exc = DuplicateKeyError("Duplicate key violation")
        
        response = await database_exception_handler(mock_request, exc)
        
        assert response.status_code == 409
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_db_connection_error_returns_503(self, mock_request):
        """Test DBConnectionError returns 503"""
        exc = DBConnectionError("Connection refused")
        
        response = await database_exception_handler(mock_request, exc)
        
        assert response.status_code == 503
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generic_database_exception_returns_500(self, mock_request):
        """Test generic DatabaseException returns 500"""
        exc = DatabaseException("Unknown database error")
        
        response = await database_exception_handler(mock_request, exc)
        
        assert response.status_code == 500


class TestStorageExceptionHandler:
    """Test storage exception handler"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_file_not_found_returns_404(self, mock_request):
        """Test FileNotFoundError returns 404"""
        exc = StorageFileNotFoundError("File not found")
        
        response = await storage_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bucket_not_found_returns_404(self, mock_request):
        """Test BucketNotFoundError returns 404"""
        exc = BucketNotFoundError("Bucket not found")
        
        response = await storage_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generic_storage_exception_returns_500(self, mock_request):
        """Test generic StorageException returns 500"""
        exc = StorageException("Unknown storage error")
        
        response = await storage_exception_handler(mock_request, exc)
        
        assert response.status_code == 500


class TestHTTPExceptionHandler:
    """Test HTTP exception handler"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_400_bad_request(self, mock_request):
        """Test 400 Bad Request"""
        exc = StarletteHTTPException(status_code=400, detail="Bad request")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 400
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_401_unauthorized(self, mock_request):
        """Test 401 Unauthorized"""
        exc = StarletteHTTPException(status_code=401, detail="Invalid token")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 401
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_403_forbidden(self, mock_request):
        """Test 403 Forbidden"""
        exc = StarletteHTTPException(status_code=403, detail="Access denied")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 403
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_404_not_found(self, mock_request):
        """Test 404 Not Found"""
        exc = StarletteHTTPException(status_code=404, detail="Resource not found")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self, mock_request):
        """Test 405 Method Not Allowed"""
        exc = StarletteHTTPException(status_code=405, detail="Method not allowed")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 405
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_409_conflict(self, mock_request):
        """Test 409 Conflict"""
        exc = StarletteHTTPException(status_code=409, detail="Resource conflict")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 409
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_422_unprocessable_entity(self, mock_request):
        """Test 422 Unprocessable Entity"""
        exc = StarletteHTTPException(status_code=422, detail="Validation failed")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_429_too_many_requests(self, mock_request):
        """Test 429 Too Many Requests"""
        exc = StarletteHTTPException(status_code=429, detail="Rate limit exceeded")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 429
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_500_internal_server_error(self, mock_request):
        """Test 500 Internal Server Error"""
        exc = StarletteHTTPException(status_code=500, detail="Internal error")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_503_service_unavailable(self, mock_request):
        """Test 503 Service Unavailable"""
        exc = StarletteHTTPException(status_code=503, detail="Service unavailable")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 503
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_status_code(self, mock_request):
        """Test unknown status code passes through"""
        exc = StarletteHTTPException(status_code=418, detail="I'm a teapot")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 418


class TestValidationExceptionHandler:
    """Test validation exception handler"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_single_field_validation_error(self, mock_request):
        """Test single field validation error"""
        # Create mock validation error
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {
                'loc': ('body', 'email'),
                'msg': 'value is not a valid email address',
                'type': 'value_error.email'
            }
        ]
        
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_fields_validation_error(self, mock_request):
        """Test multiple fields validation error"""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {
                'loc': ('body', 'email'),
                'msg': 'field required',
                'type': 'value_error.missing'
            },
            {
                'loc': ('body', 'password'),
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
        
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422


class TestGeneralExceptionHandler:
    """Test general exception handler"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_general_exception_returns_500(self, mock_request):
        """Test general exception returns 500"""
        exc = Exception("Unexpected error")
        
        response = await general_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_runtime_error_returns_500(self, mock_request):
        """Test RuntimeError returns 500"""
        exc = RuntimeError("Runtime error")
        
        response = await general_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_value_error_returns_500(self, mock_request):
        """Test ValueError returns 500"""
        exc = ValueError("Invalid value")
        
        response = await general_exception_handler(mock_request, exc)
        
        assert response.status_code == 500


class TestRegisterExceptionHandlers:
    """Test exception handler registration"""
    
    @pytest.mark.unit
    def test_register_all_handlers(self):
        """Test all exception handlers are registered"""
        app = FastAPI()
        
        register_exception_handlers(app)
        
        # Check that handlers are registered
        assert DatabaseException in app.exception_handlers
        assert StorageException in app.exception_handlers
        assert StarletteHTTPException in app.exception_handlers
        assert RequestValidationError in app.exception_handlers
        assert Exception in app.exception_handlers