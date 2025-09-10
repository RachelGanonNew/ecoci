# Import all schemas to make them available when importing from app.schemas
from .token import Token, TokenPayload
from .user import User, UserCreate, UserInDB, UserUpdate
from .repository import (
    Repository, RepositoryCreate, RepositoryUpdate, RepositoryInDB,
    RepositoryScan, RepositoryScanCreate, RepositoryScanUpdate, RepositoryScanInDB,
    ScanFinding, ScanFindingCreate, ScanFindingUpdate, ScanFindingInDB,
    FindingSeverity, FindingType, ScanStatus
)
from .recommendation import (
    Recommendation, RecommendationCreate, RecommendationUpdate, RecommendationInDB,
    RecommendationStatus, RecommendationType
)

# Make imports available directly from app.schemas
__all__ = [
    'Token', 'TokenPayload',
    'User', 'UserCreate', 'UserInDB', 'UserUpdate',
    'Repository', 'RepositoryCreate', 'RepositoryUpdate', 'RepositoryInDB',
    'RepositoryScan', 'RepositoryScanCreate', 'RepositoryScanUpdate', 'RepositoryScanInDB',
    'ScanFinding', 'ScanFindingCreate', 'ScanFindingUpdate', 'ScanFindingInDB',
    'FindingSeverity', 'FindingType', 'ScanStatus',
    'Recommendation', 'RecommendationCreate', 'RecommendationUpdate', 'RecommendationInDB',
    'RecommendationStatus', 'RecommendationType'
]
