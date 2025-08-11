from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class IssueUrgency(str, Enum):
    CRITICAL = "critical"      # Blocking AI discovery entirely
    HIGH = "high"             # Significantly limiting visibility
    MEDIUM = "medium"         # Minor impact but should be fixed


class TechnicalImpact(str, Enum):
    BLOCKING = "blocking"         # Prevents AI platforms from accessing content
    LIMITING = "limiting"         # Reduces AI citation likelihood
    OPTIMIZING = "optimizing"     # Improves AI understanding quality


class CriticalTechnicalIssue(BaseModel):
    """High-impact technical problems that executives need to know about"""
    issue: str = Field(description="The technical problem (max 15 words)")
    business_impact: str = Field(description="How this hurts AI visibility (max 20 words)")
    urgency: IssueUrgency = Field(description="How quickly this needs fixing")
    impact_type: TechnicalImpact = Field(description="Type of impact on AI discovery")
    fix_effort: str = Field(description="Implementation effort: Quick/Medium/Complex")


class QuickTechnicalWin(BaseModel):
    """Low-effort, high-impact technical improvements"""
    action: str = Field(description="What to do (max 12 words)")
    ai_benefit: str = Field(description="How this improves AI citations (max 15 words)")
    implementation_time: str = Field(description="Time to implement: Hours/Days/Weeks")
    expected_impact: str = Field(description="Expected visibility improvement: Low/Medium/High")


class AiOptimizationGap(BaseModel):
    """Specific gaps in AI-friendly content optimization"""
    gap_area: str = Field(description="Area needing optimization (e.g., 'Schema Markup', 'Content Structure')")
    current_state: str = Field(description="Current implementation status")
    ai_platforms_affected: List[str] = Field(description="Which AI platforms this impacts", max_items=3)
    optimization_needed: str = Field(description="Specific optimization required (max 20 words)")


class TechnicalHealthScore(BaseModel):
    """Overall technical readiness for AI discovery"""
    overall_score: float = Field(description="Technical health score (0-10)")
    ai_accessibility_score: float = Field(description="How easily AI platforms can access content (0-10)")
    content_structure_score: float = Field(description="Content organization for AI parsing (0-10)")
    mobile_readiness_score: float = Field(description="Mobile optimization for AI crawlers (0-10)")
    status_summary: str = Field(description="One-line technical status summary")


class StreamlinedTechnicalFoundations(BaseModel):
    """Executive-focused technical foundations assessment for AI visibility"""
    
    # High-Level Status
    technical_health: TechnicalHealthScore = Field(description="Overall technical readiness assessment")
    
    # Critical Issues (What's Broken)
    blocking_issues: List[CriticalTechnicalIssue] = Field(
        max_items=3,
        description="Top 3 technical issues blocking AI discovery"
    )
    
    # Quick Wins (What's Easy to Fix)
    immediate_improvements: List[QuickTechnicalWin] = Field(
        max_items=3,
        description="Top 3 quick technical wins for AI visibility"
    )
    
    # Strategic Gaps (What's Missing)
    ai_optimization_gaps: List[AiOptimizationGap] = Field(
        max_items=4,
        description="Top 4 AI optimization opportunities"
    )
    
    # Bottom Line Impact
    technical_impact_statement: str = Field(
        description="One powerful sentence about how technical issues affect AI visibility"
    )
    
    # Next Steps
    priority_fix_timeline: str = Field(
        description="Recommended timeline for addressing critical issues"
    )
