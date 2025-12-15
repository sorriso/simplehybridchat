"""
Path: backend/src/repositories/user_repository.py
Version: 3

Changes in v3:
- ADDED: Email validation (must contain @ and domain with TLD)
- Prevents invalid emails like "root@localhost" (no TLD)
- Raises ValueError on invalid email format

Changes in v2:
- Modified user["_key"] → user["id"]
- Repository now uses 'id' from adapter consistently

User repository for data access
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from src.repositories.base import BaseRepository
from src.database.interface import IDatabase
from src.database.exceptions import NotFoundError, DuplicateKeyError


class UserRepository(BaseRepository):
    """
    User repository
    
    Handles user data access operations.
    Extends BaseRepository with user-specific methods.
    """
    
    # Email regex: must have @ and domain with TLD
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, db: Optional[IDatabase] = None):
        """Initialize with users collection"""
        super().__init__(collection="users", db=db)
    
    @classmethod
    def validate_email(cls, email: str) -> None:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Raises:
            ValueError: If email format is invalid
        """
        if not email or not isinstance(email, str):
            raise ValueError("Email is required")
        
        if not cls.EMAIL_REGEX.match(email):
            raise ValueError(
                f"Invalid email format: {email}. "
                "Email must contain @ and a valid domain with TLD (e.g., user@example.com)"
            )
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User dict or None if not found
        """
        return self.db.find_one(self.collection, {"email": email})
    
    def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            exclude_id: Optional user ID to exclude from check (for updates)
            
        Returns:
            True if email exists
        """
        filters = {"email": email}
        users = self.db.get_all(self.collection, filters=filters, limit=2)
        
        if not users:
            return False
        
        # If excluding an ID, check if found user is different
        if exclude_id:
            return any(user["id"] != exclude_id for user in users)
        
        return True
    
    def create_with_validation(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create user with email uniqueness and format validation
        
        Args:
            user_data: User data with email
            
        Returns:
            Created user
            
        Raises:
            ValueError: If email format is invalid
            DuplicateKeyError: If email already exists
        """
        # Validate email format
        self.validate_email(user_data["email"])
        
        # Check email uniqueness
        if self.email_exists(user_data["email"]):
            raise DuplicateKeyError(f"Email already exists: {user_data['email']}")
        
        # Add timestamps
        user_data["created_at"] = datetime.utcnow().isoformat()
        user_data["updated_at"] = None
        
        return self.create(user_data)
    
    def update_with_validation(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user with email uniqueness and format validation
        
        Args:
            user_id: User ID
            updates: Fields to update
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If email format is invalid
            NotFoundError: If user not found
            DuplicateKeyError: If email already exists
        """
        # Check email format and uniqueness if email is being updated
        if "email" in updates:
            self.validate_email(updates["email"])
            
            if self.email_exists(updates["email"], exclude_id=user_id):
                raise DuplicateKeyError(f"Email already exists: {updates['email']}")
        
        # Add updated timestamp
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        return self.update(user_id, updates)
    
    def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get users by role
        
        Args:
            role: User role (user/manager/root)
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of users with specified role
        """
        return self.db.get_all(
            self.collection,
            filters={"role": role},
            skip=skip,
            limit=limit,
            sort={"created_at": -1}
        )
    
    def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get users by status
        
        Args:
            status: User status (active/disabled)
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of users with specified status
        """
        return self.db.get_all(
            self.collection,
            filters={"status": status},
            skip=skip,
            limit=limit,
            sort={"created_at": -1}
        )
    
    def count_by_role(self, role: str) -> int:
        """Count users by role"""
        return self.db.count(self.collection, filters={"role": role})
    
    def count_by_status(self, status: str) -> int:
        """Count users by status"""
        return self.db.count(self.collection, filters={"status": status})
    
    def ensure_indexes(self) -> None:
        """
        Create indexes for users collection
        
        Creates unique index on email field.
        """
        try:
            self.db.create_index(
                self.collection,
                fields=["email"],
                unique=True
            )
        except Exception as e:
            # Index might already exist, log but don't fail
            import logging
            logging.getLogger(__name__).debug(f"Index creation skipped: {e}")