# import asyncio
import logging
from typing import Dict, Any, Optional
# from twisted.internet import asyncioreactor

# # 1) Install the asyncio reactor on the current asyncio loop
# #    Must come before importing Crochet or Scrapy!
# # import ipdb; ipdb.set_trace()
# asyncioreactor.install(eventloop=asyncio.get_event_loop())

# from crochet import setup, wait_for
from flask import Flask, request, jsonify, abort
import requests
import psutil
import os
from datetime import datetime
import threading
from global_utils.utils import datetime_now_utc

# # Global constants for server configuration
# SCRAPING_SERVER_HOST = "localhost"
# SCRAPING_SERVER_PORT = 6969
# SCRAPING_SERVER_BASE_URL = f"http://{SCRAPING_SERVER_HOST}:{SCRAPING_SERVER_PORT}"

from global_config.settings import global_settings

# Setup logging
logging.basicConfig(level=global_settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Flask app instance
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# @wait_for(timeout=600.0)
def crawl_url(job_config: Dict[str, Any]) -> Any:
    """
    Execute scraping job using Twisted/Scrapy with crochet integration.
    
    This function runs the scraping job in a way that's compatible with
    Twisted's reactor while being callable from asyncio.
    
    Args:
        job_config: Configuration dictionary for the scraping job
        
    Returns:
        Result from the scraping job
        
    Raises:
        Exception: If scraping job fails or times out
    """
    try:
        from workflow_service.services.scraping.spider import run_scraping_job
        logger.info(f"Starting scraping job with config: {job_config}")
        result = run_scraping_job(job_config, use_prefect_logging=True)
        logger.info("Scraping job completed successfully")
        return result
    except Exception as e:
        logger.error(f"Scraping job failed: {str(e)}")
        raise

# Setup crochet reactor
# setup()

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify service availability.
    
    Returns:
        JSON response with current health status, metadata, and process resource usage
    """
    try:
        # Get current process information
        current_process = psutil.Process(os.getpid())
        
        # Memory information
        memory_info = current_process.memory_info()
        memory_percent = current_process.memory_percent()
        
        # CPU information  
        cpu_percent = current_process.cpu_percent(interval=0.1)  # 0.1 second interval for accuracy
        cpu_times = current_process.cpu_times()
        
        # Additional process info
        create_time = datetime.fromtimestamp(current_process.create_time()).isoformat()
        num_threads = current_process.num_threads()
        
        # System memory info for context
        system_memory = psutil.virtual_memory()
        
        process_info = {
            "pid": current_process.pid,
            "memory": {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),  # Physical memory in use (MB)
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),  # Total virtual memory (MB) 
                "percent_of_system": round(memory_percent, 2)
            },
            "cpu": {
                "percent": round(cpu_percent, 2),
                "user_time": round(cpu_times.user, 2),
                "system_time": round(cpu_times.system, 2),
                "total_time": round(cpu_times.user + cpu_times.system, 2)
            },
            "process": {
                "created_at": create_time,
                "num_threads": num_threads,
                "status": current_process.status()
            },
            "system_context": {
                "total_memory_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                "available_memory_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                "memory_usage_percent": system_memory.percent
            }
        }
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime_now_utc().isoformat(),
            "version": "1.0.0",
            "process_info": process_info
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        abort(500, description="Service unhealthy")

@app.route("/scrape", methods=["POST"])
def scrape_endpoint():
    """
    Main scraping endpoint that accepts job configuration and executes scraping.
    
    This endpoint can handle long-running scraping jobs (100+ seconds) by using
    the existing crochet integration with configurable timeouts.
    
    Request JSON body should contain:
        - job_config: Configuration dict for the scraping job
        - timeout: Optional timeout in seconds (default: 600)
        
    Returns:
        JSON response with scraping results and metadata
        
    Raises:
        Flask abort: If scraping job fails or times out
    """
    start_time = datetime_now_utc()
    
    # Parse request data
    if not request.is_json:
        abort(400, description="Request must be JSON")
        
    request_data = request.get_json()
    if not request_data:
        abort(400, description="Request body is required")
        
    job_config = request_data.get('job_config')
    if not job_config:
        abort(400, description="job_config is required")
        
    timeout = request_data.get('timeout', 600.0)
    
    try:
        logger.info(f"Received scraping request with timeout: {timeout}s")
        
        # Execute scraping job synchronously using crochet
        # crochet handles the Twisted/asyncio integration for us
        result = crawl_url(job_config)
        
        end_time = datetime_now_utc()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Scraping completed successfully in {duration:.2f}s")
        
        result['success'] = True if result.get('status') == 'completed' else False
        return jsonify(result)
        
    except Exception as e:
        end_time = datetime_now_utc()
        duration = (end_time - start_time).total_seconds()
        
        # Check if it's a timeout error
        if "timeout" in str(e).lower():
            error_msg = f"Scraping job timed out after {duration:.2f}s"
            logger.error(error_msg)
            
            return jsonify({
                "error": "timeout",
                "message": error_msg,
                "duration": duration
            }), 408
        else:
            error_msg = f"Scraping job failed: {str(e)}"
            logger.error(error_msg)
            
            return jsonify({
                "error": "scraping_failed",
                "message": error_msg,
                "duration": duration
                         }), 500


# if __name__ == "__main__":
#     """
#     Main entry point for running the Flask scraping server.
    
#     Starts the server on port 6969 with Flask's built-in development server.
#     For production, consider using a WSGI server like Gunicorn or uWSGI.
#     """
#     logger.info(f"Starting Scraping Spider Server on port {SCRAPING_SERVER_PORT}")
    
#     # Configure Flask logging
#     import logging
#     logging.basicConfig(level=logging.INFO)
    
#     app.run(
#         host="0.0.0.0",
#         port=SCRAPING_SERVER_PORT,
#         debug=False,
#         threaded=True,  # Enable threading for concurrent requests
#         # For production deployment, use a proper WSGI server:
#         # gunicorn -w 1 --threads 4 -b 0.0.0.0:6969 spider_server:app
#     )

