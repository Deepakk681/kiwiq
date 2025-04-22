import math
from typing import Dict, Tuple
from scraper_service.settings import rapid_api_settings
from scraper_service.client.schemas import PostsRequest

# Use constants from settings
POSTS_BATCH_SIZE = rapid_api_settings.BATCH_SIZE 
REACTORS_BATCH_SIZE = rapid_api_settings.DEFAULT_REACTION_LIMIT 

# Modify function signature to accept PostsRequest
def calculate_credits(req: PostsRequest) -> Tuple[int, int]:
    """
    Calculates the estimated minimum and maximum credits required for scraping posts,
    based on the PostsRequest configuration.

    Note: This estimation assumes costs for fetching posts, comments, and reactions.
          It does not include profile fetching or activity-specific costs.
          Uses batch sizes defined in rapid_api_settings.

    Args:
        req (PostsRequest): The configuration for the post scraping job.

    Returns:
        Tuple[int, int]: A tuple containing (min_credits, max_credits).
    """
    max_credits = 0
    min_credits = 0
    
    post_limit = req.post_limit 
    reaction_limit = req.reaction_limit
    # comment_limit is available in req but it is not used in this estimation logic

    # --- Post Fetching Calculation ---
    posts_are_fetched = req.post_comments == "yes" or req.post_reactions == "yes" or post_limit > 0
    
    if posts_are_fetched and post_limit > 0:
        # Add credit per batch of posts
        post_batches = math.ceil(post_limit / POSTS_BATCH_SIZE) 
        base_post_cost = post_batches * 1
        max_credits += base_post_cost
        min_credits += base_post_cost

        # --- Per-Post Calculations (Comments & Reactions) ---
        
        # Calculate credits per post for comments
        credits_per_post_for_comments = 0
        if req.post_comments == "yes":
            # Add 1 credit per post to fetch comments, regardless of comment_limit for estimation
            credits_per_post_for_comments = 1 

        # Calculate min/max credits per post for reactions
        min_credits_per_post_for_reactions = 0
        max_credits_per_post_for_reactions = 0
        if req.post_reactions == "yes":
            if reaction_limit <= REACTORS_BATCH_SIZE:
                cost = 1 
                min_credits_per_post_for_reactions = cost
                max_credits_per_post_for_reactions = cost
            else:
                # Cost for subsequent batches
                remaining = reaction_limit - REACTORS_BATCH_SIZE
                batches = math.ceil(remaining / REACTORS_BATCH_SIZE) 
                cost = 1 + (batches * 1) # Base + cost per extra batch
                min_credits_per_post_for_reactions = cost 
                max_credits_per_post_for_reactions = cost 

        # Add costs for comments/reactions *per post* fetched
        max_credits += post_limit * (credits_per_post_for_comments + max_credits_per_post_for_reactions)
        min_credits += post_limit * (credits_per_post_for_comments + min_credits_per_post_for_reactions)

    min_credits = max(0, min_credits)
    max_credits = max(0, max_credits)

    return min_credits, max_credits 