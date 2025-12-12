"""
Path: backend/src/core/config.py
Version: 5

Changes in v5:
- Added LLM_PROVIDER configuration parameter
- Added comprehensive LLM provider configurations (OpenAI, Claude, Gemini, Databricks, OpenRouter, Ollama)
- Added LLM_TIMEOUT parameter
- Restructured LLM configuration section for multi-provider support

Application configuration using pydantic-settings with Kubernetes support
All settings loaded from environment variables (dev/.env, docker, K8s secrets/configmaps)
"""

import logging
from typing import Optional, List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings
    
    Compatible with:
    - Local development (.env.local file)
    - Docker containers (environment variables)
    - Kubernetes (secrets + configmaps via envFrom)
    
    All values can be overridden via environment variables.
    """
    
    # ========================================================================
    # API Configuration
    # ========================================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    API_PREFIX: str = "/api"  # Global API prefix (e.g., "/api/v1", "/api/v2")
    
    # ========================================================================
    # Environment
    # ========================================================================
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"
    
    # ========================================================================
    # CORS
    # ========================================================================
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_CREDENTIALS: bool = True
    
    # ========================================================================
    # Database - ArangoDB
    # ========================================================================
    DB_TYPE: str = "arango"  # arango | mongo | postgres
    
    ARANGO_HOST: str = "localhost"
    ARANGO_PORT: int = 8529
    ARANGO_DATABASE: str = "chatbot"
    ARANGO_USER: str = "root"
    ARANGO_PASSWORD: str = "changeme"
    
    # MongoDB (if DB_TYPE=mongo)
    MONGO_URI: Optional[str] = None
    MONGO_DATABASE: Optional[str] = None
    
    # PostgreSQL (if DB_TYPE=postgres)
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DATABASE: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    
    # ========================================================================
    # Storage
    # ========================================================================
    STORAGE_TYPE: str = "minio"  # minio | azure | gcs

    # MinIO configuration
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_DEFAULT_BUCKET: str = "uploads"
    
    # ========================================================================
    # Authentication
    # ========================================================================
    AUTH_MODE: str = "local"  # none | local | sso
    
    # JWT (local auth)
    JWT_SECRET: str = "change-in-production-use-strong-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 12
    
    # SSO
    SSO_TOKEN_HEADER: str = "X-Auth-Token"
    SSO_NAME_HEADER: str = "X-User-Name"
    SSO_EMAIL_HEADER: str = "X-User-Email"
    
    # Multi-login
    ALLOW_MULTI_LOGIN: bool = True
    
    # ========================================================================
    # LLM Configuration
    # ========================================================================
    LLM_PROVIDER: str = "openai"  # openai | claude | gemini | databricks | openrouter | ollama
    LLM_TIMEOUT: int = 60  # seconds
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_BASE_URL: Optional[str] = None  # Optional custom endpoint
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Anthropic Claude
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-opus-20240229"
    CLAUDE_MAX_TOKENS: int = 2000
    CLAUDE_TEMPERATURE: float = 0.7
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    GEMINI_MAX_TOKENS: int = 2000
    GEMINI_TEMPERATURE: float = 0.7
    
    # Databricks
    DATABRICKS_API_KEY: Optional[str] = None
    DATABRICKS_BASE_URL: Optional[str] = None
    DATABRICKS_MODEL: str = "databricks-dbrx-instruct"
    DATABRICKS_MAX_TOKENS: int = 2000
    DATABRICKS_TEMPERATURE: float = 0.7
    
    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = "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"
    OPENROUTER_MODEL: str = "openai/gpt-oss-20b:free"
    OPENROUTER_MAX_TOKENS: int = 2000
    OPENROUTER_TEMPERATURE: float = 0.7
    
    # Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "tinyllama"  # Changed to tinyllama for faster tests
    OLLAMA_MAX_TOKENS: int = 2000
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_TIMEOUT: int = 300  # 5 minutes for model loading
    
    # ========================================================================
    # File Upload
    # ========================================================================
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILES_PER_UPLOAD: int = 5
    ALLOWED_FILE_TYPES: str = ".txt,.pdf,.doc,.docx,.md"
    
    # ========================================================================
    # Rate Limiting
    # ========================================================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # ========================================================================
    # Monitoring
    # ========================================================================
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    
    # ========================================================================
    # Maintenance Mode
    # ========================================================================
    MAINTENANCE_MODE: bool = False
    MAINTENANCE_MESSAGE: str = "System under maintenance. Please try again later."
    
    # ========================================================================
    # Kubernetes specific (injected by downward API)
    # ========================================================================
    POD_NAME: Optional[str] = None
    POD_NAMESPACE: Optional[str] = None
    POD_IP: Optional[str] = None
    
    # ========================================================================
    # Pydantic Settings Configuration
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ========================================================================
    # Kubernetes Detection
    # ========================================================================
    
    def is_kubernetes(self) -> bool:
        """
        Check if running in Kubernetes
        
        Returns:
            True if running in K8s cluster
        """
        return self.POD_NAME is not None or Path("/var/run/secrets/kubernetes.io").exists()
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    def validate_config(self) -> None:
        """
        Validate critical configuration
        
        Raises:
            ValueError: If critical config is missing or invalid
        """
        errors = []
        
        # Production checks
        if self.ENVIRONMENT == "production":
            # Database password
            if not self.ARANGO_PASSWORD or self.ARANGO_PASSWORD == "changeme":
                errors.append("ARANGO_PASSWORD must be set in production")
            
            # Storage credentials
            if self.MINIO_ACCESS_KEY == "minioadmin":
                errors.append("MINIO_ACCESS_KEY must be changed in production")
            if self.MINIO_SECRET_KEY == "minioadmin":
                errors.append("MINIO_SECRET_KEY must be changed in production")
            
            # JWT secret
            if self.JWT_SECRET == "change-in-production-use-strong-secret-key":
                errors.append("JWT_SECRET must be changed in production")
        else:
            # Development warnings
            if self.JWT_SECRET == "change-in-production-use-strong-secret-key":
                logger.warning("Using default JWT_SECRET (OK for dev)")
        
        # Port validation
        if not (1024 <= self.API_PORT <= 65535):
            errors.append(f"Invalid API_PORT: {self.API_PORT}")
        if not (1024 <= self.ARANGO_PORT <= 65535):
            errors.append(f"Invalid ARANGO_PORT: {self.ARANGO_PORT}")
        if not (1024 <= self.MINIO_PORT <= 65535):
            errors.append(f"Invalid MINIO_PORT: {self.MINIO_PORT}")
        
        if errors:
            raise ValueError(
                f"Configuration validation failed:\n" + 
                "\n".join(f"  - {error}" for error in errors)
            )
        
        logger.info("Configuration validated successfully")
    
    # ========================================================================
    # Logging
    # ========================================================================
    
    def log_config(self) -> None:
        """Log configuration (without sensitive data)"""
        logger.info("=" * 80)
        logger.info("APPLICATION CONFIGURATION")
        logger.info("=" * 80)
        logger.info(f"Environment: {self.ENVIRONMENT}")
        logger.info(f"Debug: {self.API_RELOAD}")
        logger.info(f"Log Level: {self.LOG_LEVEL}")
        logger.info(f"Running in Kubernetes: {self.is_kubernetes()}")
        
        if self.is_kubernetes():
            logger.info(f"Pod Name: {self.POD_NAME}")
            logger.info(f"Pod Namespace: {self.POD_NAMESPACE}")
        
        logger.info(f"Server: {self.API_HOST}:{self.API_PORT} (workers={self.API_WORKERS})")
        logger.info(f"Database: {self.DB_TYPE} @ {self.ARANGO_HOST}:{self.ARANGO_PORT}/{self.ARANGO_DATABASE}")
        logger.info(f"Storage: {self.STORAGE_TYPE} @ {self.MINIO_HOST}:{self.MINIO_PORT}")
        logger.info(f"Auth Mode: {self.AUTH_MODE}")
        logger.info(f"CORS Origins: {self.CORS_ORIGINS}")
        logger.info(f"Maintenance Mode: {self.MAINTENANCE_MODE}")
        logger.info("=" * 80)
    
    # ========================================================================
    # Helpers
    # ========================================================================
    
    def get_cors_origins(self) -> List[str]:
        """
        Get CORS origins as list
        
        Returns:
            List of origin URLs
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    def get_allowed_file_types(self) -> List[str]:
        """
        Get allowed file types as list
        
        Returns:
            List of file extensions
        """
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",") if ext.strip()]


# Singleton instance
settings = Settings()

# Auto-validate on import (fails fast)
import os
if os.getenv("SKIP_CONFIG_VALIDATION") != "true":
    settings.validate_config()