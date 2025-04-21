"""
URL helper utilities for the RapidAPI LinkedIn Scraper client.

This module provides utility functions for working with LinkedIn URLs,
such as URN extraction, URL parsing, and URL generation.
"""

import re
from typing import Optional, Dict, Any
from urllib.parse import quote, urlparse, parse_qs

def extract_urn_from_url(url: str) -> Optional[str]:
    """
    Extract the URN from a LinkedIn URL.
    
    Args:
        url (str): LinkedIn URL to extract URN from
        
    Returns:
        Optional[str]: Extracted URN or None if not found
    """
    # Pattern for post URNs
    post_urn_pattern = r"urn:li:activity:(\d+)"
    post_match = re.search(post_urn_pattern, url)
    if post_match:
        return post_match.group(1)
    
    # Pattern for profile URLs: linkedin.com/in/username
    profile_pattern = r"linkedin\.com/in/([a-zA-Z0-9_-]+)"
    profile_match = re.search(profile_pattern, url)
    if profile_match:
        username = profile_match.group(1)
        return f"urn:li:person:{username}"
    
    # Pattern for company URLs: linkedin.com/company/companyname
    company_pattern = r"linkedin\.com/company/([a-zA-Z0-9_-]+)"
    company_match = re.search(company_pattern, url)
    if company_match:
        company_name = company_match.group(1)
        return f"urn:li:organization:{company_name}"
    
    return None

def encode_urn(urn: str) -> str:
    """
    URL-encode a LinkedIn URN for use in API requests.
    
    Args:
        urn (str): The URN to encode
        
    Returns:
        str: URL-encoded URN
    """
    return quote(urn, safe="")

def is_valid_linkedin_url(url: str) -> bool:
    """
    Check if a URL is a valid LinkedIn URL.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if the URL is a valid LinkedIn URL, False otherwise
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc.endswith("linkedin.com")

def extract_username_from_url(url: str) -> Optional[str]:
    """
    Extract the username from a LinkedIn profile URL.
    
    Args:
        url (str): LinkedIn profile URL
        
    Returns:
        Optional[str]: Extracted username or None if not found
    """
    # Pattern for profile URLs: linkedin.com/in/username
    profile_pattern = r"linkedin\.com/in/([a-zA-Z0-9_-]+)"
    profile_match = re.search(profile_pattern, url)
    if profile_match:
        return profile_match.group(1)
    
    # Pattern for company URLs: linkedin.com/company/companyname
    company_pattern = r"linkedin\.com/company/([a-zA-Z0-9_-]+)"
    company_match = re.search(company_pattern, url)
    if company_match:
        return company_match.group(1)
    
    return None

def extract_post_id_from_url(url: str) -> Optional[str]:
    """
    Extract the post ID from a LinkedIn post URL.
    
    Args:
        url (str): LinkedIn post URL
        
    Returns:
        Optional[str]: Extracted post ID or None if not found
    """
    # Pattern for post URLs with activity IDs
    post_pattern = r"linkedin\.com/posts/[^/]+/[^/]+-(\d+)"
    post_match = re.search(post_pattern, url)
    if post_match:
        return post_match.group(1)
    
    # Alternative pattern for post URNs
    post_urn_pattern = r"urn:li:activity:(\d+)"
    post_urn_match = re.search(post_urn_pattern, url)
    if post_urn_match:
        return post_urn_match.group(1)
    
    return None 