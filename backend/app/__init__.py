"""
EcoCI Backend Application
"""

# This file makes the app directory a Python package

# Import core components to make them available at the package level
from .core.config import settings  # noqa
from .database import SessionLocal  # noqa
