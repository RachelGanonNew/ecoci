from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """User model representing application users."""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, index=True, nullable=True)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    repositories = relationship("Repository", back_populates="owner")
    slack_integration = relationship("SlackIntegration", back_populates="user", uselist=False)
    findings = relationship("Finding", back_populates="reported_by")
    recommendations = relationship("Recommendation", back_populates="created_by")

class SlackIntegration(Base, TimestampMixin):
    """Slack integration details for users."""
    __tablename__ = "slack_integrations"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slack_user_id = Column(String(100), nullable=False)
    access_token = Column(String(500), nullable=False)
    team_id = Column(String(100), nullable=False)
    team_name = Column(String(255))
    bot_user_id = Column(String(100))
    
    # Relationships
    user = relationship("User", back_populates="slack_integration")
