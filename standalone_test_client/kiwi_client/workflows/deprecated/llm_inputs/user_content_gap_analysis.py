"""
Content Gap Analysis LLM Inputs
Prompts and schemas for analyzing content gaps and generating strategic recommendations
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
import json

# =============================================================================
# ENUMS
# =============================================================================

class PriorityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"

class ContentType(str, Enum):
    EDUCATIONAL = "educational"
    THOUGHT_LEADERSHIP = "thought_leadership"
    PRACTICAL = "practical"
    COMPARATIVE = "comparative"
    RESEARCH = "research"

class EngagementLevel(str, Enum):
    ABOVE_AVERAGE = "above_average"
    AT_AVERAGE = "at_average"
    BELOW_AVERAGE = "below_average"

# =============================================================================
# SCHEMAS
# =============================================================================

# Executive Summary Schemas
class GapAnalysisSchema(BaseModel):
    """Analysis of current vs required focus areas"""
    current_enterprise_focus: str = Field(description="Current percentage of enterprise-focused content")
    required_enterprise_focus: str = Field(description="Required percentage of enterprise-focused content")
    content_depth_deficit: str = Field(description="Current vs required content depth metrics")
    authority_gap: str = Field(description="Current vs competitor authority metrics")

class ExecutiveSummarySchema(BaseModel):
    """High-level strategic overview and recommendations"""
    strategic_shift_required: str = Field(description="Primary strategic change needed")
    key_gap_analysis: GapAnalysisSchema
    success_probability: str = Field(description="Assessment of success likelihood with conditions")

# Goal Analysis Schemas
class GoalAnalysisSchema(BaseModel):
    """Analysis of specific business goal and requirements"""
    objective: str = Field(description="Specific measurable goal")
    current_barrier: str = Field(description="Primary obstacle preventing goal achievement")
    required_content_shift: str = Field(description="Specific content changes needed")
    recommended_action: str = Field(description="Concrete action plan")

class GoalAlignmentSchema(BaseModel):
    """Mapping of business goals to content strategy requirements"""
    goal_1: GoalAnalysisSchema
    goal_2: GoalAnalysisSchema
    goal_3: GoalAnalysisSchema
    goal_4: GoalAnalysisSchema

# Content Distribution Schemas
class ContentFormatSchema(BaseModel):
    """Specific content format with targeting and metrics"""
    format: str = Field(description="Type of content format")
    monthly_target: int = Field(description="Number of pieces to create monthly")
    avg_word_count: int = Field(description="Target word count per piece")
    purpose: str = Field(description="Strategic purpose and expected outcome")

class FunnelStageSchema(BaseModel):
    """Content allocation and strategy for specific funnel stage"""
    recommended_share_pct: int = Field(description="Percentage of total content allocation")
    current_company_share_pct: int = Field(description="Current allocation percentage")
    adjustment_reasoning: str = Field(description="Rationale for recommended changes")
    enterprise_focus_within_stage: int = Field(description="Percentage of stage content focused on enterprise")
    monthly_content_target: int = Field(description="Total monthly content pieces for stage")
    content_formats: List[ContentFormatSchema] = Field(description="Specific content formats and targets")

class ContentDistributionSchema(BaseModel):
    """Complete content allocation strategy across funnel stages"""
    strategic_rationale: str = Field(description="Overall rationale for distribution strategy")
    content_allocation_by_stage: Dict[str, FunnelStageSchema] = Field(description="Stage-specific allocations")

# Strategic Initiative Schemas
class InitiativeComponentSchema(BaseModel):
    """Individual component of strategic content initiative"""
    deliverable: str = Field(description="Specific deliverable or output")
    frequency: str = Field(description="How often deliverable is created")
    target_keywords: Optional[List[str]] = Field(description="SEO keywords to target", default=None)
    target_publications: Optional[List[str]] = Field(description="Target publications for outreach", default=None)
    includes: Optional[List[str]] = Field(description="Components included in deliverable", default=None)
    target_comparisons: Optional[List[str]] = Field(description="Competitive comparisons to create", default=None)
    target_clusters: Optional[List[str]] = Field(description="Content clusters to develop", default=None)
    expected_impact: str = Field(description="Projected business impact and metrics")

class StrategicInitiativeSchema(BaseModel):
    """Major content initiative with timeline and resources"""
    name: str = Field(description="Initiative name")
    duration: str = Field(description="Total time commitment")
    resource_allocation: str = Field(description="Team capacity allocation")
    components: List[InitiativeComponentSchema] = Field(description="Initiative deliverables and components")

class StrategicInitiativesSchema(BaseModel):
    """Collection of major strategic content initiatives"""
    initiative_1: StrategicInitiativeSchema
    initiative_2: StrategicInitiativeSchema
    initiative_3: StrategicInitiativeSchema

# Quality Standards Schemas
class EnterpriseContentRequirementsSchema(BaseModel):
    """Quality standards for enterprise-focused content"""
    minimum_word_count: int = Field(description="Minimum words required for enterprise content")
    research_citations_required: int = Field(description="Minimum citations per article")
    data_points_per_article: int = Field(description="Required data points per piece")
    expert_quotes_per_article: int = Field(description="Required expert quotes per piece")
    internal_links_per_article: int = Field(description="Required internal links per piece")
    cta_placement: str = Field(description="Call-to-action placement strategy")

class SEOOptimizationSchema(BaseModel):
    """SEO optimization checklist and requirements"""
    primary_keyword_density: str = Field(description="Target keyword density range")
    secondary_keyword_usage: str = Field(description="Secondary keyword usage guidelines")
    meta_description_optimization: str = Field(description="Meta description requirements")
    header_structure: str = Field(description="Required header tag structure")
    image_optimization: str = Field(description="Image optimization requirements")
    schema_markup: str = Field(description="Schema markup requirements")

class ContentQualityStandardsSchema(BaseModel):
    """Comprehensive content quality and optimization standards"""
    enterprise_content_requirements: EnterpriseContentRequirementsSchema
    seo_optimization_checklist: SEOOptimizationSchema

# Metrics and Tracking Schemas
class MilestoneSchema(BaseModel):
    """Time-based milestone with target metric"""
    timeframe: str = Field(description="Time period for milestone")
    target: str = Field(description="Specific metric target")

class GoalMetricsSchema(BaseModel):
    """Tracking metrics for specific business goal"""
    primary_kpi: str = Field(description="Main key performance indicator")
    target: str = Field(description="Specific target to achieve")
    measurement: str = Field(description="How metric will be measured")
    milestone_tracking: List[str] = Field(description="Progressive milestones toward goal")

class SuccessMetricsSchema(BaseModel):
    """Complete metrics tracking for all business goals"""
    goal_1_metrics: GoalMetricsSchema
    goal_2_metrics: GoalMetricsSchema  
    goal_3_metrics: GoalMetricsSchema
    goal_4_metrics: GoalMetricsSchema

# Resource Requirements Schemas
class TeamRoleSchema(BaseModel):
    """Individual team member role and responsibilities"""
    responsibility: str = Field(description="Primary role responsibilities")
    time_allocation: str = Field(description="Time commitment to enterprise content")
    count: Optional[int] = Field(description="Number of people in role", default=None)

class ResourceBudgetSchema(BaseModel):
    """Budget allocation for external resources"""
    industry_research_subscriptions: str = Field(description="Annual research subscription costs")
    expert_interview_budget: str = Field(description="Quarterly expert interview budget")
    design_and_multimedia_support: str = Field(description="Monthly design support budget")
    content_promotion_budget: str = Field(description="Quarterly promotion budget")

class ResourceRequirementsSchema(BaseModel):
    """Complete resource allocation for content strategy"""
    content_team_structure: Dict[str, TeamRoleSchema] = Field(description="Team structure and roles")
    external_resources: ResourceBudgetSchema

# Implementation Timeline Schemas
class ImplementationPhaseSchema(BaseModel):
    """Specific implementation phase with deliverables"""
    duration: str = Field(description="Phase duration")
    focus: str = Field(description="Primary focus area")
    key_deliverables: List[str] = Field(description="Major deliverables for phase")

class ImplementationTimelineSchema(BaseModel):
    """Complete implementation timeline across phases"""
    phase_1: ImplementationPhaseSchema
    phase_2: ImplementationPhaseSchema
    phase_3: ImplementationPhaseSchema

# Risk Management Schemas
class RiskItemSchema(BaseModel):
    """Individual risk with assessment and mitigation"""
    risk: str = Field(description="Description of potential risk")
    probability: str = Field(description="Likelihood of risk occurring")
    mitigation: str = Field(description="Strategy to mitigate risk")

class RiskMitigationSchema(BaseModel):
    """Complete risk assessment and mitigation strategy"""
    risk_1: RiskItemSchema
    risk_2: RiskItemSchema
    risk_3: RiskItemSchema
    risk_4: RiskItemSchema

# Main Content Strategy Schema
class ContentStrategyAnalysisSchema(BaseModel):
    """Complete content strategy analysis and recommendations"""
    executive_summary: ExecutiveSummarySchema
    goal_alignment_analysis: GoalAlignmentSchema
    recommended_content_distribution: ContentDistributionSchema
    strategic_content_initiatives: StrategicInitiativesSchema
    content_quality_standards: ContentQualityStandardsSchema
    success_metrics_and_tracking: SuccessMetricsSchema
    resource_requirements: ResourceRequirementsSchema
    implementation_timeline: ImplementationTimelineSchema
    risk_mitigation: RiskMitigationSchema

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

CONTENT_GAP_ANALYSIS_SYSTEM_PROMPT_TEMPLATE = """You are an expert content strategist and analyst specializing in enterprise B2B content marketing. Your role is to analyze existing content strategies, identify gaps, and provide actionable recommendations for content improvement and growth.

You have access to:
1. Company's current blog content analysis
2. Industry deep dive analysis with content distribution data and share percentages
3. Company information and context

Your task is to conduct a comprehensive content gap analysis and provide strategic recommendations that are:
- Data-driven and specific
- Aligned with business goals
- Actionable with clear timelines
- Resource-conscious and realistic

Output your analysis in the following structured JSON format:

{schema}

Be extremely detailed, specific, and logical in your recommendations. Every suggestion should be backed by data from the provided analysis and clearly connected to the stated business goals."""

CONTENT_GAP_ANALYSIS_USER_PROMPT_TEMPLATE = """I need you to analyze the content gap for {company_name} and provide comprehensive strategic recommendations.

Here is the information I have available:

**COMPANY INFORMATION:**
{company_data}

**CURRENT BLOG CONTENT ANALYSIS:**
{blog_content_analysis}

**INDUSTRY DEEP DIVE ANALYSIS (with content distribution and share percentages):**
{deep_dive_report}

**BUSINESS GOALS:**
{business_goals}

Based on this data, I need you to:

1. **Identify Content Gaps**: Compare the company's current content strategy against the industry analysis and optimal distribution percentages
2. **Align with Goals**: Ensure all recommendations directly support the stated business objectives
3. **Provide Specific Recommendations**: Include exact content types, frequencies, word counts, and distribution strategies
4. **Resource Planning**: Detail the team structure, budget, and timeline needed
5. **Risk Assessment**: Identify potential challenges and mitigation strategies

Please be very specific in your analysis and recommendations. Use the industry data with share percentages to justify your suggested content distribution. Every recommendation should have clear reasoning tied back to the business goals and industry best practices.

Output your complete analysis in structured JSON format following the provided schema."""

# Schema as JSON string for the prompt
CONTENT_GAP_ANALYSIS_SCHEMA = ContentStrategyAnalysisSchema.model_json_schema()