from typing import Dict, Any, Optional, List, Union, ClassVar, Type, Literal
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


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

USER_DNA_DOC = UserDNA.model_json_schema()

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
    goal: str = Field(description="Overall goal for the 30 days")
    method: str = Field(description="Method to achieve the goal")
    targets: str = Field(description="Quantitative targets such as number of posts, number of likes, number of comments, number of shares, etc. based on the goal.")

class ImplementationSchema(BaseModel):
    """Implementation details"""
    thirty_day_targets: ThirtyDayTargetsSchema = Field(description="30-day goals")
    ninety_day_targets: NinetyDayTargetsSchema = Field(description="90-day goals")

class ContentStrategySchema(BaseModel):
    """Content strategy document derived from user DNA (AI-generated)"""
    title: str = Field(description="Strategy title")
    foundation_elements: FoundationElementsSchema = Field(description="Foundational elements of the strategy")
    core_perspectives: List[str] = Field(description="Core content perspectives")
    content_pillars: List[ContentPillarSchema] = Field(description="Content pillar definitions")
    implementation: ImplementationSchema = Field(description="Implementation details")

CONTENT_STRATEGY_DOC = ContentStrategySchema.model_json_schema()


class SelectedGoalSchema(BaseModel):
    """Schema for a selected content goal"""
    goal_id: str = Field(description="Unique identifier for the goal")
    name: str = Field(description="Name of the goal")
    description: str = Field(description="Detailed description of the goal")

class GoalsSchema(BaseModel):
    """Schema for content goals configuration"""
    selected: List[SelectedGoalSchema] = Field(description="List of pre-selected goals")
    custom_goals: Optional[List[str]] = Field(None, description="List of user-defined custom goals")

class PostingScheduleSchema(BaseModel):
    """Schema for content posting schedule configuration"""
    posts_per_week: int = Field(description="Number of posts to publish per week")
    posting_days: List[Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]] = Field(description="Days of the week when posts should be published")
    exclude_weekends: bool = Field(True, description="Whether to exclude weekend days from posting schedule")

class AutomationLevelSchema(BaseModel):
    """Schema for content automation configuration"""
    time_commitment_minutes: str = Field(description="Expected time commitment in minutes for content creation")

class AudienceSegmentSchema(BaseModel):
    """Schema for defining a target audience segment"""
    name: str = Field(description="Name of the audience segment")
    description: str = Field(description="Detailed description of the audience segment")
    industry: Optional[str] = Field(None, description="Target industry for this segment")
    experience_level: Optional[str] = Field(None, description="Target experience level")
    position: Optional[str] = Field(None, description="Target job position")
    company_size: Optional[str] = Field(None, description="Target company size")
    investment_focus: Optional[str] = Field(None, description="Investment focus area")
    knowledge_level: Optional[str] = Field(None, description="Expected knowledge level of the audience")

class AudienceSchema(BaseModel):
    """Schema for audience configuration"""
    segments: List[AudienceSegmentSchema] = Field(description="List of target audience segments")

class UserPreferencesSchema(BaseModel):
    """Schema for user content preferences"""
    audience: AudienceSchema = Field(description="Target audience configuration")
    posting_schedule: PostingScheduleSchema = Field(description="Content posting schedule configuration")
    automation_level: AutomationLevelSchema = Field(description="Content automation configuration")

USER_PREFERENCES_DOC = UserPreferencesSchema.model_json_schema()
