"""
LinkedIn post fetcher client for RapidAPI.

This module provides a client for fetching LinkedIn posts, comments, and reactions 
using the RapidAPI LinkedIn scraper endpoint. It leverages a generic API request
handler for making calls and parsing responses.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Union

import aiohttp

from scraper_service.client.backup_changes.core_api_client import RapidAPIClient
from scraper_service.settings import rapid_api_settings
from scraper_service.client.utils.url_helper import extract_urn_from_url
from global_config.logger import get_logger
from scraper_service.client.schemas import PostReactionsRequest , ProfilePostCommentsRequest, PostComment, PostsRequest, ProfilePost, PostReaction , PostDetailsRequest , PostDetailsResponse, CompanyPostCommentsRequest, CompanyPostResponse , CompanyPost , CompanyPostAuthor , CompanyPostArticle , CompanyPostComment , CompanyPostAuthor, LikeItem , LikeActivity , LikeOwner
from scraper_service.client.backup_changes.request_schemas import (
    APIRequest, Pagination, ParseResponseConfig, ResponseBaseModel
)
from scraper_service.client.utils.url_helper import extract_urn_from_url
# Configure logging
logger = get_logger(__name__)

class LinkedinPostFetcher:
    """
    Client for fetching LinkedIn posts, comments, and reactions.
    
    This client provides methods for fetching LinkedIn posts for a user or company,
    as well as comments and reactions on those posts. It uses the RapidAPI
    LinkedIn scraper endpoint via a generic request handler.
    """
    
    def __init__(self, api_key=None, base_url=None):
        """
        Initialize the LinkedIn Post Fetcher.
        
        Args:
            api_key (Optional[str]): API key for RapidAPI. Defaults to settings value.
            base_url (Optional[str]): Host URL for RapidAPI. Defaults to settings value.
        """
        self.rapidapi_key = api_key or rapid_api_settings.RAPID_API_KEY
        self.rapidapi_host = base_url or rapid_api_settings.RAPID_API_HOST
        self.api_client = RapidAPIClient(self.rapidapi_key, self.rapidapi_host)

    async def make_api_request(
        self,
        api_request: APIRequest
    ) -> Union[ResponseBaseModel, List[ResponseBaseModel], List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Makes an API request based on the provided APIRequest configuration.

        Handles GET/POST methods, pagination, response parsing, and model validation.

        Args:
            api_request (APIRequest): Configuration object for the API request.

        Returns:
            Union[ResponseBaseModel, List[ResponseBaseModel], List[Dict[str, Any]], Dict[str, Any], None]:
            The parsed response, potentially as a list of models, single model,
            list of dicts, single dict, or None in case of errors or empty data.
            Returns None if the initial request fails or yields no data.
            If pagination fails mid-way, returns the data collected up to that point.
        """
        all_items: List[Dict[str, Any]] = []
        final_data: Union[List[Dict[str, Any]], Dict[str, Any], None] = None
        request_description = f"{api_request.method.upper()} {api_request.endpoint}" # For logging context

        # --- Pagination Logic ---
        if api_request.pagination and api_request.batch_limit:
            # Ensure pagination object is mutable for updates within the loop
            current_pagination = api_request.pagination

            while len(all_items) < api_request.batch_limit:
                query_params = api_request.get_query_params() # Includes current pagination params
                payload = api_request.get_body_payload() # Includes current pagination params (if applicable)

                # Make the actual API call using the RapidAPIClient instance
                raw_response: Dict[str, Any] = {}
                try:
                    if api_request.method.upper() == "GET":
                        raw_response = await self.api_client.make_get_request(api_request.endpoint, params=query_params)
                    elif api_request.method.upper() == "POST":
                        # Ensure payload is not None before passing
                        valid_payload = payload if payload else {}
                        raw_response = await self.api_client.make_post_request(api_request.endpoint, payload=valid_payload)
                    else:
                        logger.error(f"Unsupported HTTP method: {api_request.method} for {request_description}")
                        # Return None if this happens on the first attempt, otherwise return collected items
                        return None if not all_items else all_items[:api_request.batch_limit]


                    # Check for errors indicated in the response payload
                    # Note: RapidAPIClient's parse_response handles HTTP errors and adds 'error' key
                    if raw_response.get("error"):
                        error_msg = raw_response.get("error", "Unknown API error")
                        logger.error(f"API returned an error for {request_description} (Page/Batch {current_pagination.page or current_pagination.start}): {error_msg}")
                        # Stop pagination on error, return what we have so far (or None if first page failed)
                        break

                except Exception as e:
                    # Catch unexpected errors during the request itself
                    logger.error(f"Unexpected error during API call {request_description} (Page/Batch {current_pagination.page or current_pagination.start}): {e}", exc_info=True)
                    # Stop pagination on error
                    break

                # Extract the relevant data part using parse_response configuration
                data_part: Any = None # Can be dict, list, or None
                try:
                    data_part = api_request.parse_response(raw_response)
                except KeyError as e:
                    logger.error(f"Failed to extract data using parse_response_config: {e} for {request_description}. Response keys: {raw_response.keys()}")
                    # Stop pagination if data structure is unexpected
                    break
                except Exception as e:
                    logger.error(f"Unexpected error during response parsing for {request_description}: {e}", exc_info=True)
                    break

                # Extract the list of items from the data part based on config
                items_batch: Optional[List[Dict[str, Any]]] = None
                if data_part is None:
                    # This might be valid if the API returns e.g., {"data": null} on empty page
                    logger.info(f"Data part extracted as None for {request_description}. Assuming empty page.")
                    items_batch = [] # Treat as empty batch
                else:
                    config = api_request.parse_response_config
                    if config and config.list_items_field_name:
                        # Field explicitly tells where the list is within data_part
                        if isinstance(data_part, dict):
                             items_batch = data_part.get(config.list_items_field_name)
                        else:
                             logger.warning(f"Expected data_part to be a dict for list_items_field_name '{config.list_items_field_name}', but got {type(data_part)}. Cannot extract batch.")
                             break # Cannot proceed if structure is wrong
                    elif config and config.is_list:
                         # The extracted data_part itself should be the list
                         if isinstance(data_part, list):
                             items_batch = data_part
                         else:
                             logger.warning(f"Expected data_part to be a list based on is_list=True for {request_description}, but got {type(data_part)}. Assuming empty page.")
                             items_batch = []
                    elif isinstance(data_part, list):
                        # If no config, but data_part is a list, assume it's the batch
                        items_batch = data_part
                    else:
                        # If it's not a list and no config indicates otherwise, pagination cannot proceed
                        logger.warning(f"Pagination active for {request_description}, but did not find a list of items. Data part type: {type(data_part)}. Assuming end of results.")
                        items_batch = [] # Treat as end of results

                # --- Validate and Process Batch ---
                # Ensure items_batch is actually a list now
                if not isinstance(items_batch, list):
                    logger.warning(f"Extracted items_batch is not a list ({type(items_batch)}) for {request_description}. Stopping pagination. Response snippet: {str(raw_response)[:200]}")
                    break

                # Check if the batch is empty, indicating end of results
                if not items_batch:
                    logger.info(f"Received empty batch for {request_description}. Ending pagination.")
                    break

                # Add valid items (ensure they are dicts, log if not)
                valid_items_count = 0
                for item in items_batch:
                    if isinstance(item, dict):
                        all_items.append(item)
                        valid_items_count += 1
                    else:
                        logger.warning(f"Skipping non-dict item in batch for {request_description}: {type(item)}")
                
                logger.info(f"Fetched {valid_items_count} valid items for {request_description}. Total items: {len(all_items)} / {api_request.batch_limit}.")

                # Check if batch limit reached
                if len(all_items) >= api_request.batch_limit:
                    logger.info(f"Reached batch limit ({api_request.batch_limit}) for {request_description}. Stopping pagination.")
                    break

                # --- Update Pagination for next iteration ---
                # Attempt to find pagination token (look in common places)
                new_pagination_token = raw_response.get("paginationToken") or \
                                       raw_response.get("data", {}).get("paginationToken") or \
                                       (data_part.get("paginationToken") if isinstance(data_part, dict) else None)

                token_based = hasattr(current_pagination, 'pagination_token')

                if new_pagination_token:
                    if token_based:
                         current_pagination.pagination_token = new_pagination_token
                         logger.debug(f"Using next pagination token for {request_description}: {new_pagination_token[:10]}...")
                    else:
                         logger.warning("Received pagination token, but pagination config doesn't support it.")
                elif token_based and current_pagination.pagination_token is not None:
                    # If we were using tokens and didn't get a new one, assume end of results
                     logger.info(f"Pagination token not found in response for {request_description}. Assuming end of results.")
                     break

                # Increment page/start if applicable (handled by paginate method)
                # Only paginate if we didn't just stop due to lack of token
                if not (token_based and not new_pagination_token):
                    current_pagination.paginate()

                # Safety break: If pagination relies *only* on token (no start/page) and we don't get one, stop.
                if token_based and not new_pagination_token and current_pagination.start is None and current_pagination.page is None:
                     logger.info(f"No new pagination token and no start/page parameter for {request_description}. Stopping pagination.")
                     break
                 # Safety break: If pagination relies on start/page and they are None after paginate(), something is wrong.
                if not token_based and current_pagination.start is None and current_pagination.page is None:
                     logger.error(f"Pagination configuration error for {request_description}: start/page became None. Stopping.")
                     break


                # Add a delay between paginated requests to avoid rate limits
                await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_API_DELAY)

            # Trim results to the exact limit after the loop finishes
            final_data = all_items[:api_request.batch_limit]

        # --- Single Request Logic (No Pagination) ---
        else:
            query_params = api_request.get_query_params()
            payload = api_request.get_body_payload()
            raw_response: Dict[str, Any] = {}

            try:
                if api_request.method.upper() == "GET":
                    raw_response = await self.api_client.make_get_request(api_request.endpoint, params=query_params)
                elif api_request.method.upper() == "POST":
                    valid_payload = payload if payload else {}
                    raw_response = await self.api_client.make_post_request(api_request.endpoint, payload=valid_payload)
                else:
                    logger.error(f"Unsupported HTTP method: {api_request.method} for {request_description}")
                    return None

                # Check for errors indicated in the response payload
                if raw_response.get("error"):
                    error_msg = raw_response.get("error", "Unknown API error")
                    logger.error(f"API returned an error for single request {request_description}: {error_msg}")
                    return None # Error on single request means no data

            except Exception as e:
                logger.error(f"Unexpected error during single API call {request_description}: {e}", exc_info=True)
                return None

            # Extract data part for single request
            try:
                data_part = api_request.parse_response(raw_response)
                final_data = data_part # Could be a list or dict, or None if API returns empty data part
            except KeyError as e:
                 logger.error(f"Failed to extract data using parse_response_config for single request {request_description}: {e}. Response keys: {raw_response.keys()}")
                 return None # Cannot proceed if data structure is wrong
            except Exception as e:
                 logger.error(f"Unexpected error during response parsing for single request {request_description}: {e}", exc_info=True)
                 return None

        # --- Result Processing & Model Parsing ---
        if final_data is None:
            logger.info(f"Final data is None after request(s) for {request_description}. Returning None.")
            # Handles cases where pagination completed but found nothing, or single request yielded None data_part
            return None

        if api_request.response_model:
            # If a response model is specified, parse the final_data into it
            parsed_results: Union[ResponseBaseModel, List[ResponseBaseModel], None] = None
            model_name = api_request.response_model.__name__
            try:
                if isinstance(final_data, list):
                    # Parse each item in the list
                    parsed_results = []
                    for item in final_data:
                        if isinstance(item, dict):
                            try:
                                # Use the classmethod from ResponseBaseModel base class if needed,
                                # or just standard Pydantic initialization which handles extra fields gracefully with `extra='allow'`
                                # parsed_item = api_request.response_model.parse_response(item) # If using custom parser
                                parsed_item = api_request.response_model(**item) # Standard Pydantic parsing
                                parsed_results.append(parsed_item)
                            except Exception as parse_error:
                                logger.warning(f"Failed to parse item into {model_name} for {request_description}: {parse_error}. Item keys: {item.keys()}")
                        else:
                            logger.warning(f"Skipping non-dict item in list during model parsing for {request_description}: {item}")
                    logger.info(f"Successfully parsed {len(parsed_results)} items into {model_name} for {request_description}.")
                    return parsed_results
                elif isinstance(final_data, dict):
                     # Parse the single dictionary
                    # parsed_results = api_request.response_model.parse_response(final_data) # If using custom parser
                    parsed_results = api_request.response_model(**final_data) # Standard Pydantic parsing
                    logger.info(f"Successfully parsed single dict into {model_name} for {request_description}.")
                    return parsed_results
                else:
                     # This shouldn't happen if extraction logic is correct, but handle defensively
                     logger.error(f"Final data for {request_description} is neither list nor dict ({type(final_data)}), cannot parse with model {model_name}.")
                     return None # Cannot parse

            except Exception as e:
                # Catch errors during the Pydantic parsing itself
                logger.error(f"Error parsing response into {model_name} for {request_description}: {e}. Data type: {type(final_data)}", exc_info=True)
                # Returning None as parsing failed
                return None
        else:
            # No response model specified, return the raw extracted data (list or dict)
            logger.info(f"Returning raw data ({'list' if isinstance(final_data, list) else 'dict' if isinstance(final_data, dict) else type(final_data)}) for {request_description} as no response_model was specified.")
            return final_data

    async def fetch_share_url(self, post_url):
        """Fetches shareUrl from LinkedIn post API if not available.
        
        NOTE: costs 1 credit per request!
        """
        
        endpoint = f"/get-post?url={post_url}"
        
        response = await self.api_client.make_get_request(endpoint)

        if not response.get("success", False):
            logger.error(f"Error fetching company posts: {response.get('message')}")
            return CompanyPostResponse(posts=[])

        post_data = response.get("data", [])
        return post_data.get("shareUrl", "none")

    async def get_company_posts(self, request: PostsRequest) -> List[CompanyPostResponse]:
        """
        Fetch posts for a LinkedIn company page.
        
        Args:
            request (PostsRequest): Request object containing:
                - username (str): LinkedIn company username
                - post_limit (Optional[int]): Maximum number of posts to fetch
                - post_comments (str): "yes" or "no" to include comments
                - post_reactions (str): "yes" or "no" to include reactions
                - comment_limit (Optional[int]): Maximum number of comments per post
                - reaction_limit (Optional[int]): Maximum number of reactions per post
        
        Returns:
            List[CompanyPostResponse]: List of company posts with their details, comments, and reactions if requested.
            
        Raises:
            ValueError: If username is not provided.
            
        Example:
            >>> request = PostsRequest(username="microsoft", post_limit=5, post_comments="yes", post_reactions="yes")
            >>> posts = await fetcher.get_company_posts(request)
            >>> print(f"Retrieved {len(posts)} posts")
        
            
        NOTE: fetch_share_url costs 1 credit per request if used to fetch shareUrl for a company post!
        """
        if not request.username:
            raise ValueError("Username is required")

        post_limit = request.post_limit or rapid_api_settings.DEFAULT_POST_LIMIT
        comment_limit = request.comment_limit or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request.reaction_limit or rapid_api_settings.DEFAULT_REACTION_LIMIT

        all_posts = []
        start = 0
        pagination_token = None

        while len(all_posts) < post_limit:
            endpoint = f"{rapid_api_settings.ENDPOINTS['company_posts']}?username={request.username}&start={start}"
            if pagination_token:
                endpoint += f"&paginationToken={pagination_token}"

            response = await self.api_client.make_get_request(endpoint)

            if not response.get("success", False):
                logger.error(f"Error fetching company posts: {response.get('message')}")
                return CompanyPostResponse(posts=[])

            posts_batch = response.get("data", [])
            all_posts.extend(posts_batch)

            if len(all_posts) >= post_limit:
                break

            pagination_token = response.get("paginationToken")
            if not pagination_token:
                break

            start += rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE

        posts: List[CompanyPost] = []

        for raw_post in all_posts[:post_limit]:
            if not isinstance(raw_post, dict):
                continue

            post_url = raw_post.get("postUrl")
            # https://github.com/KiwiQAI/scraping_service/blob/kunal/rapidapi_v2/src/scraper/rapid_api/rapid_manager/company_manager.py
            share_url = raw_post.get("shareUrl") or await self.fetch_share_url(post_url)
            urn =  extract_urn_from_url(post_url)

            # Prepare nested fields
            author_data = raw_post.get("author", {}).get("company")
            author = CompanyPostAuthor(**author_data) if author_data else None

            # I have added this to handle the case where the article is not present in the response , it was giving unbound Local error
            article = None
            article_data = raw_post.get("article")
            if isinstance(article_data, dict) and "title" in article_data:
                try:
                    article = CompanyPostArticle(**article_data)
                except Exception as e:
                    logger.warning(f"Invalid article data: {article_data}, error: {e}")

            comments: List[CompanyPostComment] = []
            if request.post_comments == "yes" and urn:
                comments = await self.get_company_post_comments(
                    CompanyPostCommentsRequest(post_urn=urn),
                    comment_limit
                )
            reactions = []
            if request.post_reactions.lower() == "yes" and post_url:
                try:
                    reaction_objs = await self.get_post_reactions(
                        PostReactionsRequest(post_url=share_url),
                        reaction_limit
                    )
                    reactions = [r.model_dump() for r in reaction_objs]  
                except Exception as e:
                    logger.error(f"Error in get_profile_post_reactions: {e}")
                    reactions = []

            post = CompanyPostResponse(
                text=raw_post.get("text", ""),
                totalReactionCount=raw_post.get("totalReactionCount", 0),
                likeCount=raw_post.get("likeCount", 0),
                appreciationCount=raw_post.get("appreciationCount", 0),
                empathyCount=raw_post.get("empathyCount", 0),
                InterestCount=raw_post.get("InterestCount", 0),
                praiseCount=raw_post.get("praiseCount", 0),
                commentsCount=raw_post.get("commentsCount", 0),
                repostsCount=raw_post.get("repostsCount", 0),
                postUrl=post_url,
                postedAt=raw_post.get("postedAt", ""),
                urn=raw_post.get("urn", ""),
                author=author,
                article=article,
                video=raw_post.get("video", []),
                comments=comments,
                reactions=reactions  
            )

            posts.append(post)

        return posts

    async def get_company_post_comments(
        self, 
        request: CompanyPostCommentsRequest, 
        comment_limit: int
    ) -> List[CompanyPostComment]:
        """
        Fetch comments for a company LinkedIn post.
        
        Args:
            request (CompanyPostCommentsRequest): Request object containing:
                - post_urn (str): The URN identifier of the LinkedIn post
            comment_limit (int): Maximum number of comments to fetch
            
        Returns:
            List[CompanyPostComment]: List of parsed comment models
            
        Example:
            >>> request = CompanyPostCommentsRequest(post_urn="urn:li:activity:1234567890")
            >>> comments = await fetcher.get_company_post_comments(request, 10)
            >>> print(f"Retrieved {len(comments)} comments")
        """
        if not request.post_urn:
            return []

        endpoint = f"{rapid_api_settings.ENDPOINTS['company_post_comments']}?urn={request.post_urn}"
        response = await self.api_client.make_get_request(endpoint)

        raw_comments = []
        if isinstance(response, list):
            raw_comments = response
        elif isinstance(response, dict):
            if not response.get("success", False):
                logger.error(f"Error fetching comments: {response.get('message')}")
                return []
            data = response.get("data") 
            if isinstance(data, list): 
                raw_comments = data
            elif isinstance(data, dict):  
                raw_comments = data.get("comments", [])
        else:
            logger.error(f"Unexpected response type: {type(response)}")
            return []

        comments: List[CompanyPostComment] = []
        for c in raw_comments[:comment_limit]:
            author = c.get("author", {}) if isinstance(c, dict) else {}
            full_name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
            comments.append(CompanyPostComment(
                name=full_name,
                linkedinUrl=author.get("linkedinUrl", ""),
                title=author.get("title", ""),
                text=c.get("text", "")
            ))

        return comments

    async def get_post_reactions(self, request: PostReactionsRequest, reaction_limit: int) -> List[PostReaction]:
        """
        Fetch reactions for a LinkedIn post.
        
        Args:
            request (PostReactionsRequest): Request object containing:
                - post_url (str): LinkedIn post URL
            reaction_limit (int): Maximum number of reactions to fetch
            
        Returns:
            List[PostReaction]: List of formatted reactions
            
        Example:
            >>> request = PostReactionsRequest(post_url="https://www.linkedin.com/posts/some-post-url")
            >>> reactions = await fetcher.get_post_reactions(request, 20)
            >>> print(f"Retrieved {len(reactions)} reactions")
        """
        if not request.post_url:
            return []

        all_reactions: List[PostReaction] = []
        page = 1

        while len(all_reactions) < reaction_limit:
            payload = {"url": request.post_url, "page": page}
            response = await self.api_client.make_post_request(rapid_api_settings.ENDPOINTS['post_reactions'], payload)

            if not response.get("success", False):
                logger.error(f"Error fetching reactions: {response.get('message')}")
                return []

            raw_items = response.get("data", {}).get("items", [])
            if not raw_items:
                break

            for item in raw_items:
                try:
                    reaction = PostReaction(
                        fullName=item.get("fullName", ""),
                        headline=item.get("headline", ""),
                        reactionType=item.get("reactionType", ""),
                        profileUrl=item.get("profileUrl", "")
                    )
                    all_reactions.append(reaction)
                except Exception as e:
                    logger.warning(f"Skipping invalid reaction: {e}")

            if len(all_reactions) >= reaction_limit:
                break

            page += 1
            await asyncio.sleep(1.5)

        return [PostReaction(**reaction.model_dump()) for reaction in all_reactions[:reaction_limit]]

    async def get_profile_posts(
        self,
        request: PostsRequest
    ) -> List[ProfilePost]:
        """
        Fetch posts for a LinkedIn user profile using the generic API request handler.

        Args:
            request (PostsRequest): Request object containing:
                - username (str): LinkedIn profile username
                - post_limit (Optional[int]): Maximum number of posts to fetch
                - post_comments (str): "yes" or "no" to include comments (Handled separately after fetch)
                - post_reactions (str): "yes" or "no" to include reactions (Handled separately after fetch)
                - comment_limit (Optional[int]): Maximum number of comments per post
                - reaction_limit (Optional[int]): Maximum number of reactions per post

        Returns:
            List[ProfilePost]: List of profile posts enriched with comments/reactions if requested.
                               Returns empty list if no posts found or on error fetching posts.
        """
        if not request.username:
            logger.error("Username is required for get_profile_posts")
            return []

        post_limit = request.post_limit or rapid_api_settings.DEFAULT_POST_LIMIT

        # Define the API Request configuration for fetching the raw posts list
        api_req = APIRequest(
            endpoint=rapid_api_settings.ENDPOINTS['profile_posts'],
            method="GET",
            query_params={"username": request.username}, # Pass the username as query param
            pagination=Pagination(
                start=0, # Initial start index
                batch_size=rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE, # API returns batches of this size
                pagination_token=None, # This API uses paginationToken
                is_query_param=True # start and paginationToken are query params
            ),
            batch_limit=post_limit, # Total number of items to fetch across all pages
            parse_response_config=ParseResponseConfig(
                data_field_name="data", # The list of posts is under the 'data' key
                is_list=True # The value of 'data' field is a list
                # list_items_field_name is None as 'data' directly contains the list
            ),
            # We don't use response_model here because we need the raw dicts
            # to extract URLs/URNs for fetching comments/reactions before final parsing.
            response_model=None
        )

        # Make the API request to fetch raw post dictionaries
        # The result should be List[Dict[str, Any]] or None
        raw_posts_data: Optional[List[Dict[str, Any]]] = await self.make_api_request(api_req)

        if raw_posts_data is None: # Handles both None return and potential non-list returns from make_api_request
            logger.warning(f"No raw posts data found or error fetching posts for user {request.username}.")
            return []
        
        if not isinstance(raw_posts_data, list):
            logger.error(f"Expected list of raw posts, but got {type(raw_posts_data)}. User: {request.username}")
            return []


        # --- Post-processing: Enrich with Comments and Reactions ---
        structured_posts: List[ProfilePost] = []
        comment_limit = request.comment_limit or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request.reaction_limit or rapid_api_settings.DEFAULT_REACTION_LIMIT

        logger.info(f"Fetched {len(raw_posts_data)} raw posts for {request.username}. Now enriching...")

        # Limit the iteration just in case pagination fetched slightly more than requested batch_limit (unlikely with current logic but safe)
        # Use asyncio.gather to fetch comments and reactions concurrently for potentially faster enrichment
        enrichment_tasks = []
        post_indices_mapping = {} # Map task index back to original post_data

        for i, post_data in enumerate(raw_posts_data[:post_limit]):
             if not isinstance(post_data, dict):
                logger.warning(f"Skipping invalid raw post data item: {post_data}")
                continue
             enrichment_tasks.append(
                 self._enrich_profile_post(post_data, request, comment_limit, reaction_limit)
             )
             post_indices_mapping[i] = post_data # Store original data


        # Run enrichment tasks concurrently
        enriched_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(enriched_results):
             original_post_data = post_indices_mapping.get(i)
             if isinstance(result, Exception):
                 logger.error(f"Failed to enrich post {original_post_data.get('postUrl', 'unknown')}: {result}", exc_info=result)
             elif isinstance(result, ProfilePost):
                 structured_posts.append(result)
             elif result is None:
                 # _enrich_profile_post returns None if post_data is invalid or Pydantic fails
                 logger.warning(f"Enrichment returned None for post {original_post_data.get('postUrl', 'unknown')}.")
             else:
                  logger.error(f"Unexpected result type from enrichment: {type(result)} for post {original_post_data.get('postUrl', 'unknown')}")


        logger.info(f"Successfully enriched {len(structured_posts)} posts for {request.username}.")
        return structured_posts

    async def _enrich_profile_post(
        self,
        post_data: Dict[str, Any],
        request: PostsRequest,
        comment_limit: int,
        reaction_limit: int
    ) -> Optional[ProfilePost]:
        """
        Helper function to fetch comments/reactions for a single raw post and construct ProfilePost.

        Args:
            post_data (Dict[str, Any]): Raw dictionary for a single post.
            request (PostsRequest): Original request containing comment/reaction flags.
            comment_limit (int): Max comments to fetch.
            reaction_limit (int): Max reactions to fetch.

        Returns:
            Optional[ProfilePost]: Enriched post object or None if parsing fails.
        """
        post_url = post_data.get("postUrl")
        share_url = post_data.get("shareUrl") # Use shareUrl for reactions if available
        urn = extract_urn_from_url(post_url) if post_url else None

        comments = []
        reactions = []
        
        # Use asyncio.gather for potentially fetching comments and reactions concurrently for *this single post*
        tasks_for_post = []
        fetch_comments_flag = request.post_comments.lower() == "yes" and urn
        fetch_reactions_flag = request.post_reactions.lower() == "yes" and (share_url or post_url)

        if fetch_comments_flag:
             tasks_for_post.append(
                 self.get_profile_post_comments(
                     ProfilePostCommentsRequest(post_urn=urn),
                     comment_limit
                 )
             )
        if fetch_reactions_flag:
            reaction_url_to_use = share_url or post_url
            tasks_for_post.append(
                 self.get_post_reactions(
                     PostReactionsRequest(post_url=reaction_url_to_use),
                     reaction_limit
                 )
            )
            
        if tasks_for_post:
             results = await asyncio.gather(*tasks_for_post, return_exceptions=True)
             result_index = 0
             if fetch_comments_flag:
                  comment_result = results[result_index]
                  if isinstance(comment_result, Exception):
                      logger.error(f"Error fetching comments for post {urn}: {comment_result}", exc_info=comment_result)
                      comments = []
                  elif isinstance(comment_result, list):
                       comments = comment_result # Should be List[PostComment]
                  result_index += 1

             if fetch_reactions_flag:
                  reaction_result = results[result_index]
                  if isinstance(reaction_result, Exception):
                       reaction_url_used = share_url or post_url
                       logger.error(f"Error fetching reactions for post {reaction_url_used}: {reaction_result}", exc_info=reaction_result)
                       reactions = []
                  elif isinstance(reaction_result, list):
                        # Convert PostReaction models back to dicts for ProfilePost schema if needed
                        # Assuming get_post_reactions now returns List[PostReaction]
                        reactions = [r.model_dump() for r in reaction_result if isinstance(r, PostReaction)]
                  result_index += 1


        # Construct the final ProfilePost object
        try:
            structured_post = ProfilePost(
                text=post_data.get("text"),
                shareUrl=share_url,
                postUrl=post_url,
                totalreactions=int(post_data.get("totalReactionCount", 0)),
                totalcomments=int(post_data.get("commentsCount", 0)),
                media=post_data.get("image") or post_data.get("resharedPost", {}).get("image"),
                original_post_text=post_data.get("resharedPost", {}).get("text"),
                video=post_data.get("video") or [],
                comments=comments, # List[PostComment] from get_profile_post_comments
                reactions=reactions # List[Dict] converted from PostReaction
            )
            return structured_post
        except Exception as pydantic_error:
             logger.error(f"Failed to create ProfilePost model for post {post_url}: {pydantic_error}. Raw Data Keys: {post_data.keys()}", exc_info=True)
             return None

    async def extract_post_details_from_url(self, request: PostDetailsRequest) -> List[PostDetailsResponse]:
        """
        Extract detailed information for a LinkedIn post from its URL.
        
        Args:
            request (PostDetailsRequest): Request object containing:
                - post_url (str): LinkedIn post URL
                
        Returns:
            List[PostDetailsResponse]: List of post detail objects
            
        Example:
            >>> request = PostDetailsRequest(post_url="https://www.linkedin.com/posts/some-post-url")
            >>> details = await fetcher.extract_post_details_from_url(request)
            >>> print(f"Retrieved details for {len(details)} posts")
        """
        # Format endpoint
        endpoint = f"/get-post?url={request.post_url}"
        try:
            response = await self.api_client.make_get_request(endpoint)

            if not response.get("success", False) or "data" not in response:
                logger.error(f"API error: {response.get('message', 'Unknown error')}")
                return []

            raw_data = response["data"]
            posts: List[PostDetailsResponse] = []

            for item in raw_data:
                try:
                    posts.append(PostDetailsResponse(**item))
                except Exception as e:
                    logger.warning(f"Failed to parse post data: {e}")

            return posts

        except Exception as e:
            logger.error(f"Error in extract_post_details_from_url: {str(e)}")
            return []

    async def get_profile_post_comments(
        self,
        request: ProfilePostCommentsRequest,
        limit: Optional[int] = None
    ) -> List[PostComment]:
        """
        Get comments for a LinkedIn profile post using the generic API request handler.

        Args:
            request (ProfilePostCommentsRequest): Request object containing:
                - post_urn (str): The URN identifier of the LinkedIn post
            limit (Optional[int]): Maximum number of comments to fetch (applied *after* fetch, API may not support limit).

        Returns:
            List[PostComment]: List of parsed comment models. Returns empty list on error or no comments.
        """
        if not request.post_urn:
            logger.warning("post_urn is required for get_profile_post_comments")
            return []

        # Define the API request for fetching comments
        # Note: Endpoint structure and response format variations handled post-fetch previously.
        # Let's try defining parse_response_config more flexibly if possible, or stick to manual parse.
        # Assuming '/get-profile-posts-comments' returns {"data": {"comments": [...]}} or {"data": [...]} or just [...]
        # The generic handler might struggle with this ambiguity. Fetch raw first.
        api_req = APIRequest(
             endpoint="/get-profile-posts-comments", # Endpoint adjusted based on original code
             method="GET",
             query_params={"urn": request.post_urn},
             pagination=None, # No pagination support assumed for this endpoint
             batch_limit=None, # Fetch all available
             parse_response_config=None, # Parse manually due to response structure variations
             response_model=None # Parse manually into PostComment
        )

        # Fetch the raw response data (could be dict or list)
        raw_response_data = await self.make_api_request(api_req)

        if raw_response_data is None:
            logger.info(f"No comments data found or error fetching comments for urn {request.post_urn}.")
            return []

        # Manual parsing based on original logic to handle variations
        raw_comments: List[Dict[str, Any]] = []
        if isinstance(raw_response_data, dict):
            # Try common patterns: data.comments, then data (if list), then root comments
            data = raw_response_data.get("data")
            if isinstance(data, dict):
                raw_comments = data.get("comments", [])
            elif isinstance(data, list):
                raw_comments = data # Data itself is the list
            elif "comments" in raw_response_data: # Check root level
                 raw_comments = raw_response_data.get("comments", [])
            # Ensure it's a list
            if not isinstance(raw_comments, list):
                 logger.warning(f"Expected list of comments but found {type(raw_comments)} inside dict response for urn {request.post_urn}")
                 raw_comments = [] # Reset to empty list if not found correctly
        elif isinstance(raw_response_data, list):
             raw_comments = raw_response_data # Response is directly the list
        else:
            logger.warning(f"Unexpected response format for comments: {type(raw_response_data)}. URN: {request.post_urn}")
            return [] # Cannot parse


        # Apply limit if provided
        limit = limit or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        comments_to_parse = raw_comments[:limit]

        # Parse into PostComment models
        parsed_comments: List[PostComment] = []
        for comment_item in comments_to_parse:
            if not isinstance(comment_item, dict):
                logger.warning(f"Skipping non-dict comment item for urn {request.post_urn}: {comment_item}")
                continue
            try:
                # Use standard Pydantic parsing (assuming PostComment fields match)
                parsed_comments.append(PostComment(**comment_item))
            except Exception as e:
                logger.warning(f"Comment parse error for urn {request.post_urn}: {e}. Item keys: {comment_item.keys()}", exc_info=True)

        logger.info(f"Retrieved and parsed {len(parsed_comments)} comments for urn {request.post_urn}.")
        return parsed_comments

    async def get_user_likes_with_details(
        self, 
        request: PostsRequest
    ) -> List[LikeItem]:
        """
        Fetch posts that a LinkedIn user has liked, with detailed information.
        
        Args:
            request (PostsRequest): Request object containing:
                - username (str): LinkedIn profile username
                - post_limit (Optional[int]): Maximum number of liked posts to fetch
                - post_comments (str): "yes" or "no" to include comments for each liked post
                - post_reactions (str): "yes" or "no" to include reactions for each liked post
                - comment_limit (Optional[int]): Maximum number of comments per post
                - reaction_limit (Optional[int]): Maximum number of reactions per post
        
        Returns:
            List[LikeItem]: List of liked posts with detailed information
            
        Example:
            >>> request = PostsRequest(username="john-doe", post_limit=5, post_comments="yes", post_reactions="yes")
            >>> likes = await fetcher.get_user_likes_with_details(request)
            >>> print(f"Retrieved {len(likes)} liked posts")
        """
        post_limit = request.post_limit or rapid_api_settings.DEFAULT_POST_LIMIT
        comment_limit = request.comment_limit or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request.reaction_limit or rapid_api_settings.DEFAULT_REACTION_LIMIT

        all_likes = []
        start = 0
        pagination_token = None

        while len(all_likes) < post_limit:
            endpoint = f"{rapid_api_settings.ENDPOINTS['profile_likes']}?username={request.username}&start={start}"
            if pagination_token:
                endpoint += f"&paginationToken={pagination_token}"

            response = await self.api_client.make_get_request(endpoint)

            likes_data = response.get("data", {})
            items = likes_data.get("items", [])
            if not items:
                break

            for like in items:
                activity = LikeActivity(
                    urn=like.get("activity", {}).get("urn"),
                    username=like.get("activity", {}).get("username"),
                    postUrl=like.get("postUrl")
                )
                owner_data = like.get("owner", {}) or {}
                owner = LikeOwner(
                     urn=owner_data.get("urn"),
                    username=owner_data.get("username"),
                    firstName=owner_data.get("firstName"),
                    lastName=owner_data.get("lastName"),
                    profileUrl=owner_data.get("profileUrl"),
                    fullName=owner_data.get("fullName"),
                    headline=owner_data.get("headline"),
                    profilePicture=owner_data.get("profilePicture"),
                    linkedinUrl=owner_data.get("linkedinUrl"),
                )

                reactions = []
                if request.post_reactions == "yes":
                    reactions = await self.get_post_reactions(
                        PostReactionsRequest(post_url=like.get("postUrl", "")),
                        reaction_limit
                    )
                    reactions = [PostReaction(**r.model_dump()) for r in reactions]

                comments = []
                if request.post_comments == "yes":
                    urn = extract_urn_from_url(like.get("postUrl", ""))
                    if urn:
                        comments = await self.get_profile_post_comments(
                            ProfilePostCommentsRequest(post_urn=urn),
                            comment_limit
                        )

                like_item = LikeItem(
                    activity=activity,
                    likedAt=like.get("likedAt"),
                    text=like.get("text", ""),
                    owner=owner,
                    postUrl=like.get("postUrl", ""),
                    reactions=reactions,
                    comments=comments
                )
                all_likes.append(like_item)

            if len(all_likes) >= post_limit:
                break

            pagination_token = likes_data.get("paginationToken")
            if not pagination_token:
                break

            start += rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE

        return all_likes[:post_limit]


# async def main():
#     fetcher = LinkedinPostFetcher()
#     print(await fetcher.fetch_share_url("https://www.linkedin.com/feed/update/urn:li:activity:7320277918322946057/"))

# if __name__ == "__main__":
#     asyncio.run(main())
