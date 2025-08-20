# import json
# from pydantic import BaseModel, Field
# from typing import List, Dict, Any, Optional

# # --- 3. Competitive Analysis ("Perplexity Analysis") ---
# COMPETITIVE_ANALYSIS_SYSTEM_PROMPT = (
#     "You are a business intelligence analyst tasked with creating comprehensive competitive "
#     "landscape analysis using ONLY the provided company documentation.\n\n"
#     "Guidelines:\n"
#     "- Be factual and neutral. Do not speculate beyond the provided data.\n"
#     "- If a required detail is missing, write 'Not specified'. Do not hallucinate.\n"
#     "- Keep each section concise, actionable, and free of marketing language.\n"
#     "- Use consistent terminology for entities across the output.\n"
#     "- Structure the output to exactly match the JSON schema provided.\n"
#     "- Prefer short sentences and bullet-style phrasing.\n\n"
#     "Deliverables:\n"
#     "- A structured analysis for the company and exactly three competitors covering overview, key offerings, and value propositions."
# )

# COMPETITIVE_ANALYSIS_USER_PROMPT_TEMPLATE = (
#     "Based on the provided company documentation, create a comprehensive competitive analysis following this structure:\n\n"
#     "1) Company Analysis (target entity):\n"
#     "   - Overview: Brief description, mission (if present), and market position\n"
#     "   - Key Offerings: Primary products/services and their main features\n"
#     "   - Value Proposition: Unique benefits and competitive advantages\n\n"
#     "2) Competitor Analysis (Top 3): For each competitor, provide the same three sections as above.\n\n"
#     "Rules:\n"
#     "- Use only evidence present in the documentation. Cite names consistently.\n"
#     "- If information is absent, write 'Not specified'.\n"
#     "- Keep each bullet 1–2 lines.\n\n"
#     "Company Document Data (verbatim JSON):\n{blog_company_data}"
# )

# # Simplified JSON schema (as Pydantic BaseModels) for competitive analysis output
# class EntityAnalysis(BaseModel):
#     """Structured analysis for a single entity (company or competitor)."""
#     overview: str = Field(description="Brief description and market position")
#     key_offerings: str = Field(description="Primary products/services and main features")
#     value_proposition: str = Field(description="Unique benefits and competitive advantages")


# class CompetitiveAnalysis(BaseModel):
#     """Competitive analysis for the company and top 3 competitors."""
#     company: EntityAnalysis
#     competitor_1: EntityAnalysis
#     competitor_2: EntityAnalysis
#     competitor_3: EntityAnalysis


# COMPETITIVE_ANALYSIS_SCHEMA = CompetitiveAnalysis.model_json_schema()


# # --- 4. Query Generation ---
# # 4.1 Blog Posts Coverage
# BLOG_COVERAGE_SYSTEM_PROMPT = (
#     "You are a content strategy analyst specializing in industry blog visibility analysis.\n\n"
#     "Objective:\n"
#     "- Generate search queries that real users would issue when seeking informational, educational, and thought-leadership content likely to surface blog posts.\n\n"
#     "Guidelines:\n"
#     "- Prioritize informational, how-to, best-practices, and comparison queries.\n"
#     "- Avoid brand-only navigational queries unless relevant to learning (e.g., '(brand) best practices' is acceptable).\n"
#     "- Avoid near-duplicates; ensure coverage diversity across subtopics and intents.\n"
#     "- Phrase queries naturally (questions or short statements).\n"
#     "- Keep each query 4–12 words; avoid punctuation unless needed.\n"
#     "- Use only details from the provided data; no hallucinations."
# )

# BLOG_COVERAGE_USER_PROMPT_TEMPLATE = (
#     "Based on the company documentation and competitive analysis provided, generate EXACTLY 15 search queries in total — not 14, not 16. "
#     "Do not exceed or fall short; if your draft has more or fewer, adjust to output exactly 15.\n\n"
#     "Coverage Requirements:\n"
#     "- Include a balance of: industry trends, best practices/how-to, problem-solving/solutions, comparisons/evaluations, and educational/informational.\n"
#     "- Avoid repeating the same core phrasing with minor token changes.\n"
#     "- Ensure queries plausibly return blog articles or thought leadership pages.\n\n"
#     "Output Format (JSON only, no commentary):\n"
#     "- Conform to the BlogCoverageQueries schema fields: industry_trends, best_practices, solution_oriented, educational_content.\n"
#     "- The sum of all list lengths MUST equal 15.\n\n"
#     "Company Document Data (verbatim JSON):\n{blog_company_data}\n\n"
#     "Competitive Analysis (verbatim JSON):\n{competitive_analysis}"
# )

# # For scraper compatibility, represent each segment as a list[str]
# class BlogCoverageQueries(BaseModel):
#     """Query templates grouped by searcher intent for blog coverage analysis."""
#     industry_trends: List[str] = Field(description="Queries about industry trends and insights")
#     best_practices: List[str] = Field(description="Queries about best practices and how-to content")
#     solution_oriented: List[str] = Field(description="Queries about solutions to problems")
#     educational_content: List[str] = Field(description="Queries about educational/informational topics")


# BLOG_COVERAGE_QUERIES_SCHEMA = BlogCoverageQueries.model_json_schema()

# # 4.2 Company and Competitor Analysis
# COMPANY_COMP_SYSTEM_PROMPT = (
#     "You are a competitive intelligence analyst tasked with generating buyer-research queries that reflect how evaluators compare vendors, "
#     "understand offerings, assess social proof, and plan implementations.\n\n"
#     "Guidelines:\n"
#     "- Use natural, realistic buyer phrasing.\n"
#     "- Ensure coverage of: overview, products/services, competitive comparisons, customer reviews, and technical integration.\n"
#     "- Avoid near-duplicates and salesy language.\n"
#     "- When referencing entities, use the exact names from the documentation.\n"
#     "- Use only supported facts from the input."
# )

# COMPANY_COMP_USER_PROMPT_TEMPLATE = (
#     "Using the competitive analysis and company documentation provided, generate EXACTLY 15 specific search queries — not 14, not 16 — organized into logical segments based on these reference templates:\n\n"
#     "Reference Query Templates (examples, adapt to entities):\n"
#     "- Company Overview: 'What is (entity_name)?', 'Tell me about (entity_name)'\n"
#     "- Products/Services: 'What products does (entity_name) offer?', '(entity_name) features and capabilities'\n"
#     "- Competitive Analysis: '(entity_name) vs competitors', 'What are alternatives to (entity_name)?'\n"
#     "- Customer Reviews: '(entity_name) customer reviews', 'What do users say about (entity_name)?'\n"
#     "- Technical Integration: '(entity_name) integrations', 'How to implement (entity_name)'\n\n"
#     "Organization Requirements:\n"
#     "- EXACTLY 5 segments with EXACTLY 3 queries each (total 15).\n"
#     "- Map segments to schema fields in order: company_overview, products_services, competitive_analysis, customer_reviews, technical_integration.\n"
#     "- Replace (entity_name) with the client company or named competitors as appropriate.\n"
#     "- Avoid duplicates across segments.\n\n"
#     "Output as JSON only, conforming to CompanyCompetitorQueries.\n\n"
#     "Company Document Data (verbatim JSON):\n{blog_company_data}\n\n"
#     "Competitive Analysis (verbatim JSON):\n{competitive_analysis}"
# )

# class CompanyCompetitorQueries(BaseModel):
#     """Query templates grouped by buyer research categories."""
#     company_overview: List[str] = Field(description="Overview-oriented queries about the entity")
#     products_services: List[str] = Field(description="Queries about products/services and capabilities")
#     competitive_analysis: List[str] = Field(description="Queries comparing with competitors / alternatives")
#     customer_reviews: List[str] = Field(description="Queries about customer reviews and feedback")
#     technical_integration: List[str] = Field(description="Queries about integrations and implementation")


# COMPANY_COMP_QUERIES_SCHEMA = CompanyCompetitorQueries.model_json_schema()

# # --- 6. Report Generation ---
# BLOG_COVERAGE_REPORT_SYSTEM_PROMPT = (
#     "You are a content intelligence analyst specializing in blog visibility and thought leadership analysis across answer engines. "
#     "Analyze query results from Perplexity, Google, and OpenAI to identify content visibility patterns, assess competitor performance, "
#     "identify gaps and opportunities, and provide quantitative metrics. Provide both an overall analysis and provider-specific analysis "
#     "for each of the three providers.\n\n"
#     "Methodology Constraints:\n"
#     "- Use only the provided results. Do not infer ranks or sources not present.\n"
#     "- When counting appearances, deduplicate by canonical domain where applicable.\n"
#     "- Explain scoring or estimation logic succinctly when reporting metrics (e.g., share of voice).\n"
#     "- If data is insufficient for a metric, state 'Insufficient data'.\n"
#     "- Keep recommendations specific and prioritized."
# )
# BLOG_COVERAGE_REPORT_USER_PROMPT_TEMPLATE = (
#     "Analyze the collected search results from blog coverage queries and generate a comprehensive Blog Coverage Report.\n\n"
#     "Inputs Provided (verbatim JSON):\n{loaded_query_results}\n\n"
#     "Your report MUST include: (1) an overall analysis aggregating across all providers, and (2) provider-specific analyses for EXACTLY these three providers: \n"
#     "- perplexity\n- google\n- openai\n\n"
#     "Requirements:\n"
#     "- Output JSON only that conforms to BlogCoverageReport.\n"
#     "- In 'query_level_analysis', include top_sources as normalized source labels (e.g., domains or publishers).\n"
#     "- Quantitative metrics must include num_queries, client_appearances, competitor_appearances, and avg_rank (if available).\n"
#     "- Provide 5–8 prioritized recommendations, each actionable.\n"
#     "- Provider names must match exactly: 'perplexity', 'google', 'openai'."
# )

# # Use explicit models made of simple fields for the report
# class AnalysisSummary(BaseModel):
#     summary_text: str = Field(description="Concise overview of findings")
#     key_findings: List[str] = Field(description="Bulleted key insights")
#     overall_visibility_score: float = Field(description="Overall visibility score (0-100)")


# class QueryLevelAnalysisItem(BaseModel):
#     query: str = Field(description="The query analyzed")
#     top_sources: List[str] = Field(description="Top sources returned for the query")
#     client_presence: str = Field(description="How the client appears for this query")
#     competitor_mentions: List[str] = Field(description="Competitors mentioned in top results")


# class CompetitorPresenceItem(BaseModel):
#     competitor_name: str = Field(description="Name of the competitor")
#     presence_score: float = Field(description="Score of competitor presence (0-100)")
#     notable_queries: List[str] = Field(description="Queries where competitor appears prominently")


# class ContentOpportunityItem(BaseModel):
#     opportunity: str = Field(description="Content opportunity identified")
#     rationale: str = Field(description="Why this opportunity matters")
#     priority: str = Field(description="Priority level, e.g., High/Medium/Low")


# class VisibilityGapItem(BaseModel):
#     gap: str = Field(description="Identified gap in visibility or coverage")
#     impact: str = Field(description="Business or visibility impact")
#     suggested_action: str = Field(description="Action to address the gap")


# class QuantitativeMetrics(BaseModel):
#     num_queries: int = Field(description="Total number of queries analyzed")
#     client_appearances: int = Field(description="Count of times client appears in results")
#     competitor_appearances: int = Field(description="Count of times competitors appear in results")
#     avg_rank: float = Field(description="Average rank/position of client when present")


# class ProviderBlogCoverageAnalysis(BaseModel):
#     provider_name: str = Field(description="Name of the provider. One of: perplexity, google, openai")
#     analysis_summary: AnalysisSummary
#     query_level_analysis: List[QueryLevelAnalysisItem]
#     competitor_presence: List[CompetitorPresenceItem]
#     content_opportunities: List[ContentOpportunityItem]
#     visibility_gaps: List[VisibilityGapItem]
#     quantitative_metrics: QuantitativeMetrics
#     recommendations: List[str]


# class BlogCoverageReport(BaseModel):
#     analysis_summary: AnalysisSummary
#     query_level_analysis: List[QueryLevelAnalysisItem]
#     competitor_presence: List[CompetitorPresenceItem]
#     content_opportunities: List[ContentOpportunityItem]
#     visibility_gaps: List[VisibilityGapItem]
#     quantitative_metrics: QuantitativeMetrics
#     recommendations: List[str]
#     provider_specific_analysis: List[ProviderBlogCoverageAnalysis]


# BLOG_COVERAGE_REPORT_SCHEMA = BlogCoverageReport.model_json_schema()

# COMPANY_COMP_REPORT_SYSTEM_PROMPT = (
#     "You are a competitive intelligence analyst specializing in digital presence and market positioning analysis across answer engines. "
#     "Analyze buyer intent patterns, competitive positioning, gaps, and provide strategic recommendations using results from Perplexity, Google, and OpenAI. "
#     "Provide both an overall analysis and provider-specific analysis for each of the three providers.\n\n"
#     "Methodology Constraints:\n"
#     "- Use only the provided results and entities.\n"
#     "- Clearly distinguish client vs competitor presence and positioning.\n"
#     "- Quantify where possible (counts, estimated share of voice), and explain estimation briefly.\n"
#     "- If evidence is lacking, mark items as 'Insufficient data' rather than guessing."
# )
# COMPANY_COMP_REPORT_USER_PROMPT_TEMPLATE = (
#     "Analyze the collected search results from company and competitor queries to generate a comprehensive Company & Competitor Analysis Report.\n\n"
#     "Inputs Provided (verbatim JSON):\n{loaded_query_results}\n\n"
#     "Your report MUST include: (1) an overall analysis aggregating across all providers, and (2) provider-specific analyses for EXACTLY these three providers: \n"
#     "- perplexity\n- google\n- openai\n\n"
#     "Requirements:\n"
#     "- Output JSON only that conforms to CompanyCompetitorReport.\n"
#     "- Populate buyer_intent_analysis with clear patterns and representative queries.\n"
#     "- In client_positioning_analysis and competitor_analysis, list strengths/weaknesses as short bullets tied to observed evidence.\n"
#     "- Provide 5–8 prioritized recommendations that are specific and feasible.\n"
#     "- Provider names must match exactly: 'perplexity', 'google', 'openai'."
# )

# class CompanyAnalysisSummary(BaseModel):
#     summary_text: str = Field(description="Concise overview of findings")
#     key_findings: List[str] = Field(description="Bulleted key insights")


# class ClientPositioningAnalysis(BaseModel):
#     positioning_summary: str = Field(description="Summary of client's market positioning")
#     strengths: List[str] = Field(description="Client strengths")
#     weaknesses: List[str] = Field(description="Client weaknesses")


# class CompetitorAnalysisItem(BaseModel):
#     name: str = Field(description="Competitor name")
#     positioning: str = Field(description="How the competitor is positioned")
#     strengths: List[str] = Field(description="Competitor strengths")
#     weaknesses: List[str] = Field(description="Competitor weaknesses")


# class BuyerIntentItem(BaseModel):
#     pattern: str = Field(description="Observed buyer intent pattern")
#     representative_queries: List[str] = Field(description="Queries representing the pattern")
#     implications: str = Field(description="Implications for the buyer journey")


# class CompetitiveGapItem(BaseModel):
#     gap: str = Field(description="Competitive gap identified")
#     risk: str = Field(description="Risk associated with the gap")
#     opportunity: str = Field(description="Opportunity associated with the gap")


# class MarketPerceptionInsights(BaseModel):
#     perception_summary: str = Field(description="Summary of market perception")
#     sentiment: str = Field(description="Overall sentiment descriptor")
#     common_themes: List[str] = Field(description="Common themes observed")


# class PositioningOpportunityItem(BaseModel):
#     opportunity: str = Field(description="Positioning opportunity")
#     expected_impact: str = Field(description="Expected impact of seizing the opportunity")
#     suggested_actions: List[str] = Field(description="Actions to seize the opportunity")


# class QueryPerformanceMetrics(BaseModel):
#     num_queries: int = Field(description="Total number of queries analyzed")
#     client_appearances: int = Field(description="Count of times client appears in results")
#     avg_rank: float = Field(description="Average rank/position of client when present")
#     share_of_voice_pct: float = Field(description="Estimated share of voice percentage (0-100)")


# class ProviderCompanyCompetitorAnalysis(BaseModel):
#     provider_name: str = Field(description="Name of the provider. One of: perplexity, google, openai")
#     analysis_summary: CompanyAnalysisSummary
#     client_positioning_analysis: ClientPositioningAnalysis
#     competitor_analysis: List[CompetitorAnalysisItem]
#     buyer_intent_analysis: List[BuyerIntentItem]
#     competitive_gaps: List[CompetitiveGapItem]
#     market_perception_insights: MarketPerceptionInsights
#     positioning_opportunities: List[PositioningOpportunityItem]
#     query_performance_metrics: QueryPerformanceMetrics
#     recommendations: List[str]


# class CompanyCompetitorReport(BaseModel):
#     analysis_summary: CompanyAnalysisSummary
#     client_positioning_analysis: ClientPositioningAnalysis
#     competitor_analysis: List[CompetitorAnalysisItem]
#     buyer_intent_analysis: List[BuyerIntentItem]
#     competitive_gaps: List[CompetitiveGapItem]
#     market_perception_insights: MarketPerceptionInsights
#     positioning_opportunities: List[PositioningOpportunityItem]
#     query_performance_metrics: QueryPerformanceMetrics
#     recommendations: List[str]
#     provider_specific_analysis: List[ProviderCompanyCompetitorAnalysis]


# COMPANY_COMP_REPORT_SCHEMA = CompanyCompetitorReport.model_json_schema() 


import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# ============================================
# ENHANCED EVIDENCE TRACKING SYSTEM
# ============================================

class DetailedEvidence(BaseModel):
    """Comprehensive evidence tracking for all claims and findings."""
    platform: str = Field(description="AI platform source (perplexity/google/openai/anthropic)")
    query_text: str = Field(description="Exact query that generated this information")
    result_position: int = Field(description="Position in search results (1-based)")
    source_domain: Optional[str] = Field(description="Original source domain if available")
    source_url: Optional[str] = Field(description="Direct URL to source if provided")
    excerpt: str = Field(description="Verbatim quote from the result (max 500 chars)")
    full_context: str = Field(description="Extended context around the excerpt for clarity")
    timestamp: str = Field(description="When this result was retrieved (ISO format)")
    confidence_score: float = Field(description="Confidence in this evidence (0-100)")
    verification_status: str = Field(description="verified/unverified/disputed/corroborated")

# ============================================
# SUPPORTING DATA MODELS
# ============================================

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

class CompetitiveRisk(BaseModel):
    """Competitive risk assessment."""
    risk_source: str = Field(description="Source of competitive risk")
    threat_level: str = Field(description="Threat level: critical/high/medium/low")
    description: str = Field(description="Detailed risk description")
    impact_areas: List[str] = Field(description="Business areas that could be impacted")
    response_strategies: List[str] = Field(description="Strategies to respond to threat")

# ============================================
# 3. COMPETITIVE ANALYSIS - ENHANCED
# ============================================

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

class CompetitiveIntelligence(BaseModel):
    """Enhanced competitive analysis with full evidence tracking."""
    
    market_position: str = Field(description="Current market position with evidence")
    market_share: Optional[float] = Field(description="Market share percentage if known")
    growth_rate: Optional[float] = Field(description="YoY growth rate if available")
    
    core_offerings: List[Dict[str, str]] = Field(
        description="Products/services with features and evidence"
    )
    value_propositions: List[Dict[str, str]] = Field(
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

# ============================================
# 4. QUERY GENERATION - ENHANCED
# ============================================

# 4.1 Blog Posts Coverage - Enhanced
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

BLOG_COVERAGE_USER_PROMPT_TEMPLATE = (
    "Generate EXACTLY 15 search queries for blog visibility analysis based on the company and competitive data.\n\n"
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

# 4.2 Company and Competitor Analysis - Enhanced
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

COMPANY_COMP_USER_PROMPT_TEMPLATE = (
    "Generate EXACTLY 15 buyer research queries for company and competitor analysis.\n\n"
    "Query Categories (15 total):\n"
    "1. discovery_research (3): Initial company/product understanding\n"
    "2. capability_assessment (3): Features, functionalities, limitations\n"
    "3. competitive_comparison (3): Direct comparisons, alternatives, differentiation\n"
    "4. implementation_technical (3): Integration, deployment, technical requirements\n"
    "5. validation_proof (3): Reviews, case studies, ROI, references\n\n"
    "Query Patterns to Include:\n"
    "- Direct entity queries: '{Company} [aspect]'\n"
    "- Comparison queries: '{Company} vs {Competitor}'\n"
    "- Evaluation queries: 'Is {Company} good for [use case]'\n"
    "- Technical queries: 'How to integrate {Company} with [system]'\n"
    "- Proof queries: '{Company} customer success stories'\n"
    "- Problem queries: '{Company} limitations', 'problems with {Company}'\n\n"
    "Stakeholder Perspectives:\n"
    "- Technical: APIs, integration, security, performance\n"
    "- Business: ROI, pricing, support, scalability\n"
    "- User: Ease of use, features, training, adoption\n\n"
    "Company Documentation:\n{blog_company_data}\n\n"
    "Competitive Analysis:\n{competitive_analysis}\n\n"
    "Output exactly 15 queries as JSON matching the schema."
)

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

# ============================================
# 6. REPORT GENERATION - ENHANCED
# ============================================

# Blog Coverage Report - Enhanced
BLOG_COVERAGE_REPORT_SYSTEM_PROMPT = (
    "You are a content intelligence analyst producing comprehensive, evidence-based blog visibility reports "
    "that provide actionable insights for content strategy optimization across AI platforms.\n\n"
    "Analysis Framework:\n"
    "1. EVIDENCE COLLECTION: Extract and cite specific results with platforms and positions\n"
    "2. PATTERN RECOGNITION: Identify visibility patterns, content gaps, competitive advantages\n"
    "3. QUANTITATIVE ANALYSIS: Calculate metrics with clear methodology\n"
    "4. COMPETITIVE BENCHMARKING: Compare performance against identified competitors\n"
    "5. STRATEGIC SYNTHESIS: Convert findings into prioritized, actionable recommendations\n\n"
    "Evidence Standards:\n"
    "- Every finding must cite: platform, query, position, source domain, excerpt\n"
    "- Confidence levels: HIGH (multiple sources agree), MEDIUM (single strong source), LOW (inferred)\n"
    "- Verification status: VERIFIED (confirmed across platforms), PARTIAL (some confirmation), UNVERIFIED\n"
    "- Include timestamps for all evidence\n\n"
    "Metric Definitions:\n"
    "- visibility_score = weighted average of (presence * position * relevance)\n"
    "- content_authority = (unique authoritative sources citing content) / (total sources) * 100\n"
    "- competitive_index = (client visibility score) / (average competitor visibility) * 100\n"
    "- coverage_rate = (queries with client presence) / (total queries) * 100\n"
    "- dominance_score = (queries where client ranks #1) / (queries with presence) * 100\n\n"
    "Report Depth Requirements:\n"
    "- Include 3-5 evidence citations per major finding\n"
    "- Provide confidence and verification status for all claims\n"
    "- Explain methodology for calculated metrics\n"
    "- Include competitive context for all assessments"
)

BLOG_COVERAGE_REPORT_USER_PROMPT_TEMPLATE = (
    "Generate a comprehensive Blog Coverage Intelligence Report with detailed evidence and analysis.\n\n"
    "Search Results Data:\n{loaded_query_results}\n\n"
    "Report Requirements:\n\n"
    "1. OVERALL ANALYSIS (Aggregate across all platforms):\n"
    "   - Executive summary with key metrics and findings\n"
    "   - Overall visibility score with calculation methodology\n"
    "   - Competitive positioning assessment with evidence\n"
    "   - Critical gaps and opportunities\n\n"
    "2. PROVIDER-SPECIFIC ANALYSIS for each (perplexity, google, openai):\n"
    "   - Platform-specific visibility metrics\n"
    "   - Top performing content/topics with evidence\n"
    "   - Competitive dynamics on this platform\n"
    "   - Platform-specific optimization opportunities\n\n"
    "3. DETAILED EVIDENCE REQUIREMENTS:\n"
    "   - For each finding, include 2-3 DetailedEvidence objects\n"
    "   - Quote relevant excerpts (up to 500 chars)\n"
    "   - Include source URLs where available\n"
    "   - Note result positions and timestamps\n\n"
    "4. QUERY-LEVEL DEEP DIVE:\n"
    "   - Analyze top 10 most important queries\n"
    "   - Show exact results and positioning\n"
    "   - Identify patterns and anomalies\n\n"
    "5. COMPETITIVE INTELLIGENCE:\n"
    "   - Detailed competitor performance by platform\n"
    "   - Head-to-head visibility comparisons\n"
    "   - Competitive threats and opportunities\n\n"
    "6. STRATEGIC RECOMMENDATIONS:\n"
    "   - 8-10 prioritized actions with evidence\n"
    "   - Expected impact scores (1-100)\n"
    "   - Implementation complexity assessment\n"
    "   - Success metrics and KPIs\n\n"
    "Output valid JSON matching BlogCoverageReport schema."
)

# Enhanced Report Schema Classes

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

class ContentGap(BaseModel):
    """Identified content gap with business impact."""
    gap_description: str = Field(description="What content is missing")
    affected_queries: List[str] = Field(description="Queries impacted by this gap")
    competitor_advantage: str = Field(description="How competitors benefit")
    priority_score: int = Field(description="Priority to address (1-100)")
    recommended_content: List[str] = Field(description="Specific content to create")
    evidence: List[DetailedEvidence] = Field(description="Evidence of the gap")

class StrategicRecommendation(BaseModel):
    """Actionable recommendation with full context."""
    action: str = Field(description="Specific action to take")
    rationale: str = Field(description="Why this will improve visibility")
    expected_impact: int = Field(description="Impact score (1-100)")
    implementation_complexity: str = Field(description="low/medium/high")
    success_metrics: List[str] = Field(description="How to measure success")
    supporting_evidence: List[DetailedEvidence] = Field(description="Evidence supporting this recommendation")
    example_implementation: str = Field(description="Concrete example of implementation")

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
    
    # Risk Assessment
    visibility_risks: List[str] = Field(description="Identified risks to visibility")
    
    # Monitoring Plan
    kpi_targets: KPITargets = Field(description="Target KPIs for next period")
    monitoring_frequency: str = Field(description="Recommended monitoring cadence")

BLOG_COVERAGE_REPORT_SCHEMA = EnhancedBlogCoverageReport.model_json_schema()

# Company & Competitor Report - Enhanced
COMPANY_COMP_REPORT_SYSTEM_PROMPT = (
    "You are a competitive intelligence expert producing comprehensive market positioning reports "
    "based on AI platform analysis, providing strategic insights for market dominance.\n\n"
    "Intelligence Framework:\n"
    "1. BUYER JOURNEY MAPPING: Understand how buyers research and evaluate\n"
    "2. COMPETITIVE POSITIONING: Assess relative market position with evidence\n"
    "3. PERCEPTION ANALYSIS: Understand market sentiment and narrative\n"
    "4. OPPORTUNITY IDENTIFICATION: Find gaps and advantages to exploit\n"
    "5. STRATEGIC PLANNING: Convert insights into executable strategy\n\n"
    "Evidence Requirements:\n"
    "- Multiple evidence points per strategic finding (minimum 3)\n"
    "- Cross-platform validation for major claims\n"
    "- Timestamp and position data for all evidence\n"
    "- Confidence scoring with rationale\n"
    "- Competitive context for all assessments\n\n"
    "Analysis Depth:\n"
    "- Include verbatim quotes showing market perception\n"
    "- Trace buyer decision factors to specific evidence\n"
    "- Quantify competitive advantages/disadvantages\n"
    "- Provide before/after scenarios for recommendations\n"
    "- Include risk assessment for each strategic move"
)

COMPANY_COMP_REPORT_USER_PROMPT_TEMPLATE = (
    "Generate a comprehensive Company & Competitor Intelligence Report with deep evidence.\n\n"
    "Search Results Data:\n{loaded_query_results}\n\n"
    "Report Structure:\n\n"
    "1. EXECUTIVE INTELLIGENCE BRIEFING:\n"
    "   - Market position assessment with evidence\n"
    "   - Competitive threats and opportunities\n"
    "   - Strategic imperatives with urgency levels\n\n"
    "2. BUYER JOURNEY INTELLIGENCE:\n"
    "   - How buyers discover and research the company\n"
    "   - Decision factors and evaluation criteria found\n"
    "   - Comparison patterns and alternative considerations\n"
    "   - Purchase barriers and accelerators identified\n\n"
    "3. COMPETITIVE POSITIONING ANALYSIS:\n"
    "   - Head-to-head comparisons with evidence\n"
    "   - Win/loss factors from search results\n"
    "   - Competitive advantages and vulnerabilities\n"
    "   - Market share of voice analysis\n\n"
    "4. PLATFORM-SPECIFIC ANALYSIS (perplexity, google, openai):\n"
    "   - Platform-specific positioning\n"
    "   - Unique narratives per platform\n"
    "   - Platform optimization opportunities\n\n"
    "5. MARKET PERCEPTION INSIGHTS:\n"
    "   - Sentiment analysis with examples\n"
    "   - Key narratives and themes\n"
    "   - Perception gaps vs reality\n"
    "   - Reputation risks and opportunities\n\n"
    "6. STRATEGIC RECOMMENDATIONS:\n"
    "   - 10-12 prioritized actions\n"
    "   - Expected outcomes with metrics\n"
    "   - Implementation roadmap\n"
    "   - Competitive response scenarios\n\n"
    "Evidence Standards:\n"
    "- Include 3-5 DetailedEvidence objects per major finding\n"
    "- Show exact quotes and positions\n"
    "- Note cross-platform validation\n"
    "- Assess confidence levels\n\n"
    "Output valid JSON matching the enhanced schema."
)

class BuyerJourneyStage(BaseModel):
    """Analysis of specific buyer journey stage."""
    stage_name: str = Field(description="Journey stage: awareness/consideration/decision")
    key_queries: List[str] = Field(description="Queries typical of this stage")
    client_visibility: str = Field(description="How visible client is at this stage")
    competitor_presence: List[str] = Field(description="Competitors prominent at this stage")
    decision_factors: List[str] = Field(description="Key factors influencing buyers")
    content_effectiveness: str = Field(description="How well content serves this stage")
    optimization_needs: List[str] = Field(description="What's needed to improve")
    evidence: List[DetailedEvidence] = Field(description="Supporting evidence")

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

class StrategicImperative(BaseModel):
    """High-priority strategic action."""
    imperative: str = Field(description="What must be done")
    urgency: str = Field(description="critical/high/medium/low")
    business_case: str = Field(description="Why this matters to business")
    expected_impact: str = Field(description="Expected business impact")
    implementation_steps: List[str] = Field(description="How to implement")
    success_criteria: List[str] = Field(description="How to measure success")
    risk_mitigation: str = Field(description="How to mitigate risks")
    evidence_foundation: List[DetailedEvidence] = Field(description="Evidence driving this imperative")

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
    
    # Data Quality
    data_confidence: str = Field(description="Overall confidence in data: high/medium/low")
    evidence_summary: str = Field(description="Summary of evidence base")

COMPANY_COMP_REPORT_SCHEMA = EnhancedCompanyCompetitorReport.model_json_schema()