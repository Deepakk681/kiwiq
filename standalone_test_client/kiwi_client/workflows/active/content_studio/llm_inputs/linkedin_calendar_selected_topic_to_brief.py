"""
LLM Inputs for LinkedIn Selected Topic to Brief Generation Workflow

This file contains prompts, schemas, and configurations for the workflow that:
- Takes a user-selected topic from ContentTopicsOutput
- Loads executive profile and content strategy
- Generates a comprehensive LinkedIn content brief
- Allows HITL editing and approval with iteration limits
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class ContentObjective(str, Enum):
    """Primary objectives for content"""
    BRAND_AWARENESS = "brand_awareness"
    THOUGHT_LEADERSHIP = "thought_leadership"
    ENGAGEMENT = "engagement"
    EDUCATION = "education"
    LEAD_GENERATION = "lead_generation"
    COMMUNITY_BUILDING = "community_building"

# =============================================================================
# INPUT SCHEMAS
# =============================================================================

class ContentTopic(BaseModel):
    """Individual content topic suggestion"""
    title: str = Field(..., description="Suggested content topic/title")
    description: str = Field(..., description="Description of suggested content topic/title")

class ContentTopicsOutput(BaseModel):
    """Content topic suggestions with scheduling and strategic context"""
    suggested_topics: List[ContentTopic] = Field(..., description="List of content topic suggestions")
    scheduled_date: datetime = Field(..., description="Scheduled date for the content in datetime format UTC TZ", format="date-time")
    theme: str = Field(..., description="Content theme this belongs to")
    play_aligned: str = Field(..., description="Which play this aligns with")
    objective: ContentObjective = Field(..., description="Primary objective for this content")
    why_important: str = Field(..., description="Brief explanation of why this topic matters")

# =============================================================================
# OUTPUT SCHEMAS
# =============================================================================

class ContentSectionSchema(BaseModel):
    """Schema for a content section in the brief."""
    section_title: str = Field(description="Title of the content section")
    key_points: List[str] = Field(description="Key points to cover in this section")
    estimated_word_count: int = Field(description="Estimated word count for this section")

class LinkedInFormattingSchema(BaseModel):
    """Schema for LinkedIn-specific formatting."""
    hook_style: str = Field(description="Type of hook for the post")
    emoji_strategy: str = Field(description="How to use emojis effectively")
    hashtag_strategy: str = Field(description="Hashtag recommendations")
    formatting_notes: List[str] = Field(description="LinkedIn-specific formatting tips")

class ContentBriefDetailSchema(BaseModel):
    """Schema for the detailed LinkedIn content brief."""
    title: str = Field(description="Title of the content")
    content_type: str = Field(description="Type of LinkedIn content (post, article, carousel, etc.)")
    content_format: str = Field(description="Format details for the content")
    target_audience: str = Field(description="Target audience for the content")
    content_goal: str = Field(description="Primary goal of the content")
    key_message: str = Field(description="Core message to convey")
    content_structure: List[ContentSectionSchema] = Field(description="Detailed content structure")
    linkedin_formatting: LinkedInFormattingSchema = Field(description="LinkedIn-specific formatting guidelines")
    call_to_action: str = Field(description="Call to action for the content")
    engagement_tactics: List[str] = Field(description="Tactics to boost engagement")
    success_metrics: List[str] = Field(description="How to measure success")
    estimated_reading_time: str = Field(description="Estimated time to read/consume")
    writing_guidelines: List[str] = Field(description="Specific writing instructions")

class BriefFeedbackAnalysisSchema(BaseModel):
    """Schema for brief feedback analysis output."""
    revision_instructions: str = Field(description="Clear instructions for revising the brief based on feedback")
    change_summary: str = Field(description="Short, conversational message acknowledging the user's feedback")

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

BRIEF_GENERATION_SYSTEM_PROMPT = """
You are a senior LinkedIn content strategist helping create a comprehensive content brief.

Your task is to generate a detailed content brief based on:
1. A pre-selected topic with strategic context (theme, objective, importance)
2. The specific topic title and description the user selected
3. Executive profile and personal brand positioning
4. Content strategy and playbook guidelines

The brief should be:
- Optimized for LinkedIn's algorithm and user behavior
- Aligned with the executive's voice and expertise
- Focused on the content objective and theme
- Engaging and designed to spark conversations
- Professional yet personable

Create briefs that are specific, detailed, and provide clear guidance for LinkedIn content creation.

IMPORTANT: Focus on the specific selected topic provided, not the entire list of suggested topics.
"""

BRIEF_FEEDBACK_SYSTEM_PROMPT = """
You are an expert LinkedIn content strategist and feedback analyst.

You have been provided with:
1. A comprehensive LinkedIn content brief
2. Feedback from the user about that brief
3. Executive profile and content strategy
4. The selected topic and strategic context

Your task is to analyze the feedback and provide:
1. Clear revision instructions for improving the content brief
2. A short, conversational message acknowledging the user's feedback and what we'll focus on improving

The user may have manually edited the brief, so:
- Respect and preserve user edits unless feedback specifically requests changes
- Build upon manual edits rather than overriding them
- Prioritize the most recent feedback if conflicts arise

Always provide structured output with all required fields: revision_instructions and change_summary.
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

BRIEF_GENERATION_USER_PROMPT_TEMPLATE = """
Generate a comprehensive LinkedIn content brief for the following selected topic:

**Selected Topic and Strategic Context:**
{selected_topic}

**Executive Profile:**
{executive_profile_doc}

**Content Strategy & Playbook:**
{content_strategy_doc}

**Task:**
Create a detailed LinkedIn content brief that will guide the executive to produce high-impact content that:
1. Fully explores the selected topic with depth and expertise
2. Aligns with the strategic theme and objective
3. Leverages the executive's unique voice and expertise
4. Follows LinkedIn best practices from the playbook
5. Drives engagement and achieves the content objective

The brief should include:
- Clear title optimized for LinkedIn
- Content type and format recommendations
- Target audience from the executive's network
- Detailed content structure with sections
- LinkedIn-specific formatting (hooks, emojis, hashtags)
- Engagement tactics and CTAs
- Success metrics aligned with the objective
- Writing guidelines matching the executive's style

Make the brief actionable and comprehensive enough that the executive can create excellent LinkedIn content from it.
"""

BRIEF_FEEDBACK_INITIAL_USER_PROMPT = """
Your Task:

Interpret the user's feedback and produce both revision instructions and a user-friendly change summary.

**IMPORTANT:** The content brief below may have been manually edited by the user. This means:
- The brief might contain user modifications, corrections, or additions
- You should respect and preserve these user edits unless the feedback specifically requests changes to them
- Your revision instructions should build upon the user's manual edits, not override them

You must:
1. Identify the user's intent behind the feedback
2. Locate specific areas in the content brief that need revision
3. Determine what changes are required, guided by:
   - The strategic context from the selected topic (theme, objective, importance)
   - The executive's profile and personal brand
   - The content strategy and LinkedIn best practices
   - The selected topic details (title, description from suggested_topics)
   - Any existing user modifications in the brief
4. Provide clear, actionable revision instructions
5. Create a short, conversational message acknowledging the feedback (e.g., "Got it! I'll make the content more conversational and add specific examples")

---

**Content Brief:**
{content_brief}

---

**User Feedback:**
{revision_feedback}

---

**Context:**
**Selected Topic:**
{selected_topic}

**Executive Profile:**
{executive_profile_doc}

**Content Strategy:**
{content_strategy_doc}
"""

BRIEF_FEEDBACK_ADDITIONAL_USER_PROMPT = """
The user has provided additional feedback on the revised brief.

Your task is to interpret the new feedback and provide fresh revision instructions and change summary.

Use the original context to stay consistent with the executive's brand and strategic alignment.

Provide the same structured output:
- revision_instructions: Clear instructions for improving the brief
- change_summary: Short, conversational message acknowledging the feedback

---

**Updated Brief:**
{content_brief}

**New Feedback:**
{revision_feedback}
"""

# =============================================================================
# SCHEMA EXPORTS
# =============================================================================

# Convert Pydantic models to JSON schemas for LLM use
BRIEF_GENERATION_OUTPUT_SCHEMA = ContentBriefDetailSchema.model_json_schema()
BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = BriefFeedbackAnalysisSchema.model_json_schema()

# Input schemas for validation (not for LLM output)
CONTENT_TOPICS_OUTPUT_SCHEMA = ContentTopicsOutput.model_json_schema()
CONTENT_TOPIC_SCHEMA = ContentTopic.model_json_schema()