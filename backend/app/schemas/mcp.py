"""
MCP (Multi-Component Protocol) Schema Definitions

This module contains Pydantic models for request/response validation in the MCP API.
"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum
from datetime import datetime

class ToolParameterType(str, Enum):
    """Supported parameter types for tool definitions."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class ToolParameterSchema(BaseModel):
    """Schema for defining a tool parameter."""
    type: ToolParameterType
    description: Optional[str] = None
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    items: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, 'ToolParameterSchema']] = None
    required: Optional[List[str]] = None
    format: Optional[str] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    min_length: Optional[int] = Field(None, alias="minLength")
    max_length: Optional[int] = Field(None, alias="maxLength")
    pattern: Optional[str] = None

class ToolRegistrationRequest(BaseModel):
    """Request model for registering a new tool."""
    name: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    description: str = Field(..., min_length=1, max_length=1000)
    parameters: Dict[str, ToolParameterSchema]
    required: Optional[List[str]] = None
    timeout_seconds: int = Field(30, ge=1, le=300)
    handler: Any = Field(..., exclude=True)  # Actual handler function, excluded from schema

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            'function': lambda v: str(v)
        }

class AgentRegistrationRequest(BaseModel):
    """Request model for registering a new agent."""
    agent_id: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    capabilities: List[str] = Field(..., min_items=1)
    metadata: Optional[Dict[str, Any]] = None

class ToolExecutionRequest(BaseModel):
    """Request model for executing a tool."""
    agent_id: str = Field(..., description="ID of the agent executing the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = Field(
        None, 
        description="Optional request ID for tracking",
        min_length=1,
        max_length=100
    )
    user_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context about the user or request"
    )

class ExecutionLogFilter(BaseModel):
    """Filter parameters for querying execution logs."""
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)

class PaginatedResponse(BaseModel):
    """Generic paginated response model."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int

class ToolExecutionStatus(str, Enum):
    """Status of a tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ToolExecutionResponse(BaseModel):
    """Response model for a tool execution."""
    execution_id: str
    tool_name: str
    agent_id: str
    status: ToolExecutionStatus
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentStatus(str, Enum):
    """Status of a registered agent."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class AgentInfo(BaseModel):
    """Information about a registered agent."""
    agent_id: str
    capabilities: List[str]
    status: AgentStatus
    registered_at: datetime
    last_seen: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolInfo(BaseModel):
    """Information about a registered tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]
    timeout_seconds: int

class ServerMetrics(BaseModel):
    """Server metrics and statistics."""
    total_requests: int
    successful_executions: int
    failed_executions: int
    active_agents: int
    registered_tools: int
    uptime_seconds: float

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    dependencies: Dict[str, str] = Field(default_factory=dict)

# Update forward references for recursive models
ToolParameterSchema.update_forward_refs()

# Add custom validators
@validator('parameters', pre=True, each_item=True)
def validate_parameters(cls, v):
    """Ensure parameters have valid types and constraints."""
    if not isinstance(v, dict):
        raise ValueError("Parameters must be a dictionary")
    
    if 'type' not in v:
        raise ValueError("Parameter must have a 'type' field")
    
    param_type = v.get('type')
    if param_type not in [t.value for t in ToolParameterType]:
        raise ValueError(f"Invalid parameter type: {param_type}")
    
    return v

@validator('capabilities', each_item=True)
def validate_capabilities(cls, v):
    """Ensure capabilities are valid strings."""
    if not isinstance(v, str) or not v.strip():
        raise ValueError("Capability must be a non-empty string")
    return v.strip()

# Add example schemas for documentation
class Examples:
    TOOL_REGISTRATION = {
        "name": "calculate_total",
        "description": "Calculate the total of a list of numbers",
        "parameters": {
            "numbers": {
                "type": "array",
                "items": {"type": "number"},
                "description": "List of numbers to sum"
            }
        },
        "required": ["numbers"],
        "timeout_seconds": 10
    }
    
    TOOL_EXECUTION = {
        "agent_id": "agent-123",
        "parameters": {
            "numbers": [1, 2, 3, 4, 5]
        },
        "request_id": "req-12345",
        "user_context": {
            "user_id": "user-123",
            "session_id": "sess-abc123"
        }
    }
    
    AGENT_REGISTRATION = {
        "agent_id": "data-processor-1",
        "capabilities": ["data_processing", "report_generation"],
        "metadata": {
            "version": "1.0.0",
            "environment": "production"
        }
    }
