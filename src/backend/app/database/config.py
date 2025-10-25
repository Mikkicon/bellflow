import os
from typing import Optional
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # MongoDB connection settings
    mongodb_url: str = "mongodb+srv://bellflow:.94pu8KtKXS%23Wns@bellflowdb.6k3thec.mongodb.net/?appName=bellflowdb"
    mongodb_database: str = "bellflow"

    # MongoDB Atlas settings (for production)
    mongodb_atlas_url: Optional[str] = None
    mongodb_atlas_database: Optional[str] = None

    # Connection pool settings
    max_pool_size: int = 10
    min_pool_size: int = 1
    max_idle_time_ms: int = 30000

    # Connection timeout settings
    connect_timeout_ms: int = 20000
    server_selection_timeout_ms: int = 5000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file


# Global database settings instance
db_settings = DatabaseSettings()


def get_database_url() -> str:
    """Get the appropriate database URL based on environment."""
    if db_settings.mongodb_atlas_url:
        return db_settings.mongodb_atlas_url
    return db_settings.mongodb_url


def get_database_name() -> str:
    """Get the appropriate database name based on environment."""
    if db_settings.mongodb_atlas_database:
        return db_settings.mongodb_atlas_database
    return db_settings.mongodb_database
