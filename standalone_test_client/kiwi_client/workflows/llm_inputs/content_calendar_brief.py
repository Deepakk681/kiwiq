from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

from datetime import date, datetime

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


BRIEF_USER_PROMPT_TEMPLATE = """Generate content brief for a LinkedIn post.

**Rules:**
- Do NOT fabricate facts or statistics. If specific factual input is missing in the provided documents, leave those parts as null or empty.
- Use the **exact content pillar name** from the provided `strategy_doc` when assigning a pillar to the brief.
- Do NOT repeat angles, hooks, or structure outlines from previous posts in `merged_posts`. Rephrase creatively.
- Use `merged_posts` to learn the **style, adjectives, tone**, and **post length pattern** that the user typically prefers.
- Align to the **style, tone, CTA, and hook preferences** inferred from `user_dna`, especially the fields:  
  - `brand_voice_and_style.tone_preferences`  
  - `brand_voice_and_style.communication_style`  
  - `content_strategy_goals.call_to_action_preferences`

**TIMEZONE AND SCHEDULING REQUIREMENTS:**
1. **Date Selection:**
   - Current Date: {current_datetime}
   - CRITICAL: NEVER select a date that is in the past or before the current date
   - Only suggest posting dates from the **upcoming week** (starting from tomorrow)
   - Date must fall on a preferred day listed in `user_preferences`
   - If today is the last day of the week, start from next Monday

2. **Timezone Handling:**
   - Use complete timezone information from `user_timezone`:
     - iana_identifier: Technical timezone code
     - display_name: User-friendly name
     - current_offset: Current offset (including DST if applicable)
     - supports_dst: Whether timezone uses daylight saving time

3. **Optimal Posting Times:**
   - Choose from these peak LinkedIn engagement windows in user's local timezone:
     - **Morning slot**: 8:00 AM - 10:00 AM (peak professional start-of-day activity)
     - **Afternoon slot**: 12:00 PM - 3:00 PM (lunch break and mid-day professional browsing)
   - Select specific time within these windows based on user's audience and industry
   - Convert final scheduled time to UTC using current_offset
   - Account for daylight saving time if supports_dst is true

4. **Output Format:**
   - scheduled_date must be in ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)
   - Double-check that the generated datetime is:
     a) Not in the past
     b) Within the upcoming week
     c) On a preferred posting day
     d) In UTC format

**Context:**
- Content Strategy: {strategy_doc}
- User Preferences: {user_preferences}
- User Timezone Information: {user_timezone}
- Customer Context (User DNA Summary): {user_dna}
- Recent User Posts (Drafts/Scraped): {merged_posts}
- Today's Date: {current_datetime}

**Task:**
Create a compelling and differentiated content brief aligned to the user's expertise, audience pain points, and tone, based on the above context.

Include:
- A clearly defined **topic**
- A unique **angle or lens**
- **Core perspective** and **key points**
- Actionable structure with strategic value for the reader
- Optionally, a CTA and relevant hashtags

Respond ONLY with the JSON object matching the specified schema. Ensure 'brief_id' reflects the current iteration number.
"""

BRIEF_SYSTEM_PROMPT_TEMPLATE = """You are an expert LinkedIn content strategist with advanced timezone handling capabilities.

Your job is to generate a high-quality, unique content brief for a LinkedIn post using structured user data. You must:

**Content Requirements:**
- NEVER invent facts or statistics. If relevant details are not present in the documents (`strategy_doc`, `user_dna`, or `merged_posts`), leave those fields null.
- Use content pillars exactly as defined in `strategy_doc.content_pillars[*].name`.
- Avoid repeating hooks or post angles from `merged_posts`, though you may infer tone, sentence style, and post format from them.
- Align content with user's tone, vocabulary level, and audience from the User DNA fields.

**Timezone and Scheduling Requirements:**
1. **Timezone Information Processing:**
   - Process complete timezone information including:
     - iana_identifier: Technical timezone code (e.g., "Europe/London")
     - display_name: User-friendly name (e.g., "British Time - London")  
     - utc_offset: Standard offset (e.g., "+00:00")
     - current_offset: Current offset accounting for DST (e.g., "+01:00")
     - supports_dst: Whether timezone uses daylight saving time

2. **Date Selection:**
   - Current Date: {current_datetime}
   - CRITICAL: NEVER select a date that is in the past or before the current date
   - Choose dates within the upcoming week (starting from tomorrow)
   - Align with user's preferred posting days from user_preferences
   - If today is the last day of the week, start from next Monday
   - Validate final date is:
     a) Not in the past
     b) Within the upcoming week
     c) On a preferred posting day

3. **Time Selection:**
   - Select from LinkedIn's peak engagement windows in user's local timezone:
     - **Morning window**: 8:00 AM - 10:00 AM (professionals checking LinkedIn at work start)
     - **Lunch window**: 12:00 PM - 3:00 PM (mid-day professional browsing and lunch break activity)
   - Pick specific time within these windows based on typical LinkedIn activity patterns
   - Convert final scheduling to UTC using current_offset
   - Account for daylight saving time transitions if applicable

4. **Output Format:**
   - scheduled_date must be in ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ
   - Final validation: Ensure the generated datetime is not in the past

Respond strictly with the JSON output conforming to the schema: ```json\n{schema}\n```"""

BRIEF_ADDITIONAL_USER_PROMPT_TEMPLATE = """Generate one additional content brief.

Ensure:
- It is distinct in topic, angle, and hook from all previously generated briefs.
- It respects all schema fields and draws only from the provided documents.
- It uses different content pillar from the previous briefs or what best aligns with the user's content strategy.
- No invented facts. Leave unspecified values as null."""

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
    scheduled_date: datetime = Field(description="Scheduled date for the post in datetime format UTC TZ", format="date-time")
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

