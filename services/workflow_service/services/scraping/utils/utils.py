import uuid
from typing import Optional, List
from urllib.parse import urlparse

from global_config.logger import get_prefect_or_regular_python_logger


def generate_start_urls_uuid(start_urls: List[str], include_only_paths: Optional[List[str]] = None, exclude_paths: Optional[List[str]] = None) -> str:
    """
    Generate a deterministic UUID from the start URLs for consistency.
    
    Args:
        start_urls: List of start URLs
        include_only_paths: List of path patterns to include
        exclude_paths: List of path patterns to exclude
    Returns:
        The generated UUID string (as string, not UUID object)
    """
    if not include_only_paths:
        include_only_paths = []
    if not exclude_paths:
        exclude_paths = []
    
    # normalize include / exclude paths
    def normalize_path(path: str) -> str:
        path = path.strip()
        if path.startswith("/"):
            path = path[1:]
        if path.endswith("*"):
            path = path[:-1]
        return path
    
    include_only_paths = sorted(list(set([normalize_path(path) for path in include_only_paths])))
    exclude_paths = sorted(list(set([normalize_path(path) for path in exclude_paths])))

    path_filter_string = ""
    if exclude_paths or include_only_paths:
        path_filter_string = "include:" + ",".join(include_only_paths) + "exclude:" + ",".join(exclude_paths)
    
    try:
        def _get_netloc(url: str) -> str:
            parsed_url = urlparse(url)
            netloc = parsed_url.netloc.replace(':', '~').replace('_', '~')
            return netloc
        # Sort netlocs to ensure consistency
        sorted_netlocs = list(sorted(list(set(_get_netloc(url) for url in start_urls))))
        # Join netlocs to create a deterministic string
        combined_string = ",".join(sorted_netlocs) + path_filter_string
        # Generate UUID from the combined string
        start_urls_uuid = uuid.uuid5(uuid.NAMESPACE_URL, combined_string)
        return str(start_urls_uuid)
    except Exception as e:
        logger = get_prefect_or_regular_python_logger(
            name="workflow_service.scraping.pipelines", 
            return_non_prefect_logger=True
        )
        logger.error(f"Failed to generate UUID for start URLs: {start_urls}. Using random UUID. Error: {e}", exc_info=True)
        random_uuid = uuid.uuid4()
        return str(random_uuid)
