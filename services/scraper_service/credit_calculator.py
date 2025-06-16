import asyncio
from math import ceil
from typing import Dict, Any, Optional, Tuple
from scraper_service.settings import rapid_api_settings


# Estimated page sizes for paginated endpoints based on API behavior
# These can be overridden via environment variables in settings
COMMENTS_PAGE_SIZE = rapid_api_settings.DEFAULT_COMMENT_LIMIT  # Estimated comments per page
REACTIONS_PAGE_SIZE = rapid_api_settings.DEFAULT_REACTION_LIMIT  # Estimated reactions per page


async def credit_estimation(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the estimated credit cost for a LinkedIn scraping request.
    
    This calculator is based on the official RapidAPI LinkedIn Data API credit costs:
    - Profile/Company Data: 1 credit
    - Posts (batched): 1 credit per batch
    - Comments: 1 credit per API call (paginated based on limit)
    - Reactions: 1 credit per API call (paginated based on limit)
    - Search operations: 1 credit per page/batch
    
    Important Notes:
    - Comments and reactions endpoints are paginated. If the requested limit exceeds
      the page size, multiple API calls (and thus multiple credits) will be needed.
    - The actual page sizes may vary by endpoint and are estimates based on observed behavior.
    - This calculator provides estimates; actual credit usage may vary slightly.
    
    Args:
        req: Dictionary containing the scraping request parameters with fields:
             - type: "company" or "person"
             - profile_info: "yes" or "no"
             - post_scrap: "yes" or "no" (for entity posts)
             - post_limit: number of posts to scrape
             - post_comments: "yes" or "no"
             - comment_limit: max comments per post (affects pagination/credits)
             - post_reactions: "yes" or "no"
             - reaction_limit: max reactions per post (affects pagination/credits)
             - activity_comments: "yes" or "no" (person only)
             - activity_reactions: "yes" or "no" (person only)
             - search_post_by_keyword: "yes" or "no"
             - search_post_by_hashtag: "yes" or "no"
    
    Returns:
        Dictionary with 'max_credits', 'min_credits' and 'breakdown' with detailed component costs.
    """
    max_credits = 0
    min_credits = 0
    
    # Initialize breakdown tracking
    breakdown = {
        "profile_info": 0,
        "posts_fetching": 0,
        "comments_enrichment": {"max": 0, "min": 0},
        "reactions_enrichment": {"max": 0, "min": 0},
        "activity_fetching": 0,
        "search_operations": 0,
        "post_details": 0
    }
    
    # Get entity type with default
    entity_type = req.get('type', 'person')
    
    # Activity comments and reactions are always for persons (not companies)
    if req.get('activity_comments') == "yes" or req.get('activity_reactions') == "yes":
        entity_type = "person"
    
    # 1. Profile/Company Info: 1 credit
    if req.get('profile_info') == "yes":
        max_credits += 1
        min_credits += 1
        breakdown["profile_info"] = 1
    
    # 2. Entity Posts (Profile's Posts or Company's Posts)
    if req.get('post_scrap') == "yes":
        # Get post limit with appropriate default
        post_limit = req.get('post_limit', 0) or rapid_api_settings.DEFAULT_POST_LIMIT
        
        if post_limit > 0:
            # Posts are fetched in batches
            post_batches = ceil(post_limit / rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE)
            max_credits += post_batches
            min_credits += post_batches
            breakdown["posts_fetching"] += post_batches
            
            # Add enrichment credits using consolidated function with breakdown
            enrichment_result = calculate_post_enrichment_credits(
                post_count=post_limit,
                fetch_comments=req.get('post_comments') == "yes",
                fetch_reactions=req.get('post_reactions') == "yes",
                comment_limit=req.get('comment_limit'),
                reaction_limit=req.get('reaction_limit')
            )
            max_credits += enrichment_result['max_credits']
            min_credits += enrichment_result['min_credits']
            
            # Update breakdown from enrichment result
            breakdown["comments_enrichment"]["max"] += enrichment_result['breakdown']['comments']['max']
            breakdown["comments_enrichment"]["min"] += enrichment_result['breakdown']['comments']['min']
            breakdown["reactions_enrichment"]["max"] += enrichment_result['breakdown']['reactions']['max']
            breakdown["reactions_enrichment"]["min"] += enrichment_result['breakdown']['reactions']['min']
    
    # 3. Activity Comments (Get Profile's Comments - posts user commented on)
    if entity_type == "person" and req.get('activity_comments') == "yes":
        # Base credit for fetching posts the user commented on
        max_credits += 1
        min_credits += 1
        breakdown["activity_fetching"] += 1
        
        # Get post limit with appropriate default
        post_limit = req.get('post_limit', 0) or rapid_api_settings.DEFAULT_POST_LIMIT
        
        if post_limit > 0:
            # Add enrichment credits using consolidated function with breakdown
            enrichment_result = calculate_post_enrichment_credits(
                post_count=post_limit,
                fetch_comments=req.get('post_comments') == "yes",
                fetch_reactions=req.get('post_reactions') == "yes",
                comment_limit=req.get('comment_limit'),
                reaction_limit=req.get('reaction_limit')
            )
            max_credits += enrichment_result['max_credits']
            min_credits += enrichment_result['min_credits']
            
            # Update breakdown from enrichment result
            breakdown["comments_enrichment"]["max"] += enrichment_result['breakdown']['comments']['max']
            breakdown["comments_enrichment"]["min"] += enrichment_result['breakdown']['comments']['min']
            breakdown["reactions_enrichment"]["max"] += enrichment_result['breakdown']['reactions']['max']
            breakdown["reactions_enrichment"]["min"] += enrichment_result['breakdown']['reactions']['min']
    
    # 4. Activity Reactions (Get Profile Reactions - posts user reacted to)
    if entity_type == "person" and req.get('activity_reactions') == "yes":
        # Get post limit with appropriate default for activity reactions
        post_limit = req.get('post_limit', 0) or rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE_FOR_ACTIVITY_REACTIONS
        
        if post_limit > 0:
            # Activity reactions are fetched in batches of 100
            activity_batches = ceil(post_limit / rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE_FOR_ACTIVITY_REACTIONS)
            max_credits += activity_batches
            min_credits += activity_batches
            breakdown["activity_fetching"] += activity_batches
            
            # Add enrichment credits using consolidated function with breakdown
            enrichment_result = calculate_post_enrichment_credits(
                post_count=post_limit,
                fetch_comments=req.get('post_comments') == "yes",
                fetch_reactions=req.get('post_reactions') == "yes",
                comment_limit=req.get('comment_limit'),
                reaction_limit=req.get('reaction_limit')
            )
            max_credits += enrichment_result['max_credits']
            min_credits += enrichment_result['min_credits']
            
            # Update breakdown from enrichment result
            breakdown["comments_enrichment"]["max"] += enrichment_result['breakdown']['comments']['max']
            breakdown["comments_enrichment"]["min"] += enrichment_result['breakdown']['comments']['min']
            breakdown["reactions_enrichment"]["max"] += enrichment_result['breakdown']['reactions']['max']
            breakdown["reactions_enrichment"]["min"] += enrichment_result['breakdown']['reactions']['min']
    
    # 5. Search Operations
    if req.get('search_post_by_keyword') == "yes":
        post_limit = req.get('post_limit', 0) or rapid_api_settings.SCRAPER_SERVICE_SEARCH_BY_KEYWORD_BATCH_SIZE
        if post_limit > 0:
            # Search by keyword typically returns ~10 posts per page
            search_pages = ceil(post_limit / rapid_api_settings.SCRAPER_SERVICE_SEARCH_BY_KEYWORD_BATCH_SIZE)
            max_credits += search_pages
            min_credits += search_pages
            breakdown["search_operations"] += search_pages
    
    if req.get('search_post_by_hashtag') == "yes":
        post_limit = req.get('post_limit', 0) or rapid_api_settings.SCRAPER_SERVICE_SEARCH_BY_HASHTAG_BATCH_SIZE
        if post_limit > 0:
            # Hashtag search typically returns ~50 posts per page
            search_pages = ceil(post_limit / rapid_api_settings.SCRAPER_SERVICE_SEARCH_BY_HASHTAG_BATCH_SIZE)
            max_credits += search_pages
            min_credits += search_pages
            breakdown["search_operations"] += search_pages
    
    # 6. Post Details (Get specific post details with optional enrichment)
    if req.get('post_details') == "yes":
        # Base credit for fetching post details: 1 credit
        max_credits += 1
        min_credits += 1
        breakdown["post_details"] = 1
        
        # Add enrichment credits for comments and reactions if requested
        # Post details jobs work on a single post, so post_count = 1
        enrichment_result = calculate_post_enrichment_credits(
            post_count=1,  # Only one post for post details
            fetch_comments=req.get('post_comments') == "yes",
            fetch_reactions=req.get('post_reactions') == "yes",
            comment_limit=req.get('comment_limit'),
            reaction_limit=req.get('reaction_limit')
        )
        max_credits += enrichment_result['max_credits']
        min_credits += enrichment_result['min_credits']
        
        # Update breakdown from enrichment result
        breakdown["comments_enrichment"]["max"] += enrichment_result['breakdown']['comments']['max']
        breakdown["comments_enrichment"]["min"] += enrichment_result['breakdown']['comments']['min']
        breakdown["reactions_enrichment"]["max"] += enrichment_result['breakdown']['reactions']['max']
        breakdown["reactions_enrichment"]["min"] += enrichment_result['breakdown']['reactions']['min']
    
    return {
        "max_credits": max_credits,
        "min_credits": min_credits,
        "breakdown": breakdown
    }


def calculate_post_enrichment_credits(
    post_count: int, 
    fetch_comments: bool, 
    fetch_reactions: bool,
    comment_limit: Optional[int] = None,
    reaction_limit: Optional[int] = None,
    comments_page_size: int = COMMENTS_PAGE_SIZE,
    reactions_page_size: int = REACTIONS_PAGE_SIZE
) -> Dict[str, Any]:
    """
    Consolidated helper function to calculate credits for enriching posts with comments and reactions.
    
    This function handles all types of posts (company, person, activity) and uses the same
    default values as the actual scrapers in post_manager.py.
    
    Args:
        post_count: Number of posts to enrich
        fetch_comments: Whether to fetch comments for each post
        fetch_reactions: Whether to fetch reactions for each post
        comment_limit: Max comments per post (defaults to DEFAULT_COMMENT_LIMIT)
        reaction_limit: Max reactions per post (defaults to DEFAULT_REACTION_LIMIT)
        comments_page_size: Estimated comments returned per API page (for pagination)
        reactions_page_size: Estimated reactions returned per API page (for pagination)
        
    Returns:
        Dictionary with 'max_credits', 'min_credits' and 'breakdown' with detailed component costs.
        
    Example:
        # For 10 posts with comments (limit 100) and reactions (limit 150):
        >>> calculate_post_enrichment_credits(10, True, True, 100, 150)
        {'max_credits': 50, 'min_credits': 20, 'breakdown': {...}}
        # Max: 10 posts * (2 comment pages + 3 reaction pages) = 50
        # Min: 10 posts * (1 comment page + 1 reaction page) = 20
    """
    max_credits = 0
    min_credits = 0
    
    # Initialize breakdown
    breakdown = {
        "comments": {"max": 0, "min": 0},
        "reactions": {"max": 0, "min": 0}
    }
    
    if fetch_comments and post_count > 0:
        # Use the same default as post_manager.py
        comment_limit = comment_limit or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        
        # Calculate pages needed for comments
        # Max scenario: Need multiple pages per post
        comment_pages_per_post = ceil(comment_limit / comments_page_size)
        comment_max = post_count * comment_pages_per_post
        comment_min = post_count  # Min scenario: All comments fit in one page per post
        
        max_credits += comment_max
        min_credits += comment_min
        
        breakdown["comments"]["max"] = comment_max
        breakdown["comments"]["min"] = comment_min
        
    if fetch_reactions and post_count > 0:
        # Use the same default as post_manager.py
        reaction_limit = reaction_limit or rapid_api_settings.DEFAULT_REACTION_LIMIT
        
        # Calculate pages needed for reactions
        # Max scenario: Need multiple pages per post
        reaction_pages_per_post = ceil(reaction_limit / reactions_page_size)
        first_page_credit_cost = 2 * min(1, reaction_pages_per_post)
        remaining_pages = max(0, reaction_pages_per_post - 1)
        reaction_max = post_count * (first_page_credit_cost + remaining_pages)
        reaction_min = post_count * first_page_credit_cost  # Min scenario: All reactions fit in one page per post
        
        max_credits += reaction_max
        min_credits += reaction_min
        
        breakdown["reactions"]["max"] = reaction_max
        breakdown["reactions"]["min"] = reaction_min
    
    return {
        "max_credits": max_credits,
        "min_credits": min_credits,
        "breakdown": breakdown
    }


def estimate_credits_for_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-level function to estimate credits and provide a breakdown.
    This is now a simple wrapper around credit_estimation.
    
    Args:
        req: The scraping request dictionary
        
    Returns:
        Dictionary with detailed credit breakdown including:
        - min_credits: Minimum estimated credits
        - max_credits: Maximum estimated credits
        - breakdown: Detailed breakdown of credit usage by component
    """
    return asyncio.run(credit_estimation(req))
