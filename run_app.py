"""
Simple FastAPI runner to test the application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI application instance
app = FastAPI(
    title="AK Cloud Native Management System",
    description="Backend API for AK Cloud Native Transformation Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "AK Cloud Native Transformation Management System",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint."""
    return {
        "message": "API is working",
        "endpoints": [
            "/api/v1/auth",
            "/api/v1/applications",
            "/api/v1/subtasks",
            "/api/v1/calculation",
            "/api/v1/audit",
            "/api/v1/excel",
            "/api/v1/reports",
            "/api/v1/notifications"
        ]
    }


if __name__ == "__main__":
    print("Starting FastAPI server...")
    print("Access the API at: http://localhost:8000")
    print("Access API docs at: http://localhost:8000/docs")
    print("Access ReDoc at: http://localhost:8000/redoc")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )