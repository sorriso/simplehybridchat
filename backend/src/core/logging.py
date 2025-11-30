"""
Path: src/core/logging.py
Version: 2

Logging configuration
Sets up application-wide logging with configurable level
"""

import logging
import sys
from src.core.config import settings


def setup_logging() -> None:
    """
    Configure application logging
    
    Sets up logging with level from settings.LOG_LEVEL.
    Logs are written to stdout with timestamp and level.
    
    Example:
        # In main.py
        from src.core.logging import setup_logging
        setup_logging()
        
        # Then use logging anywhere
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Application started")
    """
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Set uvicorn loggers to same level
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(log_level)