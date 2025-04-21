"""
Comprehensive tests for all LinkedIn API client modules.

This module provides a complete test suite for all RapidAPI LinkedIn client classes and methods.
Tests include both basic functionality tests and real API interaction tests with proper error handling.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List, Optional, Union
import time

from scraper_service.client.core_api_client import RapidAPIClient 
from scraper_service.settings import rapid_api_settings
from scraper_service.client.schemas import ProfileRequest, CompanyRequest, ProfileResponse, CompanyResponse , ProfilePost , ProfilePostsRequest , CompanyPostsRequest, LikeItem , GetProfileCommentResponse
from global_config.logger import get_logger
logger = get_logger(__name__)

# Get API credentials and test data from settings
API_KEY = rapid_api_settings.RAPID_API_KEY
API_HOST = rapid_api_settings.RAPID_API_HOST

# Test data from settings
TEST_PROFILE_USERNAME = rapid_api_settings.TEST_PROFILE_USERNAME
TEST_PROFILE_URL = rapid_api_settings.TEST_PROFILE_URL
TEST_POST_PROFILE_USERNAME = rapid_api_settings.TEST_POST_PROFILE_USERNAME
TEST_POST_COMPANY_USERNAME = rapid_api_settings.TEST_POST_COMPANY_USERNAME
TEST_COMPANY_USERNAME = rapid_api_settings.TEST_COMPANY_USERNAME
TEST_COMPANY_URL = rapid_api_settings.TEST_COMPANY_URL


# Retry configuration from settings
MAX_RETRIES = rapid_api_settings.MAX_RETRIES
RETRY_DELAY = rapid_api_settings.RETRY_DELAY



async def test_core_client():
    """Test core RapidAPIClient functionality."""
    print("\n--- Testing RapidAPIClient Core Functionality ---")
    
    # Create client instance
    client = RapidAPIClient(api_key=API_KEY, base_url=API_HOST)
    
    # Test validation methods
    print("Testing API key validation...")
    is_valid = client.validate_api_key()
    print(f"API key validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    print("\nTesting direct get profile data...")
    request = ProfileRequest(username=TEST_PROFILE_USERNAME)
    response = await client.get_profile_data(request)
    
    if isinstance(response, ProfileResponse):
        try:
            profile_response = ProfileResponse.model_validate(response)
            print(f"✓ Successfully parsed profile response with Pydantic model")
            print(f"Profile details: {profile_response.firstName} {profile_response.lastName}, {profile_response.headline}")
        except Exception as e:
            print(f"✗ Failed to parse profile response: {str(e)}")
            print(f"Response keys: {list(response.keys())[:10]}")
      

    # print("\nTesting get profile comments data...")
    # request = ProfileRequest(username=TEST_PROFILE_USERNAME)
    # raw_response = await client.get_profile_post_comments(request)
    # response = GetProfileCommentResponse(**raw_response)
    # print("Profile comments data")
    # print(response, "response")
    # print(response.highlightedComments, "highlightedComments")
    # print(response.highlightedCommentsActivityCounts, "highlightedCommentsActivityCounts")
    # print(response.text, "text")
    # print(response.totalReactionCount, "totalReactionCount")
    # print(response.likeCount, "likeCount")
    # print(response.appreciationCount, "appreciationCount")
    
        
    print("\nTesting get company data...")
    request = CompanyRequest(username=TEST_COMPANY_USERNAME)
    response = await client.get_company_data(request)
    
    if isinstance(response, CompanyResponse):
        try:
            # Try to parse the response using our updated model
            company_response = CompanyResponse.model_validate(response)
            print(f"✓ Successfully parsed company response with Pydantic model")
            print(f"Company details: {company_response.data.name}, {company_response.data.tagline}")
            print(f"Followers: {company_response.data.followerCount}")

        except Exception as e:
            print(f"✗ Failed to parse company response: {str(e)}")
    
    return client




async def test_posts_client():
    """Test posts-related functionality."""
    # print("\n--- Testing Posts Client for A User profile Functionality ---")

    # Initialize post fetcher client
    # post_fetcher = LinkedinPostFetcher(api_key=API_KEY, base_url=API_HOST)

    # === 1. Test get_profile_posts ===
    # request_profile = ProfilePostsRequest(
    #     username=TEST_POST_PROFILE_USERNAME,
    #     post_comments="yes",
    #     post_reactions="yes",
    # )

    # print("\nTesting get_profile_posts method...")
    # try:
    #     posts_response = await post_fetcher.get_profile_posts(request_profile)

    #     if isinstance(posts_response, list) and posts_response:
    #         print(f"✓ Retrieved {len(posts_response)} profile posts")
    #         first_post: ProfilePost = posts_response[0]

    #         print("First profile post details:")
    #         print(f"Text: {first_post.text[:100]}..." if first_post.text else "No text found")
    #         print(f"Reactions: {first_post.totalreactions}")
    #         print(f"Comments: {first_post.totalcomments}")
    #         print(f"Comments: {first_post.comments}")
    #         print(f"Reactions: {first_post.reactions}")
    #         print(f"Post URL: {first_post.postUrl}")
    #     else:
    #         print("✗ No profile posts returned or empty list")
    # except Exception as e:
    #     print(f"✗ Error while fetching profile posts: {str(e)}")

    # === 2. Test get_company_posts ===

    # print("\n--- Testing Posts Client for A Company Page Functionality ---")
    # request_company = CompanyPostsRequest(
    #     username=TEST_POST_COMPANY_USERNAME,
    #     post_comments="yes",
    #     post_reactions="yes",
    # )

    # print("\nTesting get_company_posts method...")
    # try:
    #     company_posts = await post_fetcher.get_company_posts(request_company)

    #     if isinstance(company_posts, list) and company_posts:
    #         print(f"✓ Retrieved {len(company_posts)} company posts")
    #         first_company_post = company_posts[0]

    #         print("First company post details:")
    #         print(f"Text: {first_company_post.text[:100]}..." if first_company_post.text else "No text found")
    #         print(f"Reactions: {first_company_post.totalReactionCount}")
    #         print(f"Comments: {first_company_post.commentsCount}")
    #         print(f"Comments: {first_company_post.comments}")
    #         print(f"Reactions: {first_company_post.reactions}")
    #         print(f"Post URL: {first_company_post.postUrl}")
    #     else:
    #         print("✗ No company posts returned or empty list")
    # except Exception as e:
    #     print(f"✗ Error while fetching company posts: {str(e)}")
    # === 3. Test get_user_post_likes ===
    # post_fetcher = LinkedinPostFetcher(api_key=API_KEY, base_url=API_HOST)
    # likes_request  = ProfilePostsRequest(
    #     username=TEST_POST_PROFILE_USERNAME,
    #     post_comments="no",
    #     post_reactions="no",
    # )
    # likes_response = await post_fetcher.get_user_likes_with_details(likes_request)

    # if isinstance(likes_response, list):
    #     print(f"✓ Retrieved {len(likes_response)} likes")
    #     if likes_response:
    #         first_like: LikeItem = likes_response[0]
    #         print(f"First Like Post URL: {first_like.postUrl}")
    #         print(f"First Like Owner: {first_like.owner.firstName} {first_like.owner.lastName}")
    #     else:
    #         print("✗ No likes returned.")
    # else:
    #     print("✗ Response is not a list.")
    
    


# async def test_activity_client(client: RapidAPIClient, post_urn: str):
#     """Test activity-related functionality (comments and reactions)."""
#     print("\n--- Testing Activity Client Functionality ---")
    
#     # Create an activity fetcher
#     activity_fetcher = LinkedInActivityFetcher(api_key=API_KEY, base_url=API_HOST)
    
#     # Test comments functionality
#     print("\nTesting comments functionality...")
    
#     # Try to get comments using different endpoints
#     comments_response = await try_endpoints(
#         client,
#         COMMENTS_ENDPOINTS,
#         {"urn": post_urn, "url": TEST_POST_URL}
#     )
    
#     if isinstance(comments_response, dict) and "error" not in comments_response:
#         # Extract comments data
#         comments = []
#         if "data" in comments_response and "comments" in comments_response["data"]:
#             comments = comments_response["data"]["comments"]
#         elif "comments" in comments_response:
#             comments = comments_response["comments"]
            
#         print(f"Retrieved {len(comments)} comments")
        
#         if len(comments) > 0:
#             first_comment = comments[0]
#             print("First comment details:")
#             if "text" in first_comment:
#                 print(f"Text: {first_comment.get('text')[:100]}...")
#             if "actor" in first_comment and "name" in first_comment["actor"]:
#                 print(f"Author: {first_comment['actor'].get('name')}")
#     else:
#         print(f"Could not retrieve comments: {comments_response}")
    
#     # Test reactions functionality
#     print("\nTesting reactions functionality...")
    
#     # Try to get reactions using different endpoints
#     reactions_response = await try_endpoints(
#         client,
#         REACTIONS_ENDPOINTS,
#         {"urn": post_urn, "url": TEST_POST_URL}
#     )
    
#     if isinstance(reactions_response, dict) and "error" not in reactions_response:
#         # Extract reactions data
#         reactions = []
#         if "data" in reactions_response and "items" in reactions_response["data"]:
#             reactions = reactions_response["data"]["items"]
#         elif "reactions" in reactions_response:
#             reactions = reactions_response["reactions"]
            
#         print(f"Retrieved {len(reactions)} reactions")
        
#         if len(reactions) > 0:
#             first_reaction = reactions[0]
#             print("First reaction details:")
#             if "fullName" in first_reaction:
#                 print(f"Author: {first_reaction.get('fullName')}")
#             if "reactionType" in first_reaction:
#                 print(f"Type: {first_reaction.get('reactionType')}")
#     else:
#         print(f"Could not retrieve reactions: {reactions_response}")


# async def test_post_fetcher():
#     """Test LinkedinPostFetcher class."""
#     print("\n--- Testing LinkedinPostFetcher ---")
    
#     post_fetcher = LinkedinPostFetcher(api_key=API_KEY, base_url=API_HOST)
    
#     # Test get_profile_posts method
#     print("\nTesting get_profile_posts method...")
#     # posts = await post_fetcher.get_profile_posts(TEST_PROFILE_USERNAME, 2)
#     posts = await post_fetcher.get_reactions(TEST_POST_URL, 1)
#     print(posts, "posts")
    
#     if isinstance(posts, list):
#         print(f"Retrieved {len(posts)} posts")
#         if len(posts) > 0:
#             for i, post in enumerate(posts[:2]):
#                 print(f"Post {i+1}:")
#                 print(f"Content: {post.content[:100]}..." if hasattr(post, "content") else "No content")
#     else:
#         print("Could not retrieve posts")
    
#     # Test get_post_by_url method
#     print("\nTesting get_post_by_url method...")
#     post = await post_fetcher.get_post_by_url(TEST_POST_URL)
    
#     if post and not hasattr(post, "error"):
#         print("Post details:")
#         print(f"Content: {post.content[:100]}..." if hasattr(post, "content") else "No content")
#         print(f"Stats: {post.stats}" if hasattr(post, "stats") else "No stats")
#     else:
#         print("Could not retrieve post by URL")


# async def test_company_post_fetcher():
#     """Test CompanyPostFetcher class."""
#     print("\n--- Testing CompanyPostFetcher ---")
    
#     company_post_fetcher = CompanyPostFetcher(api_key=API_KEY, base_url=API_HOST)
    
#     # Test get_company_posts method
#     print("\nTesting get_company_posts method...")
#     posts = await company_post_fetcher.get_company_posts(TEST_COMPANY_USERNAME, 2)
    
#     if isinstance(posts, list):
#         print(f"Retrieved {len(posts)} company posts")
#         if len(posts) > 0:
#             for i, post in enumerate(posts[:2]):
#                 print(f"Company Post {i+1}:")
#                 print(f"Content: {post.content[:100]}..." if hasattr(post, "content") else "No content")
#     else:
#         print("Could not retrieve company posts")
    
#     # Test get_company_profile method
#     print("\nTesting get_company_profile method...")
#     company = await company_post_fetcher.get_company_profile(TEST_COMPANY_USERNAME)
    
#     if company and not hasattr(company, "error"):
#         print("Company details:")
#         print(f"Name: {company.name}" if hasattr(company, "name") else "No name")
#         print(f"Industry: {company.industry}" if hasattr(company, "industry") else "No industry")
#     else:
#         print("Could not retrieve company profile")

# Uncomment the test and part you want to run
async def main():
    """Run all tests."""
    print("=== Starting Comprehensive LinkedIn API Client Tests ===")
    print(f"Using API Key: {API_KEY[:5]}...{API_KEY[-5:]}")
    print(f"API Host: {API_HOST}")
    
    # Test core client , has profile , company and post data
    # client = await test_core_client()
    
    
    # # Test posts client has profile posts with comments and reactions , company posts with comments and reactions , user likes with details
    # post_urn = await test_posts_client()
    
    
    print("\n=== Comprehensive Tests Completed ===")


if __name__ == "__main__":
    asyncio.run(main()) 