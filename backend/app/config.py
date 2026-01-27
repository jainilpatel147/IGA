"""
Application Configuration
Centralized settings using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "IGA Demo"
    debug: bool = True
    
    # Database - using psycopg3 driver
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/iga_demo"
    
    # JWT Settings (Demo only - not production secure)
    jwt_secret: str = "demo-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
