"""
Setup local development environment.
This script helps set up the local development environment by creating a .env file
from .env.example and initializing the database.
"""
import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the local development environment."""
    # Paths
    root_dir = Path(__file__).parent
    env_example = root_dir / ".env.example"
    env_file = root_dir / ".env"
    
    # Create .env from .env.example if it doesn't exist
    if not env_file.exists() and env_example.exists():
        print(f"Creating {env_file} from {env_example}...")
        shutil.copy(env_example, env_file)
        print(f"Created {env_file}. Please update it with your configuration.")
    
    # Create config.local.yaml from config.example.yaml if it doesn't exist
    config_example = root_dir / "config.example.yaml"
    config_file = root_dir / "config.local.yaml"
    
    if not config_file.exists() and config_example.exists():
        print(f"Creating {config_file} from {config_example}...")
        shutil.copy(config_example, config_file)
        print(f"Created {config_file}. Please update it with your configuration.")
    
    # Initialize the database
    print("\nTo initialize the database, run:")
    print("cd backend")
    print("python -m scripts.init_db")
    
    print("\nTo start the development server, run:")
    print("cd backend")
    print("uvicorn app.main:app --reload")

if __name__ == "__main__":
    setup_environment()
