# =============================================================================
# LLM MODEL CONFIGURATIONS
# =============================================================================
"""
Configuration for different LLM models used throughout the workflow steps.
"""

from enum import Enum
from typing import List, Any, Optional, Literal
from pydantic import BaseModel, Field
from pydantic import conint

# LLM Provider
LLM_PROVIDER = "openai"

# Temperature Setting
LLM_TEMPERATURE = 0.5

# Max Tokens by Step
LLM_MAX_TOKENS_CLASSIFY = 20000  # Step 1: Post Classification
LLM_MAX_TOKENS_ANALYSIS = 20000  # Step 2: Funnel Stage Analysis
LLM_MAX_TOKENS_PORTFOLIO_ANALYSIS = 10000  # Step 3: Portfolio Batch Analysis
LLM_MAX_TOKENS_PORTFOLIO_FINAL_ANALYSIS = 20000  # Step 3: Portfolio Final Synthesis
LLM_MAX_TOKENS_TECHNICAL_SEO = 10000  # Step 4: Technical SEO Analysis

# Model Names by Step
CLASSIFICATION_MODEL = "gpt-5"  # Step 1: Post Classification
ANALYSIS_MODEL = "gpt-5"  # Step 2: Funnel Stage Analysis
PORTFOLIO_ANALYSIS_MODEL = "gpt-5"  # Step 3: Portfolio Analysis
PORTFOLIO_FINAL_ANALYSIS_MODEL = "gpt-5"  # Step 3: Portfolio Final Synthesis

# =============================================================================
# LLM Inputs for Blog Content Analysis Workflow
# =============================================================================
# This file contains prompts, schemas, and configurations organized by workflow steps:
# 1. Post Classification - Classify blog posts into sales funnel stages with quality scoring
# 2. Funnel Stage Analysis - Analyze content patterns within each funnel stage
# 3. Portfolio Analysis - Comprehensive portfolio-level content analysis
# 4. Technical SEO Analysis - Analyze technical SEO aspects of the blog

# Enums for Classification
class SalesFunnelStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    PURCHASE = "purchase"
    RETENTION = "retention"

# =============================================================================
# STEP 1: POST CLASSIFICATION
# =============================================================================
# First step that classifies blog posts into sales funnel stages (Awareness,
# Consideration, Purchase, Retention) and evaluates content quality scores.

# Post Classification System Prompt
POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE = """You are an expert content analyst specializing in sales funnel classification. Your task is to analyze blog posts and return structured outputs that strictly conform to the provided JSON schema.

## Field Guidance (align with schema exactly):
- sales_funnel_stage: Choose one of the stages above.
- primary_topic: One concise phrase capturing the main topic.
- secondary_topics: Up to 5 concise related topics.

- readability_score, clarity_score, logical_flow_score, depth_score, originality_score: Float scores on a 0-100 scale.

- expertise_score, experience_score, authoritativeness_score, trustworthiness_score: Float scores on a 0-100 scale.

- has_table_of_contents, has_faq_section, has_author_bio, has_citations, has_code_examples, has_data_visualizations: Boolean flags based on presence in the post.

- content_pattern: One of [how-to, listicle, guide, comparison, opinion, case-study, news, tutorial].
- reading_level: One of [elementary, intermediate, advanced].

- questions_addressed: Up to 3 key questions answered by the post (concise phrasing).

- people_mentioned, products_mentioned, companies_mentioned: Up to 3 items each; use canonical names.

## Output Format:
Return output that matches this JSON schema exactly:

Instructions:
1. Analyze each post using title, content, and context.
2. Use exact field names and data types from the schema.
3. Populate every field; do not add any extra fields.
4. Keep strings concise but specific; scores must be 0-100 floats.
5. Output only JSON that conforms to the schema (no prose)."""

# Post Classification User Prompt Template
POST_CLASSIFICATION_USER_PROMPT_TEMPLATE = """Please analyze and classify the following batch of blog posts:

{posts_batch_json}

For each post, produce a JSON object with these fields (exact names and types):
- post_url
- sales_funnel_stage
- primary_topic
- secondary_topics (≤ 5)
- readability_score, clarity_score, logical_flow_score, depth_score, originality_score (0-100 floats)
- expertise_score, experience_score, authoritativeness_score, trustworthiness_score (0-100 floats)
- has_table_of_contents, has_faq_section (booleans)

Ensure the final output strictly matches the provided schema and includes one object per post in the batch."""

# Variables Used in Post Classification Prompts:
"""
Variables that go into the Post Classification prompts:
- posts_batch_json: JSON representation of the batch of posts to classify (includes post URL, title, content)
"""

# Post Classification Output Schema
class PostClassificationSchema(BaseModel):
    post_url: str = Field(description="The URL of the blog post")
    sales_funnel_stage: SalesFunnelStage = Field(description="The sales funnel stage this post belongs to")
    primary_topic: str = Field(description="Main topic of the post")
    secondary_topics: List[str] = Field(description="Secondary topics covered", max_items=5)

    # Content Quality Scores (moved from group)
    readability_score: float = Field(description="Readability score (0-100)")
    clarity_score: float = Field(description="Content clarity score (0-100)")
    logical_flow_score: float = Field(description="Logical flow score (0-100)")
    depth_score: float = Field(description="Content depth score (0-100)")
    originality_score: float = Field(description="Content originality score (0-100)")

    # E-E-A-T Individual Scores (moved from group)
    expertise_score: float = Field(description="Expertise signals score (0-100)")
    experience_score: float = Field(description="Experience demonstration score (0-100)")
    authoritativeness_score: float = Field(description="Authority indicators score (0-100)")
    trustworthiness_score: float = Field(description="Trust signals score (0-100)")

    # Content Structure Detection (boolean flags)
    has_table_of_contents: bool = Field(description="Has table of contents")
    has_faq_section: bool = Field(description="Has FAQ section")

class PostClassificationBatchSchema(BaseModel):
    batch_id: str = Field(description="Batch ID")
    posts: List[PostClassificationSchema] = Field(description="List of posts")

BATCH_CLASSIFICATION_SCHEMA = PostClassificationBatchSchema.model_json_schema()

# =============================================================================
# STEP 2: FUNNEL STAGE ANALYSIS
# =============================================================================
# Second step that groups posts by funnel stage and performs detailed content
# analysis on each group to identify themes, patterns, and strategic insights.

# Funnel Stage Analysis System Prompt
FUNNEL_STAGE_ANALYSIS_SYSTEM_PROMPT_TEMPLATE = """You are an expert content strategist and analyst specializing in content intelligence. Your task is to analyze a group of blog posts for a specific sales funnel stage and return structured insights that strictly conform to the provided JSON schema.

## Analyze the group across these dimensions (mapped to schema fields):

### 1. Content Themes (content_themes)
- primary_narratives: Key narratives that repeatedly appear.
- topic_clusters: Core topics and their clusters.
- content_strategy: Concise description of the inferred strategy for this stage.
- unique_angles: Distinctive angles or perspectives observed.

### 2. E-E-A-T Analysis (eeat_analysis)
- expertise_signals: Concrete indicators of expertise.
- authority_indicators: Citations, recognitions, or authority markers.
- trust_elements: Transparency, accuracy, references, or other trust signals.

### 3. Content Quality Scoring (content_quality_scoring)
- information_density: One of [sparse, moderate, dense].
- writing_quality: Brief qualitative assessment of overall writing quality.

### 4. Question-Answer Extraction (question_answer_extraction)
- featured_snippet_potential: Questions/answers or sections likely to win featured snippets.

### 5. Content Structure Elements (content_structure_elements)
- storytelling_elements: Problem/solution, case study, data, etc.
- supporting_evidence_types: Stats, quotes, examples, research, etc.

### 6. Logical Flow & Readability (logical_flow_readability)
- storytelling_elements: Problem/solution, case study, data, etc.
- supporting_evidence_types: Stats, quotes, examples, research, etc.

### 7. Logical Flow & Readability (logical_flow_readability)
- paragraph_transitions: One of [poor, good, excellent].
- heading_hierarchy: One of [poor, good, excellent].
- content_scanability: One of [low, medium, high].

## Output Format:
Return output that matches this JSON schema exactly

## Instructions:
1. Consider all posts in the group; cite titles or short snippets only when necessary to ground findings.
2. Use exact field names and data types from the schema; populate all fields.
3. Provide multiple items for list fields when applicable.
4. Do not invent fields; return only JSON that conforms to the schema (no prose)."""

# Funnel Stage Analysis User Prompt Template
FUNNEL_STAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Please perform a content intelligence analysis of the following {funnel_stage} stage content group:

{posts_group_json}

Produce a single JSON object that strictly follows the schema and includes:
- funnel_stage: "{funnel_stage}"
- total_posts_analyzed: Integer count of posts provided
- content_themes: primary_narratives, topic_clusters, content_strategy, unique_angles
- eeat_analysis: expertise_signals, authority_indicators, trust_elements
- content_quality_scoring: information_density (sparse/moderate/dense), writing_quality
- question_answer_extraction: featured_snippet_potential
- content_structure_elements: storytelling_elements, supporting_evidence_types
- logical_flow_readability: paragraph_transitions (poor/good/excellent), heading_hierarchy (poor/good/excellent), content_scanability (low/medium/high)

Return only JSON adhering to the provided schema."""

# Variables Used in Funnel Stage Analysis Prompts:
"""
Variables that go into the Funnel Stage Analysis prompts:
- funnel_stage: Name of the funnel stage being analyzed (awareness, consideration, purchase, or retention)
- posts_group_json: JSON of posts in this funnel stage (includes post URLs, titles, content, and classification data)
"""

# Funnel Stage Analysis Output Schema
class EEATAnalysisSchema(BaseModel):
    expertise_signals: List[str] = Field(description="Specific expertise signals identified across content")
    authority_indicators: List[str] = Field(description="Authority indicators present")
    trust_elements: List[str] = Field(description="Trust-building elements found")

class ContentQualityScoringSchema(BaseModel):
    information_density: str = Field(description="Information density assessment (sparse/moderate/dense)")
    writing_quality: str = Field(description="Overall writing quality assessment")

class EntityRecognitionSchema(BaseModel):
    knowledge_graph_entities: List[str] = Field(description="Entities suitable for knowledge graphs")

class QuestionAnswerExtractionSchema(BaseModel):
    featured_snippet_potential: List[str] = Field(description="Content sections with featured snippet potential")

class ContentStructureElementsSchema(BaseModel):
    storytelling_elements: List[str] = Field(description="Storytelling elements used (problem/solution/case study/data)")
    supporting_evidence_types: List[str] = Field(description="Types of supporting evidence (stats/quotes/examples/research)")

class LogicalFlowReadabilitySchema(BaseModel):
    paragraph_transitions: str = Field(description="Quality of paragraph transitions (poor/good/excellent)")
    heading_hierarchy: str = Field(description="Heading hierarchy organization (poor/good/excellent)")
    content_scanability: str = Field(description="How easily content can be scanned (low/medium/high)")

class ContentThemesSchema(BaseModel):
    primary_narratives: List[str] = Field(description="The main list of narratives or stories being told")
    topic_clusters: List[str] = Field(description="Key topic clusters identified")
    content_strategy: str = Field(description="Inferred content strategy approach")
    unique_angles: List[str] = Field(description="Unique angles or perspectives taken")

class ContentAnalysisSchema(BaseModel):
    funnel_stage: str = Field(description="The sales funnel stage being analyzed")
    total_posts_analyzed: int = Field(description="Total number of posts analyzed in this group")
    content_themes: ContentThemesSchema = Field(description="Content themes analysis")
    eeat_analysis: EEATAnalysisSchema = Field(description="E-E-A-T (Expertise, Experience, Authority, Trust) analysis")
    content_quality_scoring: ContentQualityScoringSchema = Field(description="Content quality scoring")
    question_answer_extraction: QuestionAnswerExtractionSchema = Field(description="Question-Answer extraction for AEO/voice search")
    content_structure_elements: ContentStructureElementsSchema = Field(description="Content structure elements analysis")
    logical_flow_readability: LogicalFlowReadabilitySchema = Field(description="Logical flow and readability analysis")

FUNNEL_STAGE_ANALYSIS_SCHEMA = ContentAnalysisSchema.model_json_schema()

# =============================================================================
# STEP 3: PORTFOLIO ANALYSIS
# =============================================================================
# Third step that performs comprehensive portfolio-level content analysis by
# batching classified posts, analyzing each batch, and synthesizing results.

# Portfolio Analysis System Prompt (used for both batch analysis and final synthesis)
FINAL_ANALYSIS_SYSTEM_PROMPT = """You are a senior content strategist analyzing a complete blog content portfolio. Your role is to synthesize individual post data into strategic insights and actionable recommendations.

## Analysis Process:

### 1. Content Portfolio Health Assessment
- Calculate average scores across quality dimensions (readability, clarity, depth, originality, E-E-A-T)
- Identify overall content quality trends and patterns
- Assess structural content adoption (TOC, FAQ usage rates)

### 2. Topic Authority Analysis
- Group posts by primary_topic and analyze coverage depth
- For each major topic (3+ posts), evaluate:
  * Funnel stage coverage (awareness → retention)
  * Content depth and quality consistency
  * Authority level based on comprehensiveness
- Identify topics with strong authority vs. those needing development
- Flag topics covered in only 1-2 funnel stages (authority gaps)

### 3. Funnel Stage Analysis
- Analyze content distribution across sales funnel stages
- Compare quality scores between funnel stages
- Identify over/under-invested stages
- Map topic coverage gaps within each stage

### 4. Strategic Gap Identification
- Find topics with high post count but poor funnel coverage
- Identify high-quality topics that could be expanded
- Spot funnel stages lacking authoritative content
- Detect content format gaps (structural elements)

## Output Guidelines:
- Executive summary should highlight 1-2 key strengths and 1-2 critical gaps
- Focus on actionable insights over descriptive statistics
- Prioritize recommendations by potential impact
- Keep topic authority analysis to most significant topics (5-8 max)
- Base authority levels on both quantity and funnel stage coverage

## Authority Level Criteria:
- **Expert**: 8+ posts across 3-4 funnel stages with high quality scores
- **Strong**: 5-7 posts across 2-3 funnel stages with good quality
- **Developing**: 3-4 posts with limited funnel coverage
- **Weak**: 1-2 posts or single funnel stage coverage

Return only JSON that strictly conforms to the provided schema
"""

# Portfolio Batch Analysis User Prompt
FINAL_ANALYSIS_USER_PROMPT = """Analyze the following blog content portfolio data and generate a strategic content analysis report.

The input is a list of per-post records with fields including: post_url, primary_topic, sales_funnel_stage, readability_score, clarity_score, logical_flow_score, depth_score, originality_score, expertise_score, experience_score, authoritativeness_score, trustworthiness_score, has_table_of_contents, has_faq_section.

## Portfolio Data (Batch):

## Individual Post Analysis Results (JSON list):
{post_analysis_data}

Provide your analysis in the structured JSON format specified by the schema."""

# Portfolio Final Synthesis User Prompt
FINAL_SYNTHESIS_USER_PROMPT = """You will receive multiple batch-level portfolio analysis reports that already follow the final report schema. Consolidate them into a single final report.

Guidelines:
- Concatenate and deduplicate topic authority insights (limit to 5-8 most significant topics)
- Average numeric metrics across batches correctly (weighted by counts where applicable)
- Merge funnel stage insights (sum counts, recompute averages)
- Recompute content_structure_adoption as a single portfolio percentage

Input:
- Batch Reports (JSON list of FinalContentAnalysisReport objects):
{batch_reports_json}

Output:
- A single FinalContentAnalysisReport JSON object strictly matching the schema."""

# Variables Used in Portfolio Analysis Prompts:
"""
Variables that go into the Portfolio Analysis prompts:
- post_analysis_data: Batch of classified posts with all their quality scores and metadata
- batch_reports_json: JSON list of batch-level portfolio analysis reports (used in final synthesis)
"""

# Portfolio Analysis Output Schema
class ContentQualityMetrics(BaseModel):
    average_readability: float = Field(description="Average readability score across all posts")
    average_clarity: float = Field(description="Average clarity score across all posts")
    average_depth: float = Field(description="Average content depth score")
    average_originality: float = Field(description="Average originality score")
    overall_eeat_score: float = Field(description="Combined E-E-A-T score average")
    content_structure_adoption: float = Field(description="% of posts with good structure Table of Content/Frequently Asked Questions")

class TopicAuthorityInsight(BaseModel):
    topic_name: str = Field(description="Topic name")
    total_posts: int = Field(description="Posts covering this topic")
    funnel_coverage: List[str] = Field(description="Funnel stages covered for this topic")
    authority_level: str = Field(description="Topic authority assessment (Expert/Strong/Developing/Weak)")
    coverage_gaps: List[str] = Field(description="Missing funnel stages or content types")

class FunnelStageInsight(BaseModel):
    stage_name: str = Field(description="Sales funnel stage")
    post_count: int = Field(description="Number of posts in this stage")
    avg_quality_score: float = Field(description="Average quality score for this stage")

class FinalContentAnalysisReport(BaseModel):
    executive_summary: str = Field(description="3-4 sentence strategic overview of content portfolio health and opportunities")
    content_portfolio_health: ContentQualityMetrics = Field(description="Overall content quality metrics")
    topic_authority_analysis: List[TopicAuthorityInsight] = Field(description="Topic authority insights for top 5-8 topics", max_items=8)
    funnel_stage_insights: List[FunnelStageInsight] = Field(description="Analysis by sales funnel stage", max_items=4)
    strategic_recommendations: List[str] = Field(description="Top 4-5 actionable strategic recommendations", max_items=5)
    content_gaps_priority: List[str] = Field(description="Top 3-4 priority content gaps to address", max_items=4)

FINAL_ANALYSIS_SCHEMA = FinalContentAnalysisReport.model_json_schema()

# =============================================================================
# STEP 4: TECHNICAL SEO ANALYSIS
# =============================================================================
# Fourth step that analyzes technical SEO aspects of the blog including HTML
# health metrics, robots.txt configuration, and bot access optimization.

# Technical SEO Analysis System Prompt
TECHNICAL_SEO_SYSTEM_PROMPT_TEMPLATE = """You are a senior technical SEO analyst specializing in technical SEO audits based on measurable HTML and technical factors. Your role is to analyze concrete technical SEO metrics and create actionable reports for development teams and marketing executives.

Key responsibilities:
- Analyze technical SEO health based on measurable HTML standards and best practices
- Identify critical technical issues that impact crawlability, indexability, and user experience
- Analyze robots.txt configuration and bot access permissions
- Prioritize issues based on their direct impact on search engine visibility
- Provide specific, technically accurate recommendations with clear implementation paths
- Focus on fixing foundational technical issues before suggesting optimizations

Analysis guidelines:
- Technical requirements (HTTPS, mobile-friendly, canonical tags) are non-negotiable baselines
- Missing fundamental elements (title, H1, meta description) are critical issues
- Consider pages with <50% implementation of best practices as requiring attention
- Pages with <30% implementation need immediate action
- Prioritize issues that directly block search engines (noindex, missing titles, broken hierarchy)
- Factor in the scale of issues (e.g., 80% of pages missing meta descriptions is critical)
- Analyze robots.txt for proper bot access - blocking beneficial bots is a critical issue
- Identify opportunities to allow important SEO and AI bots that are currently blocked

Metrics interpretation:
- Title/Meta Description: Essential for SERP appearance and CTR
- H1 and Hierarchy: Critical for content understanding and accessibility
- HTTPS: Mandatory for security and ranking
- Mobile-friendly: Required for mobile-first indexing
- Canonical tags: Essential for duplicate content management
- Schema markup: Important for rich results and AI understanding
- Alt text: Critical for accessibility and image search
- Internal linking: Essential for crawlability and PageRank flow
- Robots.txt: Critical for controlling bot access and ensuring beneficial bots can crawl

Report tone: Technical, precise, actionable, and data-driven.
Report focus: Concrete technical issues with measurable impact on search performance, including bot access optimization.

You must structure your response as a valid JSON object matching the TechnicalSEOReport schema provided."""

# Technical SEO Analysis User Prompt Template
TECHNICAL_SEO_USER_PROMPT_TEMPLATE = """Please analyze the following technical SEO audit data and generate a comprehensive technical SEO report. Focus on identifying critical technical issues and providing actionable fixes, including robots.txt optimization.

## Technical SEO Audit Data:

{data}

## Robots Analysis:

{robots_analysis}

## Analysis Instructions:

1. Calculate technical health scores based on the implementation rates of SEO best practices
2. Analyze the robots.txt configuration to identify blocked beneficial bots and accessibility issues
3. Identify 3-5 critical technical issues that directly impact search visibility (including bot access issues)
4. Provide 3-4 immediate technical fixes that can be implemented quickly
5. Identify structural gaps that require longer-term development effort
6. Create specific recommendations for robots.txt optimization to improve bot access
7. Create a prioritized timeline for fixing critical issues

Focus on technical issues that can be directly measured and fixed through code changes. Pay special attention to:
- Which beneficial bots (Google, Bing, AI crawlers) are being blocked unnecessarily
- Whether important SEO bots have proper access to key site areas
- Robots.txt rules that might be preventing optimal crawling and indexing

Base all recommendations on the concrete metrics and robots analysis provided.

Please return your analysis as a valid JSON object following the TechnicalSEOReport schema."""

# Variables Used in Technical SEO Analysis Prompts:
"""
Variables that go into the Technical SEO Analysis prompts:
- data: Technical audit data from web crawler (includes HTML metrics, page structure, meta tags, etc.)
- robots_analysis: Robots.txt analysis results (includes bot access permissions and blocking rules)
"""

# Technical SEO Analysis Output Schema
class TechnicalHealth(BaseModel):
    """Technical SEO health scores based on measurable HTML metrics."""

    overall_score: conint(ge=0, le=100) = Field(
        ..., description="0-100 score based on aggregate technical SEO metrics (title, meta, headers, etc.)"
    )
    crawlability_score: conint(ge=0, le=100) = Field(
        ..., description="0-100 score based on technical factors affecting search engine crawling (HTTPS, HTML lang, canonical tags, robots.txt)"
    )
    structure_score: conint(ge=0, le=100) = Field(
        ..., description="0-100 score based on HTML structure metrics (heading hierarchy, lists, semantic HTML)"
    )
    mobile_readiness_score: conint(ge=0, le=100) = Field(
        ..., description="0-100 score based on mobile-friendly viewport and HTTPS usage"
    )
    status_summary: str = Field(
        ..., description="One-sentence summary of the technical SEO health based on measured metrics"
    )

class RobotsInsight(BaseModel):
    """Insights about robots.txt configuration and bot access."""

    bot_name: str = Field(..., description="Name of the bot or crawler (e.g., 'Googlebot', 'Bingbot', 'GPTBot')")
    current_access: Literal["Allowed", "Blocked", "Partially Blocked"] = Field(
        ..., description="Current access level based on robots.txt analysis"
    )
    recommended_access: Literal["Allow", "Block", "Selective Allow"] = Field(
        ..., description="Recommended access level for optimal SEO performance"
    )
    seo_impact: str = Field(..., description="How the current access setting impacts SEO and visibility")
    action_needed: str = Field(..., description="Specific action to take in robots.txt (e.g., 'Remove Disallow rule for /blog/')")

class TechnicalIssue(BaseModel):
    """A specific technical SEO issue identified from the metrics."""

    issue: str = Field(..., description="Specific technical problem (e.g., '45% of pages missing meta descriptions')")
    metric_value: str = Field(..., description="The actual metric value from the analysis (e.g., '45%', '2.3 avg H1s')")
    seo_impact: str = Field(..., description="How this technical issue affects search engine visibility and rankings")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Severity based on the metric value and SEO best practices"
    )

class TechnicalImprovement(BaseModel):
    """A specific technical fix based on the analyzed metrics."""

    action: str = Field(..., description="Specific technical action (e.g., 'Add missing title tags to 23% of pages')")
    current_metric: str = Field(..., description="Current metric value that needs improvement (e.g., '77% have titles')")
    target_metric: str = Field(..., description="Target metric value after implementation (e.g., '100% with titles')")
    expected_impact: Literal["High", "Medium", "Low"] = Field(
        ..., description="Expected SEO impact based on the importance of this technical factor"
    )

class TechnicalGap(BaseModel):
    """Technical implementation gap identified from the metrics."""

    gap_area: str = Field(..., description="Technical area with low metrics (e.g., 'Schema Markup', 'Open Graph')")
    current_implementation: str = Field(..., description="Current implementation percentage or metric (e.g., '15% have schema')")
    best_practice_target: str = Field(..., description="Industry best practice target (e.g., '100% schema implementation')")
    implementation_priority: Literal["High", "Medium", "Low"] = Field(
        ..., description="Priority based on SEO impact and current gap size"
    )

class KeyMetricHighlight(BaseModel):
    """Important metric to highlight from the analysis."""

    metric_name: str = Field(..., description="Name of the metric (e.g., 'Pages with H1', 'Mobile-friendly pages')")
    value: str = Field(..., description="Actual value from the analysis (e.g., '67%', '4.2 average')")
    benchmark: str = Field(..., description="SEO best practice benchmark (e.g., '100%', '1 H1 per page')")
    status: Literal["Good", "Needs Improvement", "Critical"] = Field(
        ..., description="Status based on comparison to benchmark"
    )

class TechnicalSEOReport(BaseModel):
    """
    Technical SEO report based on measurable HTML and technical metrics.
    All insights are derived from concrete, verifiable technical factors.
    """

    technical_health: TechnicalHealth = Field(
        ..., description="Overall technical health scores based on analyzed metrics"
    )

    robots_insights: List[RobotsInsight] = Field(
        ..., description="Analysis of robots.txt configuration and bot access recommendations", max_items=8
    )

    critical_technical_issues: List[TechnicalIssue] = Field(
        ..., description="Top technical issues ordered by severity, based on actual metrics", max_items=5
    )

    immediate_technical_fixes: List[TechnicalImprovement] = Field(
        ..., description="Quick technical improvements based on the metrics analyzed", max_items=4
    )

    technical_implementation_gaps: List[TechnicalGap] = Field(
        ..., description="Major technical gaps in SEO implementation", max_items=4
    )

    key_metrics: List[KeyMetricHighlight] = Field(
        ..., description="Important metrics to highlight for stakeholders", max_items=6
    )

    executive_summary: str = Field(
        ..., description="2-3 sentence executive summary of technical SEO status based on metrics, including robots.txt status"
    )

    pages_analyzed: int = Field(..., description="Total number of pages analyzed in this report")

TECHNICAL_SEO_REPORT_SCHEMA = TechnicalSEOReport.model_json_schema()