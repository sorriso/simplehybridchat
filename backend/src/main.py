"""
Path: backend/src/main.py
Version: 17

Changes in v16:
- FIX: Bootstrap checks for ANY root user (not by email)
- FIX: Updates existing root email if .env email differs
- Prevents duplicate root users when ROOT_USER_EMAIL changes in .env
- Pattern: Find root by role, update email if needed, create only if no root exists

Changes in v15:
- CRITICAL FIX: Added bootstrap_ollama() function for automatic model pull
- Ollama model is now automatically downloaded on first startup
- Idempotent: checks if model exists before pulling
- Independent of deployment method (Docker, Kubernetes, etc.)
- Startup event now calls: bootstrap_database() then bootstrap_ollama()

Changes in v14:
- CRITICAL FIX: Use settings.ROOT_USER_EMAIL/PASSWORD/NAME instead of os.getenv()
- This ensures .env values are properly read via pydantic Settings
- Removed hardcoded "root@localhost" default

FastAPI application entry point with automatic database bootstrap
"""

import logging
from datetime import datetime, UTC
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import setup_logging
from src.middleware.auth_middleware import AuthenticationMiddleware
from src.core.security import hash_password

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# Core routes (always available)
from src.api.routes import auth, users, conversations, files, user_settings, chat

# Optional routes (Phase 2, 3, 4) - import gracefully
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


async def bootstrap_ollama():
    """
    Bootstrap Ollama by ensuring the configured model is available
    
    Steps:
    1. Connect to Ollama server
    2. Check if model exists
    3. Pull model if not found
    
    Safe to run multiple times (idempotent).
    Only pulls model if it doesn't exist.
    """
    # Only bootstrap if using Ollama
    if settings.LLM_PROVIDER != "ollama":
        logger.info("Skipping Ollama bootstrap (LLM_PROVIDER != ollama)")
        return
    
    try:
        logger.info("")
        logger.info("=" * 80)
        logger.info("OLLAMA MODEL INITIALIZATION")
        logger.info("=" * 80)
        logger.info(f"Server: {settings.OLLAMA_BASE_URL}")
        logger.info(f"Model: {settings.OLLAMA_MODEL}")
        logger.info("")
        
        # Import Ollama adapter
        from src.llm.adapters.ollama_adapter import OllamaAdapter
        
        # Create temporary instance for bootstrap
        ollama = OllamaAdapter()
        ollama.connect()
        
        logger.info("[1/2] Checking if model exists...")
        
        # List available models
        try:
            models = await ollama.list_models()
            model_exists = any(
                settings.OLLAMA_MODEL in model 
                for model in models
            )
            
            if model_exists:
                logger.info(f"✓ Model '{settings.OLLAMA_MODEL}' already available")
                logger.info("Skipping download")
            else:
                logger.info(f"✗ Model '{settings.OLLAMA_MODEL}' not found")
                logger.info("")
                logger.info("[2/2] Pulling model (this may take 30-60 seconds)...")
                logger.info("")
                
                # Pull the model
                await ollama.pull_model(settings.OLLAMA_MODEL)
                
                logger.info("")
                logger.info(f"✓ Model '{settings.OLLAMA_MODEL}' successfully pulled")
                
        except Exception as e:
            logger.warning(f"Failed to check/pull Ollama model: {e}")
            logger.warning("Application will continue, but chat may not work until model is available")
            logger.warning(f"Manual pull: docker exec <container> ollama pull {settings.OLLAMA_MODEL}")
        
        # Close the client
        if ollama.client:
            await ollama.client.aclose()
        
        logger.info("=" * 80)
        logger.info("OLLAMA INITIALIZATION COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("OLLAMA BOOTSTRAP ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error("Possible causes:")
        logger.error(f"  1. Ollama is not running ({settings.OLLAMA_BASE_URL})")
        logger.error("  2. Network connectivity to Ollama server")
        logger.error("  3. Ollama service not healthy")
        logger.error("=" * 80)
        logger.warning("Application will continue, but chat may not work")


def bootstrap_database():
    """
    Bootstrap database on application startup
    
    This function:
    1. Creates the database if it doesn't exist (requires root credentials)
    2. Creates all required collections
    3. Creates indexes on collections
    4. Creates or updates the root user
    
    Supports two deployment modes:
    - Docker Compose: Uses root credentials to create everything
    - Kubernetes: Job-init creates DB, backend uses regular user
    
    All operations are logged explicitly.
    """
    logger.info("=" * 80)
    logger.info("DATABASE BOOTSTRAP - START")
    logger.info("=" * 80)
    
    try:
        from arango import ArangoClient
        from arango.exceptions import DatabaseCreateError
        
        client = ArangoClient(hosts=f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}")
        
        # Step 1: Try to create database with root credentials (if available)
        logger.info(f"[1/4] Checking database '{settings.ARANGO_DATABASE}'")
        
        db = None
        db_created = False
        
        # Check if root credentials are available (for Docker Compose)
        root_user = getattr(settings, 'ARANGO_ROOT_USER', None)
        root_password = getattr(settings, 'ARANGO_ROOT_PASSWORD', None)
        
        if root_user and root_password:
            # Docker Compose mode: use root to create DB
            try:
                logger.info(f"      Attempting with root credentials: {root_user}")
                sys_db = client.db(
                    "_system",
                    username=root_user,
                    password=root_password
                )
                
                logger.info(f"      ✓ Connected to ArangoDB _system database")
                
                db_exists = sys_db.has_database(settings.ARANGO_DATABASE)
                
                if db_exists:
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
            # Kubernetes mode: database created by job-init
            logger.info(f"      No root credentials - assuming database exists (Kubernetes mode)")
        
        # Step 2: Connect to application database with regular user
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
        
        # Step 3: Create collections and indexes
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
            }
        ]
        
        for collection_config in collections_config:
            collection_name = collection_config["name"]
            
            # Create collection if it doesn't exist
            if not db.has_collection(collection_name):
                db.create_collection(collection_name)
                logger.info(f"      ✓ Collection '{collection_name}' created")
            else:
                logger.info(f"      ✓ Collection '{collection_name}' already exists")
            
            # Create indexes
            collection = db.collection(collection_name)
            for index_config in collection_config["indexes"]:
                try:
                    collection.add_hash_index(
                        fields=index_config["fields"],
                        unique=index_config["unique"]
                    )
                    index_desc = f"{'unique' if index_config['unique'] else 'non-unique'} index on {index_config['fields']}"
                    logger.info(f"        ✓ {index_desc}")
                except Exception as e:
                    # Index might already exist
                    if "duplicate" in str(e).lower() or "already" in str(e).lower():
                        logger.info(f"        ✓ Index on {index_config['fields']} already exists")
                    else:
                        logger.warning(f"        ⚠ Failed to create index on {index_config['fields']}: {e}")
        
        # Step 4: Create or update root user
        logger.info(f"[4/4] Checking root user")
        
        root_email = settings.ROOT_USER_EMAIL
        root_password = settings.ROOT_USER_PASSWORD
        root_name = settings.ROOT_USER_NAME
        
        users_collection = db.collection("users")
        
        # Look for ANY root user (by role, not by email)
        cursor = users_collection.find({"role": "root"})
        existing_roots = [doc for doc in cursor]
        
        if existing_roots:
            # Root user exists - check if email needs update
            root_user = existing_roots[0]
            current_email = root_user.get("email")
            
            if current_email != root_email:
                # Email in .env differs from DB - update it
                logger.info(f"      ⚙ Root user exists but email differs")
                logger.info(f"        Old email: {current_email}")
                logger.info(f"        New email: {root_email}")
                
                users_collection.update({
                    "_key": root_user["_key"],
                    "email": root_email,
                    "name": root_name,
                    "updated_at": datetime.now(UTC).isoformat()
                })
                
                logger.info(f"      ✓ Root user email updated")
                logger.info(f"        User ID: {root_user['_key']}")
                logger.info(f"        Email: {root_email}")
            else:
                logger.info(f"      ✓ Root user already exists: {root_email}")
                logger.info(f"        User ID: {root_user['_key']}")
                logger.info(f"        Role: {root_user.get('role', 'unknown')}")
            
            # If there are multiple root users (shouldn't happen), log warning
            if len(existing_roots) > 1:
                logger.warning(f"      ⚠ MULTIPLE ROOT USERS FOUND: {len(existing_roots)}")
                logger.warning(f"        This should not happen - consider cleanup")
                for i, extra_root in enumerate(existing_roots[1:], start=2):
                    logger.warning(f"        Root #{i}: {extra_root.get('email')} (ID: {extra_root['_key']})")
        else:
            # No root user - create one
            logger.info(f"      ⚙ Root user not found, creating...")
            logger.info(f"        Email: {root_email}")
            logger.info(f"        Name: {root_name}")
            
            root_user = {
                "name": root_name,
                "email": root_email,
                "password_hash": hash_password(root_password),
                "role": "root",
                "status": "active",
                "group_ids": [],
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": None,
                "last_login": None
            }
            
            result = users_collection.insert(root_user)
            
            logger.info(f"      ✓ Root user created successfully")
            logger.info(f"        User ID: {result['_key']}")
            logger.info(f"        Email: {root_email}")
            logger.warning(f"      ⚠ DEFAULT CREDENTIALS IN USE")
            logger.warning(f"        Login: {root_email}")
            logger.warning(f"        Password: {root_password}")
            logger.warning(f"      ⚠ CHANGE PASSWORD AFTER FIRST LOGIN!")
        
        logger.info("=" * 80)
        logger.info("DATABASE BOOTSTRAP - COMPLETE")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("DATABASE BOOTSTRAP - FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        logger.error("APPLICATION WILL NOT START PROPERLY")
        logger.error("Please check:")
        logger.error("  1. ArangoDB is running")
        logger.error(f"  2. Credentials are correct (user: {settings.ARANGO_USER})")
        logger.error("  3. Network connectivity to ArangoDB")
        logger.error("  4. Database exists (or root credentials provided)")
        logger.error("=" * 80)
        # Don't raise - let application start but log the error
        # This allows health checks to work even if DB is down


# Create FastAPI app
app = FastAPI(
    title="Chatbot Backend API",
    version="2.0.0",
    description="Backend API for chatbot application with authentication",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware
app.add_middleware(AuthenticationMiddleware)

# Include core routers
app.include_router(auth.router, prefix=settings.API_PREFIX, tags=["Authentication"])
app.include_router(users.router, prefix=settings.API_PREFIX, tags=["Users"])
app.include_router(conversations.router, prefix=settings.API_PREFIX, tags=["Conversations"])
app.include_router(chat.router, prefix=settings.API_PREFIX, tags=["Chat"])
app.include_router(files.router, prefix=settings.API_PREFIX, tags=["Files"])
app.include_router(user_settings.router, prefix=settings.API_PREFIX, tags=["Settings"])

# Include optional routers (Phase 2, 3, 4)
if GROUPS_AVAILABLE:
    app.include_router(groups.router, prefix=settings.API_PREFIX, tags=["Groups"])
    logger.info("✓ Groups routes loaded")

if USER_GROUPS_AVAILABLE:
    app.include_router(user_groups.router, prefix=settings.API_PREFIX, tags=["User Groups"])
    logger.info("✓ User Groups routes loaded")

if ADMIN_AVAILABLE:
    app.include_router(admin.router, prefix=settings.API_PREFIX, tags=["Admin"])
    logger.info("✓ Admin routes loaded")


@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    
    Runs database bootstrap and displays startup information
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("APPLICATION STARTUP")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: 2.0.0")
    logger.info(f"API Prefix: {settings.API_PREFIX}")
    logger.info(f"Auth Mode: {settings.AUTH_MODE}")
    logger.info(f"CORS Origins: {', '.join(settings.get_cors_origins())}")
    logger.info(f"Database: ArangoDB @ {settings.ARANGO_HOST}:{settings.ARANGO_PORT}/{settings.ARANGO_DATABASE}")
    logger.info(f"Storage: {settings.STORAGE_TYPE} @ {settings.MINIO_HOST}:{settings.MINIO_PORT}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    
    if settings.LLM_PROVIDER == "ollama":
        logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
        logger.info(f"Ollama Model: {settings.OLLAMA_MODEL}")
    
    logger.info("=" * 80)
    logger.info("")
    
    # Run database bootstrap
    bootstrap_database()
    
    # Run Ollama bootstrap (if using Ollama)
    await bootstrap_ollama()
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("APPLICATION READY")
    logger.info("=" * 80)
    logger.info(f"API Server: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"Health Check: http://{settings.API_HOST}:{settings.API_PORT}/health")
    logger.info("=" * 80)
    logger.info("")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns application health status and configuration
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "api_version": "2.0.0",
        "auth_mode": settings.AUTH_MODE,
        "api_prefix": settings.API_PREFIX,
        "database": {
            "type": "arangodb",
            "host": settings.ARANGO_HOST,
            "port": settings.ARANGO_PORT,
            "database": settings.ARANGO_DATABASE
        },
        "llm": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else None
        }
    }


@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns API information and available endpoints
    """
    return {
        "message": "Chatbot Backend API",
        "version": "2.0.0",
        "docs": f"{settings.API_PREFIX}/docs",
        "health": "/health"
    }