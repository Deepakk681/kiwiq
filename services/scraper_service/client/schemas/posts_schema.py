from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from typing import Union
from scraper_service.client.schemas.base import ResponseBaseModel

class PostAuthor(ResponseBaseModel):
    id: int
    firstName: str
    lastName: str
    headline: str
    username: str
    url: str
    profilePictures: Optional[dict]  # Contains `urn` and maybe more nested image objects in future


class PostArticle(ResponseBaseModel):
    title: str
    subtitle: str
    link: str


class Mention(ResponseBaseModel):
    firstName: str
    lastName: str
    urn: str
    publicIdentifier: str

class CompanyMention(ResponseBaseModel):
    id: int
    name: str
    publicIdentifier: str
    url: str

class PostDetailsRequest(ResponseBaseModel):
    post_url: str   

class PostDetailsResponse(ResponseBaseModel):
    isBrandPartnership: bool
    text: str
    totalReactionCount: int
    likeCount: int
    appreciationCount: int
    empathyCount: int
    InterestCount: int
    praiseCount: int
    commentsCount: int
    repostsCount: int
    postUrl: str
    shareUrl: str
    postedAt: str
    postedDate: str
    postedDateTimestamp: int
    urn: str
    author: PostAuthor
    article: Optional[PostArticle] = None
    mentions: Optional[List[Mention]] = []
    companyMentions: Optional[List[CompanyMention]] = []

class PostReaction(ResponseBaseModel):
    fullName: Optional[str] = ""
    headline: Optional[str] = ""
    reactionType: Optional[str] = ""  # e.g., "LIKE", "PRAISE", etc.
    profileUrl: Optional[str] = "" 

class CompanyBase(ResponseBaseModel):
    name: str
    url: str
    urn: str

class Company(CompanyBase):
    pass

class CompanyPostAuthor(CompanyBase):
    pass



class CompanyPostArticle(ResponseBaseModel):
    title: Optional[str] = ""

class CompanyPostComment(ResponseBaseModel):
    name: str
    linkedinUrl: str
    title: str
    text: str
class CompanyPostVideo(ResponseBaseModel):
    url: str
    poster: Optional[str]
    duration: Optional[int]


class CompanyPost(ResponseBaseModel):
    text: str
    totalReactionCount: int
    likeCount: int
    appreciationCount: int
    empathyCount: int
    InterestCount: int
    praiseCount: int
    commentsCount: int
    repostsCount: int
    postUrl: str
    postedAt: str
    urn: str
    author: Optional[CompanyPostAuthor]
    article: Optional[CompanyPostArticle] = None
    video: Optional[List[CompanyPostVideo]] = None
    company: Optional[Company] = None

class CompanyPostResponse(ResponseBaseModel):
    text: str
    totalReactionCount: int
    likeCount: int
    appreciationCount: int
    empathyCount: int
    InterestCount: int
    praiseCount: int
    commentsCount: int
    repostsCount: int
    postUrl: str
    postedAt: str
    urn: str
    author: Optional[CompanyPostAuthor]
    article: Optional[CompanyPostArticle] = None
    video: Optional[List[CompanyPostVideo]] = None
    company: Optional[Company] = None
    comments: Optional[List[CompanyPostComment]] = []
    reactions: Optional[List[PostReaction]] = [] 


class Comment(ResponseBaseModel):
    id: Optional[str]
    text: Optional[str]
    author: Optional[str]
    timestamp: Optional[int]

class Reaction(ResponseBaseModel):
    type: str
    count: int

class PostsRequest(ResponseBaseModel):
    username: str
    post_reactions: str = "no"  # "yes"/"no"
    post_comments: str = "no"   # "yes"/"no"
    post_limit: Optional[int] = None
    comment_limit: Optional[int] = None
    reaction_limit: Optional[int] = None

class CompanyPostCommentsRequest(ResponseBaseModel):
    post_urn: str

class ProfilePostCommentsRequest(ResponseBaseModel):
    post_urn: str
    
class PostReactionsRequest(ResponseBaseModel):
    post_url: Optional[str] = None
    urn: Optional[str] = None

class PostCommentAuthor(ResponseBaseModel):
    name: str
    urn: str
    id: str
    username: str
    linkedinUrl: str
    title: str

class PostComment(ResponseBaseModel):
    isPinned: bool
    isEdited: bool
    threadUrn: str
    createdAt: int
    createdAtString: str
    permalink: str
    text: str
    author: PostCommentAuthor

class ProfilePost(ResponseBaseModel):
    text: Optional[str]
    shareUrl: Optional[str]
    postUrl: Optional[str]
    totalreactions: Optional[int]
    totalcomments: Optional[int]
    media: Optional[Union[str, dict, list]]  # can be image URL, dict of images, or list of videos
    original_post_text: Optional[str]
    video: Optional[List[dict]]
    comments: Optional[List[Union[Comment, PostComment]]] = []
    reactions: Optional[List[PostReaction]] = []

class ProfilePostsResponse(ResponseBaseModel):
    posts: List[ProfilePost]
    paginationToken: Optional[str] = None



class PostReaction(ResponseBaseModel):
    fullName: str
    headline: str
    reactionType: str
    profileUrl: str

class LinkedInPostComment(ResponseBaseModel):
    name: Optional[str]
    linkedin_url: Optional[str]
    title: Optional[str]
    text: Optional[str]


class LinkedInPostReaction(ResponseBaseModel):
    full_name: Optional[str]
    profile_url: Optional[str]
    headline: Optional[str]
    reaction_type: Optional[str]

class ProfilePicture(ResponseBaseModel):
    width: int
    height: int
    url: str


class LinkedInPostMedia(ResponseBaseModel):
    url: str
    width: Optional[int]
    height: Optional[int]


class LinkedInPostVideo(ResponseBaseModel):
    url: str
    poster: Optional[str]
    duration: Optional[int]


class LinkedInPost(ResponseBaseModel):
    post_id: int
    text: str
    original_post_text: Optional[str]
    post_url: str
    share_url: Optional[str]
    total_reactions: Optional[int]
    total_comments: Optional[int]
    comments: List[LinkedInPostComment] = []
    media: List[LinkedInPostMedia] = []
    video: List[LinkedInPostVideo] = []
    reactions: List[LinkedInPostReaction] = []