"""YAML-based configuration loader."""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration
default_config = {
    "debug": True,
    "environment": "development",
    "secret_key": "dev-secret-key-change-me",
    "database": {
        "url": "sqlite:///./ecoci.db",
        "echo": True,
    },
    "github": {
        "enabled": False,
        "app_id": "",
        "private_key": "",
        "webhook_secret": ""
    },
    "mcp": {
        "enabled": True,
        "max_concurrent_requests": 10
    },
    "slack": {
        "enabled": False
    },
    "cors": {
        "origins": ["*"]
    },
    "rate_limit": {
        "enabled": False
    }
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file with defaults."""
    if config_path is None:
        # Look for config in standard locations
        possible_paths = [
            Path("config.yaml"),
            Path("config.local.yaml"),
            Path("app", "config.yaml"),
            Path("app", "config.local.yaml"),
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            # No config file found, use defaults
            return default_config
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Merge with defaults
        return {**default_config, **config}
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return default_config

# Load configuration
config = load_config()

# Set environment variables for compatibility
os.environ.setdefault("SECRET_KEY", config["secret_key"])
os.environ.setdefault("DATABASE_URL", config["database"]["url"])
os.environ.setdefault("ENV", config["environment"])

if config["github"]["enabled"]:
    os.environ["GITHUB_APP_ID"] = str(config["github"]["app_id"])
    os.environ["GITHUB_APP_PRIVATE_KEY"] = config["github"]["private_key"]
    os.environ["GITHUB_WEBHOOK_SECRET"] = config["github"]["webhook_secret"]
