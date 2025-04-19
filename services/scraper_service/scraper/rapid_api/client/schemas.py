from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# === 1. Person Profile ===

class LinkedInProfile(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    headline: Optional[str]
    profile_picture: Optional[str]
    geo_country: Optional[str]
    geo_city: Optional[str]
    geo_full: Optional[str]
    geo_country_code: Optional[str]
    job_id: Optional[int]
    created_at: Optional[datetime]


class LinkedInEducation(BaseModel):
    id: int
    username: str
    school_name: Optional[str]
    degree: Optional[str]
    field_of_study: Optional[str]
    grade: Optional[str]
    start_year: Optional[int]
    start_month: Optional[int]
    end_year: Optional[int]
    end_month: Optional[int]
    description: Optional[str]
    activities: Optional[str]
    url: Optional[str]
    school_id: Optional[str]


class LinkedInPosition(BaseModel):
    id: int
    username: str
    company_id: Optional[int]
    company_name: Optional[str]
    company_username: Optional[str]
    company_url: Optional[str]
    industry: Optional[str]
    staff_count: Optional[str]
    title: Optional[str]
    location: Optional[str]
    employment_type: Optional[str]
    description: Optional[str]
    start_year: Optional[int]
    start_month: Optional[int]
    end_year: Optional[int]
    end_month: Optional[int]


# === 2. Company Profile ===

class CompanyProfile(BaseModel):
    id: int
    username: str
    name: str
    universal_name: str
    linkedin_url: str
    tagline: Optional[str]
    description: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    crunchbase_url: Optional[str]
    logo: Optional[str]
    cover: Optional[str]
    staff_count: Optional[int]
    staff_count_range: Optional[str]
    follower_count: Optional[int]
    industries: Optional[List[str]]
    founded_year: Optional[int]
    headquarter_country: Optional[str]
    headquarter_city: Optional[str]
    headquarter_postal_code: Optional[str]
    headquarter_address_line1: Optional[str]
    headquarter_address_line2: Optional[str]
    job_id: Optional[int]
    created_at: Optional[datetime]


# === 3. Post Created by User ===

class LinkedInPostComment(BaseModel):
    name: Optional[str]
    linkedin_url: Optional[str]
    title: Optional[str]
    text: Optional[str]


class LinkedInPostReaction(BaseModel):
    full_name: Optional[str]
    profile_url: Optional[str]
    headline: Optional[str]
    reaction_type: Optional[str]


class LinkedInPostMedia(BaseModel):
    url: str
    width: Optional[int]
    height: Optional[int]


class LinkedInPostVideo(BaseModel):
    url: str
    poster: Optional[str]
    duration: Optional[int]


class LinkedInPost(BaseModel):
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


# === 4. Post on which user commented ===

class ActivityCommentor(BaseModel):
    name: Optional[str]
    linkedin_url: Optional[str]
    title: Optional[str]
    text: Optional[str]


class ActivityReactor(BaseModel):
    full_name: Optional[str]
    profile_url: Optional[str]
    headline: Optional[str]
    reaction_type: Optional[str]


class ActivityMedia(BaseModel):
    url: Optional[str]
    width: Optional[int]
    height: Optional[int]


class ActivityVideo(BaseModel):
    url: Optional[str]
    poster: Optional[str]
    duration: Optional[int]


class ActivityCommentedPost(BaseModel):
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

class ActivityReactedPost(BaseModel):
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

