"""
Path: backend/src/api/routes/files.py
Version: 4.0

File upload/management endpoints with contextual scopes and versioning.

Features:
- Contextual uploads (system/user_global/user_project)
- File listing with filters (scope, project, search)
- Download with access control
- Delete with cascade (MinIO + metadata + queue)
- Duplicate detection via checksums
"""

from typing import Optional, Literal
from fastapi import APIRouter, Depends, UploadFile, File, Query, Response, status
from fastapi.responses import StreamingResponse
from beartype import beartype

from src.models.file import (
    FileUploadRequest,
    FileListRequest,
    FileResponse
)
from src.models.responses import SuccessResponse
from src.services.file_service import FileService
from src.api.deps import get_database, UserFromRequest

router = APIRouter(prefix="/files", tags=["Files"])


# Response wrappers

class SingleFileResponse(SuccessResponse):
    """Single file response wrapper"""
    data: FileResponse


class FileListResponse(SuccessResponse):
    """File list response wrapper"""
    data: list[FileResponse]


@beartype
@router.post(
    "/upload",
    response_model=SingleFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file with context"
)
async def upload_file(
    current_user: UserFromRequest,
    file: UploadFile = File(...),
    scope: Literal["system", "user_global", "user_project"] = Query(
        default="user_global",
        description="File scope"
    ),
    project_id: Optional[str] = Query(
        default=None,
        description="Project ID (required if scope=user_project)"
    ),
    db = Depends(get_database)
):
    """
    Upload file with contextual scope.
    
    **Scopes:**
    - `system`: Global files accessible to all users (admin/manager only)
    - `user_global`: User files not associated with a project
    - `user_project`: Files associated with a specific project
    
    **Constraints:**
    - Maximum size: 50MB
    - Allowed types: PDF, TXT, CSV, JSON, MD, DOCX, PPTX, XLSX
    
    **Processing:**
    - File is stored in hierarchical MinIO structure
    - Checksums calculated (MD5, SHA256, SimHash)
    - Processing queue entry created for phase 02-data_extraction
    - Duplicate detection via SHA256 checksum
    
    **Returns:**
    - File metadata with processing status and presigned URL (valid 7 days)
    
    **Raises:**
    - 400: Invalid request (missing project_id, invalid file type)
    - 403: Permission denied (non-admin uploading to system)
    - 413: File too large
    - 500: Upload failed
    """
    service = FileService(db=db)
    result = service.upload_file(
        file=file,
        user_id=current_user["id"],
        user_role=current_user.get("role", "user"),
        scope=scope,
        project_id=project_id
    )
    
    message = "File uploaded successfully"
    if result.get("duplicate_detected"):
        message += " (duplicate detected)"
    
    return SingleFileResponse(
        data=FileResponse(**result),
        message=message
    )


@beartype
@router.get(
    "",
    response_model=FileListResponse,
    summary="List files with filters"
)
async def list_files(
    current_user: UserFromRequest,
    scope: Optional[Literal["system", "user_global", "user_project"]] = Query(
        default=None,
        description="Filter by scope"
    ),
    project_id: Optional[str] = Query(
        default=None,
        description="Filter by project"
    ),
    search: Optional[str] = Query(
        default=None,
        description="Search in filename (partial match, case-insensitive)"
    ),
    db = Depends(get_database)
):
    """
    List files with optional filters.
    
    **Access Control:**
    - System files: Visible to all users
    - User global files: Only visible to owner
    - User project files: Visible to project members (TODO: implement)
    
    **Filters:**
    - `scope`: Filter by file scope
    - `project_id`: Filter by project
    - `search`: Partial filename match (case-insensitive)
    
    **Sorting:**
    - Files are sorted alphabetically by name
    
    **Returns:**
    - List of file metadata with presigned URLs (valid 7 days)
    - Includes processing status per phase
    - Includes active version configuration
    """
    service = FileService(db=db)
    files = service.list_files(
        user_id=current_user["id"],
        user_role=current_user.get("role", "user"),
        scope=scope,
        project_id=project_id,
        search=search
    )
    
    return FileListResponse(
        data=[FileResponse(**f) for f in files],
        message=f"Found {len(files)} file(s)"
    )


@beartype
@router.get(
    "/{file_id}",
    response_model=SingleFileResponse,
    summary="Get file metadata"
)
async def get_file_info(
    file_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
):
    """
    Get file metadata with presigned URL.
    
    **Access Control:**
    - System files: Accessible to all users
    - User global files: Only accessible to owner
    - User project files: Accessible to project members
    
    **Returns:**
    - Complete file metadata
    - Processing status per phase
    - Active version configuration
    - Presigned download URL (valid 7 days)
    
    **Raises:**
    - 403: Access denied
    - 404: File not found
    """
    service = FileService(db=db)
    file_info = service.get_file_info(
        file_id=file_id,
        user_id=current_user["id"],
        user_role=current_user.get("role", "user")
    )
    
    return SingleFileResponse(
        data=FileResponse(**file_info),
        message="File retrieved successfully"
    )


@beartype
@router.get(
    "/{file_id}/download",
    summary="Download file",
    responses={
        200: {
            "description": "File content",
            "content": {"application/octet-stream": {}}
        }
    }
)
async def download_file(
    file_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
):
    """
    Download file content.
    
    **Access Control:**
    - System files: Accessible to all users
    - User global files: Only accessible to owner
    - User project files: Accessible to project members
    
    **Returns:**
    - File content as streaming response
    - Content-Disposition header with original filename
    - Appropriate Content-Type header
    
    **Raises:**
    - 403: Access denied
    - 404: File not found
    - 500: Download failed
    """
    service = FileService(db=db)
    content, filename, content_type = service.download_file(
        file_id=file_id,
        user_id=current_user["id"],
        user_role=current_user.get("role", "user")
    )
    
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@beartype
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
    Delete file and all associated data.
    
    **Deletes:**
    - File from MinIO (entire directory structure)
    - Metadata from ArangoDB
    - All processing queue entries
    
    **Access Control:**
    - Owner can delete their files
    - Admin/manager can delete any file
    
    **Raises:**
    - 403: Access denied (not owner or admin)
    - 404: File not found
    - 500: Deletion failed
    """
    service = FileService(db=db)
    service.delete_file(
        file_id=file_id,
        user_id=current_user["id"],
        user_role=current_user.get("role", "user")
    )
    # 204 No Content - no response body


@beartype
@router.get(
    "/projects/{project_id}",
    response_model=FileListResponse,
    summary="List project files"
)
async def list_project_files(
    project_id: str,
    current_user: UserFromRequest,
    search: Optional[str] = Query(
        default=None,
        description="Search in filename"
    ),
    db = Depends(get_database)
):
    """
    List all files for a specific project.
    
    Convenience endpoint for fetching project files.
    Equivalent to GET /files?scope=user_project&project_id={project_id}
    
    **Access Control:**
    - Only project members can view project files (TODO: implement)
    
    **Returns:**
    - List of project files sorted alphabetically
    - Includes system files (visible to all)
    
    **Raises:**
    - 403: Access denied (not project member)
    """
    service = FileService(db=db)
    files = service.list_files(
        user_id=current_user["id"],
        user_role=current_user.get("role", "user"),
        scope="user_project",
        project_id=project_id,
        search=search
    )
    
    return FileListResponse(
        data=[FileResponse(**f) for f in files],
        message=f"Found {len(files)} file(s) for project"
    )