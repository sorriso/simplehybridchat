"""
Path: backend/src/api/routes/files.py
Version: 5

Changes in v5:
- BUGFIX: Removed response_model from DELETE endpoint
- 204 No Content must not have response body (HTTP spec violation)
- This was causing all integration tests to fail

Changes in v4:
- Implemented actual file upload/list/delete using FileService
- Removed 501 stubs
- Uses MinIO storage via FileService

Changes in v3:
- Fixed parameter order in upload_file: current_user before file
- Python requires parameters without defaults before those with defaults

Changes in v2:
- Fixed UserFromRequest usage: removed duplicate Depends()

File upload/management endpoints
"""

from fastapi import APIRouter, Depends, UploadFile, File, status
from typing import List

from src.models.file import FileResponse
from src.models.responses import EmptyResponse, SuccessResponse
from src.services.file_service import FileService
from src.api.deps import get_database, UserFromRequest

router = APIRouter(prefix="/files", tags=["Files"])


# Response wrappers
class SingleFileResponse(SuccessResponse):
    """Single file response wrapper"""
    data: FileResponse


class FileListResponse(SuccessResponse):
    """File list response wrapper"""
    data: List[FileResponse]


@router.post(
    "/upload",
    response_model=SingleFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file"
)
async def upload_file(
    current_user: UserFromRequest,
    file: UploadFile = File(...),
    db = Depends(get_database)
):
    """
    Upload file to MinIO storage
    
    Constraints:
    - Maximum size: 10MB
    - Allowed types: PDF, TXT, CSV, JSON, MD, PNG, JPEG, GIF, WebP
    
    Returns:
    - File metadata with presigned URL (valid 7 days)
    
    Raises:
    - 400: Invalid file type
    - 413: File too large
    - 500: Upload failed
    """
    service = FileService(db=db)
    result = service.upload_file(file, current_user["id"])
    
    return SingleFileResponse(
        data=FileResponse(**result),
        message="File uploaded successfully"
    )


@router.get(
    "",
    response_model=FileListResponse,
    summary="List user's files"
)
async def list_files(
    current_user: UserFromRequest,
    db = Depends(get_database)
):
    """
    List all files uploaded by the current user
    
    Returns:
    - List of file metadata with presigned URLs (valid 7 days)
    """
    service = FileService(db=db)
    files = service.list_files(current_user["id"])
    
    return FileListResponse(
        data=[FileResponse(**f) for f in files]
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file"
)
async def delete_file(
    file_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
):
    """
    Delete file from storage
    
    Deletes both:
    - File from MinIO storage
    - Metadata from database
    
    Only the file owner can delete the file.
    
    Raises:
    - 404: File not found
    - 403: Not file owner
    - 500: Deletion failed
    """
    service = FileService(db=db)
    service.delete_file(file_id, current_user["id"])
    # 204 No Content - no response body