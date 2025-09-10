from fastapi import APIRouter

api_router = APIRouter()

# Import and include routers
from .endpoints import auth, repositories, scans, recommendations, findings, mcp

# Include the routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["MCP Server"])
