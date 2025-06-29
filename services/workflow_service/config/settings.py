"""
Configuration settings for the KiwiQ Backend Service.

This module contains all the configuration settings for the application, loaded from
environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from global_config.settings import ENV_FILE_PATH, Settings, PROJECT_ROOT

class Settings(Settings):
    """Application settings loaded from environment variables."""
    # TODO: get these vars from environment directly, and ensure order of loading from env or ENV_FILE!

    AWS_BEDROCK_SECRET_ACCESS_KEY: str = ""
    AWS_BEDROCK_ACCESS_KEY_ID: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    # GOOGLE_API_KEY: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    FIREWORKS_API_KEY: str = ""
    PPLX_API_KEY: str = ""
    WEB_SEARCH_NUM_CITATIONS_PER_CREDIT: int = 2
    LLM_TOKEN_COST_MARKUP_FACTOR: float = 1.25
    
    @model_validator(mode='after')
    def validate_google_credentials(self) -> 'Settings':
        """
        Validate that GOOGLE_APPLICATION_CREDENTIALS path exists if set.
        
        This ensures that if Google credentials are configured, the file path
        is valid and accessible within the project root directory.
        
        Returns:
            Settings: The validated settings instance
            
        Raises:
            FileNotFoundError: If the credentials file path is set but doesn't exist
            ValueError: If the credentials path is outside the project root
        """
        if self.GOOGLE_APPLICATION_CREDENTIALS:
            # Convert to Path object for easier manipulation
            credentials_path = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
            
            # If it's a relative path, resolve it relative to PROJECT_ROOT
            if not credentials_path.is_absolute():
                full_path = PROJECT_ROOT / credentials_path
            else:
                full_path = credentials_path
            
            # Check if the file exists
            if not full_path.exists():
                raise FileNotFoundError(
                    f"Google Application Credentials file not found: {full_path}. "
                    f"Please ensure the file exists or update GOOGLE_APPLICATION_CREDENTIALS."
                )
            # Export the resolved path as an environment variable
            # This ensures that Google libraries can find the credentials file
            # using the standard GOOGLE_APPLICATION_CREDENTIALS environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(full_path)
            
            # Verify the path is within PROJECT_ROOT for security
            try:
                full_path.resolve().relative_to(PROJECT_ROOT.resolve())
            except ValueError:
                raise ValueError(
                    f"Google Application Credentials path must be within project root. "
                    f"Got: {full_path}, Project root: {PROJECT_ROOT}"
                )
        
        return self
    
    # model_config = SettingsConfigDict(
    #     env_file=ENV_FILE_PATH,
    #     env_file_encoding="utf-8",
    #     case_sensitive=True,
    #     extra='ignore',
    # )

# Create a global settings instance
settings = Settings() 
