"""
Path: src/database/factory.py
Version: 1.0

Database factory pattern implementation
Provides single point to get database instance based on configuration
"""

from typing import Optional
import logging

from src.core.config import settings
from src.database.interface import IDatabase
from src.database.exceptions import DatabaseException

logger = logging.getLogger(__name__)

# Singleton instance
_db_instance: Optional[IDatabase] = None


def get_database() -> IDatabase:
    """
    Factory function to get database instance based on configuration
    
    Returns appropriate database adapter based on settings.DB_TYPE:
        - "arango": ArangoDB adapter
        - "mongo": MongoDB adapter (future)
        - "postgres": PostgreSQL adapter (future)
    
    Returns:
        IDatabase implementation (singleton)
        
    Raises:
        ValueError: If DB_TYPE is not supported
        DatabaseException: If connection fails
        
    Example:
        # In service/repository
        from src.database.factory import get_database
        
        db = get_database()
        users = db.get_all("users")
        
    Note:
        This returns a singleton instance. The database connection
        is established on first call and reused for subsequent calls.
        
        To change database implementation, simply update DB_TYPE
        in configuration - no code changes needed.
    """
    global _db_instance
    
    if _db_instance is None:
        logger.info(f"Initializing database adapter: {settings.DB_TYPE}")
        
        # Import and instantiate appropriate adapter
        if settings.DB_TYPE == "arango":
            from src.database.adapters.arango_adapter import ArangoDatabaseAdapter
            _db_instance = ArangoDatabaseAdapter()
            
        elif settings.DB_TYPE == "mongo":
            # Future implementation
            try:
                from src.database.adapters.mongo_adapter import MongoDatabaseAdapter
                _db_instance = MongoDatabaseAdapter()
            except ImportError:
                raise DatabaseException(
                    "MongoDB adapter not implemented yet. "
                    "Set DB_TYPE=arango in configuration."
                )
            
        elif settings.DB_TYPE == "postgres":
            # Future implementation
            try:
                from src.database.adapters.postgres_adapter import PostgresDatabaseAdapter
                _db_instance = PostgresDatabaseAdapter()
            except ImportError:
                raise DatabaseException(
                    "PostgreSQL adapter not implemented yet. "
                    "Set DB_TYPE=arango in configuration."
                )
            
        else:
            raise ValueError(
                f"Unsupported DB_TYPE: {settings.DB_TYPE}. "
                f"Supported types: arango, mongo, postgres"
            )
        
        # Establish connection
        try:
            _db_instance.connect()
            logger.info(f"Database connection established: {settings.DB_TYPE}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            _db_instance = None
            raise DatabaseException(f"Database connection failed: {str(e)}")
    
    return _db_instance


def reset_database() -> None:
    """
    Reset database singleton instance
    
    Useful for testing or forcing reconnection.
    Closes existing connection and clears singleton.
    
    Example:
        # In tests
        from src.database.factory import reset_database
        
        def teardown():
            reset_database()  # Clean state between tests
    """
    global _db_instance
    
    if _db_instance is not None:
        try:
            _db_instance.disconnect()
            logger.info("Database connection closed")
        except Exception as e:
            logger.warning(f"Error disconnecting database: {e}")
        finally:
            _db_instance = None


def get_database_type() -> str:
    """
    Get configured database type
    
    Returns:
        Database type string (arango, mongo, postgres)
        
    Example:
        db_type = get_database_type()
        if db_type == "arango":
            # ArangoDB-specific logic
            pass
    """
    return settings.DB_TYPE


def is_connected() -> bool:
    """
    Check if database is connected
    
    Returns:
        True if database instance exists and is connected
        
    Example:
        if not is_connected():
            logger.warning("Database not connected")
            db = get_database()  # Reconnect
    """
    return _db_instance is not None