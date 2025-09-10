"""
MCP Server Initialization and Configuration

This module initializes and configures the MCP server with all necessary tools and middleware.
"""
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, Callable, Awaitable

from app.core.config import settings
from app.core.yaml_config import config  # Import YAML config

from app.services.mcp_server import MCPServer, mcp_server
from app.services.mcp_tools import register_all_tools
from app.core.mcp_security import MCPAuthMiddleware, require_auth

logger = logging.getLogger(__name__)

def setup_mcp_server(app: FastAPI) -> None:
    """
    Set up the MCP server with all tools and middleware.
    
    Args:
        app: The FastAPI application instance
    """
    if not config.get("mcp", {}).get("enabled", False):
        logger.info("MCP server is disabled in configuration")
        return
        
    logger.info("Initializing MCP server...")
    
    # Configure MCP server
    max_concurrent = config.get("mcp", {}).get("max_concurrent_requests", 10)
    development_mode = os.getenv("DEVELOPMENT_MODE", "False").lower() == "true"
    
    # Initialize the MCP server
    mcp_server.start(
        max_concurrent_requests=max_concurrent,
        development_mode=development_mode
    )
    
    if development_mode:
        logger.info("Running in development mode - webhook endpoints are disabled")
        # Add development-only endpoints
        from fastapi import APIRouter
        from app.services.github_service import GitHubService
        
        dev_router = APIRouter(prefix="/api/dev", tags=["Development"])
        
        @dev_router.post("/trigger-event")
        async def trigger_event(payload: dict):
            """Manually trigger an event (for development)"""
            service = GitHubService()
            await service.handle_webhook(payload)
            return {"status": "event processed"}
            
        app.include_router(dev_router)
    
    # Register all tools
    try:
        register_all_tools(mcp_server)
        logger.info(f"Registered {len(mcp_server.tools)} tools with MCP server")
    except Exception as e:
        logger.error(f"Failed to register tools: {str(e)}", exc_info=True)
        raise
    
    # Add MCP middleware for authentication
    app.add_middleware(MCPAuthMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add startup and shutdown event handlers
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        logger.info("Starting up MCP server...")
        
        # Initialize any required services here
        try:
            # Example: Initialize database connections, caches, etc.
            pass
        except Exception as e:
            logger.error(f"Error during startup: {str(e)}", exc_info=True)
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        logger.info("Shutting down MCP server...")
        
        # Clean up resources
        try:
            mcp_server.stop()
            
            # Close any open connections, caches, etc.
            pass
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "mcp_server": "running",
                "database": "connected",  # Add actual database status check
                "cache": "connected"      # Add actual cache status check
            }
        }
    
    logger.info("MCP server initialization complete")

# Example of how to use the MCP server in a FastAPI route
# @app.post("/api/execute-tool")
# async def execute_tool(
#     request: Request,
#     tool_name: str,
#     params: Dict[str, Any],
#     auth: Dict[str, Any] = Depends(require_auth(["execute:tools"]))
# ):
#     """
#     Execute a tool through the MCP server.
#     
#     This is just an example - in a real application, you would typically
#     use the MCP server directly in your route handlers.
#     """
#     try:
#         result = await mcp_server.execute_tool(
#             tool_name=tool_name,
#             parameters=params,
#             agent_id=auth.get("agent_id", "api"),
#             user_context={
#                 "user_id": auth.get("user_id"),
#                 "ip_address": request.client.host if request.client else None
#             }
#         )
#         return {"status": "success", "result": result}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
