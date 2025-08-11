from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

# --- Schema Definitions ---

from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class ContentType(str, Enum):
    """High-impact content types prioritized for AI visibility"""
    THOUGHT_LEADERSHIP = "thought_leadership"  # Blogs, articles with expert insights
    SOLUTION_GUIDES = "solution_guides"        # How-to guides, best practices
    CASE_STUDIES = "case_studies"             # Customer success stories
    MARKET_INSIGHTS = "market_insights"       # Industry reports, trend analysis
    INTERACTIVE_CONTENT = "interactive_content" # Tools, calculators, assessments


class ImpactLevel(str, Enum):
    """Impact assessment levels"""
    GAME_CHANGER = "game_changer"  # Transformational impact
    HIGH_IMPACT = "high_impact"    # Significant improvement
    QUICK_WIN = "quick_win"        # Fast, measurable gains


class ExecutiveDashboard(BaseModel):
    """One-page executive view - maximum impact in minimum time"""
    overall_score: float = Field(description="Overall visibility score (0-10)")
    market_position: str = Field(description="vs competitors: Leading/Competitive/Behind")
    biggest_win: str = Field(description="Your strongest advantage (1 sentence)")
    biggest_threat: str = Field(description="Most urgent competitive risk (1 sentence)")
    revenue_impact_estimate: str = Field(description="Estimated revenue impact of optimization")


class PowerMove(BaseModel):
    """High-impact opportunity with clear business case"""
    title: str = Field(description="Action-oriented title (max 6 words)")
    impact_level: ImpactLevel = Field(description="Expected impact level")
    description: str = Field(description="What to do (max 20 words)")
    business_outcome: str = Field(description="Expected business result (max 15 words)")
    implementation_weeks: int = Field(description="Weeks to implement (1-12)")
    investment_level: str = Field(description="Low/Medium/High investment required")
    success_metric: str = Field(description="How to measure success")


class ContentGap(BaseModel):
    """Critical content gap with immediate opportunity"""
    topic_area: str = Field(description="Content topic area")
    content_type: ContentType = Field(description="Recommended content format")
    search_demand: str = Field(description="Search volume: High/Medium/Emerging")
    competitor_weakness: str = Field(description="How competitors are failing here")
    ai_citation_opportunity: str = Field(description="Why AI will cite this content")
    business_case: str = Field(description="Revenue/lead impact in one sentence")


class QuickStrike(BaseModel):
    """30-day quick win with immediate ROI"""
    action: str = Field(description="Specific action to take (max 12 words)")
    effort_hours: int = Field(description="Total hours required (1-40)")
    expected_result: str = Field(description="Measurable outcome (max 10 words)")
    why_it_works: str = Field(description="Strategic rationale (max 15 words)")


class ExecutiveVisibilityLever(BaseModel):
    """Executive visibility opportunity"""
    executive_focus: str = Field(description="Which executive(s) to focus on")
    visibility_gap: str = Field(description="Current visibility limitation")
    strategic_action: str = Field(description="Specific action to take")
    authority_building_outcome: str = Field(description="How this builds market authority")
    competitive_advantage: str = Field(description="How this beats competitors")


class ActionPlan(BaseModel):
    """Immediate action plan - next 90 days"""
    power_moves: List[PowerMove] = Field(
        max_items=3,
        description="Top 3 highest-impact opportunities"
    )
    
    critical_content_gaps: List[ContentGap] = Field(
        max_items=3,
        description="Top 3 content opportunities with highest ROI"
    )
    
    quick_strikes: List[QuickStrike] = Field(
        max_items=4,
        description="Top 4 quick wins for immediate momentum"
    )
    
    executive_visibility_levers: List[ExecutiveVisibilityLever] = Field(
        max_items=2,
        description="Top 2 executive visibility opportunities"
    )


class CompetitiveIntelligence(BaseModel):
    """Critical competitive insights"""
    competitor_advantage: str = Field(description="Biggest competitor advantage to neutralize")
    market_opportunity: str = Field(description="Market gap competitors are missing")
    differentiation_play: str = Field(description="How to differentiate from pack")


class BusinessImpactProjection(BaseModel):
    """Projected business outcomes"""
    thirty_day_impact: str = Field(description="What you'll see in 30 days")
    ninety_day_impact: str = Field(description="What you'll see in 90 days")
    annual_impact_estimate: str = Field(description="Full-year potential impact")
    investment_required: str = Field(description="Total investment needed")
    roi_timeframe: str = Field(description="When investment pays back")


class ExecutiveDiagnosticReport(BaseModel):
    """Executive-ready diagnostic report - designed for decision makers"""
    
    # The Hook (30 seconds to read)
    executive_dashboard: ExecutiveDashboard = Field(description="One-page executive overview")
    
    # The Intelligence (2 minutes to read)
    competitive_intelligence: CompetitiveIntelligence = Field(description="Critical competitive insights")
    
    # The Plan (3 minutes to read)
    action_plan: ActionPlan = Field(description="90-day action plan with specific opportunities")
    
    # The Business Case (1 minute to read)
    business_impact: BusinessImpactProjection = Field(description="Projected outcomes and ROI")
    
    # Next Steps
    next_meeting_agenda: List[str] = Field(
        max_items=3,
        description="Top 3 decisions needed from leadership"
    )
    
    immediate_next_step: str = Field(
        description="Single most important action to take this week"
    )


# class ContentType(str, Enum):
#     """Content type enumeration"""
#     BLOG_POST = "blog_post"
#     WHITEPAPER = "whitepaper"
#     CASE_STUDY = "case_study"
#     INFOGRAPHIC = "infographic"
#     VIDEO = "video"
#     PODCAST = "podcast"
#     WEBINAR = "webinar"
#     SOCIAL_MEDIA_POST = "social_media_post"

# class ExecutiveSummarySchema(BaseModel):
#     """Executive Summary - 3 sentences max covering current position, biggest opportunity, and critical risk"""
#     current_position: str = Field(description="Current position assessment based on all metrics")
#     biggest_opportunity: str = Field(description="Top opportunity identified from deep research")
#     critical_risk: str = Field(description="Most urgent gap requiring immediate attention")
#     overall_diagnostic_score: float = Field(description="Overall diagnostic score (0-10)")

# class ContentOpportunitySchema(BaseModel):
#     """Individual content creation opportunity"""
#     title: str = Field(description="Suggested content title")
#     content_type: ContentType = Field(description="Type of content")
#     search_volume: int = Field(description="Target search volume")
#     social_sharing_potential: str = Field(description="Social sharing potential: High/Medium/Low")
#     ai_citation_potential: str = Field(description="AI citation potential: High/Medium/Low")
#     seo_difficulty: str = Field(description="SEO difficulty: High/Medium/Low")
#     rationale: str = Field(description="Why this company should create this content")

# class SeoQuickWinSchema(BaseModel):
#     """SEO quick win opportunity"""
#     improvement_type: str = Field(description="Type of SEO improvement")
#     description: str = Field(description="Description of the improvement")
#     expected_impact: str = Field(description="Expected impact description")
#     effort_required: str = Field(description="Effort required to implement")
#     timeline: str = Field(description="Expected timeline for results")

# class ExecutiveVisibilityActionSchema(BaseModel):
#     """Executive visibility action"""
#     action_type: str = Field(description="Type of visibility action")
#     description: str = Field(description="Detailed action description")
#     expected_outcome: str = Field(description="Expected outcome")
#     resources_needed: List[str] = Field(description="Resources required")
#     timeline: str = Field(description="Implementation timeline")

# class ImmediateOpportunitiesSchema(BaseModel):
#     """Immediate Opportunities for quick wins"""
#     top_content_opportunities: List[ContentOpportunitySchema] = Field(description="Top 5 content pieces to create")
#     seo_quick_wins: List[SeoQuickWinSchema] = Field(description="30-day impact SEO improvements")
#     executive_visibility_actions: List[ExecutiveVisibilityActionSchema] = Field(description="Executive visibility actions")
#     ai_optimization_priorities: List[str] = Field(description="AI optimization priorities")

# class Section1And8DiagnosticSchema(BaseModel):
#     """Complete diagnostic analysis combining all sections"""
#     executive_summary: ExecutiveSummarySchema = Field(description="Executive summary of findings")
#     immediate_opportunities: ImmediateOpportunitiesSchema = Field(description="Immediate action opportunities")

# Export the schema for use in the workflow
GENERATION_SCHEMA = Section1And8DiagnosticSchema.model_json_schema()

# --- Prompt Templates ---

USER_PROMPT_TEMPLATE = """
Analyze the following comprehensive content diagnostic data from sections 2-7 and provide an executive summary with immediate opportunities:

**Section 2 - Content Analysis:**
{section2_data}

**Section 3 - Digital Authority:**
{section3_data}

**Section 4 - SEO Performance:**
{section4_data}

**Section 5 - AI Visibility:**
{section5_data}

**Section 6 - Competitive Analysis:**
{section6_data}

**Section 7 - Content Strategy:**
{section7_data}

Based on this comprehensive data, provide:
1. An executive summary covering current position, biggest opportunity, and critical risk
2. Immediate opportunities including top content pieces, SEO quick wins, executive visibility actions, and AI optimization priorities

Focus on actionable insights that can be implemented within 30-90 days for maximum impact.
"""

SYSTEM_PROMPT_TEMPLATE = """
You are an expert content strategy analyst specializing in comprehensive content diagnostics and strategic recommendations.

Your task is to synthesize data from multiple diagnostic sections and provide actionable insights for content strategy improvement.

**Analysis Framework:**
1. **Executive Summary**: Synthesize current position, identify biggest opportunity, and highlight critical risks
2. **Content Opportunities**: Identify high-impact content pieces with strong SEO and social potential
3. **SEO Quick Wins**: Recommend immediate SEO improvements with 30-day impact potential
4. **Executive Visibility**: Suggest actions to improve executive thought leadership presence
5. **AI Optimization**: Prioritize AI visibility and citation optimization efforts

**Evaluation Criteria:**
- **Content Opportunities**: Consider search volume, social sharing potential, AI citation potential, and SEO difficulty
- **SEO Quick Wins**: Focus on low-effort, high-impact improvements
- **Executive Visibility**: Prioritize actions that build thought leadership and industry authority
- **AI Optimization**: Target improvements that enhance AI recognition and citation

**Output Guidelines:**
- Provide specific, actionable recommendations
- Include realistic timelines and resource requirements
- Prioritize opportunities by impact and effort
- Ensure all recommendations are data-driven and evidence-based

**Output Format:**
Provide your analysis in the following structured format:
{schema}

Ensure all fields are populated with specific, actionable insights based on the provided diagnostic data.
""" 