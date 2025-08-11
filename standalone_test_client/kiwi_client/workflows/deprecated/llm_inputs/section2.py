from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class HealthStatus(str, Enum):
    EXCELLENT = "excellent"    # 8-10
    HEALTHY = "healthy"        # 6-7.9
    NEEDS_ATTENTION = "needs_attention"  # 4-5.9
    CRITICAL = "critical"      # 0-3.9


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContentHealthAlert(BaseModel):
    """Critical issues requiring immediate attention"""
    issue: str = Field(description="Specific content health issue (max 15 words)")
    impact: str = Field(description="Business impact of this issue (max 20 words)")
    quick_fix: str = Field(description="Immediate action to address issue (max 25 words)")
    priority: ImpactLevel = Field(description="Fix priority level")


class ContentOpportunity(BaseModel):
    """High-impact content optimization opportunities"""
    area: str = Field(description="Optimization area (e.g., 'AI Readiness', 'SEO Foundation')")
    current_score: float = Field(description="Current performance score (0-10)")
    potential_score: float = Field(description="Achievable score with optimization")
    action: str = Field(description="Specific action to take (max 30 words)")
    expected_outcome: str = Field(description="Expected business result (max 20 words)")


class ContentVelocityInsight(BaseModel):
    """Publishing frequency and consistency analysis"""
    monthly_output: int = Field(description="Current posts per month")
    status: HealthStatus = Field(description="Velocity health status")
    vs_benchmark: str = Field(description="Performance vs industry (e.g., '40% below average')")
    consistency_issue: Optional[str] = Field(description="Main consistency problem, if any")
    impact_statement: str = Field(description="How velocity affects business goals")


class ContentMixInsight(BaseModel):
    """Content type performance and balance"""
    top_performer: str = Field(description="Best performing content type")
    top_performer_impact: str = Field(description="Why this type works well (max 20 words)")
    biggest_gap: str = Field(description="Most underperforming content type")
    gap_opportunity: str = Field(description="How to fix the gap (max 25 words)")
    mix_balance_score: float = Field(description="Content portfolio balance score (0-10)")


class SeoFoundationInsight(BaseModel):
    """Core SEO health assessment"""
    foundation_score: float = Field(description="Overall SEO foundation score (0-10)")
    status: HealthStatus = Field(description="SEO health status")
    biggest_win: str = Field(description="Strongest SEO asset")
    biggest_risk: str = Field(description="Most critical SEO weakness")
    technical_priority: str = Field(description="Top technical SEO fix needed")
    content_priority: str = Field(description="Top content SEO improvement needed")


class AiReadinessInsight(BaseModel):
    """AI optimization and citation readiness"""
    readiness_score: float = Field(description="AI optimization readiness (0-10)")
    status: HealthStatus = Field(description="AI readiness status")
    citation_potential: str = Field(description="Current AI citation potential (High/Medium/Low)")
    missing_elements: List[str] = Field(
        max_items=2, 
        description="Top 2 missing elements for AI optimization"
    )
    quick_wins: List[str] = Field(
        max_items=2,
        description="Top 2 quick wins for AI visibility"
    )


class ContentPerformanceSnapshot(BaseModel):
    """High-level content performance overview"""
    overall_health_score: float = Field(description="Overall content health (0-10)")
    health_status: HealthStatus = Field(description="Overall health status")
    content_strength: str = Field(description="Biggest content strength")
    critical_weakness: str = Field(description="Most urgent content weakness")
    competitive_position: str = Field(description="Position vs competitors (Leading/Competitive/Behind)")


class StreamlinedContentHealthReport(BaseModel):
    """Executive-focused content health assessment designed for quick decision-making"""
    
    # Executive Summary
    performance_snapshot: ContentPerformanceSnapshot = Field(
        description="High-level content health overview"
    )
    
    # Critical Issues (What Needs Immediate Action)
    health_alerts: List[ContentHealthAlert] = Field(
        max_items=3,
        description="Top 3 most critical content health issues"
    )
    
    # Core Performance Areas
    velocity_insight: ContentVelocityInsight = Field(
        description="Publishing frequency and consistency analysis"
    )
    
    content_mix_insight: ContentMixInsight = Field(
        description="Content type performance and portfolio balance"
    )
    
    seo_foundation: SeoFoundationInsight = Field(
        description="SEO health and technical foundation"
    )
    
    ai_readiness: AiReadinessInsight = Field(
        description="AI optimization and citation readiness"
    )
    
    # Opportunities (What To Focus On)
    top_opportunities: List[ContentOpportunity] = Field(
        max_items=3,
        description="Top 3 highest-impact optimization opportunities"
    )
    
    # Action Plan
    priority_actions: List[str] = Field(
        max_items=3,
        description="Top 3 actions to take in next 30 days (max 25 words each)"
    )
    
    # Bottom Line
    business_impact_summary: str = Field(
        description="One powerful sentence about content health business impact"
    )
    
    next_assessment_date: str = Field(
        description="When to reassess content health (typically 60-90 days)"
    )


