"""
LLM Inputs for Competitor Content Analysis Workflow

This file contains prompts, schemas, and configurations for the workflow that:
- Analyzes competitor blog content and content strategy
- Assesses content metrics, themes, and positioning
- Evaluates SEO performance and AI visibility
- Identifies content gaps and competitive positioning
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

COMPETITOR_CONTENT_ANALYSIS_SYSTEM_PROMPT = """
You are an expert content strategist and competitive intelligence analyst tasked with conducting a comprehensive analysis of a competitor's blog content and content strategy.

Your role is to:
1. Analyze the competitor's blog/content section thoroughly
2. Assess their content production metrics and publishing patterns
3. Identify their main content themes, narrative, and positioning strategy
4. Evaluate their SEO performance and optimization approach
5. Assess their AI visibility and recognition across AI platforms
6. Identify content gaps and opportunities compared to the reference company
7. Analyze their competitive positioning and differentiation claims
8. Provide a quality assessment of their content depth and authority

You have access to Perplexity search tools to gather comprehensive, real-time data about the competitor's content strategy.

Focus on providing actionable insights that can inform content strategy decisions and identify opportunities for competitive advantage.

Be thorough in your analysis and provide specific, data-driven insights wherever possible.
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

COMPETITOR_CONTENT_ANALYSIS_USER_PROMPT_TEMPLATE = """

site:{competitor_website}

Conduct a comprehensive competitive content analysis for the following company:

Competitor to Analyze:
- Competitor Name: {competitor_name}
- Competitor Website: {competitor_website}

Analysis Requirements:

1. CONTENT METRICS ANALYSIS:
   - Research their blog/content section thoroughly
   - Analyze posting frequency and content velocity over the past 3-6 months
   - Assess average word count and content length patterns
   - Identify content format mix (blogs, case studies, whitepapers, etc.)

2. CONTENT THEMES & STRATEGY:
   - Identify their primary brand narrative and positioning
   - Map out their main topic clusters and content pillars
   - Analyze their apparent content strategy approach
   - Identify unique angles or positioning they use

3. SEO PERFORMANCE ASSESSMENT:
   - Evaluate their blog's SEO health and optimization
   - Identify keywords they appear to target
   - Assess content optimization quality
   - Analyze technical SEO implementation

4. AI VISIBILITY ANALYSIS:
   - Research how often their content appears in AI platform responses
   - Assess their recognition level across AI tools (ChatGPT, Claude, Perplexity, etc.)
   - Evaluate citation rates and expert recognition
   - Identify categories where they dominate AI responses

5. CONTENT GAPS IDENTIFICATION:
   - Compare their content coverage to the reference company
   - Identify topics they cover that the reference company doesn't
   - Analyze content formats and engagement strategies they use
   - Assess their authority building approaches

6. COMPETITIVE POSITIONING:
   - Look for direct comparisons or mentions of the reference company
   - Identify how they differentiate from competitors
   - Analyze their positioning strategy and market narrative
   - Assess their competitive messaging approach

7. CONTENT QUALITY ASSESSMENT:
   - Evaluate content depth and expertise demonstration
   - Assess originality and thought leadership
   - Identify authority signals and credibility markers
   - Analyze engagement indicators and content performance

Use Perplexity search extensively to gather comprehensive, up-to-date information about the competitor's content strategy and performance.

Return your analysis in the exact JSON format specified in the schema.
"""

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================
# PART 1: CONTENT STRATEGY & SALES FUNNEL SCHEMAS
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

# COMPLETE CONTENT ANALYSIS SCHEMA - PORTFOLIO LEVEL
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict

# Enums for content strategy
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

# PART 1: CONTENT STRATEGY ANALYSIS
class CategoryTopicsSchema(BaseModel):
    """Topics covered within a specific content category"""
    category: ContentCategory = Field(description="Content category")
    topics_covered: List[str] = Field(description="List of topics covered in this category")
    post_count: int = Field(description="Number of posts in this category")
    target_keywords: List[str] = Field(description="Primary keywords targeted in this category")

class SalesFunnelContentSchema(BaseModel):
    """Content analysis for a specific sales funnel stage"""
    funnel_stage: SalesFunnelStage = Field(description="Sales funnel stage")
    total_posts: int = Field(description="Total posts targeting this funnel stage")
    categories: List[CategoryTopicsSchema] = Field(description="Content categories and their topics within this funnel stage")
    user_intents_served: List[UserIntent] = Field(description="User intents addressed in this funnel stage")

class ContentStrategyAnalysis(BaseModel):
    """Complete content strategy analysis across sales funnel"""
    total_posts: int = Field(description="Total number of posts analyzed")
    funnel_stages: List[SalesFunnelContentSchema] = Field(description="Content analysis by sales funnel stage")
    
    # Summary metrics
    most_covered_topics: List[str] = Field(description="Top 10 most frequently covered topics")
    primary_keywords_targeted: List[str] = Field(description="Main keywords being targeted across content")
    content_distribution: Dict[SalesFunnelStage, int] = Field(description="Number of posts per funnel stage")

# PART 2: SEO & CONTENT OPTIMIZATION ANALYSIS
class ContentStructureMetrics(BaseModel):
    """Content structure and organization metrics"""
    # Content length and structure
    average_word_count: int = Field(description="Average word count across posts")
    posts_with_proper_hierarchy: bool = Field(description="Posts with proper H1-H6 hierarchy")

    # FAQ implementation
    posts_with_faq: bool = Field(description="Posts with FAQ sections")
    total_faq_questions: int = Field(description="Total FAQ questions across all content")
    
    # Content organization
    posts_with_lists: bool = Field(description="Posts using numbered or bullet lists")
    posts_with_toc: bool = Field(description="Posts with table of contents")
    average_sections_per_post: float = Field(description="Average number of sections/headings per post")

    average_title_length: int = Field(description="Average title tag length")

# MASTER SCHEMA - COMPLETE CONTENT ANALYSIS
class CompleteContentAnalysis(BaseModel):
    """Master schema for complete content portfolio analysis"""
    
    # Part 1: Content Strategy Analysis
    content_strategy: ContentStrategyAnalysis = Field(description="Sales funnel → Categories → Topics analysis")
    
    # Part 2: SEO & Content Optimization Analysis  
    seo_analysis: ContentStructureMetrics = Field(description="SEO structure, optimization, and technical metrics")
    

# Convert Pydantic models to JSON schemas for LLM use
COMPETITOR_CONTENT_ANALYSIS_OUTPUT_SCHEMA = CompleteContentAnalysis.model_json_schema() 