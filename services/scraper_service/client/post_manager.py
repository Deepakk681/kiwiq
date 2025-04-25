"""
LinkedIn post fetcher client for RapidAPI.

This module provides a client for fetching LinkedIn posts, comments, and reactions 
using the RapidAPI LinkedIn scraper endpoint.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
import http.client
import json
from scraper_service.client.core_api_client import RapidAPIClient
from scraper_service.settings import rapid_api_settings
from scraper_service.client.utils.url_helper import extract_urn_from_url
from global_config.logger import get_logger

from scraper_service.client.schemas.posts_schema import (
    PostReactionsRequest , 
    ProfilePostCommentsRequest, 
    PostComment, 
    PostsRequest, 
    ProfilePost, 
    PostReaction , 
    PostDetailsRequest , 
    PostDetailsResponse, 
    CompanyPostCommentsRequest, 
    CompanyPostResponse , 
    CompanyPost , 
    CompanyPostAuthor , 
    CompanyPostArticle , 
    CompanyPostComment , 
    CompanyPostAuthor
)
from scraper_service.client.schemas.profile_schema import (

    ProfileRequest
)



from scraper_service.client.schemas.activity_schema import (
    LikeItem , 
    LikeActivity , 
    LikeOwner,
    GetProfileCommentResponse
)


from scraper_service.client.utils.url_helper import extract_urn_from_url
# Configure logging
logger = get_logger(__name__)

class LinkedinPostFetcher:
    """
    Client for fetching LinkedIn posts, comments, and reactions.
    
    This client provides methods for fetching LinkedIn posts for a user or company,
    as well as comments and reactions on those posts. It uses the RapidAPI
    LinkedIn scraper endpoint.
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

    async def get_company_posts(self, request: Dict[str, Any]) -> Union[List[CompanyPostResponse], Dict[str, Any]]:
        """
        Fetch posts for a LinkedIn company page.
        
        Args:
            request (Dict[str, Any]): Request object containing:
                - username (str): LinkedIn company username
                - post_limit (Optional[int]): Maximum number of posts to fetch
                - post_comments (str): "yes" or "no" to include comments
                - post_reactions (str): "yes" or "no" to include reactions
                - comment_limit (Optional[int]): Maximum number of comments per post
                - reaction_limit (Optional[int]): Maximum number of reactions per post
        
        Returns:
            Union[List[CompanyPostResponse], Dict[str, Any]]: List of company posts with details,
                or a dictionary containing an 'error' key on failure.
            
        Raises:
            ValueError: If username is not provided.
            
        Example:
            >>> request = PostsRequest(username="microsoft", post_limit=5, post_comments="yes", post_reactions="yes") # TODO: FIXME: this is not correct!
            >>> posts = await fetcher.get_company_posts(request)
            >>> print(f"Retrieved {len(posts)} posts")
        
            
        NOTE: fetch_share_url costs 1 credit per request if used to fetch shareUrl for a company post!
        """
        if not request['username']:
            logger.error("Username is required to fetch company posts.")
            return {"error": "Username is required"}

        post_limit = request['post_limit'] or rapid_api_settings.DEFAULT_POST_LIMIT
        comment_limit = request['comment_limit'] or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request['reaction_limit'] or rapid_api_settings.DEFAULT_REACTION_LIMIT
        fetch_comments_flag = request['post_comments'].lower() == "yes"
        fetch_reactions_flag = request['post_reactions'].lower() == "yes"

        logger.info(f"Fetching up to {post_limit} posts for company: {request['username']}")

        all_raw_posts = []
        start = 0
        pagination_token = None
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['company_posts']

        while len(all_raw_posts) < post_limit:
            params = {"username": request['username'], "start": start}
            if pagination_token:
                params["paginationToken"] = pagination_token

            logger.debug(f"Fetching company posts page starting at {start} for {request['username']}")
            response = await self.api_client.make_get_request(endpoint, params=params)

            if "error" in response:
                logger.error(f"Error fetching company posts for {request['username']} at start {start}: {response['error']}")
                return response

            response_data = response.get("data", response)

            posts_batch = []
            if isinstance(response_data, list):
                posts_batch = response_data
            elif isinstance(response_data, dict):
                posts_batch = response_data.get("items", [])

            if not posts_batch:
                logger.info(f"No more company posts found for {request['username']} at start {start}.")
                break

            all_raw_posts.extend(posts_batch)
            logger.debug(f"Fetched {len(posts_batch)} posts in this batch. Total raw posts: {len(all_raw_posts)}")

            if len(all_raw_posts) >= post_limit:
                logger.info(f"Company post limit ({post_limit}) reached for {request['username']}.")
                break

            pagination_token = response.get("paginationToken") or (response_data.get("paginationToken") if isinstance(response_data, dict) else None)
            if not pagination_token:
                logger.info(f"No pagination token found for company posts of {request['username']}.")
                break
            if len(posts_batch) < rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE:
                break

            start += rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE

        structured_posts: List[CompanyPostResponse] = []
        posts_to_process = all_raw_posts[:post_limit]
        logger.info(f"Processing {len(posts_to_process)} raw company posts for {request['username']}...")

        for i, raw_post in enumerate(posts_to_process):
            if not isinstance(raw_post, dict):
                logger.warning(f"Skipping non-dictionary item in company posts: {raw_post}")
                continue

            post_url = raw_post.get("postUrl")
            share_url = raw_post.get("shareUrl") or await self.fetch_share_url(post_url)
            urn = await extract_urn_from_url(post_url)
            urn = raw_post.get("urn") or urn
            reaction_target_url = share_url

            comments_list = []
            if fetch_comments_flag and urn and i < post_limit:
                logger.debug(f"Fetching comments for company post URN: {urn}")
                comments_result = await self.get_company_post_comments(
                    CompanyPostCommentsRequest(post_urn=urn),
                    limit=comment_limit
                )
                if isinstance(comments_result, dict) and "error" in comments_result:
                    logger.error(f"Failed to fetch comments for company post {urn}: {comments_result['error']}")
                elif isinstance(comments_result, list):
                    comments_list = comments_result

            reactions_list = []
            if fetch_reactions_flag and reaction_target_url and i < post_limit:
                logger.debug(f"Fetching reactions for company post URL: {reaction_target_url}")
                reactions_result = await self.get_post_reactions(
                    PostReactionsRequest(urn=urn),
                    limit=reaction_limit
                )
                if isinstance(reactions_result, dict) and "error" in reactions_result:
                    logger.error(f"Failed to fetch reactions for company post {reaction_target_url}: {reactions_result['error']}")
                elif isinstance(reactions_result, list):
                    reactions_list = reactions_result

            post = CompanyPostResponse.model_construct(
                **raw_post,
                comments=comments_list,
                reactions=reactions_list
            )
            structured_posts.append(post)

        logger.info(f"Successfully processed {len(structured_posts)} company posts for {request['username']}.")
        return structured_posts

    async def get_company_post_comments(
        self,
        request: CompanyPostCommentsRequest,
        limit: Optional[int] = None
    ) -> Union[List[CompanyPostComment], Dict[str, Any]]:
        """
        Fetch comments for a specific company LinkedIn post identified by its URN.

        Args:
            request (CompanyPostCommentsRequest): Request object containing the post_urn.
            limit (Optional[int]): Maximum number of comments to retrieve.
                                   Defaults to DEFAULT_COMMENT_LIMIT from settings.

        Returns:
            Union[List[CompanyPostComment], Dict[str, Any]]: A list of parsed CompanyPostComment
                models on success, or a dictionary with an 'error' key on failure.
        
        # NOTE: TODO: may require pagination!
        """
        if not request.post_urn:
            logger.warning("Cannot fetch company post comments without a post URN.")
            # Return empty list for consistency, as error dict implies API failure
            return []

        # Use the provided limit or fall back to the default setting
        comment_limit = limit if limit is not None else rapid_api_settings.DEFAULT_COMMENT_LIMIT
        logger.info(f"Fetching up to {comment_limit} comments for company post URN: {request.post_urn}")

        # Define the API endpoint and parameters
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['company_post_comments']
        params = {"urn": request.post_urn}

        # Make the API request using the core client
        response = await self.api_client.make_get_request(endpoint, params=params)

        # Check for errors returned by the API client's parsing logic
        if "error" in response:
            logger.error(f"Error fetching company post comments for URN {request.post_urn}: {response['error']}")
            return response # Propagate the error dictionary

        # --- Data Extraction ---
        # Gracefully handle different potential response structures for the comments list.
        response_data = response.get("data", response) # Prefer 'data' key if it exists
        raw_comments = []
        if isinstance(response_data, list):
            # Case 1: The response or response["data"] is directly the list of comments
            raw_comments = response_data
        elif isinstance(response_data, dict):
            # Case 2: Comments are nested under a key like "comments" or "items"
            raw_comments = response_data.get("comments", response_data.get("items", []))
        else:
            # Unexpected format
            logger.error(f"Unexpected response data format for company comments: {type(response_data)}. URN: {request.post_urn}")
            return {"error": "Unexpected data format received for company comments."}

        if not raw_comments:
            logger.info(f"No comments found for company post URN {request.post_urn}.")
            return []

        # --- Parsing and Limit Application ---
        comments: List[CompanyPostComment] = []
        count = 0
        for raw_comment in raw_comments:
            # Stop if the requested limit is reached
            # if count >= comment_limit:
            #     logger.info(f"Comment limit ({comment_limit}) reached for company post URN {request.post_urn}.")
            #     break

            # Ensure the item is a dictionary before attempting to parse
            if not isinstance(raw_comment, dict):
                logger.warning(f"Skipping non-dictionary item in company comments list for URN {request.post_urn}. Item: {raw_comment}")
                continue

            try:

                # Create the CompanyPostComment object using model_construct
                # Pass keyword arguments directly corresponding to model fields
                parsed_comment = CompanyPostComment.model_construct(
                    **raw_comment,
                    # name=full_name,
                    # linkedinUrl=author_data.get("linkedinUrl", ""),
                    # title=author_data.get("title", ""),
                    # text=raw_comment.get("text", "")
                )
                comments.append(parsed_comment)
                count += 1
            except Exception as e:
                # Log a warning if parsing fails for a specific comment
                logger.warning(f"Skipping invalid company comment data due to parsing error: {e}. URN: {request.post_urn}. Data: {raw_comment}")

        logger.info(f"Successfully retrieved and parsed {len(comments)} company comments for URN {request.post_urn}.")
        return comments

    async def get_post_reactions(
        self,
        request: PostReactionsRequest,
        limit: Optional[int] = None
    ) -> Union[List[PostReaction], Dict[str, Any]]:
        """
        Fetch reactions (likes, etc.) for a specific LinkedIn post URL.

        Handles pagination provided by the API.

        Args:
            request (PostReactionsRequest): Request object containing the post_url.
            limit (Optional[int]): Maximum number of reactions to retrieve.
                                   Defaults to DEFAULT_REACTION_LIMIT from settings.

        Returns:
            Union[List[PostReaction], Dict[str, Any]]: A list of parsed PostReaction models
                on success, or a dictionary with an 'error' key on failure.

        Note:
            This endpoint typically uses POST and paginates using a 'page' parameter.
            The API documentation should be consulted for specifics.
            https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api/playground/apiendpoint_05186403-0154-462c-ab21-a10657f13a58
        """
        if (not request.post_url) and (not request.urn):
            logger.warning("Cannot fetch post reactions without a post URL or URN.")
            return []

        # Use the provided limit or fall back to the default setting
        reaction_limit = limit if limit is not None else rapid_api_settings.DEFAULT_REACTION_LIMIT
        logger.info(f"Fetching up to {reaction_limit} reactions for post URL: {request.post_url}")

        all_reactions: List[PostReaction] = []
        page = 1 # Start pagination from page 1
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['post_reactions']

        # --- Pagination Loop ---
        while len(all_reactions) < reaction_limit:
            # Prepare the payload for the POST request
            payload = {"page": page}
            if request.urn:
                payload["urn"] = request.urn
            elif request.post_url:
                payload["url"] = request.post_url
            
            logger.debug(f"Fetching reactions page {page} for URL/URN: {request.post_url or request.urn}")

            # Make the API request using the core client
            response = await self.api_client.make_post_request(endpoint, payload=payload)

            # Check for errors returned by the API client's parsing logic
            if "error" in response:
                logger.error(f"Error fetching reactions for URL/URN {request.post_url or request.urn} on page {page}: {response['error']}")
                # If an error occurs during pagination, return what we have gathered so far, plus the error.
                # Alternatively, could just return the error dict: return response
                # Returning partial results might be useful, but signals an incomplete fetch.
                # For simplicity, let's return the error dict to clearly indicate failure.
                return response

            # --- Data Extraction ---
            # Reactions are typically nested under "items" within a "data" object
            response_data = response.get("data", {})
            raw_items = response_data.get("items", [])
            totalPages = response_data.get("totalPages", 1)

            if not raw_items:
                # No more reactions found, end pagination
                logger.info(f"No more reactions found for URL/URN {request.post_url or request.urn} on page {page}.")
                break

            # --- Parsing and Limit Application ---
            for item in raw_items:
                # # Stop if the requested limit is reached
                # if len(all_reactions) >= reaction_limit:
                #     logger.info(f"Reaction limit ({reaction_limit}) reached for URL {request.post_url}.")
                #     break # Break inner loop

                # Ensure the item is a dictionary before attempting to parse
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dictionary item in reactions list for URL/URN {request.post_url or request.urn}. Item: {item}")
                    continue

                try:
                    # Attempt to parse the raw reaction dictionary into the Pydantic model
                    # Already uses model_construct
                    reaction = PostReaction.model_construct(**item)
                    all_reactions.append(reaction)
                except Exception as e:
                    # Log a warning if parsing fails for a specific reaction
                    logger.warning(f"Skipping invalid reaction data due to parsing error: {e}. URL/URN: {request.post_url or request.urn}. Data: {item}")

            # Break outer loop if limit was reached in inner loop
            if len(all_reactions) >= reaction_limit:
                break
            
            if page >= totalPages:
                logger.info(f"Pagination limit ({totalPages}) reached for URL/URN {request.post_url or request.urn}.")
                break

            # Prepare for the next page
            page += 1
            # Consider adding a small delay if rate limiting is a concern
            await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_DEFAULT_DELAY_SECONDS) # Use configured delay

        logger.info(f"Successfully retrieved and parsed {len(all_reactions)} reactions for URL/URN {request.post_url or request.urn}.")
        return all_reactions


    async def get_profile_posts(
        self,
        request: Dict[str, Any]
    ) -> Union[List[ProfilePost], Dict[str, Any]]:
        """
        Fetch posts for a LinkedIn user profile, handling pagination.

        Optionally fetches comments and reactions for each post based on request flags.

        Args:
            request (Dict[str, Any]): Request dictionary containing:
                - username (str): LinkedIn profile username.
                - post_limit (Optional[int]): Max posts. Defaults to DEFAULT_POST_LIMIT.
                - post_comments (str): "yes"|"no". Fetch comments?
                - post_reactions (str): "yes"|"no". Fetch reactions?
                - comment_limit (Optional[int]): Max comments per post. Defaults to DEFAULT_COMMENT_LIMIT.
                - reaction_limit (Optional[int]): Max reactions per post. Defaults to DEFAULT_REACTION_LIMIT.

        Returns:
            Union[List[ProfilePost], Dict[str, Any]]: A list of parsed ProfilePost models
                on success, or a dictionary with an 'error' key on failure.
        """
        if not request.get('username'):
            logger.error("Username is required to fetch profile posts.")
            return {"error": "Username is required"}

        # Extract parameters with defaults
        username = request['username']
        post_limit = request.get('post_limit') or rapid_api_settings.DEFAULT_POST_LIMIT
        comment_limit = request.get('comment_limit') or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request.get('reaction_limit') or rapid_api_settings.DEFAULT_REACTION_LIMIT
        fetch_comments_flag = request.get('post_comments', 'no').lower() == "yes"
        fetch_reactions_flag = request.get('post_reactions', 'no').lower() == "yes"

        logger.info(f"Fetching up to {post_limit} posts for profile: {username}")

        all_raw_posts = []
        start = 0
        pagination_token = None
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['profile_posts']

        # --- Pagination Loop for Posts ---
        while len(all_raw_posts) < post_limit:
            # Prepare parameters for the GET request
            params = {"username": username, "start": start}
            if pagination_token:
                params["paginationToken"] = pagination_token

            logger.debug(f"Fetching profile posts page starting at {start} for {username}")
            response = await self.api_client.make_get_request(endpoint, params=params)

            # Check for errors
            if "error" in response:
                logger.error(f"Error fetching profile posts for {username} at start {start}: {response['error']}")
                return response # Return error dict

            # --- Data Extraction ---
            response_data = response.get("data", response)
            posts_batch = []
            if isinstance(response_data, list):
                posts_batch = response_data
            elif isinstance(response_data, dict):
                 # Adjust if the API uses a different key like "items"
                posts_batch = response_data.get("posts", response_data.get("items", []))

            if not posts_batch:
                logger.info(f"No more profile posts found for {username} at start {start}.")
                break

            all_raw_posts.extend(posts_batch)
            logger.debug(f"Fetched {len(posts_batch)} posts in this batch. Total raw posts: {len(all_raw_posts)}")

            # Check if limit reached
            if len(all_raw_posts) >= post_limit:
                logger.info(f"Profile post limit ({post_limit}) reached for {username}.")
                break # Exit loop if limit reached

            # --- Pagination Token Handling ---
            # Look for token in top level or within 'data' if it's a dict
            pagination_token = response.get("paginationToken")
            if not pagination_token and isinstance(response_data, dict):
                pagination_token = response_data.get("paginationToken")

            if not pagination_token:
                logger.info(f"No pagination token found for profile posts of {username}.")
                break # Exit loop if no token

            # Optional: Check if the number of items fetched suggests the last page
            if len(posts_batch) < rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE:
                logger.info(f"Fetched fewer posts ({len(posts_batch)}) than batch size, assuming end of results for {username}.")
                break # Exit loop if likely last page

            # Increment start for the next batch
            start += rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE # Assuming batch size matches 'start' increment logic

            # Optional delay between page fetches
            await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_DEFAULT_DELAY_SECONDS)

        # --- Processing Fetched Posts ---
        structured_posts: List[ProfilePost] = []
        posts_to_process = all_raw_posts # Ensure we don't exceed the limit; otherwise exess comments / reactions requests will also be triggered!
        logger.info(f"Processing {len(posts_to_process)} raw profile posts for {username}...")

        for i, raw_post in enumerate(posts_to_process):
            if not isinstance(raw_post, dict):
                logger.warning(f"Skipping non-dictionary item in profile posts: {raw_post}")
                continue

            post_url = raw_post.get("postUrl")
            share_url = raw_post.get("shareUrl") # Profile posts often have shareUrl directly
            urn = await extract_urn_from_url(post_url) if post_url else None
            urn = raw_post.get("urn", urn)
            # Use share_url for reactions if available, fallback to post_url (needs API confirmation)
            reaction_target_url = share_url

            # --- Fetch Comments (Conditional) ---
            comments_list: List[PostComment] = []
            if fetch_comments_flag and urn and i < post_limit:
                logger.debug(f"Fetching comments for profile post URN: {urn}")
                comments_result = await self.get_profile_post_comments(
                    ProfilePostCommentsRequest(post_urn=urn),
                    limit=comment_limit
                )
                # Check if the result is an error dict or the list of comments
                if isinstance(comments_result, dict) and "error" in comments_result:
                    logger.error(f"Failed to fetch comments for profile post {urn}: {comments_result['error']}")
                elif isinstance(comments_result, list):
                    comments_list = comments_result
                # Add delay after sub-call? Depends on rate limits.
                # await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_DEFAULT_DELAY_SECONDS)


            # --- Fetch Reactions (Conditional) ---
            reactions_list: List[PostReaction] = []
            if fetch_reactions_flag and reaction_target_url and i < post_limit:
                logger.debug(f"Fetching reactions for profile post URL: {reaction_target_url}")
                reactions_result = await self.get_post_reactions(
                    PostReactionsRequest(urn=urn),
                    limit=reaction_limit
                )
                 # Check if the result is an error dict or the list of reactions
                if isinstance(reactions_result, dict) and "error" in reactions_result:
                    logger.error(f"Failed to fetch reactions for profile post {reaction_target_url}: {reactions_result['error']}")
                elif isinstance(reactions_result, list):
                    # Convert PostReaction models back to dicts if the ProfilePost schema expects dicts
                    # If ProfilePost expects List[PostReaction], just assign: reactions_list = reactions_result
                    # reactions_list = [r.model_dump() for r in reactions_result]
                    reactions_list = reactions_result # Assuming ProfilePost expects List[PostReaction]

                # Add delay after sub-call?
                # await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_DEFAULT_DELAY_SECONDS)

            # --- Structure Final Post Object ---
            try:
                # Already uses model_construct, which is good.
                structured_post = ProfilePost.model_construct(
                    **raw_post,
                    comments=comments_list, # Assign the fetched list of models
                    reactions=reactions_list # Assign the fetched list of models
                )
                structured_posts.append(structured_post)
            except Exception as e:
                 logger.warning(f"Skipping profile post due to parsing error: {e}. Post data: {raw_post}")


        logger.info(f"Successfully processed {len(structured_posts)} profile posts for {username}.")
        return structured_posts

    async def get_profile_post_comments(
        self,
        request: ProfilePostCommentsRequest,
        limit: Optional[int] = None
    ) -> Union[List[PostComment], Dict[str, Any]]:
        """
        Get comments for a specific LinkedIn profile post identified by its URN, handling pagination.

        Args:
            request (ProfilePostCommentsRequest): Request object containing the post_urn.
            limit (Optional[int]): Maximum number of comments to retrieve across all pages.
                                   Defaults to DEFAULT_COMMENT_LIMIT.

        Returns:
            Union[List[PostComment], Dict[str, Any]]: A list of parsed PostComment models
                up to the specified limit, or a dictionary with an 'error' key on failure.
        
        # NOTE: This is a paginated API, so we need to handle pagination.
        https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api/playground/apiendpoint_32b2d880-fbcc-4494-a7c5-cf754d20dbb4
        """
        if not request.post_urn:
            logger.warning("Cannot fetch profile post comments without a post URN.")
            return []

        # Set the overall limit for comments across all pages
        comment_limit = limit if limit is not None else rapid_api_settings.DEFAULT_COMMENT_LIMIT
        logger.info(f"Fetching up to {comment_limit} comments for profile post URN: {request.post_urn}")

        # Define endpoint
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['profile_post_comments'] # Ensure this exists

        all_comments: List[PostComment] = []
        pagination_token = None
        page_count = 1 # It starts with Page #1!

        # --- Pagination Loop ---
        while len(all_comments) < comment_limit:
            # Prepare parameters for the GET request, including pagination token if available
            params = {"urn": request.post_urn}
            params["page"] = page_count
            if pagination_token:
                params["paginationToken"] = pagination_token

            logger.debug(f"Fetching profile comments page {page_count} for URN {request.post_urn}, token: {pagination_token}")
            # Make the API request
            response = await self.api_client.make_get_request(endpoint, params=params)

            # Check for errors from the API client
            if "error" in response:
                logger.error(f"Error fetching profile post comments for URN {request.post_urn} on page {page_count}: {response['error']}")
                # Return error, potentially with partially gathered comments if needed, but error dict is clearer
                return response

            # --- Data Extraction for Current Page ---
            # The response schema indicates comments are in response["data"] (which is an array)
            response_data = response.get("data", []) # Default to empty list if 'data' is missing

            # Handle case where 'data' key exists but is not a list
            if not isinstance(response_data, list):
                logger.error(f"Unexpected response data format for profile comments: expected list under 'data', got {type(response_data)}. URN: {request.post_urn}, Page: {page_count}")
                # Consider returning error or stopping pagination
                return {"error": "Unexpected data format received for profile comments."}

            raw_comments_batch = response_data

            if not raw_comments_batch:
                logger.info(f"No more comments found for profile post URN {request.post_urn} on page {page_count}.")
                break # Exit loop if no comments in this batch

            # --- Parsing and Limit Application for Current Page ---
            for raw_comment in raw_comments_batch:
                #  # Stop processing immediately if the overall limit is reached
                # if len(all_comments) >= comment_limit:
                #     logger.info(f"Overall comment limit ({comment_limit}) reached for profile post URN {request.post_urn}.")
                #     break # Break inner loop

                if not isinstance(raw_comment, dict):
                    logger.warning(f"Skipping non-dictionary item in profile comments list for URN {request.post_urn}, Page: {page_count}. Item: {raw_comment}")
                    continue

                try:
                    # Parse into Pydantic model using model_construct
                    parsed_comment = PostComment.model_construct(**raw_comment)
                    all_comments.append(parsed_comment)
                except Exception as e:
                    logger.warning(f"Skipping invalid profile comment data due to parsing error: {e}. URN: {request.post_urn}, Page: {page_count}. Data: {raw_comment}")

            # Break outer loop if limit was reached in inner loop
            if len(all_comments) >= comment_limit:
                break

            # --- Pagination Token Handling ---
            pagination_token = response.get("paginationToken")
            total_pages = response.get("totalPage") # Optional: Use totalPage for logging or early exit

            if not pagination_token:
                logger.info(f"No further pagination token found for profile post comments (URN: {request.post_urn}). Fetched {page_count} pages.")
                break # Exit loop if no more tokens

            # Optional: Check against totalPages if provided
            if total_pages is not None and page_count >= total_pages:
                 logger.info(f"Reached total pages ({total_pages}) indicated by API for profile post comments (URN: {request.post_urn}).")
                 break

            page_count += 1

            # Optional delay between page fetches
            await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_DEFAULT_DELAY_SECONDS)


        logger.info(f"Successfully retrieved and parsed {len(all_comments)} profile comments across {page_count} pages for URN {request.post_urn}.")
        # Return only up to the limit requested
        return all_comments


    async def get_user_likes_with_details(
        self,
        request: Dict[str, Any] # Changed from PostsRequest to Dict to match usage
    ) -> Union[List[LikeItem], Dict[str, Any]]:
        """
        Fetch posts that a LinkedIn user has liked, with details, handling pagination.

        Optionally fetches comments and reactions for each liked post.

        Args:
            request (Dict[str, Any]): Request dictionary containing:
                - username (str): LinkedIn profile username.
                - post_limit (Optional[int]): Max liked posts. Defaults to SCRAPER_SERVICE_BATCH_SIZE_FOR_REACTIONS.
                - post_comments (str): "yes"|"no". Fetch comments for liked posts?
                - post_reactions (str): "yes"|"no". Fetch reactions for liked posts?
                - comment_limit (Optional[int]): Max comments per liked post. Defaults to DEFAULT_COMMENT_LIMIT.
                - reaction_limit (Optional[int]): Max reactions per liked post. Defaults to DEFAULT_REACTION_LIMIT.

        Returns:
            Union[List[LikeItem], Dict[str, Any]]: A list of parsed LikeItem models
                on success, or a dictionary with an 'error' key on failure.
        """
        if not request.get('username'):
            logger.error("Username is required to fetch user likes.")
            return {"error": "Username is required"}

        # Extract parameters with defaults
        username = request['username']
        # Default limit for likes might differ, using the specific setting if available
        post_limit = request.get('post_limit') or rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE_FOR_ACTIVITY_REACTIONS
        comment_limit = request.get('comment_limit') or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request.get('reaction_limit') or rapid_api_settings.DEFAULT_REACTION_LIMIT
        fetch_comments_flag = request.get('post_comments', 'no').lower() == "yes"
        fetch_reactions_flag = request.get('post_reactions', 'no').lower() == "yes"

        logger.info(f"Fetching up to {post_limit} liked posts for profile: {username}")

        all_likes: List[LikeItem] = []
        start = 0
        pagination_token = None
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['profile_likes'] # Ensure this exists

        # --- Pagination Loop for Likes ---
        while len(all_likes) < post_limit:
            params = {"username": username, "start": start}
            if pagination_token:
                params["paginationToken"] = pagination_token

            logger.debug(f"Fetching user likes page starting at {start} for {username}")
            response = await self.api_client.make_get_request(endpoint, params=params)

            # Check for errors
            if "error" in response:
                logger.error(f"Error fetching user likes for {username} at start {start}: {response['error']}")
                return response

            # --- Data Extraction ---
            # Likes data is often nested under 'items' within 'data'
            response_data = response.get("data", {})
            items_batch = response_data.get("items", [])

            if not items_batch:
                logger.info(f"No more user likes found for {username} at start {start}.")
                break

            # --- Process Batch of Liked Items ---
            for i, raw_like in enumerate(items_batch):
                # # Stop if limit reached
                # if len(all_likes) >= post_limit:
                #     logger.info(f"User likes limit ({post_limit}) reached for {username}.")
                #     break # Break inner loop

                if not isinstance(raw_like, dict):
                     logger.warning(f"Skipping non-dictionary item in user likes list for {username}. Item: {raw_like}")
                     continue

                # --- Extract Core Like Info ---
                post_url = raw_like.get("postUrl")
                urn = await extract_urn_from_url(post_url) if post_url else None
                urn = raw_like.get("urn", urn)
                # Use postUrl for reactions/comments as shareUrl might not be present for likes
                reaction_target_url = post_url
                comment_target_urn = urn

                # --- Fetch Reactions (Conditional) ---
                reactions_list: List[PostReaction] = []
                if fetch_reactions_flag and reaction_target_url and i < post_limit:
                    logger.debug(f"Fetching reactions for liked post URL: {reaction_target_url}")
                    reactions_result = await self.get_post_reactions(
                        PostReactionsRequest(urn=urn),
                        limit=reaction_limit
                    )
                    if isinstance(reactions_result, dict) and "error" in reactions_result:
                        logger.error(f"Failed to fetch reactions for liked post {reaction_target_url}: {reactions_result['error']}")
                    elif isinstance(reactions_result, list):
                        reactions_list = reactions_result

                # --- Fetch Comments (Conditional) ---
                comments_list: List[PostComment] = []
                if fetch_comments_flag and comment_target_urn and i < post_limit:
                    logger.debug(f"Fetching comments for liked post URN: {comment_target_urn}")
                    comments_result = await self.get_profile_post_comments(
                        ProfilePostCommentsRequest(post_urn=comment_target_urn),
                        limit=comment_limit
                    )
                    if isinstance(comments_result, dict) and "error" in comments_result:
                        logger.error(f"Failed to fetch comments for liked post {comment_target_urn}: {comments_result['error']}")
                    elif isinstance(comments_result, list):
                        comments_list = comments_result

                # --- Structure Final LikeItem Object ---
                try:
                    # Use model_construct for sub-models as well
                    activity = LikeActivity.model_construct(
                        urn=urn, # URN of the like activity itself?
                        activityType=raw_like.get("action") # e.g., 'like'
                    )

                    owner_data = raw_like.get("author", {}) # Author of the *original post*
                    # Use model_construct
                    owner = LikeOwner.model_construct(
                        username=owner_data.get("username"),
                        firstName=owner_data.get("firstName"),
                        lastName=owner_data.get("lastName"),
                        profileUrl=owner_data.get("url"),
                        headline=owner_data.get("headline"),
                        postUrl=post_url, # Include postUrl within owner? Seems redundant if top-level
                    )

                    # Use model_construct for the main item
                    like_item = LikeItem.model_construct(
                        activity=activity,
                        reactions=reactions_list, # Reactions *on* the original post
                        comments=comments_list,   # Comments *on* the original post
                        **raw_like
                        # # Aggregate counts from the like item itself
                        # totalReactionCount=raw_like.get("totalReactionCount", 0),
                        # likeCount=raw_like.get("likeCount", 0),
                        # appreciationCount=raw_like.get("appreciationCount", 0),
                        # empathyCount=raw_like.get("empathyCount", 0),
                        # commentsCount=raw_like.get("commentsCount", 0)
                    )
                    all_likes.append(like_item)
                except Exception as e:
                     logger.warning(f"Skipping liked item due to parsing error: {e}. Like data: {raw_like}")

            # Break outer loop if limit was reached in inner loop
            if len(all_likes) >= post_limit:
                break

            # --- Pagination Token Handling ---
            pagination_token = response_data.get("paginationToken")
            if not pagination_token:
                logger.info(f"No pagination token found for user likes of {username}.")
                break

            # Optional: Check batch size for potential end
            if len(items_batch) < rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE_FOR_ACTIVITY_REACTIONS:
                logger.info(f"Fetched fewer liked items ({len(items_batch)}) than batch size, assuming end of results for {username}.")
                break

            # Increment start and delay
            start += rapid_api_settings.SCRAPER_SERVICE_BATCH_SIZE_FOR_ACTIVITY_REACTIONS # Use the specific batch size
            await asyncio.sleep(rapid_api_settings.SCRAPER_SERVICE_DEFAULT_DELAY_SECONDS)

        logger.info(f"Successfully processed {len(all_likes)} liked items for {username}.")
        return all_likes


    async def get_user_comments_with_details(
        self,
        request: Dict[str, Any] # Changed from ProfileRequest to Dict
    ) -> Union[List[GetProfileCommentResponse], Dict[str, Any]]:
        """
        Fetch posts that a LinkedIn user has commented on, with details, handling pagination.

        Enriches each post with comments and reactions based on request flags.

        Args:
            request (Dict[str, Any]): Request dictionary containing:
                - username (str): LinkedIn profile username.
                - post_limit (Optional[int]): Max posts commented on. Defaults to DEFAULT_POST_LIMIT.
                - post_comments (str): "yes"|"no". Fetch *other* comments on these posts?
                - post_reactions (str): "yes"|"no". Fetch reactions on these posts?
                - comment_limit (Optional[int]): Max comments per post. Defaults to DEFAULT_COMMENT_LIMIT.
                - reaction_limit (Optional[int]): Max reactions per post. Defaults to DEFAULT_REACTION_LIMIT.

        Returns:
            Union[List[GetProfileCommentResponse], Dict[str, Any]]: A list of posts the user
                commented on, enriched with details and potentially other comments/reactions,
                or a dictionary with an 'error' key on failure.
        """
        if not request.get('username'):
            logger.error("Username is required to fetch user comments.")
            return {"error": "Username is required"}

        # Extract parameters
        username = request['username']
        post_limit = request.get('post_limit') or rapid_api_settings.DEFAULT_POST_LIMIT
        comment_limit = request.get('comment_limit') or rapid_api_settings.DEFAULT_COMMENT_LIMIT
        reaction_limit = request.get('reaction_limit') or rapid_api_settings.DEFAULT_REACTION_LIMIT
        fetch_comments_flag = request.get('post_comments', 'no').lower() == "yes"
        fetch_reactions_flag = request.get('post_reactions', 'no').lower() == "yes"

        logger.info(f"Fetching up to {post_limit} posts commented on by profile: {username}")

        # --- Data Fetching ---
        # Assuming the endpoint returns a list of posts the user commented on.
        # This might need pagination similar to likes/posts if the API supports it.
        # For now, assume a single request gets all or a non-paginated set.
        endpoint = rapid_api_settings.RAPID_API_ENDPOINTS['profile_comments_made'] # Ensure this exists
        params = {"username": username} # Add start/token if pagination applies

        # Make the API request
        response = await self.api_client.make_get_request(endpoint, params=params)

        # Check for errors
        if "error" in response:
            logger.error(f"Error fetching posts commented on by {username}: {response['error']}")
            return response

        # --- Data Extraction ---
        response_data = response.get("data", response)
        raw_commented_posts = []
        if isinstance(response_data, list):
            raw_commented_posts = response_data
        elif isinstance(response_data, dict):
            # Check common keys like 'items', 'posts', 'comments'
            raw_commented_posts = response_data.get("items", response_data.get("posts", []))
        else:
             logger.error(f"Unexpected response data format for user commented posts: {type(response_data)}. User: {username}")
             return {"error": "Unexpected data format received for user commented posts."}

        if (not raw_commented_posts) or (not isinstance(raw_commented_posts, list)):
             logger.info(f"No posts found commented on by user {username}.")
             return []

        # --- Processing Fetched Posts ---
        structured_results: List[GetProfileCommentResponse] = []
        # Apply limit *before* fetching details for each post
        posts_to_process = raw_commented_posts
        logger.info(f"Processing {len(posts_to_process)} raw commented posts for {username}...")

        for i, raw_post_info in enumerate(posts_to_process):
            if not isinstance(raw_post_info, dict):
                logger.warning(f"Skipping non-dictionary item in commented posts list for {username}. Item: {raw_post_info}")
                continue

            post_url = raw_post_info.get("postUrl")
            share_url = raw_post_info.get("shareUrl") # May or may not exist here
            urn = await extract_urn_from_url(post_url) if post_url else None
            urn = raw_post_info.get("urn", urn)
            reaction_target_url = share_url or post_url # Best guess for reactions
            comment_target_urn = urn

             # --- Fetch Other Comments (Conditional) ---
            other_comments_list: List[PostComment] = []
            if fetch_comments_flag and comment_target_urn and i < post_limit:
                logger.debug(f"Fetching *other* comments for commented post URN: {comment_target_urn}")
                comments_result = await self.get_profile_post_comments(
                    ProfilePostCommentsRequest(post_urn=comment_target_urn),
                    limit=comment_limit
                )
                if isinstance(comments_result, dict) and "error" in comments_result:
                    logger.error(f"Failed to fetch comments for commented post {comment_target_urn}: {comments_result['error']}")
                elif isinstance(comments_result, list):
                    other_comments_list = comments_result

            # --- Fetch Reactions (Conditional) ---
            reactions_list: List[PostReaction] = []
            if fetch_reactions_flag and reaction_target_url and i < post_limit:
                logger.debug(f"Fetching reactions for commented post URL: {reaction_target_url}")
                reactions_result = await self.get_post_reactions(
                    PostReactionsRequest(urn=urn),
                    limit=reaction_limit
                )
                if isinstance(reactions_result, dict) and "error" in reactions_result:
                    logger.error(f"Failed to fetch reactions for commented post {reaction_target_url}: {reactions_result['error']}")
                elif isinstance(reactions_result, list):
                    reactions_list = reactions_result

            # --- Structure Final Response Object ---
            # The GetProfileCommentResponse schema needs to accommodate the original post info
            # plus the lists of other comments and reactions.
            try:
                # Already uses model_construct, which is good.
                response_item = GetProfileCommentResponse.model_construct(
                    **raw_post_info, # Pass all original fields
                    comments=other_comments_list, # Add the list of *other* comments
                    reactions=reactions_list   # Add the list of reactions
                )
                structured_results.append(response_item)
            except Exception as e:
                 logger.warning(f"Skipping commented post due to parsing error: {e}. Post data: {raw_post_info}")

        logger.info(f"Successfully processed {len(structured_results)} posts commented on by {username}.")
        return structured_results
