from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

from datetime import date

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


BRIEF_USER_PROMPT_TEMPLATE = """Generate content brief for a LinkedIn post.

**Context:**
           - Content Strategy:(this is provide you the understanding of users content strategy and goals) {strategy_doc}
           - User Preferences:(this is provide you the understanding user’s goals and target audience)Ensure these briefs align with these {user_preferences}
           - Customer Context Docs Summary/Highlights:(this will provide you the understanding of users style preferences)
 {user_dna}
           - Recent User Posts (Drafts/Scraped):(use these to make a unique post that is relevant to the user's audience, make sure you are not repeating the same post and you are not using the same angle/hook) {merged_posts}
           - Posting Schedule: The user prefers to post on days mentioned in user preferences. 
Try that scheduled_time in your brief falls on one of these days. 
           - You can use this current data (date of today) to suggest the scheduled date for the post: {current_datetime}
           
**Task:**
           Create a compelling content brief focusing on a specific topic relevant to the user's expertise and target audience, drawing inspiration from the provided context. Ensure the brief is actionable and aligns with the user's brand voice (implied from context). Define the topic, angle, key points, and optionally a CTA and hashtags. Focus on using the information from the context to create a brief that is relevant to the user's audience.


Respond ONLY with the JSON object matching the specified schema. Ensure 'brief_id' reflects the current iteration number.
"""

BRIEF_SYSTEM_PROMPT_TEMPLATE = "You are an expert LinkedIn content strategist. Generate detailed and actionable content brief(s) based on the provided user context and Optional: previous briefs. Don't generate more than 1 brief at a time and ensure each brief is different from the previous ones. Respond strictly with the JSON output conforming to the schema: ```json\n{schema}\n```"

BRIEF_ADDITIONAL_USER_PROMPT_TEMPLATE = "Generate one more content brief. Ensure it's different from your previous briefs.\n\nBe sure to follow the same schema and quality standards as your previous generations"

# --- Pydantic Schemas for LLM Outputs ---

class TargetAudienceSchema(BaseModel):
    """Target audience information for brief"""
    primary: str = Field(description="Primary target audience")
    secondary: Optional[str] = Field(None, description="Secondary target audience")


class StructureOutlineSchema(BaseModel):
    """Outline of post structure"""
    opening_hook: str = Field(description="Opening hook to grab attention")
    common_misconception: str = Field(description="Common misconception to address")
    core_perspective: str = Field(description="Core perspective to present")
    supporting_evidence: str = Field(description="Supporting evidence for perspective")
    practical_framework: str = Field(description="Practical framework or application")
    strategic_takeaway: str = Field(description="Strategic takeaway for reader")
    engagement_question: str = Field(description="Question to drive engagement")


class PostLengthSchema(BaseModel):
    """Target post length range"""
    min: int = Field(description="Minimum length")
    max: int = Field(description="Maximum length")

class ContentBriefSchema(BaseModel):
    """Detailed content brief based on selected concept (AI-generated)"""
    # uuid: str = Field(description="Unique identifier for the brief")
    title: str = Field(description="Brief title")
    scheduled_date: str = Field(description="Scheduled date for the post in YYYY-MM-DD format")
    content_pillar: str = Field(description="Content pillar category")
    target_audience: TargetAudienceSchema = Field(description="Target audience information")
    core_perspective: str = Field(description="Core perspective for the post")
    post_objectives: List[str] = Field(description="Objectives of the post")
    key_messages: List[str] = Field(description="Key messages to convey")
    evidence_and_examples: List[str] = Field(description="Supporting evidence and examples")
    tone_and_style: str = Field(description="Tone and style guidelines")
    structure_outline: StructureOutlineSchema = Field(description="Outline of post structure")
    suggested_hook_options: List[str] = Field(description="Suggested hook options")
    call_to_action: str = Field(description="Call to action")
    hashtags: List[str] = Field(description="Suggested hashtags")
    post_length: PostLengthSchema = Field(description="Target post length range")


BRIEF_LLM_OUTPUT_SCHEMA = ContentBriefSchema.model_json_schema()

