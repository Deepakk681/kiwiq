# ========================================
# SOURCE FILE REFERENCE
# ========================================
# This schema is documented here for reference only.
# The actual source file is located at:
# standalone_client/kiwi_client/workflows/active/onboarding/llm_inputs/onboarding_prompts.py
# ========================================

# Import from actual source (not used here, just for reference)
from kiwi_client.workflows.active.onboarding.llm_inputs.onboarding_prompts import (
    BLOG_COMPANY_PROFILE_SCHEMA as SOURCE_BLOG_COMPANY_PROFILE_SCHEMA
)

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class ICP(BaseModel):
    """Ideal Customer Profile (ICP) defining the company's target market for content strategy.

    This profile guides all blog content creation to ensure relevance and engagement
    with the most valuable prospects and customers.
    """
    icp_name: str = Field(
        description="Descriptive name for this ICP segment (e.g., 'Mid-market SaaS CTOs', 'Healthcare IT Directors')"
    )
    target_industry: Optional[str] = Field(
        None,
        description="Primary industry vertical this ICP operates in (e.g., 'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Education', 'Consulting', 'Real Estate')"
    )
    company_size: Optional[str] = Field(
        None,
        description="Typical company size range for this ICP as employee count (e.g., '1-10 employees', '50-200 employees', '500-1000 employees', '1000+ employees')"
    )
    buyer_persona: Optional[str] = Field(
        None,
        description="Detailed buyer persona including role, responsibilities, and decision-making authority (e.g., 'VP of Engineering at 100-500 person tech companies, responsible for infrastructure decisions')"
    )
    pain_points: Optional[List[str]] = Field(
        None,
        description="Key challenges and pain points this ICP faces that our content should address"
    )


class Competitor(BaseModel):
    """Competitive intelligence for content differentiation and market positioning.

    Understanding competitors helps create unique content angles and identify content gaps.
    """
    website_url: Optional[HttpUrl] = Field(
        None,
        description="Competitor's primary website URL for content analysis"
    )
    name: Optional[str] = Field(
        None,
        description="Competitor company name"
    )


class CompanyPostingSchedule(BaseModel):
    """Blog publishing cadence for consistent content delivery and audience engagement.

    Regular publishing schedules improve SEO performance and audience retention.
    """
    posts_per_month: int = Field(
        default=4,
        description="Target number of blog posts to publish per month (1-31 range)"
    )


class CompanyDocument(BaseModel):
    """Complete company profile for blog content strategy and automation.

    This document provides the foundation for all blog content planning, creation,
    and distribution. It should capture the company's market position, audience,
    and content objectives comprehensively.
    """
    name: str = Field(
        description="Official company name as it appears in marketing materials"
    )
    website_url: HttpUrl = Field(
        description="Company's primary website URL (canonical root domain)"
    )
    value_proposition: Optional[str] = Field(
        None,
        description="Clear, concise statement of the unique value the company provides to customers (1-2 sentences)"
    )
    icps: Optional[ICP] = Field(
        None,
        description="Primary ideal customer profile for content targeting"
    )
    competitors: Optional[List[Competitor]] = Field(
        None,
        description="Key competitors for market positioning and content differentiation"
    )
    goals: Optional[List[str]] = Field(
        None,
        description="Primary business objectives the blog content should support (e.g., 'Generate 50 qualified leads per month', 'Establish thought leadership in AI space')"
    )
    posting_schedule: Optional[CompanyPostingSchedule] = Field(
        None,
        description="Target publishing frequency and cadence"
    )


BLOG_COMPANY_PROFILE_SCHEMA = CompanyDocument.model_json_schema()
