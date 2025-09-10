"""
Recommendation model for storing optimization recommendations.
"""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Text, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from .base import Base, BaseMixin

class RecommendationStatus(enum.Enum):
    """Status of a recommendation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"

class RecommendationType(enum.Enum):
    """Types of recommendations."""
    CI_OPTIMIZATION = "ci_optimization"
    DOCKER_OPTIMIZATION = "docker_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SECURITY = "security"
    COST_SAVING = "cost_saving"
    OTHER = "other"

class Recommendation(Base, BaseMixin):
    """Model for storing optimization recommendations."""
    __tablename__ = "recommendations"
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    recommendation_type = Column(Enum(RecommendationType), nullable=False)
    status = Column(Enum(RecommendationStatus), default=RecommendationStatus.PENDING)
    priority = Column(String(50))  # low, medium, high, critical
    estimated_impact = Column(String(255))
    estimated_savings = Column(Float)
    estimated_effort = Column(String(50))  # S, M, L, XL
    
    # Foreign keys
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    finding_id = Column(Integer, ForeignKey("findings.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, title='{self.title}', type='{self.recommendation_type}')>"
