"""
Path: backend/src/core/permissions.py
Version: 2

Permission utilities for role-based access control
Implements role hierarchy: user < manager < root
"""

from typing import Dict, Any

# Role hierarchy levels
ROLE_LEVELS = {
    "user": 1,
    "manager": 2,
    "root": 3,
}


def check_permission(user: Dict[str, Any], required_role: str) -> bool:
    """
    Check if user has required permission level
    
    Role hierarchy:
        user (level 1) - Basic user access
        manager (level 2) - Can manage users and content
        root (level 3) - Full system access
    
    A user with higher role level can access lower level resources.
    For example, a manager can do everything a user can do.
    
    Args:
        user: User dict with "role" field
        required_role: Required role ("user" | "manager" | "root")
        
    Returns:
        True if user has sufficient permissions, False otherwise
        
    Example:
        user = {"role": "manager"}
        
        check_permission(user, "user")     # True (manager >= user)
        check_permission(user, "manager")  # True (manager == manager)
        check_permission(user, "root")     # False (manager < root)
    """
    user_role = user.get("role", "user")
    
    # Get role levels
    user_level = ROLE_LEVELS.get(user_role, 0)
    required_level = ROLE_LEVELS.get(required_role, 999)
    
    # User must have equal or higher level
    return user_level >= required_level


def has_role(user: Dict[str, Any], role: str) -> bool:
    """
    Check if user has exact role
    
    Args:
        user: User dict with "role" field
        role: Role to check
        
    Returns:
        True if user has exact role
        
    Example:
        user = {"role": "manager"}
        has_role(user, "manager")  # True
        has_role(user, "root")     # False
    """
    return user.get("role") == role


def is_user(user: Dict[str, Any]) -> bool:
    """Check if user has user role (or higher)"""
    return check_permission(user, "user")


def is_manager(user: Dict[str, Any]) -> bool:
    """Check if user has manager role (or higher)"""
    return check_permission(user, "manager")


def is_root(user: Dict[str, Any]) -> bool:
    """Check if user has root role"""
    return check_permission(user, "root")


def get_user_level(user: Dict[str, Any]) -> int:
    """
    Get user's permission level
    
    Returns:
        Permission level (1=user, 2=manager, 3=root, 0=unknown)
    """
    user_role = user.get("role", "user")
    return ROLE_LEVELS.get(user_role, 0)