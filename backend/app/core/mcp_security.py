"""
MCP Security Middleware

This module provides authentication and authorization for the MCP server.
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, Callable, Awaitable
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
import time
import logging

from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenPayload

logger = logging.getLogger(__name__)

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)

class AuthError(Exception):
    """Base authentication error class."""
    def __init__(self, error: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.error = error
        self.status_code = status_code

class APIKeyAuth:
    """API Key authentication handler."""
    
    def __init__(self, api_keys: Dict[str, Dict[str, Any]] = None):
        self.api_keys = api_keys or {}
    
    async def __call__(self, api_key: str = Depends(api_key_header)) -> Dict[str, Any]:
        if not api_key:
            raise AuthError("API key is missing")
        
        if api_key not in self.api_keys:
            raise AuthError("Invalid API key")
        
        key_info = self.api_keys[api_key]
        if key_info.get("revoked", False):
            raise AuthError("API key has been revoked")
        
        return key_info

class JWTAuth:
    """JWT authentication handler."""
    
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
    
    async def __call__(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_auth)
    ) -> TokenPayload:
        if not credentials:
            if self.auto_error:
                raise AuthError("Authorization header is missing")
            return None
            
        if credentials.scheme.lower() != "bearer":
            raise AuthError("Invalid authentication scheme. Use 'Bearer'")
        
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_aud": False}
            )
            token_data = TokenPayload(**payload)
            
            # Check token expiration
            if token_data.exp < time.time():
                raise AuthError("Token has expired")
                
            return token_data
            
        except (JWTError, ValidationError) as e:
            logger.error(f"JWT validation failed: {str(e)}")
            raise AuthError("Could not validate credentials")

class MCPAuthDependency:
    """Dependency for MCP authentication."""
    
    def __init__(self, required_scopes: Optional[list] = None):
        self.required_scopes = required_scopes or []
    
    async def __call__(
        self,
        request: Request,
        api_key_auth: APIKeyAuth = Depends(APIKeyAuth()),
        token_data: Optional[TokenPayload] = Depends(JWTAuth(auto_error=False))
    ) -> Dict[str, Any]:
        # Check for API key first
        try:
            api_key_info = await api_key_auth(request.headers.get("X-API-Key"))
            return {
                "auth_method": "api_key",
                "api_key_info": api_key_info,
                "scopes": api_key_info.get("scopes", [])
            }
        except AuthError:
            pass
        
        # Fall back to JWT
        if token_data:
            return {
                "auth_method": "jwt",
                "user_id": token_data.sub,
                "scopes": token_data.scopes or []
            }
        
        # No valid auth found
        raise AuthError("Not authenticated")

def has_required_scopes(
    required_scopes: list,
    user_scopes: list
) -> bool:
    """Check if user has all required scopes."""
    if not required_scopes:
        return True
    return all(scope in user_scopes for scope in required_scopes)

class MCPAuthMiddleware:
    """Middleware for MCP authentication and authorization."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        request = Request(scope, receive)
        
        # Skip auth for public endpoints
        if self._is_public_path(request.url.path):
            return await self.app(scope, receive, send)
        
        # Authenticate the request
        try:
            auth_dep = MCPAuthDependency()
            auth_info = await auth_dep(request)
            
            # Attach auth info to request state
            request.state.auth = auth_info
            
            # Check required scopes if specified in route
            route = request.scope.get("route")
            if hasattr(route, "endpoint") and hasattr(route.endpoint, "required_scopes"):
                required_scopes = route.endpoint.required_scopes
                if not has_required_scopes(required_scopes, auth_info.get("scopes", [])):
                    raise AuthError("Insufficient permissions", status.HTTP_403_FORBIDDEN)
            
            return await self.app(scope, receive, send)
            
        except AuthError as e:
            response = JSONResponse(
                status_code=e.status_code,
                content={"detail": e.error}
            )
            await response(scope, receive, send)
            return
    
    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public (no auth required)."""
        public_paths = [
            "/mcp/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        return any(path.startswith(p) for p in public_paths)

def require_auth(required_scopes: Optional[list] = None) -> Callable:
    """Dependency to require authentication with optional scopes."""
    async def dependency(
        request: Request,
        auth: Dict[str, Any] = Depends(MCPAuthDependency(required_scopes=required_scopes))
    ) -> Dict[str, Any]:
        return auth
    
    # Store required scopes on the dependency for the middleware to access
    dependency.required_scopes = required_scopes or []
    return dependency

# Example usage in FastAPI route:
# @router.get("/secure-endpoint")
# async def secure_endpoint(
#     auth: dict = Depends(require_auth(["read:data"]))
# ):
#     return {"message": "You have access!"}
