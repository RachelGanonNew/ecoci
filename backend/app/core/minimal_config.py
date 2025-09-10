"""Minimal configuration for local development and testing."""
import os

class MinimalConfig:
    # Core settings
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Database settings (SQLite for local development)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///./ecoci.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Disable external services
    GITHUB_APP_ID = None
    GITHUB_APP_PRIVATE_KEY = None
    GITHUB_WEBHOOK_SECRET = None
    SLACK_BOT_TOKEN = None
    SLACK_SIGNING_SECRET = None
    
    # Disable authentication for development
    DISABLE_AUTH = True
    
    # Disable rate limiting
    RATELIMIT_ENABLED = False

# Use this in your app.py or main.py to override settings in development
minimal_settings = MinimalConfig()
