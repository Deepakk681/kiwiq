"""
LLM Inputs for Competitor AI Visibility Testing Workflow

This file contains prompts, schemas, and configurations for the workflow that:
- Tests competitor AI visibility across platforms using web search
- Generates strategic test queries for competitor analysis
- Evaluates competitor content appearance in AI platform search results
- Identifies AI visibility gaps and competitive positioning
- Provides structured web search results for competitor analysis
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl

# =============================================================================
# WEB SEARCH SCHEMAS (INTERMEDIATE OUTPUT)
# =============================================================================

class WebSearchQueryResultSchema(BaseModel):
    """Individual web search query result"""
    query_text: str = Field(description="The exact query that was searched")
    search_results: List[str] = Field(description="List of URLs/sources found in search results")
    competitor_content_found: bool = Field(description="Whether any competitor content was found in results")
    information_from_competitor_content: str = Field(description="Information from the competitor content that was found in the search results")
    competitor_urls_found: List[str] = Field(description="Specific competitor URLs found in search results")
    other_content_found: List[str] = Field(description="Other URLs/content found instead")
    information_from_other_content: str = Field(description="Information from other content that was found in the search results")
    ranking_of_competitor_content: int = Field(description="Ranking of the competitor content in the search results")
    ranking_of_other_content: int = Field(description="Ranking of other content in the search results")
    result_summary: str = Field(description="Brief summary of what was found and any notable patterns")

class PlatformWebSearchResultsSchema(BaseModel):
    """Complete web search results from a single AI platform"""
    queries_with_competitor_content: int = Field(description="Number of queries where competitor content was found")
    queries_with_other_content: int = Field(description="Number of queries where other content was found")
    query_results: List[WebSearchQueryResultSchema] = Field(description="Detailed results for each query tested")
    overall_findings: str = Field(description="Summary of overall visibility patterns and insights")

class CompetitorAiVisibilityWebSearchSchema(BaseModel):
    """Complete web search results from competitor AI visibility testing across platforms"""
    competitor_name: str = Field(description="Name of the competitor being tested")
    platform_results: List[PlatformWebSearchResultsSchema] = Field(description="Results from each AI platform tested")

# Generate schema for the web search results output
WEB_SEARCH_GENERATION_SCHEMA = CompetitorAiVisibilityWebSearchSchema.model_json_schema()

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

COMPETITOR_AI_VISIBILITY_SYSTEM_PROMPT = """
You are an expert AI visibility testing specialist focused on competitor analysis. Your role is to generate comprehensive, strategically-designed test queries that evaluate how well a competitor's content appears in AI platform search results.

Key Responsibilities:
1. **Strategic Query Generation**: Create queries that potential customers would naturally use when searching for solutions in the competitor's industry, leveraging detailed ICP information
2. **Competitive Intelligence**: Design queries that reveal how the competitor's content competes against other companies in AI search results, especially in relation to the reference company
3. **AI Visibility Gap Analysis**: Identify specific query patterns where the competitor should have strong visibility based on their target market positioning
4. **Real-World Simulation**: Generate queries that mirror actual user search behavior and intent from the specific buyer personas identified

Guidelines for Query Creation:
- Focus on industry-specific terminology and pain points from the reference company's detailed ICP data
- Include both broad awareness-stage queries and specific solution-focused queries based on the target buyer personas
- Test variations of how customers might describe their problems using the specific pain points identified
- Consider the different buyer personas (CMO, Head of Content, VP of Marketing, Operations Lead) and their unique search patterns
- Include competitive comparison queries that test how the competitor appears when compared to the reference company
- Test both direct competitor queries and indirect topic-based queries relevant to the target industry
- Leverage the reference company's positioning, target industry, and company size information for query relevance
- Generate queries that reflect the specific goals and challenges of the target ICP

**OUTPUT REQUIREMENTS:**
You must respond with structured JSON output conforming to the CompetitorAiVisibilityWebSearchSchema. Your response should include:
- Detailed web search results for each query tested
- Specific URLs and sources found in search results
- Analysis of whether competitor content appears vs other content
- Summary statistics and insights about visibility patterns

**SCHEMA:**
```json
{schema}
```

Your output should be comprehensive test queries that effectively evaluate the competitor's AI visibility across multiple search scenarios and competitive landscapes, with all results structured according to the provided schema.
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

COMPETITOR_AI_VISIBILITY_USER_PROMPT_TEMPLATE = """
Test competitor AI visibility across platforms for competitive intelligence:

Reference Company Context:
- Company: {company_name}

Competitor to Analyze:
- Competitor Name: {competitor_name}
- Competitor Website: {competitor_website}

Based on your understanding of the reference company and it's competitor, generate the most relevant and effective queries that potential customers or industry professionals might use to discover or evaluate the competitor. Select queries that best test the visibility and recognition of the competitor in AI platforms.

**TASK:**
1. Generate 5-8 strategic test queries covering different search intents and user personas
2. For each query, perform a web search to see what content appears
3. Analyze the search results to identify:
   - Whether competitor content appears
   - What other content appears instead
   - The specific URLs and sources found
   - Patterns in visibility and positioning

**OUTPUT FORMAT:**
Respond with structured JSON following the CompetitorAiVisibilityWebSearchSchema:
- Platform name and timestamp
- Detailed results for each query tested
- Summary statistics and overall findings
- Cross-platform insights if testing multiple platforms

Focus on testing actual queries with web search to identify gaps in AI visibility for the competitor's market positioning.
"""

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================
class BrandRecognitionSchema(BaseModel):
    """Brand recognition metrics across AI platforms"""
    direct_query_accuracy: float = Field(description="Accuracy percentage for direct company queries")
    feature_description_accuracy: float = Field(description="Accuracy of product feature descriptions")
    competitor_differentiation: str = Field(description="How well AI distinguishes from competitors")

class CategoryPresenceSchema(BaseModel):
    """Presence in category-based queries"""
    mentioned_in_category: bool = Field(description="Whether mentioned in category queries")
    ranking_position: str = Field(description="Position when listed with competitors")
    context_quality: str = Field(description="Quality of context when mentioned")

class ContentCitationsSchema(BaseModel):
    """How company content is cited by AI"""
    blog_content_cited: int = Field(description="Number of times blog content cited")
    help_docs_cited: int = Field(description="Number of times help docs cited")
    third_party_citations: int = Field(description="Citations from review sites, etc.")

class ChatGPTMetricsSchema(BaseModel):
    """ChatGPT specific metrics"""
    company_mentions: int = Field(description="Number of times company is mentioned")
    content_citations: int = Field(description="Number of content citations")
    accuracy_score: float = Field(description="Accuracy of company information (0-10)")
    context_quality: str = Field(description="Quality of context when mentioned")
    competitor_comparisons: List[str] = Field(description="List of competitor comparisons made")

class PerplexityMetricsSchema(BaseModel):
    """Perplexity specific metrics"""
    company_mentions: int = Field(description="Number of times company is mentioned")
    content_citations: int = Field(description="Number of content citations")
    accuracy_score: float = Field(description="Accuracy of company information (0-10)")
    context_quality: str = Field(description="Quality of context when mentioned")
    competitor_comparisons: List[str] = Field(description="List of competitor comparisons made")

class PlatformSpecificResultsSchema(BaseModel):
    """Results broken down by AI platform"""
    chatgpt: ChatGPTMetricsSchema = Field(description="ChatGPT specific metrics")
    perplexity: PerplexityMetricsSchema = Field(description="Perplexity specific metrics")

class CompetitiveComparisonSchema(BaseModel):
    """How company compares to competitors in AI visibility"""
    top_competitors: List[str] = Field(description="List of top competitors in AI visibility")
    visibility_ranking: int = Field(description="Company's ranking among competitors")
    competitive_advantages: List[str] = Field(description="Areas where company has advantage")
    competitive_gaps: List[str] = Field(description="Areas where company lags behind")
    market_position: str = Field(description="Overall market position assessment")

class CompanyAiBaselineSchema(BaseModel):
    """Comprehensive test results showing company recognition across AI platforms"""
    brand_recognition: BrandRecognitionSchema = Field(description="Brand recognition metrics across AI platforms")
    category_presence: CategoryPresenceSchema = Field(description="Presence in category-based queries")
    content_citations: ContentCitationsSchema = Field(description="How company content is cited by AI")
    platform_specific_results: PlatformSpecificResultsSchema = Field(description="Results broken down by AI platform")
    visibility_score: float = Field(description="Overall AI visibility score (0-10)")
    competitive_comparison: CompetitiveComparisonSchema = Field(description="How company compares to competitors in AI visibility")
    baseline_timestamp: datetime = Field(description="When this baseline assessment was conducted")
    website_url: str = Field(description="Website URL of the competitor")

# Convert Pydantic models to JSON schemas for LLM use
COMPETITOR_CONTENT_ANALYSIS_OUTPUT_SCHEMA = CompanyAiBaselineSchema.model_json_schema() 