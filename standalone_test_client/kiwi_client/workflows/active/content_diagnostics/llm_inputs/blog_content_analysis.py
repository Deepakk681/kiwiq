"""
LLM inputs for blog content analysis workflow including schemas and prompt templates.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# --- Enums for Classification ---

class SalesFunnelStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    PURCHASE = "purchase"
    RETENTION = "retention"

class ContentCategory(str, Enum):
    PRODUCT_FEATURES = "product_features"
    CASE_STUDIES = "case_studies"
    CUSTOMER_TESTIMONIALS = "customer_testimonials"
    PRICING = "pricing"
    COMPARISONS = "comparisons"
    THOUGHT_LEADERSHIP = "thought_leadership"
    COMPANY_NEWS = "company_news"
    EDUCATIONAL = "educational"

class UserIntent(str, Enum):
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMMERCIAL = "commercial"
    COMPARISON = "comparison"
    RESEARCH = "research"
    PROBLEM_SOLVING = "problem_solving"

class ContentDepth(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

# --- Sales Funnel Stages constant for prompts ---
SALES_FUNNEL_STAGES = {
    "awareness": "Content that introduces the problem, educates about the industry, or builds brand awareness",
    "consideration": "Content that presents solutions, compares options, or demonstrates value propositions",
    "purchase": "Content that drives decision-making, showcases pricing, or includes clear calls-to-action",
    "retention": "Content that supports existing customers, provides advanced usage tips, or builds loyalty"
}

# --- Classification Schemas ---

class PostClassificationSchema(BaseModel):
    post_url: str = Field(description="The URL of the blog post")
    sales_funnel_stage: SalesFunnelStage = Field(description="The sales funnel stage this post belongs to")
    content_category: ContentCategory = Field(description="The primary category of the content")
    user_intent: UserIntent = Field(description="The primary user intent this content serves")
    content_depth: ContentDepth = Field(description="The depth/complexity level of the content")

class BatchClassificationSchema(BaseModel):
    batch_id: str = Field(description="Unique identifier for this batch")
    classifications: List[PostClassificationSchema] = Field(description="List of post classifications in this batch")

# --- Analysis Schemas ---

class EEATAnalysisSchema(BaseModel):
    expertise_score: float = Field(description="Expertise signals score (0-10)")
    experience_score: float = Field(description="Experience demonstration score (0-10)")
    authoritativeness_score: float = Field(description="Authority indicators score (0-10)")
    trustworthiness_score: float = Field(description="Trust signals score (0-10)")
    expertise_signals: List[str] = Field(description="Specific expertise signals identified")
    authority_indicators: List[str] = Field(description="Authority indicators present")
    trust_elements: List[str] = Field(description="Trust-building elements found")

class ContentQualityScoringSchema(BaseModel):
    readability_score: float = Field(description="Readability score (0-10)")
    clarity_score: float = Field(description="Clarity and coherence score (0-10)")
    professional_tone_score: float = Field(description="Professional tone score (0-10)")
    information_density: str = Field(description="Information density assessment (sparse/moderate/dense)")
    writing_quality: str = Field(description="Overall writing quality assessment")

class EntityRecognitionSchema(BaseModel):
    people_mentioned: List[str] = Field(description="People/experts mentioned in content")
    products_mentioned: List[str] = Field(description="Products or services mentioned")
    companies_mentioned: List[str] = Field(description="Companies or organizations mentioned")
    topics_covered: List[str] = Field(description="Main topics and concepts covered")
    knowledge_graph_entities: List[str] = Field(description="Entities suitable for knowledge graphs")

class QuestionAnswerExtractionSchema(BaseModel):
    questions_identified: List[str] = Field(description="Questions explicitly answered in content")
    voice_search_optimized: bool = Field(description="Whether content is optimized for voice search")
    aeo_compatibility: float = Field(description="Answer Engine Optimization compatibility score (0-10)")
    featured_snippet_potential: List[str] = Field(description="Content sections with featured snippet potential")

class ContentStructureElementsSchema(BaseModel):
    content_sections_identified: List[str] = Field(description="Main content sections identified (intro/body/conclusion/cta)")
    storytelling_elements: List[str] = Field(description="Storytelling elements used (problem/solution/case study/data)")
    supporting_evidence_types: List[str] = Field(description="Types of supporting evidence (stats/quotes/examples/research)")
    content_pattern: str = Field(description="Content pattern identified (listicle/how-to/guide/comparison/opinion)")
    information_hierarchy: str = Field(description="Information hierarchy quality (clear/moderate/poor)")

class LogicalFlowReadabilitySchema(BaseModel):
    logical_flow_score: float = Field(description="Logical flow and structure score (0-10)")
    paragraph_transitions: str = Field(description="Quality of paragraph transitions (poor/good/excellent)")
    heading_hierarchy: str = Field(description="Heading hierarchy organization (poor/good/excellent)")
    content_scanability: str = Field(description="How easily content can be scanned (low/medium/high)")
    reading_level: str = Field(description="Estimated reading level (elementary/intermediate/advanced)")

class ContentThemesSchema(BaseModel):
    primary_narratives: List[str] = Field(description="The main list of narratives or stories being told")
    topic_clusters: List[str] = Field(description="Key topic clusters identified")
    content_strategy: str = Field(description="Inferred content strategy approach")
    unique_angles: List[str] = Field(description="Unique angles or perspectives taken")

class ContentQualityAssessmentSchema(BaseModel):
    depth_score: float = Field(description="Content depth score (0-10)")
    originality_score: float = Field(description="Content originality score (0-10)")
    authority_signals: List[str] = Field(description="Authority signals present in content")
    engagement_indicators: List[str] = Field(description="Engagement indicators identified")

class ContentAnalysisSchema(BaseModel):
    funnel_stage: str = Field(description="The sales funnel stage being analyzed")
    total_posts_analyzed: int = Field(description="Total number of posts analyzed in this group")
    content_themes: ContentThemesSchema = Field(description="Content themes analysis")
    eeat_analysis: EEATAnalysisSchema = Field(description="E-E-A-T (Expertise, Experience, Authority, Trust) analysis")
    content_quality_scoring: ContentQualityScoringSchema = Field(description="Content quality scoring")
    question_answer_extraction: QuestionAnswerExtractionSchema = Field(description="Question-Answer extraction for AEO/voice search")
    content_structure_elements: ContentStructureElementsSchema = Field(description="Content structure elements analysis")
    logical_flow_readability: LogicalFlowReadabilitySchema = Field(description="Logical flow and readability analysis")
    
# --- Schema Definitions for LLM ---

# Convert schemas to JSON for LLM consumption
BATCH_CLASSIFICATION_SCHEMA = BatchClassificationSchema.model_json_schema()
FUNNEL_STAGE_ANALYSIS_SCHEMA = ContentAnalysisSchema.model_json_schema()

# --- Prompt Templates ---

POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE = """You are an expert content analyst specializing in sales funnel classification. Your task is to analyze blog posts and classify them according to sales funnel stages and other content dimensions.

## Classification Framework:

### Sales Funnel Stages:
{sales_funnel_stages}

### Content Categories:
- product_features: Content highlighting specific product features or capabilities
- case_studies: Real-world examples and customer success stories
- customer_testimonials: Customer reviews, testimonials, and social proof
- pricing: Pricing information, plans, and cost-related content
- comparisons: Product comparisons with competitors
- thought_leadership: Industry insights, trends, and expert opinions
- company_news: Company announcements, updates, and news
- educational: How-to guides, tutorials, and educational content

### User Intent:
- informational: Seeking information or learning
- navigational: Looking for specific pages or resources
- transactional: Ready to make a purchase or take action
- commercial: Researching products/services before purchase
- comparison: Comparing different options or solutions
- research: Conducting in-depth research on topics
- problem_solving: Seeking solutions to specific problems

### Content Depth:
- beginner: Basic concepts and introductory content
- intermediate: Moderate complexity requiring some background
- advanced: Complex concepts for experienced users
- expert: Highly technical content for specialists

## Output Format:
Provide your analysis in the following JSON schema:
{schema}

## Instructions:
1. Analyze each post carefully considering title, content, and context
2. Classify each post into the appropriate sales funnel stage
3. Assign content category, user intent, and depth level
4. Provide confidence scores (0.0-1.0) for your classifications
5. Include brief reasoning for each classification decision
6. Ensure all classifications are consistent and well-reasoned"""

POST_CLASSIFICATION_USER_PROMPT_TEMPLATE = """Please analyze and classify the following batch of blog posts:

{posts_batch_json}

For each post, provide:
1. Sales funnel stage classification
2. Content category
3. User intent
4. Content depth level
5. Confidence score (0.0-1.0)
6. Brief reasoning for the classification

Focus on the content's primary purpose and how it serves users at different stages of the customer journey."""

FUNNEL_STAGE_ANALYSIS_SYSTEM_PROMPT_TEMPLATE = """You are an expert content strategist and analyst specializing in content intelligence. Your task is to perform comprehensive analysis of blog content grouped by sales funnel stage.

## Analysis Framework:

Analyze the provided content group across these dimensions:

### 1. E-E-A-T Analysis (Expertise, Experience, Authority, Trust):
- Evaluate expertise signals (author credentials, depth of knowledge)
- Assess experience demonstration (case studies, real examples)
- Identify authority indicators (citations, industry recognition)
- Measure trust elements (transparency, accuracy, citations)

### 2. Content Quality Scoring:
- Readability and clarity assessment
- Professional tone and writing quality
- Information density and value delivery
- Content depth and comprehensiveness

### 3. Question-Answer Extraction:
- Identify questions explicitly answered
- Assess voice search optimization
- Evaluate Answer Engine Optimization (AEO) compatibility
- Identify featured snippet opportunities

### 4. Entity Recognition:
- Extract people, products, companies mentioned
- Identify key topics and concepts
- Map knowledge graph opportunities
- Track industry terminology usage

### 5. Content Intent Classification:
- Determine primary content intent (informational/transactional)
- Identify secondary intents
- Assess conversion focus and CTAs
- Evaluate user journey alignment

### 6. Content Structure Elements:
- Identify content sections and patterns
- Analyze storytelling elements used
- Evaluate supporting evidence types
- Assess information hierarchy

### 7. Logical Flow & Readability:
- Evaluate logical progression of ideas
- Assess paragraph transitions
- Check heading hierarchy
- Measure content scanability
- Determine reading level

### 8. Content Gaps & Opportunities:
- Identify uncovered topics
- Find content depth gaps
- Discover audience segment gaps
- Suggest format opportunities

### 9. Competitive Intelligence:
- Extract unique value propositions
- Assess differentiation strength
- Identify competitive advantages
- Understand market positioning

### 10. Audience Engagement Potential:
- Evaluate shareability
- Identify discussion triggers
- Find emotional hooks
- Assess community building elements

## Output Format:
Provide your analysis in the following JSON schema:
{schema}

## Instructions:
1. Analyze all posts in the funnel stage group comprehensively.
2. Provide quantitative scores where specified (0-10 scale).
3. Identify specific examples and evidence for each finding; cite post titles or brief snippets where useful.
4. Populate list fields generously with high-signal items (aim for 5-10 items when applicable).
5. If a dimension is not applicable, explain why rather than omitting it.
6. Ensure all schema fields are fully populated with detailed, actionable insights (do not be brief)."""

FUNNEL_STAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Please perform a comprehensive content intelligence analysis of the following {funnel_stage} stage content group:

{posts_group_json}

Analyze this content group across ALL the following dimensions:

## Content Intelligence Analysis Required:

1. **E-E-A-T Analysis**: Evaluate expertise, experience, authority, and trust signals. Look for author credentials, case studies, citations, and credibility markers. Include concrete examples and brief quotes/snippets where helpful.

2. **Content Quality Scoring**: Assess readability, clarity, professional tone, information density, and overall writing quality. Explain major drivers behind the scores.

3. **Question-Answer Extraction**: Identify questions answered, voice search optimization, AEO compatibility, and featured snippet opportunities. Provide multiple candidates.

4. **Entity Recognition**: Extract all people, products, companies, and topics mentioned. Identify knowledge graph opportunities. Populate lists with as many relevant items as applicable.

5. **Content Intent Classification**: Determine primary and secondary intents, conversion focus, and CTA effectiveness. Reference specific sections or CTAs.

6. **Content Structure Elements**: Identify content patterns, storytelling elements, evidence types, and information hierarchy. Note any structural weaknesses.

7. **Logical Flow & Readability**: Evaluate logical progression, transitions, content scanability, and reading level. Include concrete examples of strong/weak transitions or headings.

8. **Content Gaps & Opportunities**: Find uncovered topics, depth gaps, audience segments missed, and format opportunities. Provide actionable recommendations.

9. **Competitive Intelligence**: Extract unique value props, assess differentiation, identify advantages and positioning. Reference comparable angles across posts.

10. **Audience Engagement Potential**: Evaluate shareability, discussion triggers, emotional hooks, and community building. Suggest engagement hooks.

Remember to:
- Provide specific examples from the content
- Score all metrics on a 0-10 scale where applicable
- Populate each list with multiple items (aim for 5-10 when possible)
- Explain N/A cases briefly instead of omitting
- Keep output strictly to the provided JSON schema""" 