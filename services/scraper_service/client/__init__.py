"""
RapidAPI LinkedIn Scraper client package.

This package provides clients for fetching LinkedIn data using the RapidAPI
LinkedIn scraper endpoint.
"""

from scraper.rapid_api.client.core_api_client import RapidAPIClient
from scraper.rapid_api.client.schemas import (
    # Profile models
    ProfileRequest,
    ProfileResponse,
    
    # Company models
    CompanyRequest,
    CompanyResponse,

    #Post models
     ProfilePostCommentsRequest, PostComment, ProfilePostsRequest, ProfilePost, PostReaction , PostDetailsRequest , PostDetailsResponse, CompanyPostsRequest, CompanyPostCommentsRequest, CompanyPostResponse , CompanyPost , CompanyPostAuthor , CompanyPostArticle , CompanyPostComment , CompanyPostAuthor, LikeItem , LikeActivity , LikeOwner,
    
    #Like models
    LikeActivity,
    LikeOwner,
    LikeItem,

)

__all__ = [
    # Clients
    'RapidAPIClient',
    'LinkedinPostFetcher',
    
    # Models
    'ProfileRequest',
    'ProfileResponse',
    'CompanyRequest',
    'CompanyResponse',

    #Post models
    'ProfilePostReactionsRequest',
    'ProfilePostCommentsRequest',
    'PostComment',
    'ProfilePostsRequest',
    'ProfilePost',
    'PostReaction',
    'PostDetailsRequest',
    'PostDetailsResponse',
    'CompanyPostsRequest',
    'CompanyPostCommentsRequest',
    'CompanyPostResponse',
    'CompanyPost',
    'CompanyPostAuthor',
    'CompanyPostArticle',
    'CompanyPostComment',
    
    #Like models
    'LikeActivity',
    'LikeOwner',
    'LikeItem',
] 