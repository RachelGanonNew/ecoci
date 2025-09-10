from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime, func

# Import all models here to ensure they are registered with SQLAlchemy
from app.models.user import User  # noqa
from app.models.repository import Repository  # noqa
from app.models.scan import Scan  # noqa
from app.models.finding import Finding  # noqa
from app.models.recommendation import Recommendation  # noqa

class BaseMixin:
    """Base mixin with common model attributes."""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

# Create the declarative base
Base = declarative_base(cls=BaseMixin)
