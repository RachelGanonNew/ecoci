from sqlalchemy import Column, String, Integer, ForeignKey, Enum, JSON, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import enum

class RepositoryProvider(enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"

class Repository(Base, TimestampMixin):
    """Repository model representing source code repositories."""
    __tablename__ = "repositories"
    
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), nullable=False)
    description = Column(String(1000))
    url = Column(String(1000), nullable=False)
    provider = Column(Enum(RepositoryProvider), nullable=False)
    provider_id = Column(String(255), nullable=False)  # ID from the provider (e.g., GitHub repo ID)
    is_private = Column(Boolean, default=False)
    default_branch = Column(String(100), default="main")
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    scans = relationship("RepositoryScan", back_populates="repository")
    integrations = relationship("RepositoryIntegration", back_populates="repository")
    findings = relationship("Finding", back_populates="repository")
    recommendations = relationship("Recommendation", back_populates="repository")

class RepositoryIntegration(Base, TimestampMixin):
    """Integration details for repositories."""
    __tablename__ = "repository_integrations"
    
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # e.g., 'github', 'gitlab'
    installation_id = Column(String(255))  # GitHub App installation ID or similar
    access_token = Column(String(500))
    refresh_token = Column(String(500))
    expires_at = Column(DateTime)
    metadata_ = Column("metadata", JSON)
    
    # Relationships
    repository = relationship("Repository", back_populates="integrations")

class RepositoryScan(Base, TimestampMixin):
    """Model representing a scan of a repository for optimizations."""
    __tablename__ = "repository_scans"
    
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(String(1000))
    
    # Scan results
    total_issues_found = Column(Integer, default=0)
    estimated_cost_savings = Column(Float, default=0.0)  # in USD
    estimated_carbon_reduction = Column(Float, default=0.0)  # in kg CO2e
    
    # Relationships
    repository = relationship("Repository", back_populates="scans")
    findings = relationship("ScanFinding", back_populates="scan")

class ScanFindingType(enum.Enum):
    CI_OPTIMIZATION = "ci_optimization"
    DOCKER_OPTIMIZATION = "docker_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    OTHER = "other"

class ScanFindingSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ScanFinding(Base, TimestampMixin):
    """Individual findings from a repository scan."""
    __tablename__ = "scan_findings"
    
    scan_id = Column(Integer, ForeignKey("repository_scans.id"), nullable=False)
    finding_type = Column(Enum(ScanFindingType), nullable=False)
    severity = Column(Enum(ScanFindingSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(2000))
    file_path = Column(String(1000))
    line_number = Column(Integer)
    code_snippet = Column(String(2000))
    
    # Estimated impact
    estimated_cost_savings = Column(Float)  # in USD per month
    estimated_carbon_reduction = Column(Float)  # in kg CO2e per month
    
    # Fix details
    recommended_fix = Column(String(2000))
    fix_difficulty = Column(String(50))  # easy, medium, hard
    fix_effort = Column(String(50))  # minutes, hours, days
    
    # Status tracking
    status = Column(String(50), default="open")  # open, in_progress, resolved, wont_fix, fixed
    resolved_at = Column(DateTime)
    resolved_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    scan = relationship("RepositoryScan", back_populates="findings")
    pull_requests = relationship("PullRequest", back_populates="finding")
