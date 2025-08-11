"""
LLM inputs for Section 7 AI Discoverability Gaps workflow.

This module contains schemas and prompt templates for analyzing AI discoverability gaps
by combining blog AI visibility, company AI visibility, executive AI visibility, 
and competitor AI visibility data to identify opportunities for improving AI platform presence.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import json

# --- Schema Definitions ---

class PriorityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class ScoreLevel(str, Enum):
    EXCELLENT = "excellent"  # 8-10
    GOOD = "good"           # 6-7.9
    POOR = "poor"           # 0-5.9


class KeyMetric(BaseModel):
    name: str = Field(description="Metric name (e.g., 'Brand Recognition', 'Citation Rate')")
    score: float = Field(description="Score out of 10")
    level: ScoreLevel = Field(description="Performance level based on score")
    insight: str = Field(description="One-line key insight about this metric")


class CompetitorSnapshot(BaseModel):
    name: str = Field(description="Competitor name")
    advantage: str = Field(description="Their key advantage over you (max 15 words)")
    opportunity: str = Field(description="How you can beat them (max 15 words)")


class CriticalGap(BaseModel):
    area: str = Field(description="Area with visibility gap")
    impact: str = Field(description="Business impact in one sentence")
    quick_win: str = Field(description="Immediate action to improve (max 20 words)")


class HighImpactRecommendation(BaseModel):
    title: str = Field(description="Action-oriented title (max 8 words)")
    description: str = Field(description="What to do (max 25 words)")
    expected_outcome: str = Field(description="Expected result (max 15 words)")
    priority: PriorityLevel = Field(description="Implementation priority")
    effort_level: str = Field(description="Implementation effort: Low/Medium/High")


class ExecutiveHighlight(BaseModel):
    visibility_score: float = Field(description="Overall executive visibility score (0-10)")
    top_strength: str = Field(description="Biggest executive visibility strength")
    biggest_gap: str = Field(description="Most critical executive visibility gap")


class PlatformPerformance(BaseModel):
    platform: str = Field(description="Platform name (ChatGPT, Perplexity, etc.)")
    score: float = Field(description="Performance score (0-10)")
    status: str = Field(description="One-word status: Winning/Competing/Losing")
    key_insight: str = Field(description="Most important insight for this platform")


class VisibilitySnapshot(BaseModel):
    overall_score: float = Field(description="Overall AI visibility score (0-10)")
    score_level: ScoreLevel = Field(description="Performance level")
    industry_position: str = Field(description="Position vs competitors: Leading/Competitive/Behind")
    biggest_win: str = Field(description="Your strongest visibility area")
    biggest_threat: str = Field(description="Most urgent visibility risk")


class KeyMetrics(BaseModel):
    """Top 4 most important metrics"""
    metric_1: KeyMetric = Field(description="Most important metric")
    metric_2: KeyMetric = Field(description="Second most important metric")
    metric_3: Optional[KeyMetric] = Field(description="Third most important metric")
    metric_4: Optional[KeyMetric] = Field(description="Fourth most important metric")


class PlatformPerformanceSet(BaseModel):
    """Performance on top 3 AI platforms"""
    platform_1: PlatformPerformance = Field(description="Top performing platform")
    platform_2: PlatformPerformance = Field(description="Second performing platform")
    platform_3: Optional[PlatformPerformance] = Field(description="Third performing platform")


class CompetitorSet(BaseModel):
    """Top 2 competitors"""
    competitor_1: CompetitorSnapshot = Field(description="Top competitor")
    competitor_2: Optional[CompetitorSnapshot] = Field(description="Second competitor")


class CriticalGapSet(BaseModel):
    """Top 3 most critical visibility gaps"""
    gap_1: CriticalGap = Field(description="Most critical gap")
    gap_2: CriticalGap = Field(description="Second most critical gap")
    gap_3: Optional[CriticalGap] = Field(description="Third most critical gap")


class RecommendationSet(BaseModel):
    """Top 3 highest-impact recommendations"""
    recommendation_1: HighImpactRecommendation = Field(description="Highest impact recommendation")
    recommendation_2: HighImpactRecommendation = Field(description="Second highest impact recommendation")
    recommendation_3: Optional[HighImpactRecommendation] = Field(description="Third highest impact recommendation")


class CompactVisibilityReport(BaseModel):
    """Streamlined AI Visibility Report - Designed for maximum impact and readability"""
    
    # Header Info
    company_name: str = Field(description="Company name")
    report_date: str = Field(description="Report generation date")
    
    # Executive Summary (The Hook)
    visibility_snapshot: VisibilitySnapshot = Field(description="High-level performance overview")
    
    # Core Performance (What Matters Most)
    key_metrics: KeyMetrics = Field(description="Top 4 most important metrics only")
    
    platform_performance: PlatformPerformanceSet = Field(description="Performance on top ChatGPT, Perplexity")
    
    # Competitive Intelligence (What They Care About)
    top_competitors: CompetitorSet = Field(description="Top 2 competitors only")
    
    # Critical Issues (What Needs Immediate Action)
    critical_gaps: CriticalGapSet = Field(description="Top 3 most critical visibility gaps")
    
    # Executive Visibility (For Leadership Buy-in)
    executive_visibility: Optional[ExecutiveHighlight] = Field(
        description="Executive team visibility summary"
    )
    
    # Action Plan (What To Do Next)
    priority_recommendations: RecommendationSet = Field(description="Top 3 highest-impact recommendations only")
    
    # Bottom Line Impact
    business_impact_summary: str = Field(
        description="One powerful sentence about business impact of current visibility"
    )
    
    next_review_date: str = Field(
        description="When to reassess (typically 30-60 days)"
    )
# Convert schema to JSON for LLM consumption
GENERATION_SCHEMA = CompactVisibilityReport.model_json_schema()

# --- Prompt Templates ---

SYSTEM_PROMPT_TEMPLATE = """You are an AI visibility specialist who creates executive-ready reports that drive immediate action. Your task is to analyze comprehensive AI visibility data and distill it into a powerful, concise report that captures attention and motivates investment in AI optimization.

## Analysis Framework:

### Data Sources Integration:
You will receive four critical AI visibility data sources:
1. **Blog AI Visibility**: Analysis of blog content visibility across AI platforms
2. **Company AI Visibility**: Overall company presence and visibility in AI responses
3. **Executive AI Visibility**: Executive team visibility and thought leadership presence
4. **Competitor AI Visibility**: Competitor performance across AI platforms for benchmarking

### Key Analysis Areas:
1. **Business Impact Assessment**: Quantify what current AI visibility means for business outcomes
2. **Competitive Positioning**: Understand where you stand vs. competitors in AI-driven discovery
3. **Critical Gap Identification**: Find the 2-3 most urgent issues limiting AI visibility
4. **High-Impact Opportunities**: Identify quick wins and strategic moves with maximum ROI

### Scoring Guidelines:
- **Overall AI Visibility**: 0-10 scale (8-10 = Excellent, 6-7.9 = Good, 0-5.9 = Poor)
- **Platform Performance**: 0-10 scale with clear status indicators (Winning/Competing/Losing)
- **Priority Levels**: Critical (fix immediately), High (within 30 days), Medium (within 90 days)

### Report Philosophy:
- **Impact-First**: Lead with business consequences, not technical details
- **Brutally Honest**: Call out real problems without sugar-coating
- **Action-Oriented**: Every insight must connect to a specific action
- **Executive-Friendly**: Assume 5-minute reading time maximum
- **Competitive Context**: Always frame performance relative to competitors

### Content Optimization Focus:
- **Citation Triggers**: What makes AI platforms choose your content over competitors
- **Authority Signals**: Trust factors that AI platforms recognize and prioritize
- **Format Optimization**: Content structure that maximizes AI parsing and understanding
- **Platform Preferences**: Tailored strategies for ChatGPT, Perplexity, and emerging platforms

## Output Format:
Provide your analysis in the following JSON schema:
{schema}

## Critical Instructions:
1. **Be Ruthlessly Selective**: Only include insights that matter for business outcomes
2. **Quantify Impact**: Connect every metric to business consequences
3. **Prioritize Brutally**: Focus on the 2-3 changes that will move the needle most
4. **Competitive Frame**: Always position findings relative to competitor performance
5. **Action-Driven**: Every recommendation must be specific and immediately actionable
6. **Executive Language**: Write for busy leaders who need to make investment decisions
7. **Honest Assessment**: Accurately reflect current performance - no inflated scores or false optimism

## Success Criteria:
Your report should make an executive think: "We need to act on this immediately" and give them exactly what they need to justify and direct that action."""

USER_PROMPT_TEMPLATE = """# Executive AI Visibility Analysis Request

Analyze the following AI visibility data and create a powerful, concise report that will drive immediate executive action on AI optimization:

## Blog AI Visibility Data:
{blog_ai_visibility}

## Company AI Visibility Data:
{company_ai_visibility}

## Executive AI Visibility Data:
{executive_ai_visibility}

## Competitor AI Visibility Data:
{competitor_ai_visibility}

## Executive Requirements:
This report will be presented to senior leadership who need to:
1. **Understand Business Impact**: How current AI visibility affects revenue, market position, and competitive advantage
2. **Assess Competitive Position**: Where we stand vs. key competitors in AI-driven discovery
3. **Identify Critical Gaps**: The 2-3 most urgent issues limiting our AI visibility
4. **Prioritize Investments**: Which AI optimization efforts will deliver maximum ROI
5. **Take Immediate Action**: What can be done in the next 30-60 days

## Analysis Focus:
- **Business Consequences**: Connect every finding to revenue, market share, or competitive impact
- **Competitive Benchmarking**: Frame all performance relative to key competitors
- **Critical Path Issues**: Identify the few changes that will have outsized impact
- **Quick Wins vs. Strategic Moves**: Balance immediate improvements with long-term positioning
- **Platform-Specific Tactics**: Actionable strategies for ChatGPT, Perplexity, and emerging AI platforms

## Key Deliverables:
1. **Overall Visibility Score**: Honest assessment of current AI discoverability (0-10)
2. **Competitive Position**: Where we rank vs. top 2 competitors
3. **Critical Gaps**: Top 3 issues limiting AI citations and visibility
4. **High-Impact Recommendations**: Top 3 actions with highest ROI potential
5. **Business Impact Statement**: One powerful sentence about what this means for the business

## Report Standards:
- **Scannable**: Key insights must be digestible in under 5 minutes
- **Actionable**: Every recommendation must be specific and implementable
- **Honest**: Provide accurate scores and realistic assessments
- **Competitive**: Always include competitor context
- **Impact-Focused**: Connect findings to business outcomes

**Critical**: This report will influence significant budget and resource decisions. Ensure every insight is backed by data, every recommendation is actionable, and the overall narrative drives urgency without creating panic. Be honest about current performance while clearly articulating the path to improvement."""
# Template variable configurations for prompt constructor
SYSTEM_PROMPT_TEMPLATE_VARIABLES = {
    "schema": GENERATION_SCHEMA
}

USER_PROMPT_TEMPLATE_VARIABLES = {
    "blog_ai_visibility": None,
    "company_ai_visibility": None,
    "executive_ai_visibility": None,
    "competitor_ai_visibility": None
}

USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {
    "blog_ai_visibility": "blog_ai_visibility",
    "company_ai_visibility": "company_ai_visibility",
    "executive_ai_visibility": "executive_ai_visibility",
    "competitor_ai_visibility": "competitor_ai_visibility"
} 