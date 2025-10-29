# ========================================
# SOURCE FILE REFERENCE
# ========================================
# This schema is documented here for reference only.
# The actual source file is located at:
# standalone_client/kiwi_client/workflows/active/playbook/linkedin_content_playbook_generation/wf_llm_inputs.py
# ========================================

# Import from actual source (not used here, just for reference)
from kiwi_client.workflows.active.playbook.linkedin_content_playbook_generation.wf_llm_inputs import (
    PLAYBOOK_GENERATOR_OUTPUT_SCHEMA as SOURCE_PLAYBOOK_GENERATOR_OUTPUT_SCHEMA
)

from pydantic import BaseModel, Field
from typing import Optional, List


class ContentPlay(BaseModel):
    """Individual content play with implementation details"""
    play_name: str = Field(description="Name of the content play")
    source_path_for_implementation_strategy: str = Field(description="Exact path of the document and section used for implementation strategy. Format: 'Document Name > Section > Subsection'. Examples: 'Company Information > Target Audience > Buyer Personas', 'Diagnostic Report > Content Gaps Analysis > Missing Topics'")
    reasoning_for_implementation_strategy: str = Field(description="Reasoning for implementation strategy in 2-3 concise line points")
    implementation_strategy: str = Field(description="Blog content implementation strategy - specific topics, angles, and narrative approaches to execute this play through blog posts")
    source_path_for_content_formats: str = Field(description="Exact path of the document and section used for content format decisions. Format: 'Document Name > Section > Subsection'. Examples: 'Company Information > Available Resources > Content Team Size', 'Diagnostic Report > Competitive Analysis > Content Format Gaps'")
    reasoning_for_content_formats: str = Field(description="Reasoning for the content formats for this play in 2-3 concise line points")
    content_formats: List[str] = Field(description="Types of blog posts for this play (e.g., 'In-depth technical tutorials (3000-4000 words) with code examples and step-by-step implementation guides', 'Thought leadership pieces (1500-2000 words) challenging industry assumptions with data-backed arguments')")
    success_metrics: List[str] = Field(description="Blog content performance metrics to track (organic traffic, engagement rates, keyword rankings, etc.)")
    source_path_for_timeline: str = Field(description="Exact path of the document and section used for timeline planning. Format: 'Document Name > Section > Subsection'. Examples: 'Company Information > Available Resources > Team Capacity', 'Diagnostic Report > Opportunity Areas > Urgency Assessment'")
    reasoning_for_timeline: str = Field(description="Reasoning for the content publishing timeline")
    timeline: List[str] = Field(description="Content publishing timeline for the next 3 months with specific milestones")
    example_topics: Optional[List[str]] = Field(None, description="5-10 specific blog post topics/titles that implement this play (e.g., 'How to Solve [Specific Problem]: A Step-by-Step Guide', 'The Hidden Costs of [Industry Practice]: What Your Competitors Don't Want You to Know')")


class PlaybookGenerationOutput(BaseModel):
    """Output schema for playbook generation"""
    posts_per_week: int = Field(description="Recommended number of blog posts per week")
    playbook_title: str = Field(description="Title of the content playbook")
    executive_summary: str = Field(description="Executive summary of the playbook, this should be a concise summary of the playbook, do not add points and subpoints to it. It should be 1-2 paragraphs.")
    content_plays: List[ContentPlay] = Field(description="List of content plays with blog content implementation details")
    source_path_for_recommendations: str = Field(description="Exact path of the document and section used for recommendations. Format: 'Document Name > Section > Subsection'. Examples: 'Company Information > Business Goals > Primary Objectives', 'Diagnostic Report > Content Gaps Analysis > Missing Topic Categories'")
    reasoning_for_recommendations: str = Field(description="Reasoning for the content strategy recommendations in 2-3 concise line points")
    overall_recommendations: str = Field(description="Overall blog content strategy recommendations in 2-3 concise line points")
    next_steps: List[str] = Field(description="5-6 specific, actionable next steps for starting the blog content creation (e.g., 'Write and publish the first problem definition post on [specific topic]')")
