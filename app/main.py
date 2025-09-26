"""
AK Cloud Native Transformation Management System - Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.middleware.logging import LoggingMiddleware

# Import all models to ensure they are registered with SQLAlchemy before any queries
from app.models import User, Application, SubTask, AuditLog, Notification

# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AK Cloud Native Transformation Management",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware in correct order (LoggingMiddleware first, CORS last)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS middleware should be added last to ensure it processes requests first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include API routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "AK Cloud Native Transformation Management System",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.on_event("startup")
async def startup_event():
    """Initialize logging on application startup."""
    from app.core.logging_config import configure_logging
    configure_logging(settings)


if __name__ == "__main__":
    import uvicorn
    from app.core.logging_config import configure_logging
    
    # Configure logging before starting the server
    configure_logging(settings)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None  # Disable uvicorn's default logging config
    )