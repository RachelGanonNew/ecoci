from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import os

# Load environment variables first
from .core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EcoCI API",
    description="API for EcoCI - AI-Powered GitHub CI/CD Optimization Agent with MCP Server",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Import and configure MCP server
from .core.mcp import setup_mcp_server

# Initialize MCP server
setup_mcp_server(app)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {
        "message": "Welcome to EcoCI API with MCP Server",
        "status": "operational",
        "version": "0.2.0",
        "docs": "/api/docs"
    }

# Health check endpoint (overrides the one in mcp.py)
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring service status."""
    return {
        "status": "healthy",
        "service": "EcoCI API",
        "version": "0.2.0"
    }

# Import and include API routers
from app.api.api_v1 import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Add startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting up EcoCI API...")
    
    # Initialize any required services here
    try:
        # Verify required environment variables
        required_vars = [
            'GITHUB_APP_ID',
            'GITHUB_APP_PRIVATE_KEY',
            'SLACK_BOT_TOKEN',
            'SLACK_SIGNING_SECRET',
            'SECRET_KEY',
            'DATABASE_URL'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
        if missing_vars:
            logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        logger.info("EcoCI API startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down EcoCI API...")
    # Clean up resources here if needed
    logger.info("EcoCI API shutdown complete")
# app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])
# app.include_router(scans.router, prefix="/api/scans", tags=["Scans"])
# app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
