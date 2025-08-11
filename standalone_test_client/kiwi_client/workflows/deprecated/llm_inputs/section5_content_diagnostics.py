"""
LLM inputs for Section 5 Content Diagnostics workflow - Competitive Intelligence Analysis.

This module contains schemas and prompt templates for analyzing competitive intelligence data
by combining company AI visibility, company content analysis, competitor AI visibility, 
and competitor content analysis to generate comprehensive competitive insights.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json

# --- Schema Definitions ---

class CompetitivePosition(str, Enum):
    DOMINATING = "dominating"    # Clear market leader
    LEADING = "leading"          # Strong position
    COMPETING = "competing"      # Neck-and-neck
    LAGGING = "lagging"         # Behind but viable
    STRUGGLING = "struggling"    # Significant disadvantage


class ThreatLevel(str, Enum):
    CRITICAL = "critical"        # Immediate competitive threat
    HIGH = "high"               # Significant threat within 6 months
    MODERATE = "moderate"       # Manageable competitive pressure
    LOW = "low"                 # Minimal threat


class OpportunitySize(str, Enum):
    MASSIVE = "massive"         # Game-changing opportunity
    SIGNIFICANT = "significant" # Major competitive advantage potential
    MODERATE = "moderate"       # Solid improvement opportunity
    MINOR = "minor"            # Small incremental gain


class CompetitorThreatProfile(BaseModel):
    """Focused competitor threat assessment"""
    competitor_name: str = Field(description="Competitor company name")
    
    # Core Performance Metrics
    overall_position: CompetitivePosition = Field(description="Overall competitive position vs. you")
    ai_visibility_score: float = Field(description="AI visibility score (0-10)")
    content_volume_monthly: int = Field(description="New content pieces per month")
    
    # Threat Assessment
    threat_level: ThreatLevel = Field(description="How immediate the competitive threat is")
    primary_advantage: str = Field(description="Their biggest advantage over you (max 20 words)")
    critical_weakness: str = Field(description="Their most exploitable weakness (max 20 words)")
    
    # Strategic Intel
    winning_content_type: str = Field(description="Content format where they dominate")
    target_audience_overlap: str = Field(description="High/Medium/Low audience overlap with you")


class CompetitiveGap(BaseModel):
    """Critical areas where competitors outperform you"""
    gap_area: str = Field(description="Specific area of competitive disadvantage")
    impact_level: ThreatLevel = Field(description="Business impact of this gap")
    leading_competitor: str = Field(description="Who's winning in this area")
    catch_up_timeframe: str = Field(description="Realistic time to close gap: Weeks/Months/Quarters")
    required_investment: str = Field(description="Investment level needed: Low/Medium/High")


class MarketOpportunity(BaseModel):
    """Untapped opportunities in competitive landscape"""
    opportunity_area: str = Field(description="Specific market opportunity")
    opportunity_size: OpportunitySize = Field(description="Potential business impact")
    competitor_weakness: str = Field(description="Which competitors are weak here")
    time_to_capitalize: str = Field(description="Window to act: Immediate/Short-term/Long-term")
    success_probability: str = Field(description="Likelihood of success: High/Medium/Low")


class CompetitiveMovement(BaseModel):
    """Recent competitive shifts and trends"""
    competitor_name: str = Field(description="Competitor making the move")
    strategic_shift: str = Field(description="What they're doing differently (max 25 words)")
    potential_impact: str = Field(description="How this could affect your position (max 20 words)")
    recommended_response: str = Field(description="Your counter-move (max 20 words)")


class MarketPositioning(BaseModel):
    """Overall market position analysis"""
    your_position: CompetitivePosition = Field(description="Your current market position")
    market_leader: str = Field(description="Current market leader name")
    biggest_threat: str = Field(description="Most dangerous competitor")
    closest_competitor: str = Field(description="Competitor most similar to you")
    
    # Market Dynamics
    market_trend: str = Field(description="Overall market direction: Growing/Stable/Declining")
    consolidation_risk: str = Field(description="Risk of market consolidation: High/Medium/Low")
    new_entrant_threat: str = Field(description="Threat from new competitors: High/Medium/Low")


class CompetitiveIntelligenceReport(BaseModel):
    """Executive-focused competitive intelligence report"""
    
    # Executive Summary
    market_positioning: MarketPositioning = Field(description="Your position in the competitive landscape")
    
    # Competitive Threats (Top Priority)
    competitor_threats: List[CompetitorThreatProfile] = Field(
        max_items=3,
        description="Top 3 most important competitors to monitor"
    )
    
    # Strategic Gaps (What You're Missing)
    critical_gaps: List[CompetitiveGap] = Field(
        max_items=3,
        description="Top 3 areas where competitors have significant advantages"
    )
    
    # Market Opportunities (Where You Can Win)
    market_opportunities: List[MarketOpportunity] = Field(
        max_items=3,
        description="Top 3 opportunities to gain competitive advantage"
    )
    
    # Competitive Intelligence (What's Changing)
    recent_movements: List[CompetitiveMovement] = Field(
        max_items=3,
        description="Top 3 recent competitive moves requiring response"
    )
    
    # Bottom Line Assessment
    competitive_outlook: str = Field(
        description="One powerful sentence about your competitive position and trajectory"
    )
    
    immediate_priorities: List[str] = Field(
        max_items=2,
        description="Top 2 most urgent competitive responses needed (max 15 words each)"
    )
    
    next_analysis_date: str = Field(
        description="When to refresh competitive intelligence (typically 30-90 days)"
    )

# class CompetitorPositionSchema(BaseModel):
#     """Individual competitor analysis"""
#     competitor_name: str = Field(description="Competitor company name")
#     content_velocity: int = Field(description="Posts per month")
#     seo_performance: float = Field(description="SEO performance score")
#     ai_visibility_score: float = Field(description="AI visibility score")
#     content_themes: List[str] = Field(description="Main content themes")
#     strengths: List[str] = Field(description="Competitive strengths")
#     vulnerabilities: List[str] = Field(description="Competitive vulnerabilities")

# class AiVisibilityComparisonEntry(BaseModel):
#     competitor_name: str = Field(description="Competitor company name")
#     ai_visibility_score: float = Field(description="AI visibility score for this competitor")

# class MarketShareEntry(BaseModel):
#     competitor_name: str = Field(description="Competitor company name")
#     market_share_percent: float = Field(description="Content market share percentage for this competitor")

# class CompetitiveIntelligenceSchema(BaseModel):
#     """Competitive Intelligence analysis"""
#     content_positioning_map: List[CompetitorPositionSchema] = Field(description="Content positioning for each competitor")
#     seo_competitive_gaps: List[str] = Field(description="SEO areas where competitors lead")
#     ai_visibility_comparison: List[AiVisibilityComparisonEntry] = Field(description="AI visibility scores by competitor")
#     competitive_vulnerabilities: List[str] = Field(description="Vulnerabilities in competitive landscape")
#     market_share_analysis: List[MarketShareEntry] = Field(description="Content market share by competitor")

# Convert schema to JSON for LLM consumption
GENERATION_SCHEMA = CompetitiveIntelligenceSchema.model_json_schema()

# --- Prompt Templates ---

SYSTEM_PROMPT_TEMPLATE = """You are a senior competitive intelligence analyst specializing in content strategy and digital marketing analysis. Your task is to analyze comprehensive competitive data and generate actionable insights for strategic decision-making.

## Analysis Framework:

### Data Sources Integration:
You will receive four critical data sources:
1. **Company AI Visibility**: Our company's visibility across AI platforms and search results
2. **Company Content Analysis**: Analysis of our content strategy, themes, and performance
3. **Competitor AI Visibility**: Competitors' visibility across AI platforms and search results
4. **Competitor Content Analysis**: Analysis of competitors' content strategies and performance

### Key Analysis Areas:
1. **Content Positioning Map**: Map each competitor's content approach, velocity, and positioning
2. **SEO Competitive Gaps**: Identify areas where competitors have SEO advantages
3. **AI Visibility Comparison**: Compare AI visibility scores across all competitors
4. **Competitive Vulnerabilities**: Identify weaknesses in the competitive landscape
5. **Market Share Analysis**: Estimate content market share distribution

### Scoring Guidelines:
- **Content Velocity**: Average posts per month (estimate from available data)
- **SEO Performance**: 0.0-10.0 scale based on search visibility and ranking strength
- **AI Visibility Score**: 0.0-10.0 scale based on AI platform presence and citation frequency
- **Market Share**: Percentage estimates based on content volume and engagement

### Output Requirements:
Your analysis must be comprehensive, data-driven, and actionable. Focus on:
- Quantitative metrics wherever possible
- Clear identification of competitive advantages and gaps
- Strategic recommendations based on competitive positioning
- Specific opportunities for market share growth

## Output Format:
Provide your analysis in the following JSON schema:
{schema}

## Instructions:
1. Analyze all four data sources comprehensively
2. Generate accurate competitor position mappings with quantitative scores
3. Identify specific SEO gaps where competitors lead
4. Calculate realistic AI visibility comparisons
5. Highlight exploitable competitive vulnerabilities
6. Estimate market share distribution based on content analysis
7. Ensure all recommendations are actionable and strategic"""

USER_PROMPT_TEMPLATE = """# Competitive Intelligence Analysis Request

Please analyze the following competitive intelligence data and generate comprehensive insights:

## Company AI Visibility Data:
{company_ai_visibility}

## Company Content Analysis Data:
{company_content_analysis}

## Competitor AI Visibility Data:
{competitor_ai_visibility}

## Competitor Content Analysis Data:
{competitor_content_analysis}

## Analysis Requirements:
1. Create detailed competitor position maps with quantitative scores
2. Identify specific SEO competitive gaps and opportunities
3. Compare AI visibility scores across all competitors
4. Highlight competitive vulnerabilities that can be exploited
5. Estimate market share distribution based on content performance

Please provide a comprehensive competitive intelligence analysis following the specified schema format."""

# Template variable configurations for prompt constructor
SYSTEM_PROMPT_TEMPLATE_VARIABLES = {
    "schema": GENERATION_SCHEMA
}

SYSTEM_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {}

USER_PROMPT_TEMPLATE_VARIABLES = {
    "company_ai_visibility": None,
    "company_content_analysis": None,
    "competitor_ai_visibility": None,
    "competitor_content_analysis": None
}

USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {
    "company_ai_visibility": "company_ai_visibility",
    "company_content_analysis": "company_content_analysis",
    "competitor_ai_visibility": "competitor_ai_visibility",
    "competitor_content_analysis": "competitor_content_analysis"
} 