from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from typing import Union
from scraper_service.client.schemas.profile_schema import Image
from scraper_service.client.schemas.posts_schema import PostReaction , Comment,PostComment
from scraper_service.client.schemas.base import ResponseBaseModel

class ActivityCommentor(ResponseBaseModel):
    name: Optional[str]
    linkedin_url: Optional[str]
    title: Optional[str]
    text: Optional[str]


class ActivityReactor(ResponseBaseModel):
    full_name: Optional[str]
    profile_url: Optional[str]
    headline: Optional[str]
    reaction_type: Optional[str]


class ActivityMedia(ResponseBaseModel):
    url: Optional[str]
    width: Optional[int]
    height: Optional[int]


class ActivityVideo(ResponseBaseModel):
    url: Optional[str]
    poster: Optional[str]
    duration: Optional[int]


class ActivityCommentedPost(ResponseBaseModel):
    id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    headline: Optional[str]
    profile_url: Optional[str]
    post_text: str
    highlighted_comment: Optional[str]
    post_url: str
    total_reactions: Optional[int]
    like_count: Optional[int]
    appreciation_count: Optional[int]
    empathy_count: Optional[int]
    praise_count: Optional[int]
    funny_count: Optional[int]
    comments_count: Optional[int]
    reposts_count: Optional[int]
    created_at: Optional[datetime]
    commentors: List[ActivityCommentor] = []
    reactors: List[ActivityReactor] = []
    media: List[ActivityMedia] = []
    videos: List[ActivityVideo] = []


# === 5. Post on which user reacted ===

class ActivityReactedPost(ResponseBaseModel):
    id: int
    job_id: Optional[int]
    username: str
    action: Optional[str]
    post_text: str
    post_url: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_url: Optional[str]
    headline: Optional[str]
    like_count: Optional[int]
    comments_count: Optional[int]
    total_reactions: Optional[int]
    empathy_count: Optional[int]
    created_at: Optional[datetime]
    commentors: List[ActivityCommentor] = []
    reactors: List[ActivityReactor] = []

# === 6. Likes on User Posts ===

class LikeActivity(ResponseBaseModel):
    urn: Optional[str]
    activityType: Optional[str] = None
    

class LikeOwner(ResponseBaseModel):
    username: Optional[str] = None
    firstName: Optional[str]
    lastName: Optional[str]
    profileUrl: Optional[str] = None
    headline: Optional[str] = None
    postUrl: Optional[str] = None

class LikeItem(ResponseBaseModel):
    activity: Optional[LikeActivity] = None
    totalReactionCount : Optional[int]
    likeCount : Optional[int]
    appreciationCount : Optional[int]
    empathyCount : Optional[int]
    commentsCount : Optional[int]
    text: Optional[str] = ""
    owner: Optional[LikeOwner] = None
    postUrl: Optional[str] = None
    reactions: Optional[List[PostReaction]] = []
    comments: Optional[List[Union[Comment, PostComment]]] = []

class LikesResponse(ResponseBaseModel):
    items: List[LikeItem]
    paginationToken: Optional[str] = None


class HighlightedComment(ResponseBaseModel):
    text: str
    totalReactionCount: Optional[int] = 0
    likeCount: Optional[int] = 0
    empathyCount: Optional[int] = 0

class HighlightedCommentActivityCount(ResponseBaseModel):
    text: Optional[str]
    totalReactionCount: Optional[int]
    likeCount: Optional[int]
    empathyCount: Optional[int]
    appreciationCount: Optional[int]
    InterestCount: Optional[int]
    praiseCount: Optional[int]
    funnyCount: Optional[int]
    commentsCount: Optional[int]
    repostsCount: Optional[int]
    postUrl: Optional[str]
    postedAt: Optional[str]
    postedDate: Optional[str]
    commentedDate: Optional[str]
    urn: Optional[str]
    commentUrl: Optional[str]
    author: Optional[Dict[str, Any]]  # You can replace this with a model later
    image: Optional[List[Dict[str, Any]]]
    company: Optional[Dict[str, Any]] = {}
    article: Optional[Dict[str, Any]] = {}

# CommentImages


class CommentImage(ResponseBaseModel):
    url: str


class CommentAuthorCompany(ResponseBaseModel):
    name: str
    url: str
    urn: str


class GetProfileCommentResponse(ResponseBaseModel):
    highlightedComments: Optional[List[HighlightedComment]] = []
    highlightedCommentsActivityCounts: Optional[List[HighlightedCommentActivityCount]] = []

    text: Optional[str]
    totalReactionCount: Optional[int]
    likeCount: Optional[int]
    appreciationCount: Optional[int] = 0
    empathyCount: Optional[int] = 0
    InterestCount: Optional[int] = 0
    praiseCount: Optional[int] = 0
    funnyCount: Optional[int] = 0
    commentsCount: Optional[int]
    repostsCount: Optional[int]

    postUrl: Optional[str] #identifier for the post
    commentUrl: Optional[str]

    postedAt: Optional[str]
    postedDate: Optional[str]
    commentedDate: Optional[str]

    urn: Optional[str]

    image: Optional[List[CommentImage]] = []
    company: Optional[CommentAuthorCompany] = None