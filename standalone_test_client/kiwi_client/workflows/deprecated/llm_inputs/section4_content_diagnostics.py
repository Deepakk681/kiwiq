"""
LLM Inputs for Section 4 Content Diagnostics Workflow

This file contains prompts, schemas, and configurations for the workflow that:
- Loads blog content analysis and competitor content analysis documents
- Identifies content gaps across customer journey stages
- Validates gaps through Reddit research
- Generates market opportunity analysis with content territories
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

class ContentGapSchema(BaseModel):
    """Individual content gap identified"""
    gap_id: str = Field(description="Unique identifier for the gap (gap_01, gap_02, etc.)")
    gap_title: str = Field(description="Title of the content gap")
    gap_description: str = Field(description="Detailed description of the gap")
    customer_journey_stage: str = Field(description="Customer journey stage: awareness, consideration, purchase, retention")
    gap_priority: str = Field(description="Priority level: High, Medium, Low")
    competitor_coverage: List[str] = Field(description="Competitors who are covering this topic")
    user_pain_point: str = Field(description="The specific user pain point this gap addresses")

class ContentGapsAnalysisSchema(BaseModel):
    """Content gaps analysis across customer journey stages"""
    awareness_gaps: List[ContentGapSchema] = Field(description="Content gaps in awareness stage")
    consideration_gaps: List[ContentGapSchema] = Field(description="Content gaps in consideration stage")
    purchase_gaps: List[ContentGapSchema] = Field(description="Content gaps in purchase stage")
    retention_gaps: List[ContentGapSchema] = Field(description="Content gaps in retention stage")
    total_gaps_identified: int = Field(description="Total number of gaps identified")
    high_priority_gaps: int = Field(description="Number of high priority gaps")

class RedditResearchResultSchema(BaseModel):
    """Reddit research results for a specific gap"""
    gap_id: str = Field(description="ID of the gap being researched")
    search_queries: List[str] = Field(description="Reddit search queries used")
    user_mentions: int = Field(description="Number of user mentions found")
    user_intent: str = Field(description="Primary user intent identified")
    common_questions: List[str] = Field(description="Most common questions asked")
    pain_points: List[str] = Field(description="Key pain points mentioned")
    validation_score: float = Field(description="Validation score (0-10) indicating how important this gap is to users")
    evidence_summary: str = Field(description="Summary of evidence supporting the gap's importance")

class GapValidationSchema(BaseModel):
    """Validated content gaps with Reddit research"""
    validated_gaps: List[RedditResearchResultSchema] = Field(description="List of validated gaps with research")
    total_validated: int = Field(description="Total number of gaps validated")
    average_validation_score: float = Field(description="Average validation score across all gaps")


class OpportunityLevel(str, Enum):
    GOLDMINE = "goldmine"      # High volume, low competition, high AI potential
    STRATEGIC = "strategic"    # Medium effort, high long-term value
    QUICK_WIN = "quick_win"    # Low effort, immediate impact


class CompetitionLevel(str, Enum):
    WIDE_OPEN = "wide_open"    # 0-0.3 competition
    MODERATE = "moderate"      # 0.4-0.6 competition  
    CROWDED = "crowded"        # 0.7-1.0 competition


class CitationPotential(str, Enum):
    HIGH = "high"              # Strong AI citation signals
    MEDIUM = "medium"          # Some AI citation potential
    LOW = "low"               # Limited AI citation likelihood


class ContentTerritory(BaseModel):
    """High-impact content territory with clear business value"""
    name: str = Field(description="Territory name (max 5 words)")
    opportunity_type: OpportunityLevel = Field(description="Type of opportunity")
    monthly_volume: int = Field(description="Total monthly search volume")
    competition_level: CompetitionLevel = Field(description="Competition intensity")
    ai_citation_potential: CitationPotential = Field(description="AI citation likelihood")
    
    # Business Impact
    revenue_potential: str = Field(description="Revenue impact: High/Medium/Low")
    time_to_win: str = Field(description="Time to dominate: 3-6mo/6-12mo/12mo+")
    
    # Competitive Intelligence
    main_competitor: str = Field(description="Biggest competitor in this space")
    their_weakness: str = Field(description="Competitor's key weakness (max 15 words)")
    our_advantage: str = Field(description="Our competitive advantage (max 15 words)")
    
    # Action Plan
    content_gap: str = Field(description="What's missing from current content (max 20 words)")
    first_move: str = Field(description="Immediate action to take (max 15 words)")
    
    # Validation Indicators (subtle)
    user_demand_confirmed: bool = Field(description="Reddit research confirmed user demand")
    validation_strength: str = Field(description="Strong/Moderate/Limited validation evidence")


class KeywordCluster(BaseModel):
    """High-value keyword group with clear action plan"""
    theme: str = Field(description="Keyword theme (max 4 words)")
    total_volume: int = Field(description="Combined monthly volume")
    top_keywords: List[str] = Field(max_items=3, description="Top 3 highest-value keywords")
    content_angle: str = Field(description="Recommended content approach (max 20 words)")
    search_intent_validated: bool = Field(description="User search intent confirmed through research")


class CompetitorThreat(BaseModel):
    """Key competitor with specific intelligence"""
    name: str = Field(description="Competitor name")
    threat_level: str = Field(description="Threat level: Critical/High/Medium")
    their_strength: str = Field(description="What they do well (max 15 words)")
    beat_them_by: str = Field(description="How to outrank them (max 20 words)")
    vulnerable_area: str = Field(description="Where they're weak (max 15 words)")


class AIOptimizationOpportunity(BaseModel):
    """Specific AI citation opportunity"""
    content_type: str = Field(description="Type: Guide/Tool/Comparison/List")
    ai_trigger: str = Field(description="What makes AI platforms cite this (max 20 words)")
    authority_signal: str = Field(description="Key credibility factor needed (max 15 words)")
    implementation_effort: str = Field(description="Effort level: Low/Medium/High")
    user_questions_identified: bool = Field(description="Real user questions found for this content type")


class TerritoryInsight(BaseModel):
    """Single powerful insight about content opportunities"""
    insight: str = Field(description="Key finding (max 25 words)")
    business_impact: str = Field(description="Why this matters (max 20 words)")
    action_required: str = Field(description="What to do about it (max 15 words)")
    evidence_source: str = Field(description="Based on: Reddit/Competition/Search data")


class ContentOpportunityReport(BaseModel):
    """Executive-ready content territory analysis focused on immediate action"""
    
    # Executive Summary
    market_size: int = Field(description="Total addressable monthly search volume")
    opportunity_rating: str = Field(description="Overall market opportunity: Excellent/Good/Limited")
    competitive_position: str = Field(description="Current position: Leading/Competitive/Behind")
    research_confidence: str = Field(description="High/Medium confidence in recommendations")
    
    # Top Opportunities (The Money Makers)
    goldmine_territories: List[ContentTerritory] = Field(
        max_items=2, 
        description="Top 2 highest-value opportunities"
    )
    
    quick_wins: List[ContentTerritory] = Field(
        max_items=2,
        description="Top 2 low-effort, high-impact opportunities"
    )
    
    # Keyword Intelligence
    priority_clusters: List[KeywordCluster] = Field(
        max_items=3,
        description="Top 3 keyword clusters to target"
    )
    
    # Competitive Intelligence
    key_threats: List[CompetitorThreat] = Field(
        max_items=2,
        description="Top 2 competitors to watch/beat"
    )
    
    # AI Optimization Strategy
    ai_opportunities: List[AIOptimizationOpportunity] = Field(
        max_items=3,
        description="Top 3 AI citation opportunities"
    )
    
    # Strategic Insights
    critical_insights: List[TerritoryInsight] = Field(
        max_items=3,
        description="Top 3 strategic insights from analysis"
    )
    
    # Action Plan
    immediate_actions: List[str] = Field(
        max_items=3,
        description="Top 3 actions to take in next 30 days"
    )
    
    next_quarter_goals: List[str] = Field(
        max_items=2,
        description="Top 2 goals for next 90 days"
    )
    
    # Bottom Line
    investment_recommendation: str = Field(
        description="Resource allocation recommendation (max 30 words)"
    )
    
    expected_outcome: str = Field(
        description="Expected results from investment (max 25 words)"
    )
    
    # Validation Summary (discrete)
    validation_summary: str = Field(
        description="Brief note on research methodology used (max 20 words)"
    )

# class ContentTerritorySchema(BaseModel):
#     """Individual content territory analysis"""
#     territory_name: str = Field(description="Name of content territory")
#     search_volume: int = Field(description="Monthly search volume")
#     competition_score: float = Field(description="Competition difficulty score (0-1)")
#     ai_citation_potential: str = Field(description="AI citation potential: High/Medium/Low")
#     right_to_win_factors: List[str] = Field(description="Factors supporting right to win")
#     competing_players: List[str] = Field(description="Main competitors in this territory")
#     opportunity_score: float = Field(description="Overall opportunity score (0-10)")

# class KeywordVolumeSchema(BaseModel):
#     """Individual keyword with search volume"""
#     keyword: str = Field(description="The keyword or search term")
#     monthly_volume: int = Field(description="Monthly search volume for this keyword")

# class SearchVolumeDataSchema(BaseModel):
#     """Search volume data for key terms"""
#     primary_keywords: List[KeywordVolumeSchema] = Field(description="Search volume for primary keywords")
#     long_tail_keywords: List[KeywordVolumeSchema] = Field(description="Search volume for long-tail keywords")
#     seasonal_trends: List[KeywordVolumeSchema] = Field(description="Seasonal search volume patterns")
#     total_monthly_volume: int = Field(description="Total estimated monthly search volume")

# class CompetitorScoreSchema(BaseModel):
#     """Individual competitor with scores"""
#     competitor_name: str = Field(description="Name of the competitor")
#     authority_score: float = Field(description="Authority score of this competitor")
#     content_quality_rating: float = Field(description="Content quality rating for this competitor")
#     market_share_estimate: float = Field(description="Estimated market share for this competitor")

# class CompetitionAnalysisSchema(BaseModel):
#     """Competition analysis across territories"""
#     competitor_scores: List[CompetitorScoreSchema] = Field(description="Scores and ratings for main competitors")
#     overall_competition_difficulty: float = Field(description="Overall competition difficulty score (0-1)")

# class TerritoryCitationSchema(BaseModel):
#     """AI citation assessment for a specific territory"""
#     territory_name: str = Field(description="Name of the content territory")
#     citation_probability: str = Field(description="AI citation probability: High/Medium/Low")
#     authority_signals: List[str] = Field(description="Authority signals that support AI citation")
#     content_depth_requirement: str = Field(description="Required content depth for AI citation")
#     ai_search_alignment: float = Field(description="Alignment with AI search patterns (0-1)")

# class AICitationAssessmentSchema(BaseModel):
#     """AI citation potential by territory"""
#     territory_citations: List[TerritoryCitationSchema] = Field(description="AI citation assessment for each territory")

# class MarketOpportunityAnalysisSchema(BaseModel):
#     """Market Opportunity Analysis with validated territories"""
#     top_unclaimed_territories: List[ContentTerritorySchema] = Field(description="Top 3 unclaimed content territories")
#     search_volume_analysis: SearchVolumeDataSchema = Field(description="Detailed search volume analysis")
#     competition_landscape: CompetitionAnalysisSchema = Field(description="Comprehensive competition analysis")
#     ai_citation_assessment: AICitationAssessmentSchema = Field(description="AI citation potential assessment")
#     validation_evidence: List[str] = Field(description="Evidence supporting opportunities")

# # Export schemas for use in workflow
CONTENT_GAPS_SCHEMA = ContentGapsAnalysisSchema.model_json_schema()
GAP_VALIDATION_SCHEMA = GapValidationSchema.model_json_schema()
MARKET_OPPORTUNITY_SCHEMA = ContentOpportunityReport.model_json_schema()

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

# Content Gap Analysis Prompts
CONTENT_GAP_ANALYSIS_USER_PROMPT = """
Analyze the following content data to identify content gaps across customer journey stages:

**Our Blog Content Analysis:**
{blog_content_analysis}

**Competitor Content Analysis:**
{competitor_content_analysis}

**Task:**
Identify content gaps where our company is not covering topics that competitors are addressing, or where there are opportunities to provide unique value. Focus on the customer journey stages: AWARENESS, CONSIDERATION, PURCHASE, and RETENTION.

For each stage, identify 2 high-priority content gaps that:
1. Address real user pain points
2. Are being covered by competitors but not by us
3. Align with our company's expertise and positioning
4. Have potential for significant impact

**Analysis Guidelines:**
- Focus on actionable content opportunities
- Consider search intent and user behavior
- Identify gaps that align with our competitive advantages
- Prioritize gaps based on potential impact and feasibility
- Consider both topic gaps and angle gaps (different approaches to similar topics)

Provide your analysis in the structured format specified.
"""

CONTENT_GAP_ANALYSIS_SYSTEM_PROMPT = """
You are an expert content strategist specializing in competitive content analysis and gap identification.

Your role is to analyze content data from both our company and competitors to identify strategic content gaps across the customer journey.

**Customer Journey Stages:**
- **AWARENESS**: Content that helps users recognize they have a problem
- **CONSIDERATION**: Content that helps users evaluate solutions
- **PURCHASE**: Content that helps users make buying decisions
- **RETENTION**: Content that helps users get value and stay engaged

**Gap Identification Criteria:**
1. **Competitive Coverage**: Topics competitors are covering that we're not
2. **User Pain Points**: Real problems users are trying to solve
3. **Strategic Alignment**: Gaps that align with our expertise and positioning
4. **Impact Potential**: Gaps that could significantly impact our content strategy

**Output Format:**
Provide your analysis in the following structured format:
{schema}

Ensure each gap includes:
- Clear title and description
- Specific customer journey stage
- Priority level based on impact and feasibility
- Competitor coverage details
- Specific user pain point addressed
"""

# Reddit Research Validation Prompts
REDDIT_VALIDATION_USER_PROMPT = """
Validate the following content gaps through Reddit research:

**Content Gaps to Validate:**
{content_gaps}

**Task:**
For each content gap, conduct Reddit research to validate:
1. Are users actually asking about these topics?
2. What specific questions are they asking?
3. How frequently are these topics discussed?
4. What pain points are users expressing?
5. Is there genuine demand for content in these areas?

**Research Guidelines:**
- Search Reddit for relevant discussions and questions
- Focus on subreddits relevant to our industry and target audience
- Look for patterns in user questions and pain points
- Assess the volume and quality of discussions
- Identify specific language and terminology users use

**Validation Criteria:**
- User mention frequency
- Question specificity and urgency
- Pain point clarity
- Discussion quality and engagement
- Alignment with our target audience

Provide validation results in the structured format specified.
"""

REDDIT_VALIDATION_SYSTEM_PROMPT = """
You are a research analyst specializing in validating content opportunities through social media research.

Your task is to validate content gaps by researching real user discussions on Reddit to determine if there's genuine demand for content in these areas.

**Research Process:**
1. **Query Generation**: Create relevant Reddit search queries for each gap
2. **Discussion Analysis**: Find and analyze relevant Reddit discussions
3. **Pattern Identification**: Look for common questions, pain points, and language
4. **Validation Scoring**: Assess the importance and urgency of each gap
5. **Evidence Collection**: Gather specific examples and quotes

**Validation Metrics:**
- **User Mentions**: How frequently the topic is discussed
- **User Intent**: What users are trying to accomplish
- **Pain Points**: Specific problems users are facing
- **Question Quality**: Specificity and urgency of questions
- **Audience Alignment**: Relevance to our target audience

**Output Format:**
Provide your validation results in the following structured format:
{schema}

For each gap, provide:
- Specific search queries used
- Quantitative data on mentions and engagement
- Qualitative insights on user intent and pain points
- Validation score (0-10) based on evidence
- Summary of supporting evidence
"""

# Market Opportunity Analysis Prompts
MARKET_OPPORTUNITY_USER_PROMPT = """
Analyze the validated content gaps to identify market opportunities:

**Validated Content Gaps:**
{validated_gaps}

**Task:**
Based on the validated content gaps, identify the top 3 unclaimed content territories that represent the best opportunities for our company. For each territory:

1. **Assess Search Volume**: Estimate monthly search volume for key terms
2. **Evaluate Competition**: Analyze competition difficulty and identify main players
3. **AI Citation Potential**: Assess potential for AI citation and visibility
4. **Right to Win Factors**: Identify our competitive advantages
5. **Opportunity Scoring**: Calculate overall opportunity score

**Analysis Criteria:**
- **Search Volume**: Analyze primary keywords, long-tail opportunities, and seasonal trends
- **Competition**: Assess competitor authority, content quality, and market share distribution
- **AI Citation**: Evaluate citation probability, authority signals, and AI search alignment
- **Right to Win**: Factors that give us competitive advantage
- **Strategic Fit**: Alignment with our expertise and positioning

**Output Format:**
Provide your analysis in the following structured format:
{schema}

**Schema Structure:**
- **top_unclaimed_territories**: List of ContentTerritorySchema objects (max 3)
- **search_volume_analysis**: SearchVolumeDataSchema with lists of KeywordVolumeSchema objects
- **competition_landscape**: CompetitionAnalysisSchema with list of CompetitorScoreSchema objects
- **ai_citation_assessment**: AICitationAssessmentSchema with list of TerritoryCitationSchema objects
- **validation_evidence**: List of evidence strings supporting opportunities

Focus on territories that combine:
- Strong user demand (validated through research)
- Manageable competition
- High AI citation potential
- Clear right to win factors
"""

MARKET_OPPORTUNITY_SYSTEM_PROMPT = """
You are a strategic content analyst specializing in market opportunity assessment and content territory mapping.

Your role is to analyze validated content gaps and identify the most promising content territories for strategic content investment.

**Territory Assessment Framework:**

1. **Search Volume Analysis**
   - Estimate monthly search volume for primary and long-tail keywords
   - Analyze seasonal variations and trends
   - Calculate total monthly volume across all relevant terms
   - Identify keyword opportunities with high volume and low competition
   - Structure as lists of KeywordVolumeSchema objects

2. **Competition Landscape**
   - Identify main competitors in each territory
   - Assess competitor authority scores and content quality ratings
   - Estimate market share distribution among competitors
   - Calculate overall competition difficulty scores (0-1, where 0 = no competition, 1 = extremely competitive)
   - Structure as list of CompetitorScoreSchema objects

3. **AI Citation Potential**
   - Evaluate citation probability for each territory (High/Medium/Low)
   - Identify authority signals that support AI citation
   - Assess required content depth for AI recognition
   - Calculate alignment with AI search patterns (0-1)
   - Structure as list of TerritoryCitationSchema objects

4. **Right to Win Factors**
   - Identify unique competitive advantages
   - Consider expertise, experience, and positioning
   - Assess ability to create differentiated content

5. **Opportunity Scoring**
   - Combine all factors into overall opportunity score (0-10)
   - Weight factors based on strategic importance
   - Consider implementation feasibility

**Output Format:**
Provide your analysis in the following structured format:
{schema}

**Schema Structure:**
- **top_unclaimed_territories**: List of ContentTerritorySchema objects (max 3)
- **search_volume_analysis**: SearchVolumeDataSchema with lists of KeywordVolumeSchema objects
- **competition_landscape**: CompetitionAnalysisSchema with list of CompetitorScoreSchema objects
- **ai_citation_assessment**: AICitationAssessmentSchema with list of TerritoryCitationSchema objects
- **validation_evidence**: List of evidence strings supporting opportunities

Focus on territories that offer the best combination of:
- Validated user demand
- Manageable competition
- High strategic value
- Clear competitive advantages
""" 