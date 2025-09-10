"""Mock implementation of MCP endpoints for local development."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional

router = APIRouter()

@router.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """Mock implementation of tools listing."""
    return {
        "tools": [
            {
                "name": "mock-tool-1",
                "description": "Mock tool for local development",
                "parameters": {}
            },
            {
                "name": "mock-tool-2",
                "description": "Another mock tool for local development",
                "parameters": {}
            }
        ]
    }

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

# Add more mock endpoints as needed
