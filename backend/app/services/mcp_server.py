"""
MCP (Multi-Component Protocol) Server for Agentic APIs

This module implements a production-ready MCP server that enables secure,
scalable communication between AI agents and external services.
"""
from typing import Dict, List, Any, Optional, Callable, Awaitable
import logging
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ToolDefinition(BaseModel):
    """Definition of a tool that can be executed by agents."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = []
    timeout_seconds: int = 30
    
class RegisteredAgent(BaseModel):
    """Metadata for a registered agent."""
    agent_id: str
    capabilities: List[str]
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "active"
    metadata: Dict[str, Any] = {}

class MCPServer:
    """
    MCP Server for managing agent communications and tool execution.
    
    This class provides a production-ready implementation of an MCP server that:
    - Registers and manages agent connections
    - Maintains a registry of available tools
    - Handles secure tool execution with permission checks
    - Provides monitoring and metrics
    """
    
    def __init__(self):
        self.agents: Dict[str, RegisteredAgent] = {}
        self.tools: Dict[str, tuple[ToolDefinition, Callable[..., Awaitable[Any]]]] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.metrics = {
            "total_requests": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "active_agents": 0,
        }
    
    async def register_agent(
        self, 
        agent_id: str, 
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> RegisteredAgent:
        """Register a new agent with the MCP server."""
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")
            
        agent = RegisteredAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            metadata=metadata or {}
        )
        
        self.agents[agent_id] = agent
        self.metrics["active_agents"] = len([a for a in self.agents.values() if a.status == "active"])
        
        logger.info(f"Registered agent: {agent_id} with capabilities: {capabilities}")
        return agent
    
    def register_tool(
        self, 
        tool_definition: Dict[str, Any], 
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a new tool with the MCP server."""
        try:
            tool_def = ToolDefinition(**tool_definition)
            self.tools[tool_def.name] = (tool_def, handler)
            logger.info(f"Registered tool: {tool_def.name}")
        except Exception as e:
            logger.error(f"Failed to register tool: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tool definition: {str(e)}"
            )
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_id: str,
        request_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ToolExecutionResult:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Dictionary of parameters for the tool
            agent_id: ID of the agent making the request
            request_id: Optional request ID for tracking
            user_context: Optional user context for the execution
            
        Returns:
            ToolExecutionResult containing the result or error
        """
        self.metrics["total_requests"] += 1
        execution_id = request_id or self._generate_request_id()
        start_time = datetime.now(timezone.utc)
        
        try:
            # Validate agent
            agent = self.agents.get(agent_id)
            if not agent or agent.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Agent {agent_id} is not registered or inactive"
                )
            
            # Update last seen
            agent.last_seen = datetime.now(timezone.utc).isoformat()
            
            # Get tool definition and handler
            if tool_name not in self.tools:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tool '{tool_name}' not found"
                )
                
            tool_def, handler = self.tools[tool_name]
            
            # Validate parameters
            self._validate_parameters(tool_def, parameters)
            
            # Execute the tool
            logger.info(f"Executing tool: {tool_name} with params: {parameters}")
            result = await handler(**parameters, user_context=user_context or {})
            
            # Log successful execution
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.metrics["successful_executions"] += 1
            
            execution_result = ToolExecutionResult(
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
            
            self._log_execution(
                execution_id=execution_id,
                tool_name=tool_name,
                agent_id=agent_id,
                parameters=parameters,
                result=execution_result,
                status="success",
                execution_time_ms=execution_time
            )
            
            return execution_result
            
        except HTTPException:
            raise
            
        except Exception as e:
            # Log the error
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self.metrics["failed_executions"] += 1
            
            error_result = ToolExecutionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_time
            )
            
            self._log_execution(
                execution_id=execution_id,
                tool_name=tool_name,
                agent_id=agent_id,
                parameters=parameters,
                result=error_result,
                status="error",
                execution_time_ms=execution_time,
                error=str(e)
            )
            
            logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tool execution failed: {str(e)}"
            )
    
    def _validate_parameters(self, tool_def: ToolDefinition, parameters: Dict[str, Any]) -> None:
        """Validate parameters against the tool definition."""
        # Check required parameters
        for param in tool_def.required:
            if param not in parameters:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {param}"
                )
        
        # Check parameter types (simplified)
        for param, value in parameters.items():
            if param in tool_def.parameters:
                expected_type = tool_def.parameters[param].get("type")
                if expected_type and not isinstance(value, self._get_python_type(expected_type)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Parameter '{param}' should be of type {expected_type}"
                    )
    
    def _get_python_type(self, type_str: str) -> type:
        """Convert JSON schema type to Python type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_map.get(type_str, str)
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
    
    def _log_execution(
        self,
        execution_id: str,
        tool_name: str,
        agent_id: str,
        parameters: Dict[str, Any],
        result: ToolExecutionResult,
        status: str,
        execution_time_ms: float,
        error: Optional[str] = None
    ) -> None:
        """Log tool execution details."""
        log_entry = {
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "agent_id": agent_id,
            "parameters": parameters,
            "status": status,
            "execution_time_ms": execution_time_ms,
            "result": result.dict() if hasattr(result, 'dict') else str(result),
        }
        
        if error:
            log_entry["error"] = error
        
        self.execution_log.append(log_entry)
        
        # Keep only the last 1000 executions in memory
        if len(self.execution_log) > 1000:
            self.execution_log = self.execution_log[-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current server metrics."""
        return {
            **self.metrics,
            "registered_tools": len(self.tools),
            "active_agents": len([a for a in self.agents.values() if a.status == "active"]),
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds()
            if hasattr(self, 'start_time') else 0
        }
    
    def start(self) -> None:
        """Start the MCP server."""
        self.start_time = datetime.now(timezone.utc)
        logger.info("MCP Server started")
    
    def stop(self) -> None:
        """Stop the MCP server."""
        logger.info("MCP Server stopped")

# Global instance
mcp_server = MCPServer()

# Start the server when module is imported
mcp_server.start()
