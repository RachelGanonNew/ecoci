from .base import Base, BaseMixin

# Import all models here to ensure they are registered with SQLAlchemy
from .user import User, SlackIntegration
from .repository import Repository, RepositoryProvider, RepositoryIntegration, RepositoryScan, ScanFinding, ScanFindingType, ScanFindingSeverity
from .finding import Finding, FindingSeverity, FindingStatus
from .recommendation import Recommendation, RecommendationStatus, RecommendationType

# Make models available for direct import
__all__ = [
    'Base', 'BaseMixin',
    'User', 'SlackIntegration',
    'Repository', 'RepositoryProvider', 'RepositoryIntegration',
    'RepositoryScan', 'ScanFinding', 'ScanFindingType', 'ScanFindingSeverity',
    'Finding', 'FindingSeverity', 'FindingStatus',
    'Recommendation', 'RecommendationStatus', 'RecommendationType'
]
