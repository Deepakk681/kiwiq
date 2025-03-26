"""
Configuration settings for the KiwiQ Backend Service.

This module contains all the configuration settings for the application, loaded from
environment variables with sensible defaults.
"""
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

from global_config.settings import ENV_FILE_PATH

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # TODO: get these vars from environment directly, and ensure order of loading from env or ENV_FILE!
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore',
    )

# Create a global settings instance
settings = Settings() 
