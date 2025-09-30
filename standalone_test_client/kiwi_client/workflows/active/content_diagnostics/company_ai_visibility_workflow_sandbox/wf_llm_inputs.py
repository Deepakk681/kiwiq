import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
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
MAX_TOKENS_FOR_COVERAGE_REPORT = 10000

# =============================================================================
# SUPPORTING DATA MODELS
# =============================================================================
"""Data models used across multiple workflow steps."""

class DetailedEvidence(BaseModel):
    """Comprehensive evidence tracking for all claims and findings."""
    platform: str = Field(description="AI platform source (perplexity/google/openai)")
    query_text: str = Field(description="Exact query that generated this information")
    result_position: int = Field(description="Position in search results (1-based)")
    source_domain: Optional[str] = Field(description="Original source domain if available")
    source_url: Optional[str] = Field(description="Direct URL to source if provided")
    full_context: str = Field(description="Extended context around the excerpt for clarity")
    confidence_score: float = Field(description="Confidence in this evidence (0-100)")

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
    source_queries: List[str] = Field(description="Original queries that revealed this opportunity")

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

class CompetitiveRisk(BaseModel):
    """Competitive risk assessment."""
    risk_source: str = Field(description="Source of competitive risk")
    threat_level: str = Field(description="Threat level: critical/high/medium/low")
    description: str = Field(description="Detailed risk description")
    impact_areas: List[str] = Field(description="Business areas that could be impacted")
    response_strategies: List[str] = Field(description="Strategies to respond to threat")
    source_queries: List[str] = Field(description="Queries that revealed this competitive risk")

# =============================================================================
# LLM Inputs for Company AI Visibility Workflow
# =============================================================================
# Workflow Steps:
# 1. Competitive Analysis
# 2. Blog Coverage Query Generation
# 3. Company Comparison Query Generation
# 4. Blog Coverage Report Generation
# 5. Company Comparison Report Generation

# =============================================================================
# STEP 1: COMPETITIVE ANALYSIS
# =============================================================================
# Description: Performs initial competitive analysis using Perplexity AI to analyze
# company positioning against competitors, identify key differentiators and market position

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
    market_share: Optional[float] = Field(description="Market share percentage if known")
    growth_rate: Optional[float] = Field(description="YoY growth rate if available")

    core_offerings: List[str] = Field(
        description="Products/services with features and evidence"
    )
    value_propositions: List[str] = Field(
        description="Unique value props with supporting evidence"
    )
    target_segments: List[str] = Field(description="Primary customer segments")

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
# Description: Generates queries to test blog content visibility in AI responses,
# creates targeted queries based on company's blog topics incorporating competitive
# analysis insights

# System Prompt
BLOG_COVERAGE_SYSTEM_PROMPT = (
    "You are a content intelligence strategist specializing in thought leadership visibility optimization.\n\n"
    "Your mission: Generate authentic search queries that reflect real user behavior when seeking "
    "educational content, industry insights, and thought leadership that would surface blog posts.\n\n"
    "Query Generation Framework:\n"
    "- INTENT MAPPING: Align queries to information-seeking, problem-solving, and learning intents\n"
    "- FUNNEL COVERAGE: Include awareness, consideration, and decision-stage queries\n"
    "- NATURAL LANGUAGE: Mirror actual user search patterns on AI platforms\n"
    "- TOPIC DIVERSITY: Cover technical, strategic, and industry-trend angles\n"
    "- COMPETITIVE CONTEXT: Include comparison and alternative-seeking queries\n\n"
    "Query Quality Criteria:\n"
    "- Specificity: Precise enough to return relevant content\n"
    "- Authenticity: Phrases real users would actually type\n"
    "- Coverage: No redundant variations, maximum topic breadth\n"
    "- Length: 4-15 words reflecting natural search behavior\n"
    "- Mix: Questions (40%), how-to (30%), comparisons (20%), trends (10%)"
)

# User Prompt Template
BLOG_COVERAGE_USER_PROMPT_TEMPLATE = (
    "Generate EXACTLY 15 search queries for blog visibility analysis based on the company and competitive data.\n\n"
    "Current Date: {current_date}\n\n"
    "Query Distribution Requirements:\n"
    "- industry_insights (3-4): Trends, market analysis, future predictions\n"
    "- educational_guides (3-4): How-to, tutorials, best practices, frameworks\n"
    "- problem_solutions (3-4): Challenge-focused, troubleshooting, optimization\n"
    "- thought_leadership (2-3): Opinion pieces, strategic perspectives, innovation\n"
    "- comparative_analysis (1-2): Versus content, alternatives, decision criteria\n\n"
    "Query Construction Rules:\n"
    "1. Mix query formats:\n"
    "   - Questions: 'How do I...', 'What is the best way to...', 'Why should...'\n"
    "   - Statements: 'guide to...', 'best practices for...', 'trends in...'\n"
    "   - Comparisons: 'X vs Y for...', 'alternatives to...', 'choosing between...'\n\n"
    "2. Include industry-specific terminology from the documentation\n"
    "3. Vary specificity levels (broad industry to specific use cases)\n"
    "4. Consider different user personas (technical, business, strategic)\n"
    "5. Total must equal EXACTLY 15 queries\n\n"
    "Company Documentation:\n{blog_company_data}\n\n"
    "Competitive Analysis:\n{competitive_analysis}\n\n"
    "Return only JSON matching the schema."
)

# Variables Used:
# - {current_date}: Current date for temporal context
# - {blog_company_data}: Company profile information
# - {competitive_analysis}: Results from competitive analysis

# Output Schema
class EnhancedBlogCoverageQueries(BaseModel):
    """Comprehensive query set for blog visibility analysis."""

    industry_insights: List[str] = Field(
        description="Queries about industry trends, market analysis, future predictions",
        min_items=2, max_items=3
    )
    educational_guides: List[str] = Field(
        description="How-to guides, tutorials, best practices, implementation frameworks",
        min_items=2, max_items=3
    )
    problem_solutions: List[str] = Field(
        description="Problem-solving, troubleshooting, optimization queries",
        min_items=2, max_items=3
    )
    thought_leadership: List[str] = Field(
        description="Strategic perspectives, innovation, industry opinions",
        min_items=2, max_items=3
    )
    comparative_analysis: List[str] = Field(
        description="Comparison queries, alternatives, decision criteria",
        min_items=2, max_items=3
    )

BLOG_COVERAGE_QUERIES_SCHEMA = EnhancedBlogCoverageQueries.model_json_schema()

# =============================================================================
# STEP 3: COMPANY COMPARISON QUERY GENERATION
# =============================================================================
# Description: Generates queries to compare company against competitors in AI responses,
# tests how AI engines position the company in the market and evaluates relative
# visibility and positioning

# System Prompt
COMPANY_COMP_SYSTEM_PROMPT = (
    "You are a buyer intelligence analyst generating queries that reflect real buyer research patterns "
    "during vendor evaluation and competitive assessment processes.\n\n"
    "Buyer Journey Mapping:\n"
    "- AWARENESS: Initial discovery and understanding queries\n"
    "- CONSIDERATION: Feature comparison and capability assessment\n"
    "- EVALUATION: Deep-dive technical and implementation queries\n"
    "- VALIDATION: Social proof and risk assessment queries\n"
    "- DECISION: Final comparison and selection criteria\n\n"
    "Query Authenticity Requirements:\n"
    "- Use actual buyer language and concerns\n"
    "- Include both high-level and technical queries\n"
    "- Reflect different stakeholder perspectives\n"
    "- Consider risk and compliance angles\n"
    "- Include ROI and value validation queries"
)

# User Prompt Template
COMPANY_COMP_USER_PROMPT_TEMPLATE = (
    "Generate EXACTLY 15 buyer research queries for company and competitor analysis.\n\n"
    "Query Categories (15 total):\n"
    "1. discovery_research (3): Initial company/product understanding\n"
    "2. capability_assessment (3): Features, functionalities, limitations\n"
    "3. competitive_comparison (3): Direct comparisons, alternatives, differentiation\n"
    "4. implementation_technical (3): Integration, deployment, technical requirements\n"
    "5. validation_proof (3): Reviews, case studies, ROI, references\n\n"
    "Query Patterns to Include:\n"
    "- Direct entity queries: 'Company [aspect]'\n"
    "- Comparison queries: 'Company vs Competitor'\n"
    "- Evaluation queries: 'Is Company good for [use case]'\n"
    "- Technical queries: 'How to integrate Company with [system]'\n"
    "- Proof queries: 'Company customer success stories'\n"
    "- Problem queries: 'Company limitations', 'problems with Company'\n\n"
    "Stakeholder Perspectives:\n"
    "- Technical: APIs, integration, security, performance\n"
    "- Business: ROI, pricing, support, scalability\n"
    "- User: Ease of use, features, training, adoption\n\n"
    "Company Documentation:\n{blog_company_data}\n\n"
    "Competitive Analysis:\n{competitive_analysis}\n\n"
    "Output exactly 15 queries as JSON matching the schema."
)

# Variables Used:
# - {blog_company_data}: Company profile information
# - {competitive_analysis}: Competitive analysis results

# Output Schema
class EnhancedCompanyCompetitorQueries(BaseModel):
    """Buyer journey query set for company evaluation."""

    discovery_research: List[str] = Field(
        description="Initial discovery and understanding queries",
        min_items=3, max_items=3
    )
    capability_assessment: List[str] = Field(
        description="Feature and functionality evaluation queries",
        min_items=3, max_items=3
    )
    competitive_comparison: List[str] = Field(
        description="Direct comparison and alternative queries",
        min_items=3, max_items=3
    )
    implementation_technical: List[str] = Field(
        description="Technical integration and deployment queries",
        min_items=3, max_items=3
    )
    validation_proof: List[str] = Field(
        description="Social proof, reviews, and validation queries",
        min_items=3, max_items=3
    )

COMPANY_COMP_QUERIES_SCHEMA = EnhancedCompanyCompetitorQueries.model_json_schema()

# =============================================================================
# STEP 4: BLOG COVERAGE REPORT GENERATION
# =============================================================================
# Description: Analyzes blog coverage query results from AI engines and generates
# comprehensive report on how well blog content appears in AI responses, identifies
# coverage gaps and opportunities

# System Prompt
BLOG_COVERAGE_REPORT_SYSTEM_PROMPT = (
    "You are a content intelligence analyst producing comprehensive, evidence-based blog visibility reports "
    "that provide actionable insights for content strategy optimization across AI platforms.\n\n"
    "CRITICAL REQUIREMENT - QUERY CITATION MANDATE:\n"
    "- EVERY finding, insight, problem, opportunity, or recommendation MUST include the exact queries that revealed it\n"
    "- NO statement should be made without listing the specific search queries used as evidence\n"
    "- Include source_queries field for every major finding\n"
    "- Populate citation_reasoning with clear connections between queries and conclusions\n\n"
    "Analysis Framework:\n"
    "1. EVIDENCE COLLECTION: Extract and cite specific results with platforms, positions, and EXACT QUERIES\n"
    "2. PATTERN RECOGNITION: Identify visibility patterns, content gaps, competitive advantages WITH QUERY SOURCES\n"
    "3. QUANTITATIVE ANALYSIS: Calculate metrics with clear methodology and SUPPORTING QUERIES\n"
    "4. COMPETITIVE BENCHMARKING: Compare performance against identified competitors WITH QUERY EVIDENCE\n"
    "5. STRATEGIC SYNTHESIS: Convert findings into prioritized, actionable recommendations WITH QUERY CITATIONS\n\n"
    "Evidence Standards:\n"
    "- Every finding must cite: platform, query, position, source domain, excerpt, AND original search queries\n"
    "- Confidence levels: HIGH (multiple sources agree), MEDIUM (single strong source), LOW (inferred)\n"
    "- Verification status: VERIFIED (confirmed across platforms), PARTIAL (some confirmation), UNVERIFIED\n"
    "- Include timestamps for all evidence\n"
    "- List the exact queries that led to each conclusion in source_queries fields\n\n"
    "Metric Definitions:\n"
    "- visibility_score = weighted average of (presence * position * relevance)\n"
    "- content_authority = (unique authoritative sources citing content) / (total sources) * 100\n"
    "- competitive_index = (client visibility score) / (average competitor visibility) * 100\n"
    "- coverage_rate = (queries with client presence) / (total queries) * 100\n"
    "- dominance_score = (queries where client ranks #1) / (queries with presence) * 100\n\n"
    "Report Depth Requirements:\n"
    "- Include 3-5 evidence citations per major finding WITH QUERY SOURCES\n"
    "- Provide confidence and verification status for all claims\n"
    "- Explain methodology for calculated metrics\n"
    "- Include competitive context for all assessments\n"
    "- MANDATORY: Every insight must trace back to specific queries that revealed it"
)

# User Prompt Template
BLOG_COVERAGE_REPORT_USER_PROMPT_TEMPLATE = (
    "Generate a comprehensive Blog Coverage Intelligence Report with detailed evidence and analysis.\n\n"
    "Search Results Data:\n{loaded_query_results}\n\n"
    "MANDATORY QUERY CITATION REQUIREMENTS:\n"
    "- For EVERY finding, gap, opportunity, threat, or recommendation, you MUST specify the exact queries that revealed it\n"
    "- Fill source_queries fields with the specific search queries used\n"
    "- Complete citation_reasoning fields explaining how the queries led to each conclusion\n"
    "- NO insight should be provided without clear query traceability\n"
    "- When mentioning competitor advantages, list the queries that showed this\n"
    "- When identifying content gaps, specify which queries revealed the gaps\n\n"
    "Report Requirements:\n\n"
    "1. OVERALL ANALYSIS (Aggregate across all platforms):\n"
    "   - Executive summary with key metrics and findings + SOURCE QUERIES\n"
    "   - Overall visibility score with calculation methodology + SUPPORTING QUERIES\n"
    "   - Competitive positioning assessment with evidence + QUERY SOURCES\n"
    "   - Critical gaps and opportunities + REVEALING QUERIES\n\n"
    "2. PROVIDER-SPECIFIC ANALYSIS for each (perplexity, google, openai):\n"
    "   - Platform-specific visibility metrics + MEASUREMENT QUERIES\n"
    "   - Top performing content/topics with evidence + SOURCE QUERIES\n"
    "   - Competitive dynamics on this platform + ANALYSIS QUERIES\n"
    "   - Platform-specific optimization opportunities + OPPORTUNITY QUERIES\n\n"
    "3. DETAILED EVIDENCE REQUIREMENTS:\n"
    "   - For each finding, include 2-3 DetailedEvidence objects WITH ORIGINAL QUERIES\n"
    "   - Quote relevant excerpts (up to 500 chars) + QUERY THAT FOUND IT\n"
    "   - Include source URLs where available + SEARCH QUERY USED\n"
    "   - Note result positions and timestamps + EXACT QUERY TEXT\n\n"
    "4. QUERY-LEVEL DEEP DIVE:\n"
    "   - Analyze top 10 most important queries WITH RESULTS BREAKDOWN\n"
    "   - Show exact results and positioning FOR EACH QUERY\n"
    "   - Identify patterns and anomalies ACROSS QUERIES\n"
    "   - Explain what each query reveals about visibility\n\n"
    "5. COMPETITIVE INTELLIGENCE:\n"
    "   - Detailed competitor performance by platform + ANALYSIS QUERIES\n"
    "   - Head-to-head visibility comparisons + COMPARISON QUERIES\n"
    "   - Competitive threats and opportunities + THREAT-REVEALING QUERIES\n\n"
    "6. STRATEGIC RECOMMENDATIONS:\n"
    "   - 5-7 prioritized actions with evidence + SUPPORTING QUERIES\n"
    "   - Expected impact scores (1-100) + IMPACT-INDICATING QUERIES\n"
    "   - Implementation complexity assessment + COMPLEXITY-REVEALING QUERIES\n"
    "   - Success metrics and KPIs + MEASUREMENT QUERIES\n\n"
    "CRITICAL: Every content_gaps, content_opportunities, competitive_analysis, and recommendations object MUST have:\n"
    "- source_queries: List of exact queries that revealed this insight\n"
    "- citation_reasoning: Clear explanation of how the queries support the finding\n\n"
    "Output valid JSON matching BlogCoverageReport schema."
)

# Variables Used:
# - {loaded_query_results}: Results from AI engine queries on blog coverage

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

class VisibilityMetrics(BaseModel):
    """Comprehensive visibility metrics with methodology."""
    visibility_score: float = Field(description="Overall visibility score (0-100)")
    calculation_method: str = Field(description="How the score was calculated")
    coverage_rate: float = Field(description="% of queries with presence")
    average_position: float = Field(description="Average position when present")
    dominance_score: float = Field(description="% of #1 rankings when present")
    content_authority: float = Field(description="Authority score based on sources")
    competitive_index: float = Field(description="Performance vs competitors (100 = average)")

class QueryAnalysis(BaseModel):
    """Deep analysis of individual query performance."""
    query: str = Field(description="The analyzed query")
    platforms_present: List[str] = Field(description="Platforms where client appears")
    best_position: int = Field(description="Best position achieved")
    client_presence: str = Field(description="How client appears in results")
    competitor_dynamics: List[str] = Field(description="Competitor positioning")
    content_type: str = Field(description="Type of content surfaced")
    optimization_opportunity: str = Field(description="How to improve for this query")
    supporting_evidence: List[DetailedEvidence] = Field(description="Evidence for findings")

class CompetitorPerformance(BaseModel):
    """Detailed competitor performance analysis."""
    competitor_name: str
    visibility_score: float = Field(description="Competitor's visibility score")
    queries_dominated: List[str] = Field(description="Queries where competitor ranks #1")
    content_advantages: List[str] = Field(description="Content areas where competitor excels")
    platform_strength: PlatformStrengthMetrics = Field(description="Performance by platform")
    competitive_threats: List[str] = Field(description="Specific threats posed")
    evidence_samples: List[DetailedEvidence] = Field(description="Supporting evidence")
    analysis_queries: List[str] = Field(description="Queries used to analyze this competitor")

class ContentGap(BaseModel):
    """Identified content gap with business impact."""
    gap_description: str = Field(description="What content is missing")
    affected_queries: List[str] = Field(description="Queries impacted by this gap")
    competitor_advantage: str = Field(description="How competitors benefit")
    priority_score: int = Field(description="Priority to address (1-100)")
    recommended_content: List[str] = Field(description="Specific content to create")
    evidence: List[DetailedEvidence] = Field(description="Evidence of the gap")
    source_queries: List[str] = Field(description="Original queries that revealed this gap")

class StrategicRecommendation(BaseModel):
    """Actionable recommendation with full context."""
    action: str = Field(description="Specific action to take")
    rationale: str = Field(description="Why this will improve visibility")
    expected_impact: int = Field(description="Impact score (1-100)")
    implementation_complexity: str = Field(description="low/medium/high")
    success_metrics: List[str] = Field(description="How to measure success")
    supporting_evidence: List[DetailedEvidence] = Field(description="Evidence supporting this recommendation")
    example_implementation: str = Field(description="Concrete example of implementation")
    source_queries: List[str] = Field(description="Queries that led to this recommendation")

class PlatformBlogAnalysis(BaseModel):
    """Platform-specific blog visibility analysis."""
    platform: str = Field(description="Platform name: perplexity/google/openai")
    metrics: VisibilityMetrics
    top_performing_queries: List[QueryAnalysis] = Field(description="Best performing queries")
    content_gaps: List[ContentGap] = Field(description="Platform-specific gaps")
    competitive_landscape: List[CompetitorPerformance] = Field(description="Competitor performance")
    optimization_priorities: List[str] = Field(description="Platform-specific priorities")
    unique_insights: List[str] = Field(description="Insights unique to this platform")

class EnhancedBlogCoverageReport(BaseModel):
    """Comprehensive blog coverage intelligence report."""

    # Executive Summary
    executive_summary: str = Field(description="High-level findings and key takeaways")
    report_confidence: str = Field(description="Overall confidence in findings: high/medium/low")
    data_quality_assessment: str = Field(description="Assessment of data completeness and quality")

    # Overall Metrics
    overall_metrics: VisibilityMetrics

    # Detailed Query Analysis
    query_performance: List[QueryAnalysis] = Field(
        description="Performance analysis for each query"
    )

    # Competitive Intelligence
    competitive_analysis: List[CompetitorPerformance] = Field(
        description="Detailed competitor performance"
    )

    # Content Strategy
    content_gaps: List[ContentGap] = Field(
        description="Identified content gaps with impact"
    )

    content_opportunities: List[ContentOpportunity] = Field(
        description="Content opportunities identified"
    )

    # Platform-Specific Analysis
    platform_analyses: List[PlatformBlogAnalysis] = Field(
        description="Detailed analysis per platform"
    )

    # Strategic Recommendations
    recommendations: List[StrategicRecommendation] = Field(
        description="Prioritized strategic recommendations",
        min_items=5, max_items=7
    )

    # Authority Site Analysis
    authority_backlink_analysis: AuthorityBacklinkAnalysis = Field(
        description="Analysis of competitor authority site citations and PR strategy"
    )

    # Risk Assessment
    visibility_risks: List[str] = Field(description="Identified risks to visibility")

    # Monitoring Plan
    kpi_targets: KPITargets = Field(description="Target KPIs for next period")
    monitoring_frequency: str = Field(description="Recommended monitoring cadence")

BLOG_COVERAGE_REPORT_SCHEMA = EnhancedBlogCoverageReport.model_json_schema()

# =============================================================================
# STEP 5: COMPANY COMPARISON REPORT GENERATION
# =============================================================================
# Description: Analyzes company comparison results from AI engines and generates
# competitive report evaluating company's positioning vs competitors, identifies
# competitive advantages and weaknesses, provides strategic recommendations

# System Prompt
COMPANY_COMP_REPORT_SYSTEM_PROMPT = (
    "You are a competitive intelligence expert producing comprehensive market positioning reports "
    "based on AI platform analysis, providing strategic insights for market dominance.\n\n"
    "CRITICAL REQUIREMENT - QUERY CITATION MANDATE:\n"
    "- EVERY finding, insight, threat, opportunity, or strategic recommendation MUST include the exact queries that revealed it\n"
    "- NO analysis should be made without listing the specific search queries used as evidence\n"
    "- Include source_queries or analysis_queries fields for every major finding\n"
    "- Populate citation_reasoning with clear connections between queries and strategic conclusions\n"
    "- When identifying buyer journey patterns, specify which queries revealed each stage\n"
    "- When assessing competitive positioning, list the queries that showed relative strengths/weaknesses\n\n"
    "Intelligence Framework:\n"
    "1. BUYER JOURNEY MAPPING: Understand how buyers research and evaluate WITH QUERY EVIDENCE\n"
    "2. COMPETITIVE POSITIONING: Assess relative market position with evidence AND SUPPORTING QUERIES\n"
    "3. PERCEPTION ANALYSIS: Understand market sentiment and narrative WITH PERCEPTION QUERIES\n"
    "4. OPPORTUNITY IDENTIFICATION: Find gaps and advantages to exploit WITH OPPORTUNITY QUERIES\n"
    "5. STRATEGIC PLANNING: Convert insights into executable strategy WITH STRATEGIC QUERIES\n\n"
    "Evidence Requirements:\n"
    "- Multiple evidence points per strategic finding (minimum 3) WITH ORIGINAL QUERIES\n"
    "- Cross-platform validation for major claims WITH VALIDATING QUERIES\n"
    "- Timestamp and position data for all evidence WITH SOURCE QUERIES\n"
    "- Confidence scoring with rationale AND QUERY SUPPORT\n"
    "- Competitive context for all assessments WITH COMPARISON QUERIES\n\n"
    "Analysis Depth:\n"
    "- Include verbatim quotes showing market perception WITH ORIGINATING QUERIES\n"
    "- Trace buyer decision factors to specific evidence AND REVEALING QUERIES\n"
    "- Quantify competitive advantages/disadvantages WITH MEASUREMENT QUERIES\n"
    "- Provide before/after scenarios for recommendations WITH SUPPORTING QUERIES\n"
    "- Include risk assessment for each strategic move WITH RISK-INDICATING QUERIES"
)

# User Prompt Template
COMPANY_COMP_REPORT_USER_PROMPT_TEMPLATE = (
    "Generate a comprehensive Company & Competitor Intelligence Report with deep evidence.\n\n"
    "Search Results Data:\n{loaded_query_results}\n\n"
    "MANDATORY QUERY CITATION REQUIREMENTS:\n"
    "- For EVERY strategic finding, competitive insight, buyer journey pattern, or recommendation, you MUST specify the exact queries that revealed it\n"
    "- Fill analysis_queries, positioning_queries, perception_queries, and driving_queries fields\n"
    "- Complete citation_reasoning fields explaining how the queries led to each strategic conclusion\n"
    "- NO strategic insight should be provided without clear query traceability\n"
    "- When identifying competitive threats, list the queries that revealed the threat\n"
    "- When analyzing buyer journey stages, specify which queries showed each stage behavior\n"
    "- When assessing market perception, list the queries that revealed sentiment\n\n"
    "Report Structure:\n\n"
    "1. EXECUTIVE INTELLIGENCE BRIEFING:\n"
    "   - Market position assessment with evidence + ASSESSMENT QUERIES\n"
    "   - Competitive threats and opportunities + THREAT-REVEALING QUERIES\n"
    "   - Strategic imperatives with urgency levels + IMPERATIVE-DRIVING QUERIES\n\n"
    "2. BUYER JOURNEY INTELLIGENCE:\n"
    "   - How buyers discover and research the company + DISCOVERY QUERIES\n"
    "   - Decision factors and evaluation criteria found + DECISION QUERIES\n"
    "   - Comparison patterns and alternative considerations + COMPARISON QUERIES\n"
    "   - Purchase barriers and accelerators identified + BARRIER/ACCELERATOR QUERIES\n\n"
    "3. COMPETITIVE POSITIONING ANALYSIS:\n"
    "   - Head-to-head comparisons with evidence + COMPARISON QUERIES\n"
    "   - Win/loss factors from search results + WIN/LOSS QUERIES\n"
    "   - Competitive advantages and vulnerabilities + ADVANTAGE/VULNERABILITY QUERIES\n"
    "   - Market share of voice analysis + VOICE-SHARE QUERIES\n\n"
    "4. PLATFORM-SPECIFIC ANALYSIS (perplexity, google, openai):\n"
    "   - Platform-specific positioning + POSITIONING QUERIES\n"
    "   - Unique narratives per platform + NARRATIVE QUERIES\n"
    "   - Platform optimization opportunities + OPPORTUNITY QUERIES\n\n"
    "5. MARKET PERCEPTION INSIGHTS:\n"
    "   - Sentiment analysis with examples + SENTIMENT QUERIES\n"
    "   - Key narratives and themes + NARRATIVE QUERIES\n"
    "   - Perception gaps vs reality + GAP-REVEALING QUERIES\n"
    "   - Reputation risks and opportunities + RISK/OPPORTUNITY QUERIES\n\n"
    "6. STRATEGIC RECOMMENDATIONS:\n"
    "   - 10-12 prioritized actions + SUPPORTING QUERIES\n"
    "   - Expected outcomes with metrics + OUTCOME-INDICATING QUERIES\n"
    "   - Implementation roadmap + IMPLEMENTATION QUERIES\n"
    "   - Competitive response scenarios + RESPONSE-SCENARIO QUERIES\n\n"
    "Evidence Standards:\n"
    "- Include 3-5 DetailedEvidence objects per major finding WITH ORIGINAL QUERIES\n"
    "- Show exact quotes and positions WITH SOURCE QUERIES\n"
    "- Note cross-platform validation WITH VALIDATING QUERIES\n"
    "- Assess confidence levels WITH CONFIDENCE-SUPPORTING QUERIES\n\n"
    "CRITICAL: Every buyer_journey_analysis, competitive_positioning, market_perception, strategic_imperatives, reputation_risks, and competitive_risks object MUST have:\n"
    "- Appropriate query fields (analysis_queries, positioning_queries, perception_queries, driving_queries, etc.)\n"
    "- citation_reasoning: Clear explanation of how the queries support the strategic finding\n\n"
    "Output valid JSON matching the enhanced schema."
)

# Variables Used:
# - {loaded_query_results}: Company comparison query results from AI engines

# Output Schema
class BuyerJourneyStage(BaseModel):
    """Analysis of specific buyer journey stage."""
    stage_name: str = Field(description="Journey stage: awareness/consideration/decision")
    key_queries: List[str] = Field(description="Queries typical of this stage")
    client_visibility: str = Field(description="How visible client is at this stage")
    competitor_presence: List[str] = Field(description="Competitors prominent at this stage")
    decision_factors: List[str] = Field(description="Key factors influencing buyers")
    optimization_needs: List[str] = Field(description="What's needed to improve")
    evidence: List[DetailedEvidence] = Field(description="Supporting evidence")
    analysis_queries: List[str] = Field(description="Specific queries used to analyze this stage")

class CompetitivePositioning(BaseModel):
    """Detailed competitive positioning analysis."""
    competitor_name: str
    relative_strength: float = Field(description="Strength vs client (0-100)")
    head_to_head_wins: List[str] = Field(description="Where competitor wins")
    head_to_head_losses: List[str] = Field(description="Where client wins")
    differentiation_factors: List[str] = Field(description="Key differentiators")
    market_narrative: str = Field(description="How market perceives comparison")
    threat_level: str = Field(description="high/medium/low threat assessment")
    counter_strategies: List[str] = Field(description="How to counter this competitor")
    evidence_base: List[DetailedEvidence] = Field(description="Evidence for analysis")

class MarketPerception(BaseModel):
    """Market perception and sentiment analysis."""
    overall_sentiment: str = Field(description="positive/neutral/negative/mixed")
    sentiment_score: float = Field(description="Sentiment score (-100 to +100)")
    key_narratives: List[str] = Field(description="Main stories about company")
    perception_strengths: List[str] = Field(description="Positive perceptions")
    perception_weaknesses: List[str] = Field(description="Negative perceptions")
    narrative_examples: List[DetailedEvidence] = Field(description="Example narratives")
    perception_gaps: List[str] = Field(description="Gaps between reality and perception")
    narrative_opportunities: List[str] = Field(description="Opportunities to shape narrative")
    perception_queries: List[str] = Field(description="Queries used to assess market perception")

class StrategicImperative(BaseModel):
    """High-priority strategic action."""
    imperative: str = Field(description="What must be done")
    implementation_steps: List[str] = Field(description="How to implement")
    success_criteria: List[str] = Field(description="How to measure success")
    evidence_foundation: List[DetailedEvidence] = Field(description="Evidence driving this imperative")
    driving_queries: List[str] = Field(description="Queries that revealed the need for this imperative")

class PlatformCompanyAnalysis(BaseModel):
    """Platform-specific company analysis."""
    platform: str
    visibility_metrics: VisibilityMetrics
    positioning_narrative: str = Field(description="How company is positioned")
    competitive_landscape: List[CompetitivePositioning]
    unique_challenges: List[str] = Field(description="Platform-specific challenges")
    optimization_priorities: List[str] = Field(description="Platform-specific priorities")
    content_performance: ContentPerformance = Field(description="Content performance metrics")

class EnhancedCompanyCompetitorReport(BaseModel):
    """Comprehensive company and competitor intelligence report."""

    # Executive Briefing
    executive_briefing: str = Field(description="C-suite level strategic summary")
    market_position_score: float = Field(description="Overall market position (0-100)")
    competitive_threat_level: str = Field(description="Overall threat assessment")

    # Buyer Journey Intelligence
    buyer_journey_analysis: List[BuyerJourneyStage] = Field(
        description="Analysis by buyer journey stage"
    )
    purchase_drivers: List[str] = Field(description="Key factors driving purchase decisions")
    purchase_barriers: List[str] = Field(description="Barriers preventing purchase")

    # Competitive Intelligence
    competitive_positioning: List[CompetitivePositioning] = Field(
        description="Detailed competitive analysis"
    )
    market_share_voice: float = Field(description="Estimated share of voice (0-100)")
    competitive_advantages: List[str] = Field(description="Sustainable competitive advantages")
    competitive_vulnerabilities: List[str] = Field(description="Exploitable vulnerabilities")

    # Market Perception
    market_perception: MarketPerception

    # Platform-Specific Analysis
    platform_analyses: List[PlatformCompanyAnalysis] = Field(
        description="Analysis per platform"
    )

    # Strategic Imperatives
    strategic_imperatives: List[StrategicImperative] = Field(
        description="Priority strategic actions",
        min_items=10, max_items=12
    )

    # Authority Site Analysis
    authority_backlink_analysis: AuthorityBacklinkAnalysis = Field(
        description="Analysis of competitor authority site citations and PR strategy"
    )

    # Risk Assessment
    reputation_risks: List[ReputationRisk] = Field(
        description="Identified reputation risks with severity"
    )
    competitive_risks: List[CompetitiveRisk] = Field(
        description="Competitive threats requiring monitoring"
    )

    # Success Metrics
    kpi_dashboard: KPIDashboard = Field(
        description="Current KPIs and targets"
    )
    monitoring_triggers: List[str] = Field(
        description="Events requiring immediate action"
    )

COMPANY_COMP_REPORT_SCHEMA = EnhancedCompanyCompetitorReport.model_json_schema()