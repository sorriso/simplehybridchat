"""
Path: backend/src/models/file.py
Version: 3

Changes in v3:
- Made url Optional[str] for graceful degradation when URL generation fails
- Allows system to continue serving file metadata even if presigned URL fails

Changes in v2:
- FileResponse now inherits from CamelCaseModel
- Ensures camelCase serialization for frontend compatibility

File models for upload/storage
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.base import CamelCaseModel


class FileResponse(CamelCaseModel):
    """
    File response
    
    Inherits from CamelCaseModel for automatic camelCase serialization:
    - uploaded_at â†’ uploadedAt
    - uploaded_by â†’ uploadedBy
    
    url is Optional to handle cases where presigned URL generation fails
    """
    id: str
    name: str
    size: int
    type: str
    url: Optional[str] = None
    uploaded_at: datetime
    uploaded_by: str


class FileInDB(BaseModel):
    """File as stored in database"""
    name: str
    size: int
    type: str
    object_name: str  # MinIO object name
    uploaded_at: datetime
    uploaded_by: str