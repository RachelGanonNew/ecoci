from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class RecommendationType(str, Enum):
    """Types of recommendations."""
    CI_OPTIMIZATION = "ci_optimization"
    DOCKER_OPTIMIZATION = "docker_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    SCHEDULING_OPTIMIZATION = "scheduling_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SECURITY = "security"
    COST_SAVING = "cost_saving"
    CARBON_REDUCTION = "carbon_reduction"
    OTHER = "other"

class RecommendationStatus(str, Enum):
    """Status of a recommendation."""
    PENDING = "pending"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"

class RecommendationImpact(str, Enum):
    """Impact level of a recommendation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecommendationEffort(str, Enum):
    """Implementation effort for a recommendation."""
    QUICK_WIN = "quick_win"  # < 1 hour
    SMALL = "small"          # 1-4 hours
    MEDIUM = "medium"        # 4-8 hours
    LARGE = "large"          # 1-3 days
    EXTRA_LARGE = "xlarge"   # > 3 days

class RecommendationBase(BaseModel):
    """Base recommendation schema with common fields."""
    title: str = Field(..., max_length=255)
    description: str
    recommendation_type: RecommendationType
    status: RecommendationStatus = RecommendationStatus.PENDING
    impact: RecommendationImpact
    effort: RecommendationEffort
    estimated_savings: Optional[float] = None  # in USD
    estimated_carbon_reduction: Optional[float] = None  # in kg CO2e
    implementation_details: Optional[str] = None
    pr_url: Optional[HttpUrl] = None
    metadata: Dict[str, Any] = {}

class RecommendationCreate(RecommendationBase):
    """Schema for creating a new recommendation."""
    repository_id: int
    scan_id: Optional[int] = None
    finding_id: Optional[int] = None
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None

class RecommendationUpdate(BaseModel):
    """Schema for updating a recommendation."""
    status: Optional[RecommendationStatus] = None
    assigned_to: Optional[int] = None
    pr_url: Optional[HttpUrl] = None
    comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RecommendationInDBBase(RecommendationBase):
    """Base schema for recommendation stored in DB."""
    id: int
    repository_id: int
    scan_id: Optional[int] = None
    finding_id: Optional[int] = None
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Recommendation(RecommendationInDBBase):
    """Recommendation schema for API responses."""
    pass

class RecommendationWithRelated(Recommendation):
    """Recommendation schema with related entities."""
    repository: Optional[Dict[str, Any]] = None
    scan: Optional[Dict[str, Any]] = None
    finding: Optional[Dict[str, Any]] = None
    created_by_user: Optional[Dict[str, Any]] = None
    assigned_to_user: Optional[Dict[str, Any]] = None

class RecommendationSummary(BaseModel):
    """Summary of recommendations."""
    total: int = 0
    pending: int = 0
    approved: int = 0
    implemented: int = 0
    rejected: int = 0
    by_type: Dict[RecommendationType, int] = {}
    by_impact: Dict[RecommendationImpact, int] = {}
    by_effort: Dict[RecommendationEffort, int] = {}
    total_estimated_savings: float = 0.0
    total_estimated_carbon_reduction: float = 0.0

class RecommendationBulkUpdate(BaseModel):
    """Schema for bulk updating recommendations."""
    recommendation_ids: List[int]
    status: Optional[RecommendationStatus] = None
    assigned_to: Optional[int] = None
    comment: Optional[str] = None

class RecommendationFilter(BaseModel):
    """Filter options for querying recommendations."""
    repository_id: Optional[int] = None
    scan_id: Optional[int] = None
    finding_id: Optional[int] = None
    recommendation_type: Optional[RecommendationType] = None
    status: Optional[RecommendationStatus] = None
    impact: Optional[RecommendationImpact] = None
    effort: Optional[RecommendationEffort] = None
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class RecommendationStats(BaseModel):
    """Statistics about recommendations."""
    total_recommendations: int = 0
    recommendations_implemented: int = 0
    recommendations_pending: int = 0
    recommendations_approved: int = 0
    recommendations_rejected: int = 0
    total_estimated_savings: float = 0.0
    total_estimated_carbon_reduction: float = 0.0
    recommendations_by_type: Dict[RecommendationType, int] = {}
    recommendations_by_impact: Dict[RecommendationImpact, int] = {}
    recommendations_by_effort: Dict[RecommendationEffort, int] = {}

class RecommendationCommentBase(BaseModel):
    """Base schema for recommendation comments."""
    content: str
    is_internal: bool = False  # Whether the comment is visible to all or just the team

class RecommendationCommentCreate(RecommendationCommentBase):
    """Schema for creating a new recommendation comment."""
    user_id: int
    recommendation_id: int

class RecommendationCommentUpdate(BaseModel):
    """Schema for updating a recommendation comment."""
    content: Optional[str] = None
    is_internal: Optional[bool] = None

class RecommendationCommentInDBBase(RecommendationCommentBase):
    """Base schema for recommendation comment stored in DB."""
    id: int
    user_id: int
    recommendation_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class RecommendationComment(RecommendationCommentInDBBase):
    """Recommendation comment schema for API responses."""
    user: Optional[Dict[str, Any]] = None

class RecommendationWithComments(Recommendation):
    """Recommendation schema with comments included."""
    comments: List[RecommendationComment] = []

class RecommendationTimelineEventType(str, Enum):
    """Types of timeline events for recommendations."""
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    COMMENT_ADDED = "comment_added"
    ASSIGNEE_CHANGED = "assignee_changed"
    IMPLEMENTATION_STARTED = "implementation_started"
    IMPLEMENTATION_COMPLETED = "implementation_completed"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"

class RecommendationTimelineEvent(BaseModel):
    """Timeline event for a recommendation."""
    event_type: RecommendationTimelineEventType
    timestamp: datetime
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Dict[str, Any] = {}

class RecommendationWithTimeline(Recommendation):
    """Recommendation schema with timeline events."""
    timeline: List[RecommendationTimelineEvent] = []

class RecommendationBulkCreate(BaseModel):
    """Schema for bulk creating recommendations."""
    repository_id: int
    scan_id: Optional[int] = None
    created_by: int
    recommendations: List[Dict[str, Any]]  # List of recommendation data

class RecommendationTemplate(BaseModel):
    """Template for common recommendations."""
    title: str
    description: str
    recommendation_type: RecommendationType
    impact: RecommendationImpact
    effort: RecommendationEffort
    implementation_details: str
    default_estimated_savings: Optional[float] = None
    default_estimated_carbon_reduction: Optional[float] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
