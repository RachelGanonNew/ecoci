"""
Finding model for storing security and quality findings.
"""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base, BaseMixin

class FindingSeverity(enum.Enum):
    """Severity levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class FindingStatus(enum.Enum):
    """Status of a finding."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    FALSE_POSITIVE = "false_positive"

class Finding(Base, BaseMixin):
    """Base finding model for storing various types of findings."""
    __tablename__ = "findings"
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(Enum(FindingSeverity), nullable=False)
    status = Column(Enum(FindingStatus), default=FindingStatus.OPEN)
    file_path = Column(String(1000))
    line_number = Column(Integer)
    code_snippet = Column(Text)
    recommendation = Column(Text)
    
    # Foreign keys
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    scan_id = Column(Integer, ForeignKey("repository_scans.id"))
    
    # Relationships
    repository = relationship("Repository", back_populates="findings")
    scan = relationship("RepositoryScan", back_populates="findings")
    recommendations = relationship("Recommendation", back_populates="finding")
    reported_by_id = Column(Integer, ForeignKey("users.id"))
    reported_by = relationship("User", back_populates="findings")
    
    def __repr__(self):
        return f"<Finding(id={self.id}, title='{self.title}', severity='{self.severity}')>"

# Add any additional finding-related models or enums below
