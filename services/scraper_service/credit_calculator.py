from math import ceil
from typing import Dict, Any
from scraper_service.settings import rapid_api_settings


async def credit_estimation(req: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate the estimated credit cost for a LinkedIn scraping request.
    
    Args:
        req: Dictionary containing the scraping request parameters with fields:
             - type: "company" or "person"
             - profile_info: "yes" or "no"
             - post_scrap: "yes" or "no" (for entity posts)
             - post_limit: number of posts to scrape
             - post_comments: "yes" or "no"
             - comment_limit: max comments per post
             - post_reactions: "yes" or "no"
             - reaction_limit: max reactions per post
             - activity_comments: "yes" or "no" (person only)
             - activity_reactions: "yes" or "no" (person only)
    
    Returns:
        Dictionary with 'max_credits' and 'min_credits' estimates
    """
    max_credits = 0
    min_credits = 0
    p = rapid_api_settings
    
    # Get type with default
    entity_type = req.get('type', 'person')
    
    # Activity comments and reactions are always for persons (not companies)
    # These job types don't require the 'type' field in ScrapingRequest
    if req.get('activity_comments') == "yes" or req.get('activity_reactions') == "yes":
        entity_type = "person"
    
    if entity_type == "company":
        if req.get('profile_info') == "yes":
            # Add 1 credit for enabling profile_info
            max_credits += 1
            min_credits += 1
            
        if req.get('post_scrap') == "yes":
            # Add credits for the number of posts to be scraped (batches of 50)
            post_limit = req.get('post_limit', 0)
            if post_limit > 0:
                post_batches = ceil(post_limit / 50)
                max_credits += post_batches * 1
                min_credits += post_batches * 1
            
            if req.get('post_comments') == "yes":
                # Add 1 credit per post to get commenters
                max_credits += post_limit * 1
                min_credits += post_limit * 1
                
            if req.get('post_reactions') == "yes":
                reaction_limit = req.get('reaction_limit', p.DEFAULT_REACTION_LIMIT)
                for _ in range(post_limit):
                    if reaction_limit <= 49:
                        max_credits += 3
                        min_credits += 1
                    else:
                        remaining = reaction_limit - 49
                        batches = ceil(remaining / 49)
                        max_credits += 3 + (batches * 2)
                        min_credits += 1 + (batches * 1)

    if entity_type == "person":
        if req.get('profile_info') == "yes":
            # Add 1 credit for enabling profile_info
            max_credits += 1
            min_credits += 1
        
        if req.get('post_scrap') == "yes":
            # Add credits for the number of posts to be scraped (batches of 50)
            post_limit = req.get('post_limit', 0)
            if post_limit > 0:
                post_batches = ceil(post_limit / 50)
                max_credits += post_batches * 1
                min_credits += post_batches * 1

            if req.get('post_comments') == "yes":
                # Add 1 credit per post to get commenters
                max_credits += post_limit * 1
                min_credits += post_limit * 1

            if req.get('post_reactions') == "yes":
                reaction_limit = req.get('reaction_limit', p.DEFAULT_REACTION_LIMIT)
                for _ in range(post_limit):
                    if reaction_limit <= p.DEFAULT_REACTION_LIMIT:
                        max_credits += 1
                        min_credits += 1
                    else:
                        remaining = reaction_limit - p.DEFAULT_REACTION_LIMIT
                        batches = ceil(remaining / p.DEFAULT_REACTION_LIMIT)
                        max_credits += 1 + (batches * 1)
                        min_credits += 1 + (batches * 1)
        
        if req.get('activity_comments') == "yes":
            # Add base credit for activity comments
            max_credits += 1
            min_credits += 1
            
            post_limit = req.get('post_limit', 0)
            
            if req.get('post_comments') == "yes" and post_limit > 0:
                # Add 1 credit per post to get commenters
                max_credits += post_limit * 1
                min_credits += post_limit * 1
                
            if req.get('post_reactions') == "yes" and post_limit > 0:
                reaction_limit = req.get('reaction_limit', p.DEFAULT_REACTION_LIMIT)
                for _ in range(post_limit):
                    if reaction_limit <= 49:
                        max_credits += 3
                        min_credits += 1
                    else:
                        remaining = reaction_limit - 49
                        batches = ceil(remaining / 49)
                        max_credits += 3 + (batches * 2)
                        min_credits += 1 + (batches * 1)
        
        if req.get('activity_reactions') == "yes":
            # Add credits for activity reactions (batches of 100)
            post_limit = req.get('post_limit', 0)
            if post_limit > 0:
                activity_reactions_batches = ceil(post_limit / 100)
                max_credits += activity_reactions_batches * 1
                min_credits += activity_reactions_batches * 1

                if req.get('post_comments') == "yes":
                    # Add 1 credit per post to get commenters
                    max_credits += post_limit * 1
                    min_credits += post_limit * 1

                if req.get('post_reactions') == "yes":
                    reaction_limit = req.get('reaction_limit', p.DEFAULT_REACTION_LIMIT)
                    for _ in range(post_limit):
                        if reaction_limit <= 49:
                            max_credits += 3
                            min_credits += 1
                        else:
                                                    remaining = reaction_limit - 49
                        batches = ceil(remaining / 49)
                        max_credits += 3 + (batches * 2)
                        min_credits += 1 + (batches * 1)
    
    # Handle search jobs (keyword and hashtag searches)
    if req.get('search_post_by_keyword') == "yes":
        # Search by keyword: 1 credit per page/batch
        # Assuming ~10-20 posts per page based on typical API responses
        post_limit = req.get('post_limit', 0)
        if post_limit > 0:
            # Conservative estimate: ~10 posts per page
            search_pages = ceil(post_limit / 10)
            max_credits += search_pages
            # Optimistic estimate: ~20 posts per page
            min_pages = ceil(post_limit / 20)
            min_credits += min_pages
    
    if req.get('search_post_by_hashtag') == "yes":
        # Search by hashtag: 1 credit per page/batch
        # Based on search_posts.py, typically 45 posts per page
        post_limit = req.get('post_limit', 0)
        if post_limit > 0:
            # Hashtag search typically returns ~45 posts per page
            search_pages = ceil(post_limit / 45)
            max_credits += search_pages
            min_credits += search_pages

    return {"max_credits": max_credits,"min_credits":min_credits}
