"""
LLM inputs for deep research content strategy workflow including schemas and prompt templates.
"""

from typing import List, Dict, Any, Optional
import json

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# --- Schema Definitions ---

class SuccessfulContentPatternSchema(BaseModel):
    """Individual successful content pattern"""
    pattern: str = Field(description="Pattern description")
    why_it_works: str = Field(description="Explanation of why this pattern is effective")
    industry_adoption: str = Field(description="Level of industry adoption (high/medium/low)")

class IndustryBestPracticesSchema(BaseModel):
    """Industry best practices analysis (flattened)"""
    educational_content_pct: float = Field(description="Percentage of educational content in the mix")
    thought_leadership_pct: float = Field(description="Percentage of thought leadership content in the mix")
    product_focused_pct: float = Field(description="Percentage of product-focused content in the mix")
    comparative_content_pct: float = Field(description="Percentage of comparative content in the mix")
    industry_insights_pct: float = Field(description="Percentage of industry insights content in the mix")
    successful_content_patterns: List[SuccessfulContentPatternSchema] = Field(description="List of successful content patterns identified")




class ContentFormatStrategySchema(BaseModel):
    """Individual content format strategy"""
    format: str = Field(description="Content format type")
    content_type: str = Field(description="Content type classification")
    strategic_purpose: str = Field(description="Why this format works at this stage")
    stage_share_pct: float = Field(description="Percentage share within this stage")
    effectiveness_score: int = Field(description="Effectiveness score (1-5)")
    typical_content_depth: str = Field(description="Typical content depth level")
    industry_benchmark_performance: str = Field(description="Performance relative to industry benchmark")

class TopicCategorySchema(BaseModel):
    """Individual topic category"""
    category: str = Field(description="Broad topic category")
    priority_level: int = Field(description="Priority level (1-5)")
    content_volume_recommendation: str = Field(description="Recommended content volume")
    example_topics: List[str] = Field(description="Example topics within this category")

class FunnelStageAnalysisSchema(BaseModel):
    """Complete analysis for a single funnel stage (flattened)"""
    stage: str = Field(description="Funnel stage name")
    business_impact_score: int = Field(description="Business impact score (1-5)")
    reach_potential_score: int = Field(description="Reach potential score (1-5)")
    industry_priority_level: int = Field(description="Industry priority level (1-5)")
    recommended_share_pct: float = Field(description="Recommended percentage allocation for this stage")
    rationale: str = Field(description="Why this allocation based on industry best practices")
    primary_personas: List[str] = Field(description="Primary personas for this stage")
    user_intent: str = Field(description="What users are trying to accomplish at this stage")
    content_consumption_context: str = Field(description="How/when they typically consume content")
    content_format_strategy: List[ContentFormatStrategySchema] = Field(description="Content format strategies for this stage")
    topic_categories: List[TopicCategorySchema] = Field(description="Topic categories for this stage")

class DeepResearchContentStrategySchema(BaseModel):
    """Complete deep research content strategy report"""
    industry_best_practices: IndustryBestPracticesSchema = Field(description="Industry best practices analysis")
    funnel_stage_analysis: List[FunnelStageAnalysisSchema] = Field(description="Analysis for all funnel stages")

# Export the schema for use in the workflow
GENERATION_SCHEMA_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY = DeepResearchContentStrategySchema.model_json_schema()

# --- Prompt Templates ---

SYSTEM_PROMPT_TEMPLATE_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY = """You are an expert B2B content strategist. Research company domain best practices using public web data, industry latest reports, customers feebacks and queries, user goals, and competitors content analysis to create an ideal content distribution blueprint for the specified company.

Your research should focus on:
1. Industry best practices for content distribution
2. Successful content strategies from competitors
3. User behavior and queries on platforms like Reddit and Quora
4. Content performance patterns across different funnel stages
5. Optimal content mix and format strategies

Provide comprehensive, data-driven insights that can inform content strategy decisions.

**Research Guidelines:**
- Use web search to find current industry reports and case studies
- Analyze competitor content strategies and performance
- Research user queries and pain points on social platforms
- Identify successful content patterns and formats
- Provide data-backed recommendations with specific percentages and scores
- Focus on actionable insights that can be implemented immediately

**Output Format:**
Provide your analysis in the following structured format:
```json
{schema}
```

Ensure all fields are populated with accurate, research-backed data that reflects current industry best practices.
"""

USER_PROMPT_TEMPLATE_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY = """### Company Profile
- **Company Info**: {company_info}

## Research Focus

Focus on the best suitable for content distribution across buyer journey stages in the domain of our company. Analyze what other successful companies are doing for content strategy, particularly those in the same space. Also pay attention to what users are asking on platforms like reddit and quora.

Research successful content strategies from companies like:
- Grammarly Business (direct competitor)
- Jasper AI (direct competitor) 
- Copy.ai (direct competitor)

**Specific Research Areas:**
1. **Content Mix Analysis**: What percentage of content should be educational vs thought leadership vs product-focused
2. **Funnel Stage Optimization**: How to allocate content across awareness, consideration, decision, adoption, expansion, and advocacy stages
3. **Format Effectiveness**: Which content formats work best at each stage
4. **Topic Strategy**: What topics and categories should be prioritized
5. **Competitive Intelligence**: How competitors are structuring their content strategies
6. **User Behavior**: What users are searching for and discussing online

**Research Requirements:**
- Use web search to find current industry data and reports
- Analyze competitor content strategies and performance metrics
- Research user queries on platforms like Reddit, Quora, and industry forums
- Identify successful content patterns and their effectiveness scores
- Provide specific percentages and recommendations based on industry benchmarks
```"""



SYSTEM_PROMPT_TEMPLATE_FOR_LINKEDIN_RESEARCH = """
You are a senior B2B social-media strategist and industry analyst with full web-browsing capabilities.

MISSION
• Produce a deep-research report that guides an executive’s LinkedIn strategy.
• Output **MUST** be valid JSON that matches the “LinkedInResearchReport” Pydantic schema (see below).

KEY RULES
1. **Peer & category benchmark** – Select 5-10 comparator executives (same function + industry, similar company size/funding stage, preferably same region).  
2. **Freshness** – All performance metrics and trend references come from the last 90 days unless clearly noted otherwise.  
3. **Privacy** – Do NOT expose peer names, job titles, or personal bios. Use anonymous `peer_id` slugs.  
4. **Sources** – For any field that calls for a `source_id`, assign a unique integer (starting at 1 and incrementing globally). Do not include a reference list in the final JSON.  
5. **Completeness** – Populate every field; if data is genuinely unavailable, return an empty string `""` or empty list `[]`, but keep the field present.  
6. **Numbers** – Use plain numbers (no % symbols). Dates **MUST** be ISO (`YYYY-MM-DD`).  
7. **No extraneous keys** – Output must validate against the schema exactly; no additional properties or nesting levels.

SCHEMA (reference, not to be reproduced in the output)
──────────────────────────────────────────────
class LinkedInResearchReport(BaseModel):
    peers: List[Peer]
    repeated_high_leverage_tactics: List[HighLeverageTactic]
    macro_trends: List[TrendItem]
    micro_trends: List[TrendItem]
    narrative_hooks_ranked: List[NarrativeHook]
    personas: List[Persona]
    topic_map: List[TopicMapItem]
──────────────────────────────────────────────

After analysis, respond with the single JSON object only—no prose, no markdown fence.
"""

USER_PROMPT_TEMPLATE_FOR_LINKEDIN_RESEARCH = """
Please execute the LinkedIn deep-research workflow using the instructions in the system prompt.

EXECUTIVE CONTEXT
LinkedIn user profile:
{linkedin_user_profile}

LinkedIn scraped profile:
{linkedin_scraped_profile}

DELIVERABLE
Return a fully populated **LinkedInResearchReport** JSON document that obeys the schema and rules provided in the system prompt.
"""

# ───────────────────────────────────────────────────────
# Re-usable “dict-like” helper models
# ───────────────────────────────────────────────────────



class RisingTerm(BaseModel):
    """Keyword or hashtag showing fast growth but low competition."""
    term: str = Field(description="Exact keyword or hashtag (without #).")
    YoY_search_growth_pct: float = Field(description="Year-over-year search-volume growth percentage (e.g. 0.42 = 42 %).")

# ───────────────────────────────────────────────────────
# SECTION-1  PEER & CATEGORY BENCHMARK
# ───────────────────────────────────────────────────────

class Peer(BaseModel):
    """Benchmark datapoints for a single comparator executive."""
    profile_url: str = Field(description="Direct link to the peer’s public LinkedIn profile.")
    headline: str = Field(description="Role and company as shown on LinkedIn (e.g. 'CRO @ FinTechCo').")
    avg_posts_per_month_90d: int = Field(description="Average number of posts per month in the last 90 days.")
    text_pct: int = Field(description="Percentage of text-only posts.")
    carousel_pct: int = Field(description="Percentage of multi-image carousel posts.")
    doc_pct: int = Field(description="Percentage of document/PDF posts.")
    video_pct: int = Field(description="Percentage of native video posts.")
    poll_pct: int = Field(description="Percentage of LinkedIn poll posts.")
    median_engagement: float = Field(description="Median engagements over the last 90 days.")
    signature_moves: List[str] = Field(description="Recurring content plays (e.g. 'Friday AMA').")
    content_pillars: List[str] = Field(description="Primary thematic buckets the peer posts about (max five).")

class HighLeverageTactic(BaseModel):
    """A repeatable tactic distilled from multiple peers."""
    tactic: str = Field(description="Short name of the tactic (e.g. 'Multi-image carousel playbooks').")
    tactic_desciption: str = Field(description="Detailed description of the tactic.")
    prevalence_pct: int = Field(description="Percentage of peers who use this tactic.")
    median_ER_lift: float = Field(description="Median engagement lift versus each peer’s own baseline.")


# ───────────────────────────────────────────────────────
# SECTION-2  INDUSTRY TREND RESEARCH
# ───────────────────────────────────────────────────────

class TrendItem(BaseModel):
    """Macro-level or micro-level industry development."""
    title: str = Field(description="Concise label for the trend or development.")
    summary: str = Field(description="One-sentence explanation with supporting numbers or facts.")

class NarrativeHook(BaseModel):
    """Story angle the executive could credibly adopt."""
    hook: str = Field(description="Headline of the narrative (e.g. 'AI-driven supply-chain resilience').")
    proof_points: List[str] = Field(description="Bullet list of supporting statistics or news bites.")
    relevance_score: int = Field(description="Fit with executive goals and expertise (1 = low, 5 = high).")


# ───────────────────────────────────────────────────────
# SECTION-3  AUDIENCE & TOPIC INTELLIGENCE
# ───────────────────────────────────────────────────────
class Persona(BaseModel):
    """Snapshot of a priority audience segment."""
    role_titles: List[str] = Field(description="Representative job titles within this segment.")
    seniority: str = Field(description="Typical seniority band (e.g. 'C-level / VP').")
    urgent_pain_points: List[str] = Field(description="List of acute needs or frustrations experienced by the persona.")
    preferred_formats: List[str] = Field(description="Content types this persona engages with most.")
    tone_style: str = Field(description="Voice or style that resonates with the persona (e.g. 'Data-driven yet pragmatic').")

class TopicMapItem(BaseModel):
    """One content pillar that will guide editorial planning."""
    pillar: str = Field(description="Umbrella theme (e.g. 'Smart Factory ROI').")
    sub_topics: List[str] = Field(description="Specific angles nested under the pillar.")
    data_hook_examples: List[str] = Field(description="Stat-driven hooks to make the topic tangible.")
    recommended_formats: List[str] = Field(description="Best-fit LinkedIn formats for this pillar.")
    emotional_angle: str = Field(description="Core feeling the content should evoke (e.g. 'Cost-saving pride').")

# ───────────────────────────────────────────────────────
# ROOT MODEL
# ───────────────────────────────────────────────────────

class LinkedInResearchReport(BaseModel):
    peers: List[Peer] = Field(description="List of benchmark peers (ideally 5-10).")
    repeated_high_leverage_tactics: List[HighLeverageTactic] = Field(description="Rank-ordered list of the most effective, commonly observed tactics.")
    macro_trends: List[TrendItem] = Field(description="Broad market or regulatory shifts.")
    micro_trends: List[TrendItem] = Field(description="Niche product or technology developments.")
    narrative_hooks_ranked: List[NarrativeHook] = Field(description="Top narrative hooks ordered by relevance_score.")
    personas: List[Persona] = Field(description="Audience segments derived from CRM, social data and forums.")
    topic_map: List[TopicMapItem] = Field(description="Three to five pillars that will structure ongoing content.")


SCHEMA_TEMPLATE_FOR_LINKEDIN_RESEARCH = LinkedInResearchReport.model_json_schema()



# ───────────────────────────────────────────────────────────────────────────────
# COMBINED DEEP RESEARCH: CONTENT STRATEGY + LINKEDIN RESEARCH
# ───────────────────────────────────────────────────────────────────────────────

class CombinedDeepResearchSchema(BaseModel):
    """Combined deep research report including both content strategy and LinkedIn research"""
    content_strategy_research: DeepResearchContentStrategySchema = Field(description="Comprehensive content strategy research and recommendations")
    linkedin_research: LinkedInResearchReport = Field(description="LinkedIn strategy research and competitor analysis")

# Export the combined schema for use in the workflow
GENERATION_SCHEMA_FOR_COMBINED_DEEP_RESEARCH = CombinedDeepResearchSchema.model_json_schema()

# --- Combined Prompt Templates ---

SYSTEM_PROMPT_TEMPLATE_FOR_COMBINED_DEEP_RESEARCH = """You are an expert B2B content strategist and LinkedIn strategy consultant with comprehensive research capabilities.

Your mission is to conduct two parallel research streams and deliver a unified strategic report:

**STREAM 1: CONTENT STRATEGY RESEARCH**
Research company domain best practices using public web data, industry reports, customer feedback, user goals, and competitor content analysis to create an ideal content distribution blueprint.

Focus areas:
1. Industry best practices for content distribution across buyer journey stages
2. Successful content strategies from competitors
3. User behavior and queries on platforms like Reddit and Quora
4. Content performance patterns across different funnel stages
5. Optimal content mix and format strategies

**STREAM 2: LINKEDIN STRATEGY RESEARCH**
Produce a deep-research report that guides executive LinkedIn strategy through peer benchmarking and industry analysis.

Focus areas:
1. Peer & category benchmark – Select 12-15 comparator executives (same function + industry, similar company size/funding stage)
2. Industry trend research – macro/micro trends and narrative hooks
3. Audience & topic intelligence – personas, keyword gaps, and topic mapping

**RESEARCH GUIDELINES:**
- Use web search to find current industry reports and case studies (last 90 days when possible)
- Analyze competitor content strategies and performance across both blog/content and LinkedIn
- Research user queries and pain points on social platforms
- Identify successful content patterns and formats for both channels
- Provide data-backed recommendations with specific percentages and scores
- Focus on actionable insights that can be implemented immediately
- For LinkedIn research: Use anonymous peer_id slugs, no personal information exposure
- Ensure all performance metrics are recent (last 90 days unless noted)

**OUTPUT FORMAT:**
Provide your analysis in the following structured format:
```json
{schema}
```

Ensure all fields are populated with accurate, research-backed data that reflects current industry best practices for both content strategy and LinkedIn execution."""

USER_PROMPT_TEMPLATE_FOR_COMBINED_DEEP_RESEARCH = """### Company Profile
- **Company Info**: {company_info}

### LinkedIn User Profile
{linkedin_user_profile}

### LinkedIn Scraped Profile
{linkedin_scraped_profile}

## Combined Research Requirements

### CONTENT STRATEGY RESEARCH
Focus on optimal content distribution across buyer journey stages in our company's domain. Analyze successful strategies from companies in the same space and user behavior on platforms like Reddit and Quora.

**Research Areas:**
1. **Content Mix Analysis**: Percentage breakdown of educational vs thought leadership vs product-focused content
2. **Funnel Stage Optimization**: Content allocation across awareness, consideration, decision, adoption, expansion, and advocacy stages
3. **Format Effectiveness**: Which content formats work best at each stage
4. **Topic Strategy**: Priority topics and categories
5. **Competitive Intelligence**: How competitors structure their content strategies
6. **User Behavior**: What users are searching for and discussing online

### LINKEDIN STRATEGY RESEARCH
Conduct comprehensive LinkedIn strategy research for the executive, including peer benchmarking, industry trends, and audience intelligence.

**Research Areas:**
1. **Peer Benchmarking**: Analyze 12-15 comparable executives in similar roles/industries
2. **Industry Trends**: Macro and micro trends relevant to the executive's domain
3. **Narrative Hooks**: Story angles the executive could credibly adopt
4. **Audience Personas**: Key segments to target with specific pain points and preferences
5. **Keyword/Hashtag Analysis**: Rising terms with low competition and high growth
6. **Topic Mapping**: 3-5 content pillars to structure ongoing LinkedIn content

**COMPETITIVE ANALYSIS TARGETS:**
Research successful strategies from companies like:
- Grammarly Business (direct competitor)
- Jasper AI (direct competitor) 
- Copy.ai (direct competitor)

**DELIVERABLE:**
Return a fully populated **CombinedDeepResearchSchema** JSON document with both content strategy recommendations and LinkedIn strategy insights based on current industry data and competitor analysis."""
