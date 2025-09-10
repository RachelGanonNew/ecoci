from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class UserUpdate(UserBase):
    """Schema for updating an existing user."""
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    current_password: Optional[str] = None

class UserInDBBase(UserBase):
    """Base schema for user stored in DB."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class User(UserInDBBase):
    """User schema for API responses."""
    pass

class UserInDB(UserInDBBase):
    """User schema for internal use, includes hashed password."""
    hashed_password: str

class UserProfile(BaseModel):
    """User profile schema with additional information."""
    user: User
    repositories_count: int = 0
    scans_count: int = 0
    findings_count: int = 0
    estimated_savings: float = 0.0
    carbon_reduction: float = 0.0

class UserStats(BaseModel):
    """User statistics schema."""
    total_repositories: int = 0
    total_scans: int = 0
    total_findings: int = 0
    open_findings: int = 0
    fixed_findings: int = 0
    estimated_monthly_savings: float = 0.0
    estimated_annual_savings: float = 0.0
    total_carbon_reduction: float = 0.0  # in kg CO2e

class UserNotificationSettings(BaseModel):
    """User notification settings schema."""
    email_notifications: bool = True
    slack_notifications: bool = False
    daily_summary: bool = True
    weekly_report: bool = True
    critical_issues: bool = True
    new_recommendations: bool = True
    scan_completed: bool = True
    pr_created: bool = True
    pr_merged: bool = True

class UserIntegrations(BaseModel):
    """User integrations schema."""
    github_connected: bool = False
    github_username: Optional[str] = None
    slack_connected: bool = False
    slack_team: Optional[str] = None
    slack_channel: Optional[str] = None

class UserPreferences(BaseModel):
    """User preferences schema."""
    theme: str = "light"  # 'light', 'dark', 'system'
    timezone: str = "UTC"
    language: str = "en"
    currency: str = "USD"
    carbon_unit: str = "kg"  # 'kg', 'lbs', 't'
    energy_unit: str = "kWh"  # 'kWh', 'MJ', 'BTU'
