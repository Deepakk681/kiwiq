from enum import Enum


class JobType(Enum):
    FETCH_USER_PROFILE = "fetch_user_profile" # username / or extract username from URL
    FETCH_COMPANY_PROFILE = "fetch_company_profile" # username / or extract username from URL
    FETCH_USER_POSTS = "fetch_user_posts" # username / or extract username from URL
    FETCH_COMPANY_POSTS = "fetch_company_posts" # username / or extract username from URL
    FETCH_USER_LIKES = "fetch_user_likes" # username / or extract username from URL
    FETCH_USER_COMMENTS_ACTIVITY = "fetch_user_comments_activity"   # username / or extract username from URL
    
    FETCH_POST_REACTIONS = "fetch_post_reactions"  # SHARE URL needed here! For few company posts returned from RAPIDAPI, this is not available so need another API for this? (Same provider) 
    FETCH_POST_COMMENTS = "fetch_post_comments"  # 1 function using URN; Extract URN from post URL or convert Share URL to URN?

