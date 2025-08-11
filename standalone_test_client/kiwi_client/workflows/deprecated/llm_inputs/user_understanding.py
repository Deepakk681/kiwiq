from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


### GENERATION SCHEMA ###

class ProfessionalIdentitySchema(BaseModel):
    """Professional background and identity"""
    full_name: str = Field(description="User's full name")
    job_title: str = Field(description="Current job title")
    industry_sector: str = Field(description="Industry or business sector")
    company_name: str = Field(description="Current company name")
    company_size: str = Field(description="Size of current company")
    years_of_experience: int = Field(description="Years of professional experience")
    professional_certifications: List[str] = Field(description="Professional certifications held")
    areas_of_expertise: List[str] = Field(description="Areas of professional expertise")
    career_milestones: List[str] = Field(description="Significant career achievements")
    professional_bio: str = Field(description="Professional biography summary")

class LinkedInEngagementMetricsSchema(BaseModel):
    """Engagement performance metrics"""
    average_likes_per_post: int = Field(description="Average likes per post")
    average_comments_per_post: int = Field(description="Average comments per post")
    average_shares_per_post: int = Field(description="Average shares per post")

class LinkedInProfileAnalysisSchema(BaseModel):
    """Analysis of LinkedIn profile"""
    follower_count: int = Field(description="Number of LinkedIn followers")
    connection_count: int = Field(description="Number of LinkedIn connections")
    profile_headline_analysis: str = Field(description="Analysis of profile headline")
    about_section_summary: str = Field(description="Summary of 'About' section")
    engagement_metrics: LinkedInEngagementMetricsSchema = Field(description="Engagement performance metrics")
    top_performing_content_pillars: List[str] = Field(description="Best performing content categories")
    content_posting_frequency: str = Field(description="How often content is posted")
    content_types_used: List[str] = Field(description="Types of content posted")
    network_composition: List[str] = Field(description="Composition of LinkedIn network")

class BrandVoiceAndStyleSchema(BaseModel):
    """Personal brand voice characteristics"""
    communication_style: str = Field(description="Overall communication style")
    tone_preferences: List[str] = Field(description="Preferred tones in communication")
    vocabulary_level: str = Field(description="Level of vocabulary used")
    sentence_structure_preferences: str = Field(description="Preferred sentence structures")
    content_format_preferences: List[str] = Field(description="Preferred content formats")
    emoji_usage: str = Field(description="How emojis are used")
    hashtag_usage: str = Field(description="How hashtags are used")
    storytelling_approach: str = Field(description="Approach to storytelling")

class ContentStrategyGoalsSchema(BaseModel):
    """Content strategy goals and targets"""
    primary_goal: str = Field(description="Primary content goal")
    secondary_goals: List[str] = Field(description="Secondary content goals")
    target_audience_demographics: str = Field(description="Target audience demographics")
    ideal_reader_personas: List[str] = Field(description="Ideal reader descriptions")
    audience_pain_points: List[str] = Field(description="Pain points of target audience")
    value_proposition_to_audience: str = Field(description="Value proposition offered")
    call_to_action_preferences: List[str] = Field(description="Preferred calls to action")
    content_pillar_themes: List[str] = Field(description="Content pillar themes")
    topics_of_interest: List[str] = Field(description="Topics of interest to cover")
    topics_to_avoid: List[str] = Field(description="Topics to avoid covering")

class PersonalContextSchema(BaseModel):
    """Personal background context"""
    personal_values: List[str] = Field(description="Personal values")
    professional_mission_statement: str = Field(description="Professional mission statement")
    content_creation_challenges: List[str] = Field(description="Challenges in content creation")
    personal_story_elements_for_content: List[str] = Field(description="Personal story elements to use")
    notable_life_experiences: List[str] = Field(description="Notable life experiences")
    inspirations_and_influences: List[str] = Field(description="Sources of inspiration")
    books_resources_they_reference: List[str] = Field(description="Books and resources referenced")
    quotes_they_resonate_with: List[str] = Field(description="Resonating quotes")


class AnalyticsInsightsSchema(BaseModel):
    """Analytical insights about content"""
    optimal_content_length: str = Field(description="Optimal content length")
    audience_geographic_distribution: str = Field(description="Geographic distribution of audience")
    engagement_time_patterns: str = Field(description="Patterns in engagement timing")
    keyword_performance_analysis: str = Field(description="Performance of keywords")
    competitor_benchmarking: str = Field(description="Benchmark against competitors")
    growth_rate_metrics: str = Field(description="Growth rate metrics")


class SuccessMetricsSchema(BaseModel):
    """Metrics to measure success"""
    content_performance_kpis: List[str] = Field(description="KPIs for content performance")
    engagement_quality_metrics: List[str] = Field(description="Metrics for engagement quality")
    conversion_goals: List[str] = Field(description="Conversion goals")
    brand_perception_goals: List[str] = Field(description="Brand perception goals")
    timeline_for_expected_results: str = Field(description="Timeline for expected results")
    benchmarking_standards: str = Field(description="Standards for benchmarking")

class UserDNA(BaseModel):
    """Comprehensive user DNA profile derived from all inputs (AI-generated)"""
    professional_identity: ProfessionalIdentitySchema = Field(description="Professional background and identity")
    linkedin_profile_analysis: LinkedInProfileAnalysisSchema = Field(description="Analysis of LinkedIn profile")
    brand_voice_and_style: BrandVoiceAndStyleSchema = Field(description="Personal brand voice characteristics")
    content_strategy_goals: ContentStrategyGoalsSchema = Field(description="Content strategy goals and targets")
    personal_context: PersonalContextSchema = Field(description="Personal background context")
    analytics_insights: AnalyticsInsightsSchema = Field(description="Analytical insights about content")
    success_metrics: SuccessMetricsSchema = Field(description="Metrics to measure success")

GENERATION_SCHEMA = UserDNA.model_json_schema()

########################

### USER PROMPT TEMPLATE ###
USER_PROMPT_TEMPLATE = """

Analyze following information about the user to build their User DNA.

**Available Data to Analyze:**

- LinkedIn Profile Data: {linkedin_profile}
- Content Analysis Results: {content_analysis}
- User Preferences: {user_preferences}
- Content Pillars: {content_pillars}
- Core Beliefs and Perspectives: {core_beliefs_perspectives}
- Sources Analysis: {user_source_analysis}
- Building Blocks Methodology: {building_blocks}
- AI Copilot Guidelines: {methodology_implementation}

**Instructions for Using the Above Documents:**

- Use the **LinkedIn Profile Data** to understand the user's professional background, experience, education, and positioning on the platform. This will inform their industry focus, career stage, and potential influence.
- Use **Content Preferences** to define their goals, audience focus, and posting rhythm. These reflect how the user wants to show up on LinkedIn and what success looks like for them.
- Use **Content Pillars** to capture the primary domains the user wants to focus on in their content strategy. These will map to the user's thematic expertise.
- Use **Core Beliefs and Perspectives** to surface the user's worldview, operating principles, and unique angles — all essential to understanding their authentic voice.
- Use **Content Analysis Results** to identify patterns in their current or past LinkedIn content: tone, types of posts, engagement levels, performance gaps, and high-performing themes. This helps define their current content personality and areas for refinement.
- Use **Content Source Analysis** to assess what type of raw material the user already draws from (e.g., conversations, client work, readings, industry commentary) — which informs both their natural storytelling inputs and content creation ease.
- Apply the **Building Blocks Methodology** to understand how the user's ideas can be modularized into different strategic content units (authority, story, tactical, point of view, etc.).
- Apply the **AI Copilot Guidelines** to anticipate how this user is likely to collaborate with an AI content agent — what aspects they'll likely want automated, what decisions they'll want to stay involved in, and how feedback and iteration should be handled.

**Important Guidelines for Missing Information:**
- For any field where information is not available, use "[Information Not Available]" instead of null

**Task:**

Create a comprehensive **User DNA profile** for the user, based only on the data provided in the documents listed above. The final output must match the required JSON schema for User DNA exactly — do not include any information outside of the schema or fabricate missing details.

All details must be based directly on the source data. Do not summarize or generalize unless explicitly instructed. The User DNA should provide a precise foundation for all future content generation and strategic guidance.

**Respond ONLY with the JSON object matching the specified schema.**
"""

### SYSTEM PROMPT TEMPLATE ###
SYSTEM_PROMPT_TEMPLATE = """
You are an expert in professional branding and LinkedIn strategy. Gather and analyze information about the user to build their User DNA profile. Use the provided LinkedIn profile, content analysis, and additional materials to complete the User DNA Template. Focus on extracting meaningful insights that can inform an effective User DNA.

**Important Guidelines for Missing Information:**
- For any field where information is not available, use "[Information Not Available]" instead of null

Respond strictly with the JSON output conforming to the schema:

```json
{schema}
```
"""
