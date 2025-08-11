from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Schema Definitions ---

class ContentThemeSchema(BaseModel):
    """Individual content theme with frequency data"""
    theme: str = Field(description="Content theme name (e.g., 'AI Strategy')")
    frequency: str = Field(description="Frequency percentage (e.g., '40%')")

# Section 1: Current Position Scorecard
class LinkedInPowerScoreSchema(BaseModel):
    """LinkedIn Power Score breakdown"""
    total_score: str = Field(description="Total LinkedIn Power Score out of 100 (sum of all component scores)")
    profile_strength: str = Field(description="Profile strength score out of 25 (completeness + optimization + professional branding)")
    content_impact: str = Field(description="Content impact score out of 25 (avg engagement rate × content quality × consistency)")
    industry_visibility: str = Field(description="Industry visibility score out of 25 (mentions + thought leadership + industry recognition)")
    digital_authority: str = Field(description="Digital authority score out of 25 (web presence + AI recognition + search dominance)")

class ContentPerformanceStatsSchema(BaseModel):
    """Key content performance statistics"""
    follower_count: int = Field(description="Current follower count")
    posting_frequency: str = Field(description="Posts per week/month (e.g., '3 posts per week')")
    average_engagement_rate: str = Field(description="Average engagement rate percentage (total engagements ÷ total impressions × 100)")
    engagement_vs_peers: str = Field(description="Peers' average engagement rate for comparison - industry benchmark percentage")
    content_themes: List[ContentThemeSchema] = Field(description="Top 3 content themes with frequency data")

class DigitalAuthorityMetricsSchema(BaseModel):
    """Digital authority measurements"""
    web_visibility_score: str = Field(description="Web visibility score out of 10 (Google results quality + first page dominance + credible mentions)")
    ai_recognition_score: str = Field(description="AI recognition score out of 10 (ChatGPT/Perplexity/Claude biographical accuracy + expertise recognition)")
    google_results_count: int = Field(description="Total mentions online (e.g., 15,400)")
    first_page_dominance: str = Field(description="Number of first page results you control out of 10 (owned content ÷ total first page results)")
    expert_query_performance: str = Field(description="Performance when AI is asked about your expertise out of 10 (mention frequency + accuracy + context)")

class CurrentPositionScorecardSchema(BaseModel):
    """Complete current position analysis"""
    linkedin_power_score: LinkedInPowerScoreSchema = Field(description="LinkedIn Power Score breakdown")
    content_performance_stats: ContentPerformanceStatsSchema = Field(description="Key content performance metrics")
    digital_authority_metrics: DigitalAuthorityMetricsSchema = Field(description="Digital authority measurements")


class CompetitivePositionSchema(BaseModel):
    """Executive's competitive standing"""
    biggest_content_advantage: List[str] = Field(description="Specific strengths with supporting data")
    content_gap_analysis: List[str] = Field(description="Things competitors cover that you don't")
    search_dominance_analysis: List[str] = Field(description="What queries you own vs competitors")
    biggest_visibility_gap: List[str] = Field(description="Specific weakness with impact assessment")
    missing_from_search: List[str] = Field(description="Important content related to your expertise not ranking - try to explain in one sentence")
    ai_recognition_gap: List[str] = Field(description="What AI doesn't know about you vs competitors")

class BenchmarkComparisonSchema(BaseModel):
    """Quantitative benchmarks vs competitors"""
    your_avg_engagement: str = Field(description="Your average engagement rate percentage (likes + comments + shares ÷ followers × 100)")
    your_posting_frequency: str = Field(description="Your posting frequency")
    top_performers_frequency: str = Field(description="Top performers' posting frequency")
    your_ai_visibility: str = Field(description="Your AI visibility score out of 10 (biographical accuracy + expertise recognition across AI platforms)")
    competitors_ai_visibility: str = Field(description="Competitors' average AI visibility score out of 10 (industry peer benchmark)")

class IndustryLeaderComparisonSchema(BaseModel):
    """Complete comparison with industry leaders"""
    competitive_position: CompetitivePositionSchema = Field(description="Your competitive standing")
    benchmark_comparison: BenchmarkComparisonSchema = Field(description="Quantitative performance benchmarks")

# Section 3: Top 3 Opportunities
class OpportunitySchema(BaseModel):
    """Individual opportunity structure"""
    priority: str = Field(description="Priority level (High, Medium/High)")
    action: str = Field(description="One specific action/initiative based on analysis")
    reason: str = Field(description="Why this is a good opportunity")

class TopOpportunitiesSchema(BaseModel):
    """Top 3 strategic opportunities"""
    quick_win: OpportunitySchema = Field(description="Provide two top 30-day quick win opportunities")
    power_move: OpportunitySchema = Field(description="Provide two top 90-day strategic power moves")
    game_changer: OpportunitySchema = Field(description="Provide two top 6-month transformational opportunities")

# Complete Report Schema
class LinkedInAnalysisReportSchema(BaseModel):
    """Complete High-Impact LinkedIn Analysis Report"""
    current_position_scorecard: CurrentPositionScorecardSchema = Field(description="Visual scorecard of current position")
    industry_leader_comparison: IndustryLeaderComparisonSchema = Field(description="Comparison with industry leaders")
    top_opportunities: TopOpportunitiesSchema = Field(description="Top 3 strategic opportunities")

# Export the schema for use in the workflow
GENERATION_SCHEMA = LinkedInAnalysisReportSchema.model_json_schema()

# --- Prompt Templates ---

USER_PROMPT_TEMPLATE = """
Analyze the following digital authority data and provide a comprehensive, honest assessment:

**Web Presence Audit:**
{web_presence_audit}

**AI Visibility Test:**
{ai_visibility_test}

Based on this data, provide a detailed analysis of the digital authority status including:
1. Current LinkedIn metrics and performance
2. Web presence audit results
3. AI recognition gaps and opportunities
4. Specific recommendations for building authority

**Important:** Be realistic and honest in your assessment. If the data shows poor performance, low engagement, or significant weaknesses, state this clearly. Do not try to present only positive aspects - provide a balanced view that accurately reflects both strengths and areas needing improvement.

Focus on actionable insights and concrete metrics where available.
"""

SYSTEM_PROMPT_TEMPLATE = """
You are an expert digital marketing analyst specializing in executive thought leadership and digital authority assessment.

Your task is to analyze digital presence data and provide structured insights about an executive's current digital authority status.

**Key Analysis Areas:**
1. **LinkedIn Metrics**: Evaluate follower count, engagement rates, content themes, and posting frequency
2. **Web Presence**: Assess Google search results, speaking engagements, podcast appearances, and industry mentions
3. **AI Recognition**: Identify gaps in AI recognition and biographical accuracy
4. **Authority Opportunities**: Recommend specific actions to build digital authority

**Analysis Guidelines:**
- Be precise with numerical data when available
- Provide realistic, honest assessments based on the data provided - DO NOT sugar-coat or inflate results
- Clearly identify weaknesses, gaps, and areas needing improvement alongside strengths
- Be direct about underperformance when the data shows it
- Consider industry context and standards to provide accurate benchmarking
- Focus on actionable recommendations that address real problems
- Avoid overly positive language that doesn't reflect actual performance

**Critical Requirement:** This analysis must be balanced and truthful. If the data shows poor performance, low engagement, or significant gaps, state this clearly. Do not try to spin negative results into positive ones.

**Output Format:**
Provide your analysis in the following structured format:
{schema}

Ensure all fields are populated with accurate data from the provided sources, reflecting the true state of digital authority.
""" 