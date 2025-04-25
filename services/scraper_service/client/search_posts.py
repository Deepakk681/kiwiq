import http.client
import json
from typing import Dict, List, Any, Optional, Union, TypeVar, Type, Generic
from scraper_service.settings import rapid_api_settings
import http.client
import json
from fastapi import FastAPI, Depends, HTTPException,APIRouter, Header


class SearchPosts:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.host = base_url 
        
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.host,
            'Content-Type': "application/json"
        }

    async def search_post_by_keyword(self, keyword: str, total_posts: Optional[int] = None) -> List[dict]:
        if not total_posts:
            total_posts = rapid_api_settings.SCRAPER_SERVICE_SEARCH_BY_KEYWORD_BATCH_SIZE
        
        credit_used = 0
        conn = http.client.HTTPSConnection(self.host)
    
        headers = self.headers
        collected_posts = []
        page = 1

        while len(collected_posts) < total_posts:
            credit_used= credit_used+1
            payload = json.dumps({
                "keyword": keyword,
                "sortBy": "date_posted",
                "datePosted": "",
                "page": page,
                "contentType": "",
                "fromMember": [],
                "fromCompany": [],
                "mentionsMember": [],
                "mentionsOrganization": [],
                "authorIndustry": [],
                "authorCompany": [],
                "authorTitle": ""
            })
            
            endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['search_post_by_keyword']
            try:
                conn.request("POST", endpoint, body=payload, headers=headers)
                res = conn.getresponse()
                data = res.read()
            except Exception as e:
                return {"error": "Failed to connect to API", "message": str(e)}

            try:
                response_json = json.loads(data.decode("utf-8"))
                posts = response_json.get("data", {}).get("items", [])
                
                if not posts:
                    break  # Stop if no more posts are available

                collected_posts.extend(posts)

                if len(collected_posts) >= total_posts:
                    break  # Stop if we've collected enough posts

                page += 1  # Move to the next page

            except json.JSONDecodeError:
                return {"error": "Failed to decode API response", "message": str(e)}

        return collected_posts  # {"posts": collected_posts, "credit_used":credit_used}
    
    
    async def search_post_by_hashtag(self, hashtag: str, total_posts: Optional[int] = None) -> List[dict]:
        if not total_posts:
            total_posts = rapid_api_settings.SCRAPER_SERVICE_SEARCH_BY_HASHTAG_BATCH_SIZE
        
        credit_used = 0
        conn = http.client.HTTPSConnection(self.host)
        headers = self.headers
        post_limit= total_posts
        collected_posts = []
        pagination_token = ""
        start = 0

        while len(collected_posts) < post_limit:
            credit_used= credit_used+1
            payload = json.dumps({
                "hashtag": hashtag,
                "sortBy": "REV_CHRON",
                "start": str(start),
                "paginationToken": pagination_token
            })

            endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['search_post_by_hashtag']
            try:
                conn.request("POST", endpoint, body=payload, headers=headers)
                res = conn.getresponse()
                data = res.read()
            except Exception as e:
                return {"error": "Failed to connect to API", "message": str(e)}

            try:
                response_json = json.loads(data.decode("utf-8"))
                posts = response_json.get("data", {}).get("items", [])
                pagination_token = response_json.get("data", {}).get("paginationToken", "")
                total_posts = response_json.get("data", {}).get("total", 0)

                if not posts:
                    break  # No more posts to fetch

                collected_posts.extend(posts)

                if not pagination_token or len(collected_posts) >= total_posts:
                    break

                # Increment start for next batch (typically count per page is 45)
                start += len(posts)

            except json.JSONDecodeError:
                return {"error": "Failed to decode API response", "message": str(e)}

        return collected_posts  # {"posts": collected_posts, "credit_used":credit_used}
