"""
Security utilities for the application.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import TokenData, decode_token
from app.core.password import pwd_context, verify_password, get_password_hash
from app.crud.user import get_user_by_email, get_user_by_api_key
from app.database import get_db_session
from app.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

# Password verification and hashing functions are now in core.password

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db_session)
) -> User:
    """
    Verify the API key and return the associated user.
    
    Args:
        api_key: The API key from the request header
        db: Database session
        
    Returns:
        User: The user associated with the API key
        
    Raises:
        HTTPException: If the API key is invalid or not provided
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
        
    user = get_user_by_api_key(db, api_key=api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user


async def get_current_user(
    db: Session = Depends(get_db_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
