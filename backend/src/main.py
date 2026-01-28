"""
Path: backend/src/main.py
Version: 21.1

Changes in v21.1:
- FIX: Added missing 'name' field to root user (was causing 500 error)
- FEATURE: Root user email/password now configurable via env vars
- ROOT_USER_EMAIL (default: root@example.com)
- ROOT_USER_PASSWORD (default: RootPass123)
- Root user gets name from email local part or "Root Admin"

Changes in v21.0:
- SECURITY: Bootstrap root user with SHA256+Bcrypt
- Added sha256_hash() function
- Root password: "RootPass123" → SHA256 → Bcrypt → Store
"""

import logging
import hashlib
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import setup_logging
from src.middleware.auth_middleware import AuthenticationMiddleware
from src.core.security import hash_password

setup_logging()
logger = logging.getLogger(__name__)

from src.api.routes import auth, users, conversations, files, user_settings, chat

try:
    from src.api.routes import groups
    GROUPS_AVAILABLE = True
except ImportError:
    GROUPS_AVAILABLE = False

try:
    from src.api.routes import user_groups
    USER_GROUPS_AVAILABLE = True
except ImportError:
    USER_GROUPS_AVAILABLE = False

try:
    from src.api.routes import admin
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False


def sha256_hash(text: str) -> str:
    """
    Compute SHA256 hash identical to frontend
    
    Frontend (JavaScript):
    await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
    
    Backend (Python):
    hashlib.sha256(text.encode()).hexdigest()
    
    Both produce identical 64-character hex strings
    
    Args:
        text: Plaintext string to hash
        
    Returns:
        SHA256 hash as hexadecimal string (64 chars)
    
    Example:
        sha256_hash("RootPass123")
        # Returns: "8edd5407e819806dbe247aa7242bf2ff5250d39deba5ca69826546279b0f36e8"
    """
    return hashlib.sha256(text.encode()).hexdigest()


def bootstrap_database():
    """
    Bootstrap database on application startup
    
    SECURITY MODEL FOR ROOT USER:
    1. Plaintext: ROOT_USER_PASSWORD env var or "RootPass123"
    2. SHA256: sha256_hash(password) = "8edd..."
    3. Bcrypt: hash_password("8edd...") = "$2b$12..."
    4. Store: "$2b$12..."
    
    This matches frontend behavior:
    - Frontend: password → SHA256 → send
    - Backend: receive SHA256 → Bcrypt → store
    
    ROOT USER CONFIGURATION:
    - Email: ROOT_USER_EMAIL env var or "root@example.com"
    - Password: ROOT_USER_PASSWORD env var or "RootPass123"
    - Name: Extracted from email local part or "Root Admin"
    
    This function:
    1. Creates database if doesn't exist
    2. Creates all required collections
    3. Creates indexes
    4. Creates or updates root user with SHA256+Bcrypt
    """
    from arango import ArangoClient
    
    logger.info("="*80)
    logger.info("BOOTSTRAP: Starting database initialization")
    logger.info("="*80)
    
    arango_url = f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}"
    logger.info(f"      Connecting to ArangoDB at: {arango_url}")
    client = ArangoClient(hosts=arango_url)
    
    db_created = False
    db = None
    
    try:
        logger.info(f"[1/4] Checking database '{settings.ARANGO_DATABASE}'")
        
        if settings.ARANGO_ROOT_PASSWORD:
            logger.info(f"      Root credentials available - will create database if needed")
            try:
                sys_db = client.db(
                    '_system',
                    username='root',
                    password=settings.ARANGO_ROOT_PASSWORD
                )
                
                if sys_db.has_database(settings.ARANGO_DATABASE):
                    logger.info(f"      ✓ Database '{settings.ARANGO_DATABASE}' already exists")
                else:
                    logger.info(f"      ⚙ Creating database '{settings.ARANGO_DATABASE}'...")
                    sys_db.create_database(settings.ARANGO_DATABASE)
                    logger.info(f"      ✓ Database '{settings.ARANGO_DATABASE}' created successfully")
                    db_created = True
                    
            except Exception as e:
                logger.warning(f"      ⚠ Root connection failed: {e}")
                logger.warning(f"      Assuming database exists (Kubernetes mode)")
        else:
            logger.info(f"      No root credentials - assuming database exists (Kubernetes mode)")
        
        logger.info(f"[2/4] Connecting to database '{settings.ARANGO_DATABASE}'")
        logger.info(f"      User: {settings.ARANGO_USER}")
        
        try:
            db = client.db(
                settings.ARANGO_DATABASE,
                username=settings.ARANGO_USER,
                password=settings.ARANGO_PASSWORD
            )
            logger.info(f"      ✓ Connected to database '{settings.ARANGO_DATABASE}'")
        except Exception as e:
            logger.error(f"      ✗ Failed to connect to database: {e}")
            raise
        
        logger.info(f"[3/4] Creating collections and indexes")
        
        collections_config = [
            {
                "name": "users",
                "indexes": [
                    {"type": "hash", "fields": ["email"], "unique": True},
                    {"type": "hash", "fields": ["role"], "unique": False},
                    {"type": "hash", "fields": ["status"], "unique": False},
                ]
            },
            {
                "name": "user_groups",
                "indexes": [
                    {"type": "hash", "fields": ["name"], "unique": False},
                ]
            },
            {
                "name": "groups",
                "indexes": [
                    {"type": "hash", "fields": ["name"], "unique": True},
                    {"type": "hash", "fields": ["status"], "unique": False},
                ]
            },
            {
                "name": "conversations",
                "indexes": [
                    {"type": "hash", "fields": ["user_id"], "unique": False},
                    {"type": "hash", "fields": ["status"], "unique": False},
                ]
            },
            {
                "name": "messages",
                "indexes": [
                    {"type": "hash", "fields": ["conversation_id"], "unique": False},
                ]
            },
            {
                "name": "files",
                "indexes": [
                    {"type": "hash", "fields": ["user_id"], "unique": False},
                    {"type": "hash", "fields": ["conversation_id"], "unique": False},
                ]
            },
            {
                "name": "settings",
                "indexes": [
                    {"type": "hash", "fields": ["user_id"], "unique": True},
                ]
            },
            {
                "name": "processing_queue",
                "indexes": [
                    {"type": "hash", "fields": ["user_id"], "unique": False},
                    {"type": "hash", "fields": ["status"], "unique": False},
                    {"type": "hash", "fields": ["file_id"], "unique": False},
                ]
            },
            {
                "name": "conversation_groups",
                "indexes": [
                    {"type": "hash", "fields": ["conversation_id"], "unique": False},
                    {"type": "hash", "fields": ["group_id"], "unique": False},
                ]
            }
        ]
        
        for collection_config in collections_config:
            collection_name = collection_config["name"]
            
            if not db.has_collection(collection_name):
                db.create_collection(collection_name)
                logger.info(f"      ✓ Collection '{collection_name}' created")
            else:
                logger.info(f"      ✓ Collection '{collection_name}' already exists")
            
            collection = db.collection(collection_name)
            for index_config in collection_config.get("indexes", []):
                try:
                    existing_indexes = collection.indexes()
                    index_exists = any(
                        set(idx.get("fields", [])) == set(index_config["fields"])
                        for idx in existing_indexes
                    )
                    
                    if not index_exists:
                        collection.add_hash_index(
                            fields=index_config["fields"],
                            unique=index_config.get("unique", False)
                        )
                        logger.info(f"        → Index on {index_config['fields']} created")
                    else:
                        logger.info(f"        → Index on {index_config['fields']} already exists")
                except Exception as e:
                    logger.warning(f"        ⚠ Failed to create index on {index_config['fields']}: {e}")
        
        logger.info(f"[4/4] Bootstrapping root user with SHA256+Bcrypt")
        
        users_collection = db.collection("users")
        
        # Get root user credentials from environment or use defaults
        root_email = getattr(settings, 'ROOT_USER_EMAIL', 'root@example.com')
        root_password_plaintext = getattr(settings, 'ROOT_USER_PASSWORD', 'RootPass123')
        
        # Extract name from email local part
        root_name = root_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        if root_name.lower() == 'root':
            root_name = 'Root Admin'
        
        logger.info(f"      Root user configuration:")
        logger.info(f"        Email: {root_email}")
        logger.info(f"        Name: {root_name}")
        logger.info(f"        Password: {'*' * len(root_password_plaintext)}")
        
        # Check if root user exists
        root_user = None
        try:
            cursor = users_collection.find({"email": root_email})
            root_user = next(cursor, None)
        except Exception as e:
            logger.warning(f"      ⚠ Failed to check for root user: {e}")
        
        # Compute password hash using same method as frontend
        root_password_sha256 = sha256_hash(root_password_plaintext)
        root_password_bcrypt = hash_password(root_password_sha256)
        
        logger.info(f"      Root password SHA256: {root_password_sha256[:16]}...")
        
        if root_user:
            logger.info(f"      ✓ Root user already exists (ID: {root_user['_key']})")
            
            needs_update = False
            updates = {}
            
            # Ensure name field exists
            if 'name' not in root_user or not root_user['name']:
                updates["name"] = root_name
                needs_update = True
            
            if root_user.get("status") != "active":
                updates["status"] = "active"
                needs_update = True
            
            if root_user.get("role") != "admin":
                updates["role"] = "admin"
                needs_update = True
            
            # Always update password (in case it changed in env)
            updates["password_hash"] = root_password_bcrypt
            updates["updated_at"] = datetime.now(UTC).isoformat()
            needs_update = True
            
            if needs_update:
                users_collection.update({"_key": root_user["_key"]}, updates)
                logger.info(f"      ⚙ Root user updated: {', '.join(updates.keys())}")
        else:
            # Create root user
            root_data = {
                "name": root_name,
                "email": root_email,
                "password_hash": root_password_bcrypt,
                "role": "admin",
                "status": "active",
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat()
            }
            
            try:
                result = users_collection.insert(root_data)
                logger.info(f"      ✓ Root user created (ID: {result['_key']})")
                logger.info(f"        Name: {root_name}")
                logger.info(f"        Email: {root_email}")
                logger.info(f"        Password: {root_password_plaintext}")
                logger.info(f"        Role: admin")
                logger.info(f"        Security: SHA256+Bcrypt")
            except Exception as e:
                logger.error(f"      ✗ Failed to create root user: {e}")
                raise
        
        logger.info("="*80)
        logger.info("BOOTSTRAP: Database initialization completed successfully")
        logger.info("="*80)
        
    except Exception as e:
        logger.error("="*80)
        logger.error(f"BOOTSTRAP: Failed with error: {e}")
        logger.error("="*80)
        raise


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    bootstrap_database()
    
    app = FastAPI(
        title="Hybrid Chat API",
        version="1.0.0",
        description="Hybrid Chat API with authentication and LLM integration"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(AuthenticationMiddleware)
    
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(user_settings.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    
    if GROUPS_AVAILABLE:
        app.include_router(groups.router, prefix="/api")
        logger.info("✓ Groups routes registered")
    
    if USER_GROUPS_AVAILABLE:
        app.include_router(user_groups.router, prefix="/api")
        logger.info("✓ User Groups routes registered")
    
    if ADMIN_AVAILABLE:
        app.include_router(admin.router, prefix="/api")
        logger.info("✓ Admin routes registered")
    
    @app.get("/api/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0"}
    
    return app


app = create_app()