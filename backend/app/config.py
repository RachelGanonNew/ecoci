from pydantic import HttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "EcoCI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # API settings
    API_PREFIX: str = "/api"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # In production, replace with your frontend URL
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ecoci.db")
    
    # Authentication settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # GitHub App settings
    GITHUB_APP_ID: Optional[str] = os.getenv("GITHUB_APP_ID")
    GITHUB_APP_PRIVATE_KEY: Optional[str] = os.getenv("GITHUB_APP_PRIVATE_KEY")
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_WEBHOOK_SECRET: Optional[str] = os.getenv("GITHUB_WEBHOOK_SECRET")
    
    # Slack settings
    SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: Optional[str] = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_CLIENT_ID: Optional[str] = os.getenv("SLACK_CLIENT_ID")
    SLACK_CLIENT_SECRET: Optional[str] = os.getenv("SLACK_CLIENT_SECRET")
    SLACK_REDIRECT_URI: Optional[str] = os.getenv("SLACK_REDIRECT_URI")
    
    # Carbon and cost calculation settings
    CARBON_INTENSITY: float = float(os.getenv("CARBON_INTENSITY", "0.5"))  # kg CO2e per kWh
    COST_PER_KWH: float = float(os.getenv("COST_PER_KWH", "0.12"))  # USD per kWh
    
    # Celery settings (for background tasks)
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Sentry settings (for error tracking)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # Validate CORS origins
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()
