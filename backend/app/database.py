from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment variables or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecoci.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create a scoped session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for all models
Base = declarative_base()

def init_db():
    """
    Initialize the database by creating all tables.
    This should be called when the application starts.
    """
    # Import all models here to ensure they are registered with SQLAlchemy
    from .models import Base  # This imports all models through __init__.py
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Log the tables that were created
    print("Initialized database with tables:", list(Base.metadata.tables.keys()))

@contextmanager
def get_db():
    """
    Dependency for getting a database session.
    Use this in FastAPI path operations to get a database session.
    
    Example:
        def get_user(db: Session = Depends(get_db)):
            return db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """
    Get a database session directly (for use outside of FastAPI).
    Remember to close the session when done.
    """
    return SessionLocal()
