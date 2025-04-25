from math import ceil
from scraper_service.settings import rapid_api_settings
from scraper_service.client.schemas.job_config_schema import ScrapingRequest


async def credit_estimation(req: ScrapingRequest):
    
    max_credits = 0
    min_credits = 0
    p = rapid_api_settings
    
    if req['type'] == "company":
        if req['profile_info'] == "yes":
            # Add 1 credit for enabling post_scrap
            max_credits += 1
            min_credits += 1
            
        if req['post_scrap'] == "yes":
            # Add credits for the number of posts to be scraped (batches of 50)
            post_batches = ceil(req['post_limit'] / 50)
            max_credits += post_batches * 1
            min_credits += post_batches * 1
            
            if req['post_comments'] == "yes":
                # Add 1 credit per post to get commenters
                max_credits += req['post_limit'] * 1
                min_credits += req['post_limit'] * 1
                
            if req['post_reactions'] == "yes":
                count=1
                for _ in range(req['post_limit']):
                    count=count+1
                    reactors = req['reaction_limit']
                    if reactors <= 49:
                        max_credits += 3
                        min_credits += 1
                    else:
                        remaining = reactors - 49
                        batches = ceil(remaining / 49)
                        max_credits += 3 + (batches * 2)
                        min_credits += 1 +(batches * 1)

    if req['type'] == "person":
        if req['profile_info'] == "yes":
            # Add 1 credit for enabling post_scrap
            max_credits += 1
            min_credits += 1
        
        if req['post_scrap'] == "yes":
            # Add credits for the number of posts to be scraped (batches of 50)
            post_batches = ceil(req['post_limit'] / 50)
            max_credits += post_batches * 1
            min_credits += post_batches * 1

            if req['post_comments'] == "yes":
                # Add 1 credit per post to get commenters
                max_credits += req['post_limit'] * 1
                min_credits += req['post_limit'] * 1

            if req['post_reactions'] == "yes":
                for _ in range(req['post_limit']):
                    reactors = req['reaction_limit']
                    if reactors <= p.REACTORS_BATCH:
                        max_credits += 1
                        min_credits += 1
                    else:
                        remaining = reactors - p.REACTORS_BATCH
                        batches = ceil(remaining / p.REACTORS_BATCH)
                        max_credits += 1 + (batches * 1)
                        min_credits += 1 +(batches * 1)
        
        if req['activity_comments'] == "yes":
    
            # Add credits for the number of posts to be scraped (batches of 50)
            max_credits += 1
            min_credits += 1
            
            if req['post_comments'] == "yes":
                # Add 1 credit per post to get commenters
                max_credits += req['post_limit'] * 1
                min_credits += req['post_limit'] * 1
                
            if req['post_reactions'] == "yes":
                for _ in range(req['post_limit']):
                   
                    reactors = req['reaction_limit']
                    if reactors <= 49:
                        max_credits += 3
                        min_credits += 1
                    else:
                        remaining = reactors - 49
                        batches = ceil(remaining / 49)
                        max_credits += 3 + (batches * 2)
                        min_credits += 1 +(batches * 1)
        
        if req['activity_reactions'] == "yes":

            # Add credits for the number of posts to be scraped (batches of 50)
            activity_reactions_batches = ceil(req['post_limit'] / 100)
            max_credits += activity_reactions_batches * 1
            min_credits += activity_reactions_batches * 1


            if req['post_comments'] == "yes":
                # Add 1 credit per post to get commenters
                max_credits += req['post_limit'] * 1
                min_credits += req['post_limit'] * 1

            if req['post_reactions'] == "yes":
                for _ in range(req['post_limit']):
                    
                    reactors = req['reaction_limit']
                    if reactors <= 49:
                        max_credits += 3
                        min_credits += 1
                    else:
                        remaining = reactors - 49
                        batches = ceil(remaining / 49)
                        max_credits += 3 + (batches * 2)
                        min_credits += 1 +(batches * 1)

    return {"max_credits": max_credits,"min_credits":min_credits}