from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

class StrategyAudienceSchema(BaseModel):
    """Target audience segments for strategy"""
    primary: str = Field(description="Primary audience")
    secondary: Optional[str] = Field(description="Secondary audience")
    tertiary: Optional[str] = Field(description="Tertiary audience")

class FoundationElementsSchema(BaseModel):
    """Foundational elements of the strategy"""
    expertise: List[str] = Field(description="Areas of expertise")
    core_beliefs: List[str] = Field(description="Core beliefs")
    objectives: List[str] = Field(description="Strategy objectives")

class PostPerformanceAnalysisSchema(BaseModel):
    """Analysis of post performance"""
    current_engagement: str = Field(description="Current engagement levels")
    content_that_resonates: str = Field(description="Content types that resonate with audience")
    audience_response: str = Field(description="How audience responds to content")

class ContentPillarSchema(BaseModel):
    """Content pillar definitions"""
    name: str = Field(description="Pillar name")
    pillar: str = Field(description="Pillar theme")
    sub_topic: List[str] = Field(description="Sub-topics within pillar")

class ThirtyDayTargetsSchema(BaseModel):
    """30-day goals"""
    goal: str = Field(description="Overall goal for the 30 days")
    method: str = Field(description="Method to achieve the goal")
    targets: str = Field(description="Quantitative targets such as number of posts, number of likes, number of comments, number of shares, etc. based on the goal.")

class NinetyDayTargetsSchema(BaseModel):
    """90-day goals"""
    goal: str = Field(description="Overall goal for the 90 days")
    method: str = Field(description="Method to achieve the goal")
    targets: str = Field(description="Quantitative targets such as number of posts, number of likes, number of comments, number of shares, etc. based on the goal.")

class ImplementationSchema(BaseModel):
    """Implementation details"""
    thirty_day_targets: ThirtyDayTargetsSchema = Field(description="30-day goals")
    ninety_day_targets: NinetyDayTargetsSchema = Field(description="90-day goals")

class ContentStrategySchema(BaseModel):
    """Content strategy document derived from user DNA (AI-generated)"""
    title: str = Field(description="Strategy title")
    target_audience: StrategyAudienceSchema = Field(description="Target audience segments")
    foundation_elements: FoundationElementsSchema = Field(description="Foundational elements of the strategy")
    core_perspectives: List[str] = Field(description="Core content perspectives")
    content_pillars: List[ContentPillarSchema] = Field(description="Content pillar definitions")
    post_performance_analysis: Optional[PostPerformanceAnalysisSchema] = Field(description="Analysis of current post performance", default=None)
    implementation: ImplementationSchema = Field(description="Implementation details")

GENERATION_SCHEMA = ContentStrategySchema.model_json_schema()


SYSTEM_PROMPT_TEMPLATE = """
You are a strategic LinkedIn content consultant specializing in professional branding and audience growth. Develop comprehensive content strategy tailored to the user's professional background and goals. Respond strictly with the JSON output conforming to the schema: 
```json
{schema}
```
"""

USER_PROMPT_TEMPLATE = """
As a world-class content strategist, your task is to develop a comprehensive LinkedIn content strategy document for user using the Content Strategy Methodology. Analyze the provided inputs to understand user's background, goals, and voice. Fill in the Content Strategy Template with their Content Pillars, Target Audience, Content Goals, Tone and Voice Guidelines, Posting Frequency, Content Mix, and Implementation Plan.

Do not make up any information. Only use the information provided in the inputs.

**Strategic Framework:**

- Content Methodology:(use these as a methodology to create the strategy) {building_blocks}
- Implementation Guidelines:(use these as a guideline to implement the methodology) {methodology_implementation}

**User Information:**

- Content Preferences: {user_preferences}
- Content Pillars: {content_pillars}
- Core Beliefs & Perspectives: {core_beliefs_perspectives}
- User Source Analysis: {user_source_analysis}

**Instructions for Using the Above Documents:**

- Use *Content Preferences* to define the user's audience, goals, tone, and posting cadence.
- Use *Content Pillars* to shape the key domains around which the strategy will be structured. Any topics or themes shared are to be treated as **examples only** — not exhaustive or prescriptive. The AI agent using this strategy must independently generate fresh content ideas aligned with the intent of each pillar.
- Use *Core Beliefs & Perspectives* to establish the user's worldview, positioning, and messaging anchors.
- Use *User Source Analysis* only where relevant — focus on useful details such as platform behavior insights, storytelling patterns, or audience motivations. Do not include irrelevant background.
- Apply the *Building Blocks Methodology* to design modular content pieces suited to different content types (awareness, authority, engagement, etc.).
- Follow the *AI Copilot Guidelines* to simulate a working model where content is co-created, improved over time through performance feedback, and personalized iteratively.

**Important Note:**

Clearly mention that any specific examples in this strategy (such as content topics, headlines, or formats) are for **illustration only**. The AI content generation agent using this strategy must **not** reuse them directly or limit itself to those examples. It should ideate original, relevant content within the strategic direction defined here — adapting to the user's goals and evolving audience needs.

This content strategy will be used by an AI content writing agent to drive weekly content planning and execution.
"""
