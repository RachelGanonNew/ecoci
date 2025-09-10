"""
Application Configuration

This module contains all the configuration settings for the EcoCI application.
"""
import os
import yaml
from typing import List, Optional, Dict, Any, Union
from pydantic import AnyHttpUrl, validator, HttpUrl, PostgresDsn, Field
from pydantic_settings import BaseSettings

# Try to load config from YAML if it exists
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
config = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "EcoCI API"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]  # In production, specify exact origins
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    JWT_ALGORITHM: str = "HS256"
    
    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ecoci")
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        db = values.get("POSTGRES_DB")
        
        # Construct the DSN string directly
        auth_part = f"{user}:{password}@" if user and password else ""
        return f"postgresql://{auth_part}{host}/{db}"
    
    # GitHub App settings
    GITHUB_APP_ID: str = os.getenv("GITHUB_APP_ID", "")
    GITHUB_APP_PRIVATE_KEY: str = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    # Slack settings
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    
    # MCP Server settings
    MCP_SERVER_ENABLED: bool = os.getenv("MCP_SERVER_ENABLED", "True").lower() in ("true", "1", "t")
    MCP_MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MCP_MAX_CONCURRENT_REQUESTS", "100"))
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Keys (for external services)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Feature flags
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "False").lower() in ("true", "1", "t")
    
    # SQLAlchemy specific
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()

# Set SQLAlchemy database URI if not already set
if not settings.SQLALCHEMY_DATABASE_URI:
    settings.SQLALCHEMY_DATABASE_URI = settings.DATABASE_URL or "sqlite:///./ecoci.db"

# Configure logging
import logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Validate required settings on import
if settings.DEBUG:
    logging.warning("Running in DEBUG mode. Do not run in production with DEBUG=True.")

# Validate GitHub configuration
if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
    logging.warning(
        "GitHub App ID or Private Key not set. GitHub integration will not work. "
        "Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY environment variables."
    )

# Validate Slack configuration
if not settings.SLACK_BOT_TOKEN or not settings.SLACK_SIGNING_SECRET:
    logging.warning(
        "Slack Bot Token or Signing Secret not set. Slack integration will not work. "
        "Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET environment variables."
    )

# Log configuration on startup
logging.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
logging.info(f"Debug mode: {settings.DEBUG}")
logging.info(f"Database URL: {settings.DATABASE_URL}" if settings.DATABASE_URL else "Database URL not configured")
