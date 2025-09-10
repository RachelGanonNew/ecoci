from pydantic import BaseModel, Field
from typing import Optional

class Token(BaseModel):
    """Schema for access token response."""
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[int] = None  # user ID
    exp: Optional[int] = None  # expiration timestamp
    iat: Optional[int] = None  # issued at timestamp
    jti: Optional[str] = None  # JWT ID
