"""
CRUD operations for User model.
"""
from typing import Optional, Any, Dict, Union, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.password import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
    """Get a user by API key."""
    return db.query(User).filter(User.api_key == api_key).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        is_superuser=user.is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(
    db: Session, db_user: User, user_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    """Update a user."""
    user_data = user_in.dict(exclude_unset=True) if isinstance(user_in, dict) else user_in
    
    if "password" in user_data and user_data["password"]:
        hashed_password = get_password_hash(user_data["password"])
        del user_data["password"]
        user_data["hashed_password"] = hashed_password
    
    for field, value in user_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def is_active(user: User) -> bool:
    """Check if a user is active."""
    return user.is_active

def is_superuser(user: User) -> bool:
    """Check if a user is a superuser."""
    return user.is_superuser
