"""
Initialize the database with required tables.
Run this script to set up a fresh SQLite database.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from app.models.base import Base
from app.core.config import settings

def init_db():
    """Initialize the database with all tables."""
    # Create database directory if it doesn't exist
    db_path = Path("./ecoci.db")
    db_path.parent.mkdir(exist_ok=True)
    
    # Create SQLAlchemy engine
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
