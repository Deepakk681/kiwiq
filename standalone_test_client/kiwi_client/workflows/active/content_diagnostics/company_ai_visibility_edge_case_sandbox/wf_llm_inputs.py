import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

# =============================================================================
# LLM MODEL CONFIGURATIONS
# =============================================================================
"""Configuration for different LLM models used throughout the workflow steps."""

# LLM Provider, Temperature, Max Tokens by Step, Model Names by Step

# Competitive Analysis (Step 1) - Perplexity
LLM_PROVIDER_FOR_INITITAL_ANALYSIS = "perplexity"
LLM_MODEL_FOR_INITITAL_ANALYSIS = "sonar-pro"
LLM_TEMPERATURE_FOR_INITIAL_ANALYSIS = 0.8
LLM_MAX_TOKENS_FOR_INITIAL_ANALYSIS = 2000

# Query Generation & Report Generation (Steps 2-5) - Anthropic
LLM_PROVIDER_FOR_REPORT = "anthropic"
LLM_MODEL_FOR_REPORT = "claude-sonnet-4-20250514"
LLM_TEMPERATURE_FOR_REPORT = 0.5
LLM_MAX_TOKENS_FOR_REPORT = 5000

# Report generation token limits
MAX_TOKENS_FOR_COVERAGE_REPORT = 10000

# =============================================================================
# SUPPORTING DATA MODELS
# =============================================================================
"""Data models used across multiple workflow steps."""

class DetailedEvidence(BaseModel):
    """Comprehensive evidence tracking for all claims and findings."""
    platform: str = Field(description="AI platform source (perplexity/google/openai/anthropic)")
    query_text: str = Field(description="Exact query that generated this information")
    source_url: Optional[str] = Field(description="Direct URL to source if provided")
    full_context: str = Field(description="Extended context around the excerpt for clarity")

class CitationReason(BaseModel):
    """Citation with reasoning for findings."""
    finding_statement: str = Field(description="The specific finding or claim being made")
    supporting_queries: List[str] = Field(description="Exact queries that led to this finding")
    reasoning: str = Field(description="Why this evidence supports the finding")

class PlatformStrengthMetrics(BaseModel):
    """Platform-specific performance metrics."""
    perplexity: float = Field(description="Performance score on Perplexity (0-100)")
    google: float = Field(description="Performance score on Google (0-100)")
    openai: float = Field(description="Performance score on OpenAI (0-100)")

class KPITargets(BaseModel):
    """Target KPI values for monitoring."""
    visibility_score: float = Field(description="Target visibility score")
    coverage_rate: float = Field(description="Target coverage rate")
    average_position: float = Field(description="Target average position")
    dominance_score: float = Field(description="Target dominance score")
    content_authority: float = Field(description="Target content authority score")
    competitive_index: float = Field(description="Target competitive index")

class KPIDashboard(BaseModel):
    """Current KPI values and targets."""
    visibility_score: float = Field(description="Current visibility score")
    coverage_rate: float = Field(description="Current coverage rate")
    average_position: float = Field(description="Current average position")
    dominance_score: float = Field(description="Current dominance score")
    content_authority: float = Field(description="Current content authority score")
    competitive_index: float = Field(description="Current competitive index")
    market_share_voice: float = Field(description="Current market share of voice")

class CompetitiveDynamics(BaseModel):
    """Competitive dynamics and market analysis."""
    market_trends: List[str] = Field(description="Key market trends identified")
    competitive_intensity: str = Field(description="Level of competitive intensity: high/medium/low")
    market_share_shifts: List[str] = Field(description="Notable market share changes")
    innovation_pace: str = Field(description="Rate of innovation in market: fast/moderate/slow")
    customer_switching_barriers: List[str] = Field(description="Barriers to customer switching")

class ContentOpportunity(BaseModel):
    """Content opportunity with detailed analysis."""
    opportunity_type: str = Field(description="Type of content opportunity")
    description: str = Field(description="Detailed description of opportunity")
    target_queries: List[str] = Field(description="Queries this opportunity would target")
    expected_impact: str = Field(description="Expected impact: high/medium/low")
    implementation_effort: str = Field(description="Implementation effort: high/medium/low")
    priority_score: int = Field(description="Priority score (1-100)")
    source_queries: List[str] = Field(description="Original queries that revealed this opportunity")
    citation_reasoning: CitationReason = Field(description="Citation and reasoning for this opportunity")

class ContentPerformance(BaseModel):
    """Content performance metrics."""
    top_performing_topics: List[str] = Field(description="Best performing content topics")
    underperforming_areas: List[str] = Field(description="Areas needing improvement")
    content_gap_score: float = Field(description="Overall content gap score (0-100)")
    engagement_quality: str = Field(description="Quality of content engagement: high/medium/low")

class ReputationRisk(BaseModel):
    """Reputation risk assessment."""
    risk_type: str = Field(description="Type of reputation risk")
    severity: str = Field(description="Risk severity: critical/high/medium/low")
    description: str = Field(description="Detailed risk description")
    mitigation_strategies: List[str] = Field(description="Strategies to mitigate risk")
    monitoring_indicators: List[str] = Field(description="Key indicators to monitor")
    source_queries: List[str] = Field(description="Queries that revealed this risk")
    citation_reasoning: CitationReason = Field(description="Citation and reasoning for this risk assessment")

class CompetitiveRisk(BaseModel):
    """Competitive risk assessment."""
    risk_source: str = Field(description="Source of competitive risk")
    threat_level: str = Field(description="Threat level: critical/high/medium/low")
    description: str = Field(description="Detailed risk description")
    impact_areas: List[str] = Field(description="Business areas that could be impacted")
    response_strategies: List[str] = Field(description="Strategies to respond to threat")
    source_queries: List[str] = Field(description="Queries that revealed this competitive risk")
    citation_reasoning: CitationReason = Field(description="Citation and reasoning for this risk assessment")

# =============================================================================
# LLM Inputs for Company AI Visibility Edge Case Workflow
# =============================================================================
# Workflow Steps:
# 1. Competitive Analysis
# 2. Blog Coverage Query Generation
# 3. Company Comparison Query Generation
# 4. Blog Coverage Report Generation (AI Visibility & Discovery Analysis)
# 5. Company Comparison Report Generation (Competitive Market Intelligence)

# =============================================================================
# STEP 1: COMPETITIVE ANALYSIS
# =============================================================================
# Description: Analyzes the competitive landscape using Perplexity AI and identifies
# key competitors, market positioning, and competitive dynamics

# System Prompt
COMPETITIVE_ANALYSIS_SYSTEM_PROMPT = (
    "You are a senior competitive intelligence analyst creating comprehensive, evidence-based competitive "
    "landscape analyses using company documentation and market data.\n\n"
    "Core Principles:\n"
    "- EVIDENCE-FIRST: Every statement must cite specific source text with page/section references\n"
    "- QUANTITATIVE: Include metrics, market share, growth rates where available\n"
    "- STRATEGIC: Focus on actionable intelligence, not just descriptions\n"
    "- COMPREHENSIVE: Cover all aspects - products, positioning, strengths, weaknesses, opportunities\n"
    "- TRACEABLE: Enable fact-checking by providing clear source attribution\n\n"
    "Analysis Framework:\n"
    "- Market Context: Size, growth, key trends, regulatory factors\n"
    "- Competitive Dynamics: Direct vs indirect competitors, substitutes, new entrants\n"
    "- Differentiation Analysis: Unique value props, competitive moats, vulnerabilities\n"
    "- Strategic Implications: Threats, opportunities, recommended actions\n\n"
    "Evidence Requirements:\n"
    "- Quote relevant passages verbatim when making claims\n"
    "- Note document section/page for each fact used\n"
    "- Mark confidence level for inferred vs explicit information\n"
    "- Flag any contradictory information found"
)

# User Prompt Template
COMPETITIVE_ANALYSIS_USER_PROMPT_TEMPLATE = (
    "Create a comprehensive, evidence-based competitive analysis using the provided documentation.\n\n"
    "Structure your analysis as follows:\n\n"
    "1) TARGET COMPANY DEEP DIVE:\n"
    "   - Market Position: Current standing, market share if known, growth trajectory\n"
    "   - Core Offerings: Products/services with specific features and benefits\n"
    "   - Value Proposition: Unique selling points with supporting evidence\n"
    "   - Target Segments: Primary customer segments and use cases\n"
    "   - Competitive Advantages: Demonstrable strengths with proof points\n"
    "   - Strategic Challenges: Known weaknesses or gaps\n\n"
    "2) TOP 3 COMPETITORS ANALYSIS:\n"
    "   For each competitor, provide:\n"
    "   - Market Position & Share\n"
    "   - Core Offerings & Differentiation\n"
    "   - Target Market Overlap/Divergence\n"
    "   - Competitive Threats Posed\n"
    "   - Vulnerabilities to Exploit\n"
    "   - Recent Strategic Moves\n\n"
    "3) COMPETITIVE DYNAMICS:\n"
    "   - Head-to-Head Comparisons\n"
    "   - Market Share Trends\n"
    "   - Innovation Comparison\n"
    "   - Customer Perception Differences\n\n"
    "Evidence Requirements:\n"
    "- Every claim must include source_reference with document location\n"
    "- Include confidence_level (high/medium/low) for each analysis point\n"
    "- Provide verbatim quotes for critical claims\n"
    "- Note any information gaps explicitly\n\n"
    "Company Documentation:\n{blog_company_data}\n\n"
    "Output only valid JSON matching the schema."
)

# Variables Used:
# - {blog_company_data}: Company profile information from loaded company document

# Output Schema
class CompetitiveIntelligence(BaseModel):
    """Enhanced competitive analysis with full evidence tracking."""

    market_position: str = Field(description="Current market position with evidence")
    name: str = Field(description="Name of the company")
    market_share: Optional[float] = Field(description="Market share percentage if known")
    growth_rate: Optional[float] = Field(description="YoY growth rate if available")

    core_offerings: List[str] = Field(
        description="Products/services with features and evidence"
    )
    value_propositions: List[str] = Field(
        description="Unique value props with supporting evidence"
    )
    target_segments: List[str] = Field(description="Primary customer segments")

    source_queries: List[str] = Field(description="Queries used to gather this intelligence")
    citation_reasoning: List[CitationReason] = Field(description="Citations and reasoning for key findings")

class EnhancedCompetitiveAnalysis(BaseModel):
    """Comprehensive competitive landscape with evidence."""

    company: CompetitiveIntelligence
    competitor_1: CompetitiveIntelligence
    competitor_2: CompetitiveIntelligence
    competitor_3: CompetitiveIntelligence

    strategic_implications: List[str] = Field(
        description="Key strategic takeaways and recommendations"
    )
    information_gaps: List[str] = Field(
        description="Critical information not available in documentation"
    )

COMPETITIVE_ANALYSIS_SCHEMA = EnhancedCompetitiveAnalysis.model_json_schema()

# =============================================================================
# STEP 2: BLOG COVERAGE QUERY GENERATION
# =============================================================================
# Description: Generates search queries using Three-Category Query Framework to assess
# blog content coverage across AI platforms, focusing on buyer consideration, brand
# perception, and market trends

# System Prompt
BLOG_COVERAGE_SYSTEM_PROMPT = (
    "You are a content intelligence analyst generating queries to gather comprehensive information about "
    "what content gets cited on AI platforms and how companies perform in this space.\n\n"
    "Your mission: Generate queries using a Three-Category Query Framework to gather broad coverage "
    "of existing content performance on AI answer engines like Perplexity, ChatGPT, and Gemini.\n\n"
    "Three-Category Query Framework:\n"
    "- BUYER CONSIDERATION QUERIES: Used to gather information on how prospects evaluate solutions\n"
    "- BRAND PERCEPTION QUERIES: Used to gather information on trust signals, reviews, and reputation indicators\n"
    "- MARKET TREND QUERIES: Used to gather information on emerging topics, industry shifts, and opportunities\n\n"
    "Funnel Coverage Strategy:\n"
    "- TOP-OF-FUNNEL (awareness): Used to gather data on educational, informational, and trend-based content\n"
    "- MID-FUNNEL (consideration): Used to gather information on comparison, evaluation, and decision-support content\n"
    "- BOTTOM-OF-FUNNEL (decision): Used to capture data on implementation, case studies, and proof-point content\n\n"
    "Query Strategy:\n"
    "- Focus on 'how to', 'best practices', 'implementation guide' patterns\n"
    "- Include comparison and benchmark queries for buyer consideration\n"
    "- Target tutorial and educational content queries for awareness\n"
    "- Look for dataset and tool-related searches for decision support\n"
    "- Identify what makes content authoritative for brand perception\n"
    "- Analyze competitor content performance and emerging industry trends\n\n"
    "Generate queries that provide comprehensive coverage of the content landscape."
)

# User Prompt Template
BLOG_COVERAGE_USER_PROMPT_TEMPLATE = (
    "Generate EXACTLY 15 queries using the Three-Category Query Framework to gather comprehensive information "
    "about content performance on AI platforms for a company in their domain.\n\n"
    "Current Date: {current_date}\n\n use this date for the year in the queries"
    "Three-Category Query Distribution (15 total):\n\n"
    "BUYER CONSIDERATION QUERIES (5 queries):\n"
    "- content_performance (2): High-performing content formats, topic effectiveness\n"
    "- decision_support (2): Implementation guides, case studies, proof points\n"
    "- evaluation_criteria (1): What to look for, selection frameworks\n\n"
    "BRAND PERCEPTION QUERIES (5 queries):\n"
    "- trust_signals (2): Reviews, testimonials, reputation indicators\n"
    "- authority_content (2): Expert opinions, thought leadership, industry recognition\n"
    "- credibility_factors (1): What makes companies/solutions better than competitors\n\n"
    "MARKET TREND QUERIES (2 queries):\n"
    "- emerging_topics (2): New trends, rising technologies, future directions\n\n"
    "Funnel Coverage Guidelines:\n"
    "- TOP-OF-FUNNEL (3 queries): Focus on educational, trend, and awareness content\n"
    "- MID-FUNNEL (3 queries): Emphasize comparison, evaluation, and consideration content\n"
    "- BOTTOM-OF-FUNNEL (3 queries): Target implementation, decision, and proof content\n\n"
    "Query Examples by Category:\n\n"
    "Buyer Consideration:\n"
    "- 'most effective [domain] content formats that get cited'\n"
    "- 'best [domain] implementation case studies'\n"
    "- 'how to evaluate [domain] solutions checklist'\n\n"
    "Brand Perception:\n"
    "- '[company] reviews and user experiences'\n"
    "- 'most trusted [domain] experts and thought leaders'\n"
    "- 'what makes [domain] companies reliable'\n\n"
    "Market Trends:\n"
    "- 'emerging trends in [domain] industry 2024'\n"
    "- '[domain] market evolution and future directions'\n\n"
    "Company Context:\n{blog_company_data}\n\n"
    "Competitive Analysis:\n{competitive_analysis}\n\n"
    "Focus on queries that reveal what content formats and topics get consistently cited.\n"
    "Balance across awareness, consideration, and decision stages.\n"
    "Include emerging industry topics and competitive landscape analysis.\n"
    "Generate queries that provide broad coverage of existing content performance.\n"
    "Return only JSON matching the schema."
)

# Variables Used:
# - {current_date}: Current date for temporal context and year in queries
# - {blog_company_data}: Company profile information
# - {competitive_analysis}: Results from competitive analysis

# Output Schema
class EnhancedBlogCoverageQueries(BaseModel):
    """Content-focused query set using Three-Category Query Framework."""

    # Buyer Consideration Queries (5 total)
    content_performance: List[str] = Field(
        description="High-performing content formats, topic effectiveness",
        min_items=2, max_items=2
    )
    decision_support: List[str] = Field(
        description="Implementation guides, case studies, proof points",
        min_items=2, max_items=2
    )
    evaluation_criteria: List[str] = Field(
        description="What to look for, selection frameworks",
        min_items=1, max_items=1
    )

    # Brand Perception Queries (5 total)
    trust_signals: List[str] = Field(
        description="Reviews, testimonials, reputation indicators",
        min_items=2, max_items=2
    )
    authority_content: List[str] = Field(
        description="Expert opinions, thought leadership, industry recognition",
        min_items=2, max_items=2
    )
    credibility_factors: List[str] = Field(
        description="What makes companies/solutions better than competitors",
        min_items=1, max_items=1
    )

    # Market Trend Queries (2 total)
    emerging_topics: List[str] = Field(
        description="New trends, rising technologies, future directions",
        min_items=2, max_items=2
    )
    industry_shifts: List[str] = Field(
        description="Market changes, adoption patterns, evolution",
        min_items=2, max_items=2
    )

BLOG_COVERAGE_QUERIES_SCHEMA = EnhancedBlogCoverageQueries.model_json_schema()

# =============================================================================
# STEP 3: COMPANY COMPARISON QUERY GENERATION
# =============================================================================
# Description: Generates queries using Three-Category Query Framework for competitive
# content intelligence, gathering information about competitor content performance and
# market landscape across the buyer journey

# System Prompt
COMPANY_COMP_SYSTEM_PROMPT = (
    "You are a competitive intelligence analyst using the Three-Category Query Framework to gather "
    "comprehensive information about competitor content performance and market landscape on AI platforms.\n\n"
    "Three-Category Information Gathering Framework:\n"
    "- BUYER CONSIDERATION: Used to gather data on how competitors appear in evaluation and comparison queries\n"
    "- BRAND PERCEPTION: Used to gather information on competitor trust signals, authority, and reputation content\n"
    "- MARKET TRENDS: Used to gather data on emerging topics, industry shifts, and market opportunities\n\n"
    "Funnel-Based Information Collection:\n"
    "- TOP-OF-FUNNEL: Used to gather data on educational content, trend positioning, awareness strategies\n"
    "- MID-FUNNEL: Used to gather information on comparison content, evaluation criteria, consideration approaches\n"
    "- BOTTOM-OF-FUNNEL: Used to gather data on implementation content, proof points, decision support\n\n"
    "Focus on gathering information about:\n"
    "- What competitors publish that gets cited across the buyer journey\n"
    "- Current content performance at each funnel stage\n"
    "- Emerging topics and competitor positioning\n"
    "- Existing differentiation approaches in buyer consideration moments\n"
    "- Current brand perception and trust signal strategies\n"
    "- Existing content performance with high visibility potential\n\n"
    "Generate queries that provide comprehensive coverage of the competitive content landscape."
)

# User Prompt Template
COMPANY_COMP_USER_PROMPT_TEMPLATE = (
    "Generate EXACTLY 15 queries using the Three-Category Query Framework to gather comprehensive information "
    "about competitive content landscape and performance across the buyer journey.\n\n"
    "Current Date: {current_date}\n\n use this date for the year in the queries"
    "Three-Category Query Distribution (15 total):\n\n"
    "BUYER CONSIDERATION QUERIES (5 queries):\n"
    "- competitor_comparisons (2): How competitors stack up in evaluations\n"
    "- evaluation_gaps (2): Comparison content, decision frameworks\n"
    "- consideration_content (1): What prospects need during evaluation\n\n"
    "BRAND PERCEPTION QUERIES (2 queries):\n"
    "- competitor_authority (2): Competitor thought leadership and trust signals\n\n"
    "MARKET TREND QUERIES (2 queries):\n"
    "- emerging_topics (2): New industry trends, rising technologies\n\n"
    "Funnel Coverage Guidelines:\n"
    "- TOP-OF-FUNNEL (3 queries): Educational content, trend positioning, awareness strategies\n"
    "- MID-FUNNEL (3 queries): Comparison content, evaluation approaches, consideration strategies\n"
    "- BOTTOM-OF-FUNNEL (3 queries): Implementation content, proof points, decision support\n\n"
    "Query Examples by Category:\n\n"
    "Buyer Consideration:\n"
    "- '[domain] solution comparison matrix 2024'\n"
    "- 'how to evaluate [domain] vendors checklist'\n"
    "- '[competitor] vs alternatives detailed analysis'\n\n"
    "Brand Perception:\n"
    "- '[competitor] thought leadership and expertise'\n"
    "- 'most trusted [domain] companies and why'\n"
    "- '[domain] industry authority and credibility signals'\n\n"
    "Market Trends:\n"
    "- 'emerging [domain] technologies and trends 2024'\n"
    "- '[domain] industry evolution next 2-3 years'\n\n"
    "Company Context:\n{blog_company_data}\n\n"
    "Competitive Analysis:\n{competitive_analysis}\n\n"
    "Generate queries specific to the company's domain and competitive landscape.\n"
    "Focus on gathering comprehensive information about existing content performance across all funnel stages.\n"
    "Include emerging industry topics and competitor positioning strategies.\n"
    "Generate queries that provide broad coverage of the competitive content landscape.\n"
    "Output exactly 9 queries as JSON."
)

# Variables Used:
# - {current_date}: Current date for temporal context and year in queries
# - {blog_company_data}: Company profile information
# - {competitive_analysis}: Competitive analysis results

# Output Schema
class EnhancedCompanyCompetitorQueries(BaseModel):
    """Competitive content intelligence query set using Three-Category Framework."""

    # Buyer Consideration Queries (5 total)
    competitor_comparisons: List[str] = Field(
        description="How competitors stack up in evaluations",
        min_items=2, max_items=2
    )
    evaluation_gaps: List[str] = Field(
        description="Comparison content, decision frameworks",
        min_items=2, max_items=2
    )
    consideration_content: List[str] = Field(
        description="What prospects need during evaluation",
        min_items=1, max_items=1
    )

    # Brand Perception Queries (2 total)
    competitor_authority: List[str] = Field(
        description="Competitor thought leadership and trust signals",
        min_items=2, max_items=2
    )

    # Market Trend Queries (2 total)
    emerging_topics: List[str] = Field(
        description="New industry trends, rising technologies",
        min_items=2, max_items=2
    )

COMPANY_COMP_QUERIES_SCHEMA = EnhancedCompanyCompetitorQueries.model_json_schema()

# =============================================================================
# STEP 4: BLOG COVERAGE REPORT GENERATION (AI VISIBILITY & DISCOVERY ANALYSIS)
# =============================================================================
# Description: Conducts comprehensive AI visibility and discovery analysis based on
# search results from multiple platforms, analyzing which content dominates AI responses,
# competitive positioning, content theme performance, and brand trust

# System Prompt
BLOG_COVERAGE_REPORT_SYSTEM_PROMPT = (
    "You are an AI visibility analyst conducting comprehensive analysis of how content performs "
    "across AI platforms and what this reveals about market positioning and competitive dynamics.\n\n"
    "Core Analysis Framework:\n"
    "- AI VISIBILITY ANALYSIS: Which content dominates AI responses with citation frequency as performance proxy\n"
    "- COMPETITIVE POSITIONING: How AI positions brands against each other in head-to-head scenarios\n"
    "- CONTENT THEME PERFORMANCE: Which topics and content clusters consistently appear in AI responses\n"
    "- FUNNEL COVERAGE INTELLIGENCE: How well different buyer journey stages are represented\n"
    "- BRAND PERCEPTION INSIGHTS: How AI characterizes brand authority, trust, and credibility\n\n"
    "Evidence Requirements:\n"
    "- Every finding must include specific citations from query results\n"
    "- Quantify citation frequencies and response patterns where possible\n"
    "- Document exact AI responses and source attributions\n"
    "- Map content performance across different AI platforms\n"
    "- Track brand mentions and competitive comparisons\n\n"
    "Focus on data-driven insights about current market positioning, not implementation recommendations."
)

# User Prompt Template
BLOG_COVERAGE_REPORT_USER_PROMPT_TEMPLATE = (
    "Conduct comprehensive AI visibility and discovery analysis using the provided search results.\n\n"
    "Search Results:\n{loaded_query_results}\n\n"
    "Generate an analytical report covering:\n\n"
    "1. AI VISIBILITY & DISCOVERY INTELLIGENCE:\n"
    "   - Which specific content pieces (yours and competitors') AI systems frequently cite\n"
    "   - Citation frequency analysis as performance proxy\n"
    "   - Content gaps where your brand is absent but should be present\n"
    "   - Platform-specific citation patterns\n\n"
    "2. COMPETITIVE POSITIONING MATRIX:\n"
    "   - Head-to-head brand comparisons in AI responses\n"
    "   - Strength/weakness mapping for each competitor\n"
    "   - How AI characterizes each brand's unique value proposition\n"
    "   - Market perception differences across brands\n\n"
    "3. CONTENT THEME PERFORMANCE DASHBOARD:\n"
    "   - High-performing topics/clusters that consistently appear\n"
    "   - Funnel stage effectiveness (awareness vs consideration vs decision)\n"
    "   - Topic opportunity identification where no brand dominates\n"
    "   - Content format performance analysis\n\n"
    "4. FUNNEL COVERAGE INTELLIGENCE:\n"
    "   - Query distribution analysis across buyer journey stages\n"
    "   - How AI guides users through the conversion pathway\n"
    "   - Critical content gaps for buyer questions\n"
    "   - Stage-specific performance metrics\n\n"
    "5. BRAND TRUST & PERCEPTION INSIGHTS:\n"
    "   - AI responses to trust-related queries about each brand\n"
    "   - Review sentiment analysis from AI responses\n"
    "   - Credibility factors AI uses to establish brand authority\n"
    "   - Reputation risk indicators\n\n"
    "Evidence Requirements:\n"
    "- Include specific quotes and citations from search results\n"
    "- Quantify patterns with citation counts where possible\n"
    "- Reference exact AI platform responses\n"
    "- Document source URLs and query contexts\n\n"
    "Focus on current market positioning insights with proper citations.\n"
    "Output JSON matching the schema."
)

# Variables Used:
# - {loaded_query_results}: Search results from blog coverage queries across multiple platforms

# Output Schema
class AuthorityBacklinkAnalysis(BaseModel):
    """Analysis of competitor authority site citations and PR strategy."""
    authority_sites_found: List[str] = Field(
        description="High authority domains where competitors are cited (e.g., techcrunch.com, forbes.com)",
        max_items=8
    )
    competitor_citation_patterns: List[str] = Field(
        description="How competitors are mentioned on authority sites",
        max_items=6
    )
    pr_strategy_insights: List[str] = Field(
        description="Insights about competitor PR/outreach strategies",
        max_items=5
    )
    missed_opportunities: List[str] = Field(
        description="Authority sites where client could potentially get coverage",
        max_items=4
    )

class FunnelStagePerformance(BaseModel):
    """Performance metrics by funnel stage."""
    awareness: int = Field(description="Citations in awareness stage")
    consideration: int = Field(description="Citations in consideration stage")
    decision: int = Field(description="Citations in decision stage")

class TrustScoreIndicator(BaseModel):
    """Trust score indicator with value."""
    indicator_name: str = Field(description="Name of trust indicator")
    indicator_value: str = Field(description="Value or description of trust signal")

class CitationPattern(BaseModel):
    """Citation pattern by content type."""
    content_type: str = Field(description="Type of content")
    citation_count: int = Field(description="Number of citations")

class BrandPerformanceRanking(BaseModel):
    """Brand performance ranking on platform."""
    brand_name: str = Field(description="Brand name")
    ranking_position: int = Field(description="Ranking position (1=best)")

class ContentFormatPerformance(BaseModel):
    """Content format performance metrics."""
    format_name: str = Field(description="Content format type")
    citation_count: int = Field(description="Number of citations")

class PlatformPerformance(BaseModel):
    """Platform-specific performance metrics."""
    platform_name: str = Field(description="AI platform name")
    performance_description: str = Field(description="Performance description")

class PositioningAdvantage(BaseModel):
    """Brand positioning advantage."""
    advantage_area: str = Field(description="Area of advantage")
    advantage_description: str = Field(description="Description of advantage")

class InnovationLeadership(BaseModel):
    """Innovation leadership mapping."""
    innovation_area: str = Field(description="Area of innovation")
    leading_brand: str = Field(description="Brand leading in this area")

class AIVisibilityContent(BaseModel):
    """Content analysis for AI platform visibility."""
    content_title: str = Field(description="Specific content title or piece")
    content_source: str = Field(description="Brand/company that created it")
    citation_frequency: int = Field(description="Number of times cited across platforms")
    platforms_citing: List[str] = Field(description="AI platforms that cite this content", max_items=5)
    content_type: str = Field(description="Format: blog/whitepaper/case_study/tutorial/research")
    query_contexts: List[str] = Field(description="Types of queries where this appears", max_items=5)
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence and citations", max_items=3)

class ContentGapAnalysis(BaseModel):
    """Analysis of content gaps in AI responses."""
    gap_topic: str = Field(description="Topic area with gap")
    query_types: List[str] = Field(description="Query types revealing this gap", max_items=3)
    current_leaders: List[str] = Field(description="Brands currently filling this space", max_items=3)
    gap_severity: str = Field(description="critical/high/medium/low")
    citation_evidence: CitationReason = Field(description="Evidence for this gap")

class CompetitivePositioning(BaseModel):
    """Head-to-head competitive analysis from AI responses."""
    competitor_name: str = Field(description="Competitor brand name")
    positioning_description: str = Field(description="How AI characterizes this brand")
    strength_areas: List[str] = Field(description="Areas where AI positions them as strong", max_items=4)
    weakness_areas: List[str] = Field(description="Areas where AI positions them as weak", max_items=4)
    unique_value_props: List[str] = Field(description="Unique value propositions cited by AI", max_items=3)
    head_to_head_comparisons: List[str] = Field(description="Direct comparison results", max_items=3)
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting citations", max_items=3)

class ContentThemePerformance(BaseModel):
    """Performance analysis of content themes."""
    theme_name: str = Field(description="Content theme or topic cluster")
    citation_volume: int = Field(description="Total citations across platforms")
    funnel_stage_performance: FunnelStagePerformance = Field(description="Citations by funnel stage")
    dominant_brands: List[str] = Field(description="Brands dominating this theme", max_items=3)
    content_formats: List[str] = Field(description="Most cited content formats for this theme", max_items=4)
    opportunity_level: str = Field(description="high/medium/low opportunity for new entrants")
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=3)

class FunnelCoverageAnalysis(BaseModel):
    """Buyer journey coverage analysis."""
    funnel_stage: str = Field(description="awareness/consideration/decision")
    query_distribution: float = Field(description="Percentage of queries in this stage")
    content_coverage_score: float = Field(description="How well this stage is covered (0-100)")
    leading_content_types: List[str] = Field(description="Most effective content types", max_items=4)
    coverage_gaps: List[str] = Field(description="Specific gaps in coverage", max_items=4)
    conversion_pathways: List[str] = Field(description="How AI guides users through this stage", max_items=3)
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting citations", max_items=3)

class BrandTrustPerception(BaseModel):
    """Brand trust and perception analysis from AI responses."""
    brand_name: str = Field(description="Brand being analyzed")
    trust_score_indicators: List[TrustScoreIndicator] = Field(description="Trust signals AI references", max_items=6)
    review_sentiment_summary: str = Field(description="Overall sentiment in AI responses about reviews")
    credibility_factors: List[str] = Field(description="Factors AI uses to establish authority", max_items=5)
    reputation_risks: List[str] = Field(description="Potential reputation risks identified", max_items=3)
    trust_comparison_ranking: int = Field(description="Relative trust ranking among competitors (1=highest)")
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=4)

class PlatformSpecificInsights(BaseModel):
    """Platform-specific content performance insights."""
    platform_name: str = Field(description="AI platform name")
    citation_patterns: List[CitationPattern] = Field(description="Citation patterns by content type", max_items=8)
    preferred_content_formats: List[str] = Field(description="Most cited formats on this platform", max_items=4)
    unique_characteristics: List[str] = Field(description="Platform-specific behavior patterns", max_items=3)
    brand_performance_ranking: List[BrandPerformanceRanking] = Field(description="Brand performance ranking on this platform", max_items=6)

class AIVisibilityDiscoveryReport(BaseModel):
    """Comprehensive AI Visibility & Discovery Analysis Report."""

    # Executive Summary
    executive_summary: str = Field(description="Key findings and market positioning insights")
    overall_visibility_score: float = Field(description="Overall AI visibility score (0-100)")

    # 1. AI Visibility & Discovery Intelligence
    winning_content_analysis: List[AIVisibilityContent] = Field(
        description="Content that dominates AI responses",
        max_items=8
    )
    content_gap_analysis: List[ContentGapAnalysis] = Field(
        description="Areas where brand is absent but should be present",
        max_items=6
    )
    platform_specific_insights: List[PlatformSpecificInsights] = Field(
        description="Platform-specific citation patterns",
        max_items=4
    )

    # 2. Competitive Positioning Matrix
    competitive_positioning: List[CompetitivePositioning] = Field(
        description="Head-to-head competitive analysis",
        max_items=5
    )
    market_perception_summary: str = Field(description="Overall market perception landscape")

    # 3. Content Theme Performance Dashboard
    theme_performance: List[ContentThemePerformance] = Field(
        description="High-performing content themes",
        max_items=6
    )

    # 4. Funnel Coverage Intelligence
    funnel_coverage: List[FunnelCoverageAnalysis] = Field(
        description="Buyer journey coverage analysis",
        min_items=3, max_items=3
    )

    # 5. Brand Trust & Perception Insights
    brand_trust_analysis: List[BrandTrustPerception] = Field(
        description="Trust and credibility analysis for each brand",
        max_items=5
    )

    # 6. Authority Site Analysis
    authority_backlink_analysis: AuthorityBacklinkAnalysis = Field(
        description="Analysis of competitor authority site citations and PR strategy"
    )

BLOG_COVERAGE_REPORT_SCHEMA = AIVisibilityDiscoveryReport.model_json_schema()

# =============================================================================
# STEP 5: COMPANY COMPARISON REPORT GENERATION (COMPETITIVE MARKET INTELLIGENCE)
# =============================================================================
# Description: Conducts comprehensive competitive market intelligence analysis based on
# search results, analyzing competitive positioning, market trends, brand authority,
# content strategy effectiveness, and market opportunities

# System Prompt
COMPANY_COMP_REPORT_SYSTEM_PROMPT = (
    "You are a competitive market intelligence analyst conducting comprehensive analysis of competitive "
    "positioning, market dynamics, and brand perception based on AI platform responses and market data.\n\n"
    "Core Analysis Framework:\n"
    "- COMPETITIVE POSITIONING MATRIX: How brands are positioned relative to each other in AI responses\n"
    "- MARKET TREND INTELLIGENCE: Emerging topics, market shifts, and future opportunity predictions\n"
    "- BRAND PERCEPTION ANALYSIS: How AI characterizes each brand's authority, trust, and credibility\n"
    "- CONTENT STRATEGY EFFECTIVENESS: Which competitive content strategies are winning in AI citations\n"
    "- MARKET OPPORTUNITY MAPPING: Where gaps exist and which brands are best positioned to fill them\n\n"
    "Evidence Requirements:\n"
    "- Every insight must include specific citations from AI platform responses\n"
    "- Quantify competitive dynamics with citation patterns and response frequencies\n"
    "- Document exact brand positioning language used by AI systems\n"
    "- Track market perception shifts and competitive momentum indicators\n"
    "- Map content performance across different competitive scenarios\n\n"
    "Focus on strategic market intelligence about current competitive landscape and positioning dynamics."
)

# User Prompt Template
COMPANY_COMP_REPORT_USER_PROMPT_TEMPLATE = (
    "Conduct comprehensive competitive market intelligence analysis using the provided search results.\n\n"
    "Search Results:\n{loaded_query_results}\n\n"
    "Generate a strategic market intelligence report covering:\n\n"
    "1. COMPETITIVE POSITIONING MATRIX:\n"
    "   - How AI positions each brand relative to others in head-to-head scenarios\n"
    "   - Unique positioning language and value propositions AI uses for each brand\n"
    "   - Competitive strength/weakness mapping across key areas\n"
    "   - Market share of voice analysis in AI responses\n\n"
    "2. MARKET TREND INTELLIGENCE:\n"
    "   - Emerging topics gaining AI attention and citation volume\n"
    "   - Market evolution patterns and trajectory analysis\n"
    "   - Future opportunity predictions based on trend analysis\n"
    "   - Technology and industry shift indicators\n\n"
    "3. BRAND PERCEPTION & AUTHORITY ANALYSIS:\n"
    "   - How AI characterizes each brand's expertise and authority\n"
    "   - Trust and credibility signals AI references for each competitor\n"
    "   - Reputation risk and opportunity indicators\n"
    "   - Brand differentiation factors in AI responses\n\n"
    "4. CONTENT STRATEGY EFFECTIVENESS:\n"
    "   - Which competitive content strategies are winning in AI citations\n"
    "   - Content format and topic performance across competitors\n"
    "   - Citation volume and frequency patterns\n"
    "   - Platform-specific competitive performance\n\n"
    "5. MARKET OPPORTUNITY MAPPING:\n"
    "   - Underserved market segments and topic areas\n"
    "   - Competitive gaps and white space opportunities\n"
    "   - Brand positioning advantages and disadvantages\n"
    "   - Market entry and expansion opportunities\n\n"
    "6. COMPETITIVE DYNAMICS ANALYSIS:\n"
    "   - Market momentum indicators and trajectory shifts\n"
    "   - Competitive threat assessment\n"
    "   - Innovation leadership patterns\n"
    "   - Customer switching and preference signals\n\n"
    "Evidence Requirements:\n"
    "- Include specific quotes and citations from search results\n"
    "- Quantify competitive patterns with citation frequencies\n"
    "- Reference exact AI platform responses and positioning language\n"
    "- Document source URLs and query contexts\n\n"
    "Focus on strategic intelligence about competitive positioning and market dynamics.\n"
    "Output JSON matching the schema."
)

# Variables Used:
# - {loaded_query_results}: Search results from company comparison queries across multiple platforms

# Output Schema
class CompetitiveBrandPositioning(BaseModel):
    """Detailed competitive positioning analysis from AI responses."""
    brand_name: str = Field(description="Brand name")
    ai_positioning_language: str = Field(description="How AI typically describes this brand")
    unique_value_propositions: List[str] = Field(description="Unique value props cited by AI", max_items=4)
    competitive_strengths: List[str] = Field(description="Areas where AI positions brand as strong", max_items=4)
    competitive_weaknesses: List[str] = Field(description="Areas where AI identifies weaknesses", max_items=4)
    head_to_head_results: List[str] = Field(description="Results in direct comparisons", max_items=4)
    market_share_voice: float = Field(description="Percentage of relevant AI responses mentioning this brand")
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=3)

class MarketTrendIntelligence(BaseModel):
    """Market trend and opportunity analysis."""
    trend_topic: str = Field(description="Emerging trend or topic area")
    citation_growth_rate: float = Field(description="Growth rate in AI citations/mentions")
    market_evolution_stage: str = Field(description="early/emerging/growing/mature/declining")
    leading_brands: List[str] = Field(description="Brands leading in this trend", max_items=3)
    opportunity_level: str = Field(description="high/medium/low opportunity for new entrants")
    future_trajectory: str = Field(description="Predicted future direction")
    technology_shift_indicators: List[str] = Field(description="Key technology shift signals", max_items=3)
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=3)

class BrandAuthorityAnalysis(BaseModel):
    """Brand authority and perception analysis."""
    brand_name: str = Field(description="Brand name")
    authority_characterization: str = Field(description="How AI characterizes brand's expertise")
    trust_signals: List[str] = Field(description="Trust and credibility factors AI references", max_items=5)
    expertise_areas: List[str] = Field(description="Areas where AI recognizes expertise", max_items=4)
    reputation_risks: List[str] = Field(description="Potential reputation vulnerabilities", max_items=3)
    differentiation_factors: List[str] = Field(description="Key differentiation points", max_items=4)
    authority_ranking: int = Field(description="Relative authority ranking among competitors (1=highest)")
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=4)

class ContentStrategyEffectiveness(BaseModel):
    """Analysis of competitive content strategy performance."""
    brand_name: str = Field(description="Brand name")
    winning_content_strategies: List[str] = Field(description="Most effective content approaches", max_items=4)
    content_format_performance: List[ContentFormatPerformance] = Field(description="Citation counts by content format", max_items=8)
    topic_dominance_areas: List[str] = Field(description="Topics where brand dominates", max_items=4)
    platform_performance: List[PlatformPerformance] = Field(description="Performance by AI platform", max_items=4)
    citation_volume_trend: str = Field(description="increasing/stable/decreasing")
    content_gaps: List[str] = Field(description="Areas lacking content", max_items=3)
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=3)

class MarketOpportunityMapping(BaseModel):
    """Market opportunity and competitive gap analysis."""
    opportunity_area: str = Field(description="Market segment or topic area")
    opportunity_size: str = Field(description="large/medium/small market opportunity")
    current_leaders: List[str] = Field(description="Brands currently leading this area", max_items=3)
    competitive_gaps: List[str] = Field(description="Specific gaps in competitive coverage", max_items=4)
    entry_barriers: List[str] = Field(description="Barriers to entry in this area", max_items=3)
    positioning_advantages: List[PositioningAdvantage] = Field(description="Brand advantages for this opportunity", max_items=5)
    market_entry_feasibility: str = Field(description="easy/moderate/difficult")
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=3)

class CompetitiveDynamicsAnalysis(BaseModel):
    """Analysis of competitive dynamics and market momentum."""
    market_momentum_indicators: List[str] = Field(description="Key momentum shift signals", max_items=4)
    competitive_threats: List[str] = Field(description="Emerging competitive threats", max_items=4)
    innovation_leadership: List[InnovationLeadership] = Field(description="Innovation leadership by brand/area", max_items=6)
    customer_preference_signals: List[str] = Field(description="Customer switching/preference indicators", max_items=4)
    market_consolidation_trends: List[str] = Field(description="Consolidation or fragmentation signals", max_items=3)
    disruption_potential: str = Field(description="high/medium/low potential for market disruption")
    citation_evidence: List[DetailedEvidence] = Field(description="Supporting evidence", max_items=3)

class CompetitiveMarketIntelligenceReport(BaseModel):
    """Comprehensive Competitive Market Intelligence Analysis Report."""

    # Executive Summary
    executive_summary: str = Field(description="Key competitive intelligence findings")
    competitive_landscape_overview: str = Field(description="Overall competitive landscape assessment")

    # 1. Competitive Positioning Matrix
    competitive_positioning: List[CompetitiveBrandPositioning] = Field(
        description="Head-to-head competitive positioning analysis",
        max_items=6
    )
    positioning_summary: str = Field(description="Overall positioning dynamics summary")

    # 2. Market Trend Intelligence
    market_trends: List[MarketTrendIntelligence] = Field(
        description="Emerging trends and market evolution analysis",
        max_items=6
    )
    future_opportunities: str = Field(description="Future opportunity predictions")

    # 3. Brand Perception & Authority Analysis
    brand_authority: List[BrandAuthorityAnalysis] = Field(
        description="Brand authority and perception analysis",
        max_items=6
    )

    # 4. Content Strategy Effectiveness
    content_strategy_analysis: List[ContentStrategyEffectiveness] = Field(
        description="Competitive content strategy performance",
        max_items=6
    )

    # 5. Market Opportunity Mapping
    market_opportunities: List[MarketOpportunityMapping] = Field(
        description="Market opportunities and competitive gaps",
        max_items=6
    )

    # 6. Competitive Dynamics Analysis
    competitive_dynamics: CompetitiveDynamicsAnalysis = Field(
        description="Market momentum and competitive dynamics"
    )

    # 7. Authority Site Analysis
    authority_backlink_analysis: AuthorityBacklinkAnalysis = Field(
        description="Analysis of competitor authority site citations and PR strategy"
    )

COMPANY_COMP_REPORT_SCHEMA = CompetitiveMarketIntelligenceReport.model_json_schema()