"""
Path: backend/src/models/file.py
Version: 4.1

Changes in v4.1:
- ADDED: status field to FileResponse for frontend compatibility
- status is always "completed" for successfully uploaded files
- Maintains all v4.0 features (scopes, processing, checksums, etc.)

File models for upload/storage with contextual scopes and versioning.
"""

from typing import Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel


# Request models

class FileUploadRequest(BaseModel):
    """Request model for file upload with context"""
    scope: Literal["system", "user_global", "user_project"] = Field(
        default="user_global",
        description="File scope (system/user_global/user_project)"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID (required if scope=user_project)"
    )


class FileListRequest(BaseModel):
    """Request model for file listing with filters"""
    scope: Optional[Literal["system", "user_global", "user_project"]] = Field(
        default=None,
        description="Filter by scope"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Filter by project"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search in filename (partial match)"
    )


# Response models

class PhaseStatus(BaseModel):
    """Processing status for a single phase"""
    status: str = Field(description="Phase status (pending/processing/completed/failed)")
    active_version: Optional[str] = Field(
        default=None,
        description="Active version for this phase"
    )
    available_versions: list[str] = Field(
        default_factory=list,
        description="Available versions for this phase"
    )
    last_updated: Optional[str] = Field(
        default=None,
        description="Last update timestamp"
    )


class ProcessingStatus(BaseModel):
    """Overall processing status with phases"""
    global_status: str = Field(
        alias="global",
        description="Global processing status"
    )
    phases: dict[str, PhaseStatus] = Field(
        description="Status per phase"
    )
    last_updated: str = Field(
        description="Last update timestamp"
    )


class ChecksumInfo(BaseModel):
    """File checksums"""
    md5: str = Field(description="MD5 hash")
    sha256: str = Field(description="SHA256 hash")
    simhash: str = Field(description="SimHash for near-duplicate detection")


class FileResponse(CamelCaseModel):
    """
    File response with contextual scopes and versioning.
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - uploaded_at → uploadedAt
    - uploaded_by → uploadedBy
    - minio_path → minioPath
    - project_id → projectId
    - processing_status → processingStatus
    - active_configuration → activeConfiguration
    - promoted_at → promotedAt
    - promoted_by → promotedBy
    - duplicate_detected → duplicateDetected
    
    url is Optional to handle cases where presigned URL generation fails
    """
    id: str = Field(description="File identifier")
    name: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    type: str = Field(description="MIME type")
    minio_path: str = Field(description="Base path in MinIO")
    
    scope: str = Field(description="File scope (system/user_global/user_project)")
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID (if scope=user_project)"
    )
    
    uploaded_by: str = Field(description="User who uploaded the file")
    uploaded_at: str = Field(description="Upload timestamp")
    
    checksums: ChecksumInfo = Field(description="File checksums")
    processing_status: ProcessingStatus = Field(description="Processing status")
    
    active_configuration: dict[str, str] = Field(
        default_factory=dict,
        description="Active versions per phase"
    )
    
    promoted: bool = Field(
        default=False,
        description="Whether file was promoted to system"
    )
    promoted_at: Optional[str] = Field(
        default=None,
        description="Promotion timestamp"
    )
    promoted_by: Optional[str] = Field(
        default=None,
        description="User who promoted the file"
    )
    
    url: Optional[str] = Field(
        default=None,
        description="Presigned download URL"
    )
    duplicate_detected: Optional[bool] = Field(
        default=False,
        description="Whether duplicate was detected during upload"
    )
    
    # NEW in v4.1: Frontend compatibility
    status: Literal["completed"] = Field(
        default="completed",
        description="File upload status (always 'completed' for returned files)"
    )
    
    class Config:
        populate_by_name = True


class FileInDB(BaseModel):
    """
    File as stored in database.
    
    Maintains backward compatibility with v3 while adding v4 fields.
    """
    name: str
    size: int
    type: str
    minio_path: str  # Changed from object_name to minio_path in v4
    uploaded_at: datetime
    uploaded_by: str
    
    # v4 additions
    scope: str = "user_global"
    project_id: Optional[str] = None
    checksums: Optional[dict[str, str]] = None
    processing_status: Optional[dict[str, Any]] = None
    active_configuration: Optional[dict[str, str]] = None
    promoted: bool = False
    promoted_at: Optional[datetime] = None
    promoted_by: Optional[str] = None