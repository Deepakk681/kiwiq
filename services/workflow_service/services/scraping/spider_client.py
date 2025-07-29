import asyncio
import logging
from typing import Dict, Any, Optional

from global_config.logger import get_prefect_or_regular_python_logger
import httpx
from datetime import datetime

from global_utils.utils import datetime_now_utc
from global_config.settings import global_settings


async def request_scrape_and_wait(
    job_config: Dict[str, Any], 
    timeout: float = 600.0,
    server_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper method to submit scraping job to server and wait for response.
    
    This is a convenience method that can be used programmatically to submit
    scraping jobs to the FastAPI server and wait for results. Handles long wait 
    times (100s of seconds) by making HTTP requests to the /scrape endpoint.
    
    Args:
        job_config: Configuration dictionary for the scraping job
        timeout: Maximum time to wait for job completion in seconds
        server_url: Optional custom server URL (defaults to global constant)
        
    Returns:
        Dict containing the scraping results and metadata
        
    Raises:
        Exception: If HTTP request fails, scraping fails, or times out
        
    Example:
        ```python
        job_config = {
            "url": "https://example.com",
            "settings": {"CONCURRENT_REQUESTS": 1}
        }
        result = await request_scrape_and_wait(job_config, timeout=300.0)
        ```
    """
    logger = get_prefect_or_regular_python_logger(name="trigger_web_scraper_job")
    base_url = server_url or global_settings.SCRAPING_SERVER_URL
    scrape_url = f"{base_url}/scrape"
    
    logger.info(f"Submitting scraping request to {scrape_url} with {timeout}s timeout")
    
    start_time = datetime_now_utc()
    
    # Prepare request payload
    request_payload = {
        "job_config": job_config,
        "timeout": timeout
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout + 30.0) as client:  # Add buffer to HTTP timeout
            logger.info(f"Making POST request to scraping server: {scrape_url}")
            
            response = await client.post(
                scrape_url,
                json=request_payload,
                headers={"Content-Type": "application/json"}
            )
            
            end_time = datetime_now_utc()
            duration = (end_time - start_time).total_seconds()
            
            # Handle successful response
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Scraping request completed successfully in {duration:.2f}s")
                
                response_data['success'] = True
                response_data['duration'] = duration
                response_data['timestamp'] = end_time.isoformat()
                response_data['job_config'] = job_config
                return response_data
            
            # Handle timeout response
            elif response.status_code == 408:
                error_data = response.json()
                error_msg = f"Scraping request timed out: {error_data.get('detail', {}).get('message', 'Unknown timeout')}"
                logger.error(error_msg)
                
                return {
                    "success": False,
                    "error": "timeout",
                    "message": error_msg,
                    "duration": duration,
                    "timestamp": end_time.isoformat(),
                    "job_config": job_config,
                    "server_response": error_data
                }
            
            # Handle other HTTP errors
            else:
                try:
                    error_data = response.json()
                    error_msg = f"Server error: {error_data.get('detail', {}).get('message', 'Unknown error')}"
                except:
                    error_msg = f"Server returned status {response.status_code}: {response.text}"
                
                logger.error(error_msg)
                
                return {
                    "success": False,
                    "error": "server_error",
                    "message": error_msg,
                    "duration": duration,
                    "timestamp": end_time.isoformat(),
                    "job_config": job_config,
                    "status_code": response.status_code
                }
                
    except httpx.TimeoutException:
        end_time = datetime_now_utc()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"HTTP request timed out after {duration:.2f}s"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": "http_timeout",
            "message": error_msg,
            "duration": duration,
            "timestamp": end_time.isoformat(),
            "job_config": job_config
        }
        
    except httpx.RequestError as e:
        end_time = datetime_now_utc()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"HTTP request failed: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": "http_request_failed",
            "message": error_msg,
            "duration": duration,
            "timestamp": end_time.isoformat(),
            "job_config": job_config
        }
        
    except Exception as e:
        end_time = datetime_now_utc()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"Unexpected error during scraping request: {str(e)}"
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": "unexpected_error",
            "message": error_msg,
            "duration": duration,
            "timestamp": end_time.isoformat(),
            "job_config": job_config
        }
