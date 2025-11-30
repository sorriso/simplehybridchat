"""
Path: src/main.py
Version: 4

FastAPI application entry point with authentication
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import setup_logging
from src.middleware.auth_middleware import AuthenticationMiddleware
from src.api.routes import auth, users

# Setup logging
setup_logging()

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

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Chatbot Backend API",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "auth_mode": settings.AUTH_MODE,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "auth_mode": settings.AUTH_MODE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )