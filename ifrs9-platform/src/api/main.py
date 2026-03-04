"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from src.utils.logging_config import setup_logging
from src.api.routes import imports, classification, staging, ecl, audit, instruments

# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

# Create FastAPI app
app = FastAPI(
    title="IFRS 9 Automation Platform",
    description="IFRS 9 automation platform for commercial banks in Uganda",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(imports.router)
app.include_router(classification.router)
app.include_router(staging.router)
app.include_router(ecl.router)
app.include_router(audit.router)
app.include_router(instruments.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IFRS 9 Automation Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check database, redis, rabbitmq connections
    return {"status": "ready"}


@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    return {
        "title": "IFRS 9 Automation Platform API",
        "version": "1.0.0",
        "endpoints": {
            "imports": "/api/v1/imports",
            "classification": "/api/v1/classification",
            "staging": "/api/v1/staging",
            "ecl": "/api/v1/ecl",
            "audit": "/api/v1/audit",
            "instruments": "/api/v1/instruments"
        },
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        }
    }

