"""
MCP (Multi-Component Protocol) API Endpoints

This module provides the FastAPI router for the MCP server's HTTP API.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
import json

from ....services.mcp_server import mcp_server, ToolDefinition, RegisteredAgent, ToolExecutionResult
from ....core.security import get_current_user, verify_api_key
from ....models.user import User
from ....schemas.mcp import (
    ToolRegistrationRequest,
    ToolExecutionRequest,
    AgentRegistrationRequest,
    ExecutionLogFilter,
    PaginatedResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/agents/register", response_model=RegisteredAgent)
async def register_agent(
    request: Request,
    agent_data: AgentRegistrationRequest,
    current_user: User = Depends(get_current_user)
) -> RegisteredAgent:
    """
    Register a new agent with the MCP server.
    
    Agents must register before they can execute tools. Each agent must provide
    a unique ID and a list of capabilities.
    """
    try:
        # Extract request metadata
        metadata = {
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
            "user_id": str(current_user.id) if current_user else None,
            "capabilities": agent_data.capabilities
        }
        
        # Register the agent
        agent = await mcp_server.register_agent(
            agent_id=agent_data.agent_id,
            capabilities=agent_data.capabilities,
            metadata=metadata
        )
        
        return agent
        
    except Exception as e:
        logger.error(f"Agent registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent registration failed: {str(e)}"
        )

@router.post("/tools/register", status_code=status.HTTP_201_CREATED)
async def register_tool(
    tool_data: ToolRegistrationRequest,
    current_user: User = Depends(get_current_user),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Register a new tool with the MCP server.
    
    Tools must be registered before they can be executed by agents. Each tool
    must provide a name, description, and parameter schema.
    """
    try:
        # Register the tool with the MCP server
        mcp_server.register_tool(
            tool_definition={
                "name": tool_data.name,
                "description": tool_data.description,
                "parameters": tool_data.parameters,
                "required": tool_data.required or [],
                "timeout_seconds": tool_data.timeout_seconds or 30
            },
            handler=tool_data.handler
        )
        
        return {
            "status": "success",
            "message": f"Tool '{tool_data.name}' registered successfully"
        }
        
    except Exception as e:
        logger.error(f"Tool registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool registration failed: {str(e)}"
        )

@router.post("/tools/execute/{tool_name}", response_model=ToolExecutionResult)
async def execute_tool(
    tool_name: str,
    execution_request: ToolExecutionRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> ToolExecutionResult:
    """
    Execute a tool with the provided parameters.
    
    Only registered agents can execute tools. The agent must provide a valid
    agent_id and the tool must be registered with the MCP server.
    """
    try:
        # Execute the tool
        result = await mcp_server.execute_tool(
            tool_name=tool_name,
            parameters=execution_request.parameters,
            agent_id=execution_request.agent_id,
            request_id=execution_request.request_id,
            user_context={
                "user_id": str(current_user.id) if current_user else None,
                "email": current_user.email if current_user else None,
                "ip_address": request.client.host if request.client else None,
                **execution_request.user_context
            } if execution_request.user_context else {
                "user_id": str(current_user.id) if current_user else None,
                "email": current_user.email if current_user else None,
                "ip_address": request.client.host if request.client else None
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )

@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_tools(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    List all registered tools with their definitions.
    """
    tools = []
    for tool_name, (tool_def, _) in mcp_server.tools.items():
        tools.append({
            "name": tool_def.name,
            "description": tool_def.description,
            "parameters": tool_def.parameters,
            "required": tool_def.required,
            "timeout_seconds": tool_def.timeout_seconds
        })
    return tools

@router.get("/agents", response_model=List[Dict[str, Any]])
async def list_agents(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    List all registered agents.
    """
    return [
        {
            "agent_id": agent.agent_id,
            "capabilities": agent.capabilities,
            "status": agent.status,
            "registered_at": agent.registered_at,
            "last_seen": agent.last_seen,
            "metadata": agent.metadata
        }
        for agent in mcp_server.agents.values()
    ]

@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get server metrics and statistics.
    """
    return mcp_server.get_metrics()

@router.get("/logs/executions", response_model=PaginatedResponse)
async def get_execution_logs(
    filter_params: ExecutionLogFilter = Depends(),
    current_user: User = Depends(get_current_user)
) -> PaginatedResponse:
    """
    Get execution logs with filtering and pagination.
    """
    try:
        # Apply filters
        logs = mcp_server.execution_log
        
        if filter_params.agent_id:
            logs = [log for log in logs if log.get("agent_id") == filter_params.agent_id]
            
        if filter_params.tool_name:
            logs = [log for log in logs if log.get("tool") == filter_params.tool_name]
            
        if filter_params.status:
            logs = [log for log in logs if log.get("status") == filter_params.status]
            
        if filter_params.start_time:
            logs = [log for log in logs if log["timestamp"] >= filter_params.start_time]
            
        if filter_params.end_time:
            logs = [log for log in logs if log["timestamp"] <= filter_params.end_time]
        
        # Apply pagination
        total = len(logs)
        start = (filter_params.page - 1) * filter_params.page_size
        end = start + filter_params.page_size
        paginated_logs = logs[start:end]
        
        return {
            "items": paginated_logs,
            "total": total,
            "page": filter_params.page,
            "page_size": filter_params.page_size,
            "total_pages": (total + filter_params.page_size - 1) // filter_params.page_size
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution logs: {str(e)}"
        )

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

# Add error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@router.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
