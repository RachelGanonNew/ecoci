"""
MCP Tools Package

This package contains all the tools that can be registered with the MCP server.
"""
import logging
from typing import Dict, Any, Callable, Awaitable, Optional

# Update import to use absolute path
from app.services.mcp_server import MCPServer
from app.services.mcp_tools.github_tools import register_github_tools
from app.services.mcp_tools.slack_tools import register_slack_tools

logger = logging.getLogger(__name__)

def register_all_tools(mcp_server: MCPServer) -> None:
    """
    Register all available tools with the MCP server.
    
    Args:
        mcp_server: The MCP server instance to register tools with
    """
    logger.info("Registering all MCP tools...")
    
    # Register GitHub tools
    try:
        register_github_tools(mcp_server)
        logger.info("Successfully registered GitHub tools")
    except Exception as e:
        logger.error(f"Failed to register GitHub tools: {str(e)}", exc_info=True)
    
    # Register Slack tools
    try:
        register_slack_tools(mcp_server)
        logger.info("Successfully registered Slack tools")
    except Exception as e:
        logger.error(f"Failed to register Slack tools: {str(e)}", exc_info=True)
    
    logger.info(f"Total tools registered: {len(mcp_server.tools)}")
