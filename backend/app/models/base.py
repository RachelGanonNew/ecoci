from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime, func

# Create the base declarative class
Base = declarative_base()

class BaseMixin:
    """Mixin with common model attributes."""
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
