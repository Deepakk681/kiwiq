# ========================================
# SOURCE FILE REFERENCE
# ========================================
# This schema is documented here for reference only.
# The actual source file is located at:
# standalone_client/kiwi_client/workflows/active/onboarding/llm_inputs/onboarding_prompts.py
# ========================================

# Import from actual source (not used here, just for reference)
from kiwi_client.workflows.active.onboarding.llm_inputs.onboarding_prompts import (
    LINKEDIN_PROFILE_SCHEMA as SOURCE_LINKEDIN_PROFILE_SCHEMA
)

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from enum import Enum


class WeekDay(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ContentGoals(BaseModel):
    """Captures the primary and secondary content creation goals for LinkedIn strategy.

    These goals drive content planning and should be specific, measurable outcomes
    the executive wants to achieve through their LinkedIn presence.
    """
    primary_goal: Optional[str] = Field(
        None,
        description="The main objective for LinkedIn content (e.g., 'Build thought leadership in AI/ML space', 'Generate qualified leads for consulting services')"
    )
    secondary_goal: Optional[str] = Field(
        None,
        description="Secondary content objective that supports the primary goal (e.g., 'Increase brand awareness', 'Network with industry peers')"
    )


class PostingSchedule(BaseModel):
    """Defines the LinkedIn posting cadence and timing preferences for content automation.

    This schedule will be used by content planning and publishing systems to optimize
    engagement and maintain consistent presence.
    """
    posts_per_week: int = Field(
        default=0,
        description="Number of posts to publish per week (0-14 range for practical limits)"
    )
    posting_days: List[WeekDay] = Field(
        default_factory=list,
        description="Preferred days of the week for posting content"
    )
    exclude_weekends: bool = Field(
        default=False,
        description="Whether to avoid posting on Saturday and Sunday"
    )


class Timezone(BaseModel):
    """IANA timezone configuration for scheduling content at optimal times.

    Critical for ensuring posts go live when the target audience is most active.
    All scheduling systems should use the IANA identifier as the source of truth.
    """
    iana_identifier: str = Field(
        default="",
        description="IANA timezone identifier (e.g., 'America/New_York', 'Europe/London')"
    )
    display_name: str = Field(
        default="",
        description="Human-readable timezone name for UI display (e.g., 'Eastern Time', 'GMT')"
    )
    utc_offset: str = Field(
        default="",
        description="Current UTC offset in format '+/-HH:MM' (e.g., '-05:00', '+01:00')"
    )
    supports_dst: bool = Field(
        default=False,
        description="Whether this timezone observes Daylight Saving Time"
    )
    current_offset: str = Field(
        default="",
        description="Current offset accounting for DST if applicable"
    )


class LinkedInProfileDocument(BaseModel):
    """Complete LinkedIn executive profile for content automation and strategy.

    This document serves as the foundation for all LinkedIn content generation,
    scheduling, and personalization. It should capture the executive's professional
    brand, goals, and preferences comprehensively.
    """
    profile_url: HttpUrl = Field(
        description="Valid LinkedIn profile URL (e.g., 'https://www.linkedin.com/in/username/')"
    )
    username: Optional[str] = Field(
        None,
        description="LinkedIn username/handle extracted from profile URL"
    )
    persona_tags: Optional[List[str]] = Field(
        None,
        description="Professional persona keywords that define the executive's brand (e.g., ['AI Expert', 'Tech Leader', 'Startup Advisor'])"
    )
    content_goals: Optional[ContentGoals] = Field(
        None,
        description="Strategic objectives for LinkedIn content creation"
    )
    posting_schedule: Optional[PostingSchedule] = Field(
        None,
        description="Preferred timing and frequency for content publication"
    )
    timezone: Optional[Timezone] = Field(
        None,
        description="Timezone configuration for optimal content scheduling"
    )


LINKEDIN_PROFILE_SCHEMA = LinkedInProfileDocument.model_json_schema()
