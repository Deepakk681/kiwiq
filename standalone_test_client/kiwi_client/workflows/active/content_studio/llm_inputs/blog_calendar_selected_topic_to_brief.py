"""
LLM Inputs for Selected Topic to Brief Generation Workflow

This file contains prompts, schemas, and configurations for the workflow that:
- Takes a user-selected topic from ContentTopicsOutput
- Loads company context
- Generates a comprehensive content brief
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
    section: str = Field(description="Name of the content section")
    description: str = Field(description="Description of what should be covered in this section")
    word_count: int = Field(description="Estimated word count for this section")

class SEOKeywordsSchema(BaseModel):
    """Schema for SEO keywords."""
    primary_keyword: str = Field(description="Primary keyword for the content")
    secondary_keywords: List[str] = Field(description="Secondary keywords to include")
    long_tail_keywords: List[str] = Field(description="Long-tail keywords for SEO")

class BrandGuidelinesSchema(BaseModel):
    """Schema for brand guidelines."""
    tone: str = Field(description="Tone of voice for the content")
    voice: str = Field(description="Brand voice characteristics")
    style_notes: List[str] = Field(description="Additional style guidelines and notes")

class ResearchSourceSchema(BaseModel):
    """Schema for a research source."""
    source: str = Field(description="Name or description of the research source")
    key_insights: List[str] = Field(description="Key insights extracted from this source")

class ContentBriefDetailSchema(BaseModel):
    """Schema for the detailed content brief."""
    title: str = Field(description="Title of the content")
    target_audience: str = Field(description="Target audience for the content")
    content_goal: str = Field(description="Primary goal of the content")
    key_takeaways: List[str] = Field(description="Key takeaways for the audience")
    content_structure: List[ContentSectionSchema] = Field(description="Detailed content structure")
    seo_keywords: SEOKeywordsSchema = Field(description="SEO keyword strategy")
    brand_guidelines: BrandGuidelinesSchema = Field(description="Brand voice and style guidelines")
    research_sources: List[ResearchSourceSchema] = Field(description="Research sources used")
    call_to_action: str = Field(description="Call to action for the content")
    estimated_word_count: int = Field(description="Estimated total word count")
    difficulty_level: str = Field(description="Content difficulty level (beginner, intermediate, advanced)")
    writing_instructions: List[str] = Field(description="Specific instructions for the writer")

class BriefFeedbackAnalysisSchema(BaseModel):
    """Schema for brief feedback analysis output."""
    revision_instructions: str = Field(description="Clear instructions for revising the brief based on feedback")
    change_summary: str = Field(description="Short, conversational message acknowledging the user's feedback")

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

BRIEF_GENERATION_SYSTEM_PROMPT = """
You are a senior content strategist helping create a comprehensive content brief for a blog post.

Your task is to generate a detailed content brief based on:
1. A pre-selected topic with strategic context (theme, objective, importance)
2. The specific topic title and description the user selected
3. Company context and positioning

The brief should be:
- Aligned with the content objective and theme
- Comprehensive and actionable for content creators
- Optimized for the target audience
- Consistent with brand tone and messaging
- SEO-optimized while maintaining quality

Create briefs that are specific, detailed, and provide clear guidance to content creators.

IMPORTANT: Focus on the specific selected topic provided, not the entire list of suggested topics.
"""

BRIEF_FEEDBACK_SYSTEM_PROMPT = """
You are an expert content strategist and feedback analyst.

You have been provided with:
1. A comprehensive content brief
2. Feedback from the user about that brief
3. Company context
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
Generate a comprehensive content brief for the following selected topic:

**Selected Topic and Strategic Context:**
{selected_topic}

**Company Context:**
{company_doc}

**Content Playbook:**
{playbook_doc}

**Task:**
Create a detailed content brief that will guide a writer to produce high-impact content that:
1. Fully explores the selected topic (from suggested_topics list) with depth and expertise
2. Aligns with the strategic theme and objective specified in the selected topic
3. Resonates with the target audience's needs and pain points from company ICPs
4. Maintains consistency with the company's brand and positioning
5. Follows the playbook guidelines and best practices
6. Provides practical value while achieving the content objective

The brief should include:
- Clear title based on the selected topic
- Target audience definition from company ICPs
- Specific content goals aligned with the strategic objective
- Detailed content structure with sections and word counts
- SEO keyword strategy
- Brand voice and tone guidelines
- Key takeaways for readers
- Strong call-to-action
- Specific writing instructions

Make the brief actionable and comprehensive enough that a writer can create excellent content from it.
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
   - The company's positioning and target audience from company doc
   - The selected topic details (title, description from suggested_topics)
   - The playbook guidelines
   - Any existing user modifications in the brief
4. Provide clear, actionable revision instructions
5. Create a short, conversational message acknowledging the feedback (e.g., "Got it! I'll make the brief more actionable with specific examples")

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

**Company Context:**
{company_doc}

**Playbook:**
{playbook_doc}
"""

BRIEF_FEEDBACK_ADDITIONAL_USER_PROMPT = """
The user has provided additional feedback on the revised brief.

Your task is to interpret the new feedback and provide fresh revision instructions and change summary.

Use the original context to stay consistent with the company's goals and strategic alignment.

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