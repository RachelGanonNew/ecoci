# Import all schemas to make them available when importing from app.schemas
from .token import Token, TokenPayload
from .user import User, UserCreate, UserInDB, UserUpdate
from .repository import (
    Repository, RepositoryCreate, RepositoryUpdate, RepositoryInDBBase,
    Scan, ScanCreate, ScanUpdate, ScanInDBBase,
    Finding, FindingCreate, FindingUpdate, FindingInDBBase,
    FindingSeverity, FindingType, ScanStatus, RepositoryWithScans, ScanWithFindings,
    RepositoryScanSummary, ScanSummary
)
from .recommendation import (
    Recommendation, RecommendationCreate, RecommendationUpdate, RecommendationInDBBase,
    RecommendationStatus, RecommendationType, RecommendationWithRelated
)

# Make imports available directly from app.schemas
__all__ = [
    'Token', 'TokenPayload',
    'User', 'UserCreate', 'UserInDB', 'UserUpdate',
    'Repository', 'RepositoryCreate', 'RepositoryUpdate', 'RepositoryInDBBase',
    'Scan', 'ScanCreate', 'ScanUpdate', 'ScanInDBBase', 'RepositoryWithScans', 'ScanWithFindings',
    'RepositoryScanSummary', 'ScanSummary',
    'Finding', 'FindingCreate', 'FindingUpdate', 'FindingInDBBase',
    'FindingSeverity', 'FindingType', 'ScanStatus',
    'Recommendation', 'RecommendationCreate', 'RecommendationUpdate', 'RecommendationInDBBase',
    'RecommendationStatus', 'RecommendationType', 'RecommendationWithRelated'
]
