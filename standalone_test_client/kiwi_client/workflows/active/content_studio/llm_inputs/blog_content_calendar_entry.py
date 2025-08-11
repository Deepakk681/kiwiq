from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

from datetime import date, datetime

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


# --- Content Objective Enum ---
class ContentObjective(str, Enum):
    """Primary objectives for blog content"""
    BRAND_AWARENESS = "brand_awareness"
    THOUGHT_LEADERSHIP = "thought_leadership"
    ENGAGEMENT = "engagement"
    EDUCATION = "education"
    LEAD_GENERATION = "lead_generation"
    SEO_OPTIMIZATION = "seo_optimization"
    PRODUCT_AWARENESS = "product_awareness"


BRIEF_USER_PROMPT_TEMPLATE = """Generate content topic suggestions for blog posts.

**Rules:**
- Do NOT fabricate facts or statistics. Base suggestions on the provided documents and company expertise.
- Use the **exact content pillar names** from the provided `playbook` when assigning themes to topics.
- Generate diverse and unique topic ideas that align with the company's expertise and audience needs.
- Align suggestions to the **expertise areas and topics of interest** from the `company_doc` and `playbook`.

**SCHEDULING REQUIREMENTS:**
1. **Date Selection:**
   - Current Date: {current_datetime}
   - CRITICAL: NEVER select a date that is in the past or before the current date
   - Schedule topics across the **next 2 weeks** (14 days starting from tomorrow)
   - Distribute topics evenly across the 2-week period
   - If today is the last day of the week, start from next Monday

2. **Output Format:**
   - scheduled_date must be in ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)
   - Double-check that the generated datetime is:
     a) Not in the past
     b) Within the next 2 weeks
     c) In UTC format

**Context:**
- Company Profile: {company_doc}
- Content Strategy/Playbook: {playbook}
- Diagnostic Report (if available): {diagnostic_report}
- Publishing Schedule: {schedule_config}
- Today's Date: {current_datetime}

**Task:**
Create compelling topic suggestions that align with the company's expertise, audience pain points, and content strategy.

**CRITICAL REQUIREMENTS:**
- Generate exactly **4 topic ideas** for each scheduled date
- All 4 topics must be unified around **one common theme** from the company's content pillars
- The theme must align with a specific **play** from the company's strategy (a "play" is a strategic content approach or pillar from the content strategy)
- Each individual topic should:
  - Be clearly defined with a descriptive **title** and **description**
  - Connect to the company's **areas of expertise**
  - Address **audience pain points** mentioned in the company profile/playbook
  - Offer a unique angle or perspective within the common theme
  - Complement the other 3 topics to provide comprehensive coverage of the theme
  - Consider SEO optimization opportunities
- Have a clear **objective** (brand awareness, thought leadership, SEO, etc.) for the entire topic set
- Include explanation of **why this topic matters** to the audience

Respond ONLY with the JSON object matching the specified schema.
"""

BRIEF_SYSTEM_PROMPT_TEMPLATE = """You are an expert blog content strategist specializing in topic ideation and content planning.

Your job is to generate high-quality, strategic content topic suggestions using structured company data. You must:

**Content Requirements:**
- NEVER invent facts or statistics. Base all suggestions on information from the documents (`company_doc`, `playbook`, or `diagnostic_report`).
- Use content pillars exactly as defined in `playbook.content_pillars[*].name` or `playbook.content_pillar_themes`.
- Generate topics that leverage the company's demonstrated expertise.
- Address audience pain points from the company profile and playbook.
- Consider SEO optimization opportunities for blog content.

**Topic Generation Requirements:**
- Generate exactly **4 topic ideas** for each scheduled date
- All 4 topics must be unified around **one common theme** from the company's content pillars
- Each topic should offer a unique angle or perspective within that common theme
- The theme must align with a specific **play** from the company's content strategy (a "play" is a strategic content approach or pillar)
- Each of the 4 topics should complement each other to provide comprehensive coverage of the theme
- Vary the complexity and depth of topics within the theme
- Consider seasonal relevance and industry trends where applicable
- Ensure the 4 topics work together as a cohesive content set for that scheduled date
- Consider blog-specific factors like SEO keywords, long-form content potential, and evergreen value

**Scheduling Requirements:**
1. **Date Selection:**
   - Current Date: {current_datetime}
   - CRITICAL: NEVER select a date that is in the past or before the current date
   - Schedule topics across the next 2 weeks (14 days starting from tomorrow)
   - Distribute topics evenly across the 2-week period
   - If today is the last day of the week, start from next Monday
   - Validate final date is:
     a) Not in the past
     b) Within the next 2 weeks

2. **Output Format:**
   - scheduled_date must be in ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ
   - Final validation: Ensure the generated datetime is not in the past

Respond strictly with the JSON output conforming to the schema: ```json\n{schema}\n```"""

BRIEF_ADDITIONAL_USER_PROMPT_TEMPLATE = """Generate one additional content topic suggestion for the blog.

**CRITICAL REQUIREMENTS:**
- Generate exactly **4 topic ideas** for the scheduled date
- All 4 topics must be unified around **one common theme** from the company's content pillars
- The theme must align with a specific **play** from the company's content strategy
- Each topic should offer a unique angle or perspective within the common theme

Ensure:
- It is distinct in theme and scheduled date from all previously generated suggestions
- It respects all schema fields and draws only from the provided documents
- It uses a different content pillar/theme from previous suggestions or what best aligns with the company's content strategy
- It has a unique scheduled date that fits within the 2-week planning window
- No invented facts. Base all suggestions on the provided company context
- Consider SEO opportunities for blog content

**Example Structure:**
If previous suggestion was "Product Features & Innovation", this could be "Industry Insights & Trends" with 4 topics around market analysis and thought leadership."""

# --- Pydantic Schemas for LLM Outputs ---

class ContentTopic(BaseModel):
    """Individual blog content topic suggestion"""
    title: str = Field(..., description="Suggested blog post title")
    description: str = Field(..., description="Description of the blog post topic and main points to cover")
    target_keywords: Optional[List[str]] = Field(None, description="Target SEO keywords for this blog post")

class BlogContentTopicsOutput(BaseModel):
    """Blog content topic suggestions with scheduling and strategic context"""
    suggested_topics: List[ContentTopic] = Field(..., description="List of blog content topic suggestions")
    scheduled_date: datetime = Field(..., description="Scheduled publication date for the content in datetime format UTC TZ", format="date-time")
    theme: str = Field(..., description="Content theme/pillar this belongs to")
    play_aligned: str = Field(..., description="Which strategic play this aligns with")
    objective: ContentObjective = Field(..., description="Primary objective for this content set")
    why_important: str = Field(..., description="Brief explanation of why this topic matters to the audience")
    seo_focus: Optional[str] = Field(None, description="Primary SEO focus or keyword theme for this content set")


BRIEF_LLM_OUTPUT_SCHEMA = BlogContentTopicsOutput.model_json_schema()