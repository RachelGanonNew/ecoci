from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class RepositoryProvider(str, Enum):
    """Supported repository providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    OTHER = "other"

class RepositoryVisibility(str, Enum):
    """Repository visibility levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"

class RepositoryBase(BaseModel):
    """Base repository schema with common fields."""
    name: str = Field(..., max_length=255)
    full_name: str = Field(..., max_length=512)
    description: Optional[str] = None
    url: HttpUrl
    provider: RepositoryProvider
    provider_id: str = Field(..., max_length=255)
    is_private: bool = True
    default_branch: str = "main"
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    last_commit_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class RepositoryCreate(RepositoryBase):
    """Schema for creating a new repository."""
    owner_id: int

class RepositoryUpdate(BaseModel):
    """Schema for updating a repository."""
    description: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class RepositoryInDBBase(RepositoryBase):
    """Base schema for repository stored in DB."""
    id: int
    owner_id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Repository(RepositoryInDBBase):
    """Repository schema for API responses."""
    pass

class RepositoryWithStats(Repository):
    """Repository schema with statistics."""
    total_scans: int = 0
    total_findings: int = 0
    open_findings: int = 0
    last_scan_at: Optional[datetime] = None
    estimated_monthly_savings: float = 0.0
    estimated_annual_savings: float = 0.0
    total_carbon_reduction: float = 0.0  # in kg CO2e

class ScanStatus(str, Enum):
    """Status of a repository scan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScanBase(BaseModel):
    """Base scan schema with common fields."""
    status: ScanStatus = ScanStatus.PENDING
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class ScanCreate(ScanBase):
    """Schema for creating a new scan."""
    repository_id: int
    triggered_by: Optional[int] = None

class ScanUpdate(BaseModel):
    """Schema for updating a scan."""
    status: Optional[ScanStatus] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ScanInDBBase(ScanBase):
    """Base schema for scan stored in DB."""
    id: int
    repository_id: int
    triggered_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Scan(ScanInDBBase):
    """Scan schema for API responses."""
    pass

class ScanWithFindings(Scan):
    """Scan schema with findings included."""
    findings: List["Finding"] = []
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0

class FindingSeverity(str, Enum):
    """Severity levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class FindingType(str, Enum):
    """Types of findings."""
    CI_OPTIMIZATION = "ci_optimization"
    DOCKER_OPTIMIZATION = "docker_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SECURITY = "security"
    COST_SAVING = "cost_saving"
    CARBON_REDUCTION = "carbon_reduction"
    OTHER = "other"

class FindingStatus(str, Enum):
    """Status of a finding."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    FALSE_POSITIVE = "false_positive"

class FindingBase(BaseModel):
    """Base finding schema with common fields."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    finding_type: FindingType
    severity: FindingSeverity
    status: FindingStatus = FindingStatus.OPEN
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    estimated_cost_savings: Optional[float] = None  # in USD
    estimated_carbon_reduction: Optional[float] = None  # in kg CO2e
    recommended_fix: Optional[str] = None
    fix_difficulty: Optional[str] = None  # easy, medium, hard
    fix_effort: Optional[str] = None  # e.g., "1 hour", "2-4 hours"
    metadata: Dict[str, Any] = {}

class FindingCreate(FindingBase):
    """Schema for creating a new finding."""
    scan_id: int
    repository_id: int

class FindingUpdate(BaseModel):
    """Schema for updating a finding."""
    status: Optional[FindingStatus] = None
    assigned_to: Optional[int] = None
    comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class FindingInDBBase(FindingBase):
    """Base schema for finding stored in DB."""
    id: int
    scan_id: int
    repository_id: int
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Finding(FindingInDBBase):
    """Finding schema for API responses."""
    pass

# Update forward references
ScanWithFindings.update_forward_refs()

class ScanSummary(BaseModel):
    """Summary of a scan with aggregated statistics."""
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    info_findings: int = 0
    estimated_cost_savings: float = 0.0  # in USD
    estimated_carbon_reduction: float = 0.0  # in kg CO2e
    findings_by_type: Dict[FindingType, int] = {}
    findings_by_severity: Dict[FindingSeverity, int] = {}

class RepositoryScanSummary(BaseModel):
    """Summary of scans for a repository."""
    repository: Repository
    last_scan: Optional[Scan] = None
    total_scans: int = 0
    total_findings: int = 0
    open_findings: int = 0
    scan_summary: Optional[ScanSummary] = None

class RepositoryWithScans(Repository):
    """Repository schema with scans included."""
    scans: List[Scan] = []
    scan_summary: Optional[ScanSummary] = None
