"""
Path: backend/src/api/routes/__init__.py
Version: 1

API routes package initialization
Exposes all route modules for import
"""

# Core routes (always available)
from . import auth
from . import users
from . import conversations
from . import files
from . import user_settings
from . import chat

# Optional routes (Phase 2, 3, 4)
try:
    from . import groups
except ImportError:
    pass

try:
    from . import user_groups
except ImportError:
    pass

try:
    from . import admin
except ImportError:
    pass

__all__ = [
    "auth",
    "users",
    "conversations",
    "files",
    "user_settings",
    "chat",
    "groups",
    "user_groups",
    "admin",
]