"""
Path: src/middleware/error_handler.py
Version: 2

Global error handling middleware
Standardizes error responses across the application
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.database.exceptions import (
    DatabaseException,
    NotFoundError,
    DuplicateKeyError,
    ConnectionError as DBConnectionError
)
from src.storage.exceptions import (
    StorageException,
    FileNotFoundError,
    BucketNotFoundError
)

logger = logging.getLogger(__name__)


async def database_exception_handler(request: Request, exc: DatabaseException) -> JSONResponse:
    """
    Handle database exceptions
    
    Converts database exceptions to standardized JSON responses.
    """
    logger.error(f"Database error on {request.url}: {exc}")
    
    # Determine status code based on exception type
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        code = "NOT_FOUND"
    elif isinstance(exc, DuplicateKeyError):
        status_code = status.HTTP_409_CONFLICT
        code = "DUPLICATE_KEY"
    elif isinstance(exc, DBConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        code = "DATABASE_UNAVAILABLE"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = "DATABASE_ERROR"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": str(exc),
            "code": code
        }
    )


async def storage_exception_handler(request: Request, exc: StorageException) -> JSONResponse:
    """
    Handle storage exceptions
    
    Converts storage exceptions to standardized JSON responses.
    """
    logger.error(f"Storage error on {request.url}: {exc}")
    
    # Determine status code based on exception type
    if isinstance(exc, FileNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        code = "FILE_NOT_FOUND"
    elif isinstance(exc, BucketNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        code = "BUCKET_NOT_FOUND"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = "STORAGE_ERROR"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": str(exc),
            "code": code
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions
    
    Standardizes FastAPI HTTP exceptions.
    """
    logger.warning(f"HTTP {exc.status_code} on {request.url}: {exc.detail}")
    
    # Map status codes to error codes
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    
    code = code_map.get(exc.status_code, "ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "code": code
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors
    
    Converts Pydantic validation errors to user-friendly format.
    """
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "code": "VALIDATION_ERROR",
            "details": {
                "errors": errors,
                "fields": [err["loc"][-1] for err in exc.errors()]
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions
    
    Catch-all for unexpected errors. Logs full error but returns
    generic message to client (don't expose internal details).
    """
    logger.exception(f"Unhandled exception on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app
    
    Call this in main.py during app initialization.
    
    Example:
        from src.middleware.error_handler import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
    """
    # Database exceptions
    app.add_exception_handler(DatabaseException, database_exception_handler)
    app.add_exception_handler(NotFoundError, database_exception_handler)
    app.add_exception_handler(DuplicateKeyError, database_exception_handler)
    app.add_exception_handler(DBConnectionError, database_exception_handler)
    
    # Storage exceptions
    app.add_exception_handler(StorageException, storage_exception_handler)
    app.add_exception_handler(FileNotFoundError, storage_exception_handler)
    app.add_exception_handler(BucketNotFoundError, storage_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Catch-all
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered")