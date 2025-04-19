"""
Settings for the RapidAPI LinkedIn scraper client.

This module provides configuration settings for the RapidAPI LinkedIn scraper client,
inheriting from the global settings configuration.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from global_config.settings import Settings as GlobalSettings


class RapidAPISettings(GlobalSettings):
    """
    Settings for the RapidAPI LinkedIn scraper client.
    
    This class inherits from the global settings and provides additional configuration
    specific to the RapidAPI LinkedIn scraper client.
    Settings can be provided through environment variables or .env files.
    """
    
    # API Settings
    RAPID_API_KEY: Optional[str] = os.getenv("RAPID_API_KEY")
    RAPID_API_BASE_URL: str = "linkedin-profiles-and-company-data.p.rapidapi.com"
    RAPID_API_HOST: str = "linkedin-profiles-and-company-data.p.rapidapi.com"
    
    # Request Settings
    DEFAULT_POST_LIMIT: int = 3
    DEFAULT_COMMENT_LIMIT: int = 10
    DEFAULT_REACTION_LIMIT: int = 5
    DEFAULT_PROFILE_LIMIT: int = 5
    DEFAULT_COMPANY_LIMIT: int = 5
    
    # Rate Limiting Settings
    DEFAULT_DELAY_SECONDS: int = 5
    BATCH_SIZE: int = 50
    RATE_LIMIT_REQUESTS: int = 10  # Number of requests per time window
    RATE_LIMIT_PERIOD: int = 60    # Time window in seconds
    RATE_LIMIT_BACKOFF: int = 2    # Exponential backoff multiplier
    MAX_RETRIES: int = 3           # Maximum number of retry attempts
    
    # Default Headers
    @property
    def DEFAULT_HEADERS(self) -> Dict[str, str]:
        return {
            "X-RapidAPI-Key": self.RAPID_API_KEY,
            "X-RapidAPI-Host": self.RAPID_API_HOST,
            "Content-Type": "application/json"
        }
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    MIN_PAGE_SIZE: int = 5
    
    # Cache Settings
    CACHE_EXPIRY: int = 3600  # Default cache expiry in seconds (1 hour)
    PROFILE_CACHE_EXPIRY: int = 86400  # Profile cache expiry (24 hours)
    COMPANY_CACHE_EXPIRY: int = 86400  # Company cache expiry (24 hours)
    POST_CACHE_EXPIRY: int = 3600  # Post cache expiry (1 hour)
    
    # Request Timeout
    REQUEST_TIMEOUT: int = 30  # Request timeout in seconds
    
    # Endpoint Configuration
    ENDPOINTS: Dict[str, str] = {
        "profile": "/",
        "company": "/get-company-details",
        "posts": "/get-post",
        "comments": "/get-post-comments",
        "reactions": "/get-post-reactions"
    }
    
    # Test Mode
    TEST_MODE: bool = os.getenv("RAPID_API_TEST_MODE", "False").lower() == "true"
    TEST_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "test_data")
    
    class Config:
        """
        Pydantic configuration for settings.
        """
        env_file = ".env"
        env_prefix = "SCRAPER_"
        case_sensitive = True
        
    def get_scraper_settings(self) -> Dict[str, Any]:
        """
        Get all scraper-specific settings as a dictionary.
        Used for configuration overrides.
        
        Returns:
            Dict[str, Any]: Dictionary of scraper settings
        """
        return {
            "rapid_api_key": self.RAPID_API_KEY,
            "rapid_api_host": self.RAPID_API_HOST,
            "rapid_api_base_url": self.RAPID_API_BASE_URL,
            "default_post_limit": self.DEFAULT_POST_LIMIT,
            "default_comment_limit": self.DEFAULT_COMMENT_LIMIT,
            "default_reaction_limit": self.DEFAULT_REACTION_LIMIT,
            "test_mode": self.TEST_MODE
        }

    def validate_api_key(self) -> bool:
        """
        Validate that the API key is set.
        
        Returns:
            bool: True if API key is set, False otherwise
        """
        return bool(self.RAPID_API_KEY)

# Create settings instance
rapid_api_settings = RapidAPISettings() 