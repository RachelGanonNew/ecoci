# Import all models here to make them available when importing from app.models
from .base import Base, TimestampMixin
from .user import User, SlackIntegration
from .repository import (
    Repository, RepositoryProvider, RepositoryIntegration,
    RepositoryScan, ScanFinding, ScanFindingType, ScanFindingSeverity
)
from .finding import Finding
from .recommendation import Recommendation, RecommendationStatus, RecommendationType

# Make models available for direct import
__all__ = [
    'Base', 'TimestampMixin',
    'User', 'SlackIntegration',
    'Repository', 'RepositoryProvider', 'RepositoryIntegration',
    'RepositoryScan', 'ScanFinding', 'ScanFindingType', 'ScanFindingSeverity',
    'Finding',
    'Recommendation', 'RecommendationStatus', 'RecommendationType'
]
