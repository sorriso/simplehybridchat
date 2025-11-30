"""
Path: src/database/exceptions.py
Version: 1.0

Database-specific exceptions for error handling
All database adapters should raise these exceptions for consistent error handling
"""


class DatabaseException(Exception):
    """
    Base exception for all database operations
    
    All database-related errors should inherit from this exception
    to allow catching all database errors with a single except clause.
    
    Example:
        try:
            db.create("users", data)
        except DatabaseException as e:
            logger.error(f"Database error: {e}")
    """
    pass


class NotFoundError(DatabaseException):
    """
    Document not found in database
    
    Raised when attempting to access a document that doesn't exist.
    
    Example:
        try:
            user = db.get_by_id("users", "nonexistent")
            if not user:
                raise NotFoundError("User not found")
        except NotFoundError:
            # Handle missing document
            pass
    """
    pass


class DuplicateKeyError(DatabaseException):
    """
    Unique constraint violation
    
    Raised when attempting to insert/update a document with a value
    that violates a unique index constraint.
    
    Example:
        try:
            db.create("users", {"email": "existing@example.com"})
        except DuplicateKeyError:
            # Email already exists
            return {"error": "Email already registered"}
    """
    pass


class ConnectionError(DatabaseException):
    """
    Database connection error
    
    Raised when unable to establish or maintain connection to database.
    
    Example:
        try:
            db.connect()
        except ConnectionError:
            logger.critical("Cannot connect to database")
            raise
    """
    pass


class ValidationError(DatabaseException):
    """
    Data validation error
    
    Raised when document data doesn't meet schema/validation requirements.
    
    Example:
        try:
            db.create("users", {"email": "invalid-email"})
        except ValidationError as e:
            return {"error": f"Invalid data: {e}"}
    """
    pass


class TransactionError(DatabaseException):
    """
    Transaction operation error
    
    Raised when transaction commit/rollback fails.
    Used in databases that support transactions.
    
    Example:
        try:
            with db.transaction():
                db.create("users", user_data)
                db.create("sessions", session_data)
        except TransactionError:
            # Transaction rolled back
            logger.error("Transaction failed")
    """
    pass


class QueryError(DatabaseException):
    """
    Query execution error
    
    Raised when a query has syntax errors or cannot be executed.
    
    Example:
        try:
            db.find_many("users", {"invalid_field": {"$regex": "["}})
        except QueryError:
            return {"error": "Invalid query syntax"}
    """
    pass


class PermissionError(DatabaseException):
    """
    Database permission error
    
    Raised when database user doesn't have sufficient privileges.
    
    Example:
        try:
            db.create_collection("admin_logs")
        except PermissionError:
            logger.error("Insufficient database permissions")
    """
    pass


class TimeoutError(DatabaseException):
    """
    Database operation timeout
    
    Raised when operation exceeds configured timeout limit.
    
    Example:
        try:
            db.get_all("users", limit=1000000)  # Very large query
        except TimeoutError:
            return {"error": "Query took too long"}
    """
    pass


class CollectionNotFoundError(DatabaseException):
    """
    Collection/table doesn't exist
    
    Raised when attempting to access a non-existent collection.
    
    Example:
        try:
            db.get_all("nonexistent_collection")
        except CollectionNotFoundError:
            db.create_collection("nonexistent_collection")
    """
    pass