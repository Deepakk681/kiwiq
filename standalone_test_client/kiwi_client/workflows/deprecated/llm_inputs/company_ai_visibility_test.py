from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from datetime import datetime
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# Schema definitions for web search results (intermediate output)
class WebSearchQueryResultSchema(BaseModel):
    """Individual web search query result"""
    query_text: str = Field(description="The exact query that was searched")
    search_results: List[str] = Field(description="List of URLs/sources found in search results")
    company_content_found: bool = Field(description="Whether any company content was found in results")
    information_from_company_content: str = Field(description="Information from the company content that was found in the search results")
    company_urls_found: List[str] = Field(description="Specific company URLs found in search results")
    competitor_content_found: List[str] = Field(description="Competitor URLs/content found instead")
    information_from_competitor_content: str = Field(description="Information from the competitor content that was found in the search results")
    ranking_of_company_content: int = Field(description="Ranking of the company content in the search results")
    ranking_of_competitor_content: int = Field(description="Ranking of the competitor content in the search results")
    result_summary: str = Field(description="Brief summary of what was found and any notable patterns")

class PlatformWebSearchResultsSchema(BaseModel):
    """Complete web search results from a single AI platform"""
    queries_with_company_content: int = Field(description="Number of queries where company content was found")
    queries_with_competitor_content: int = Field(description="Number of queries where competitor content was found")
    query_results: List[WebSearchQueryResultSchema] = Field(description="Detailed results for each query tested")
    overall_findings: str = Field(description="Summary of overall visibility patterns and insights")

class AiVisibilityWebSearchSchema(BaseModel):
    """Complete web search results from AI visibility testing across platforms"""
    company_name: str = Field(description="Name of the company being tested")
    platform_results: List[PlatformWebSearchResultsSchema] = Field(description="Results from each AI platform tested")

# Generate schema for the web search results output
WEB_SEARCH_GENERATION_SCHEMA = AiVisibilityWebSearchSchema.model_json_schema()

# Schema definitions adapted for company AI visibility testing
# Company AI Visibility Baseline Report
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


# Generate schema for the output
GENERATION_SCHEMA = CompanyAiBaselineSchema.model_json_schema()

# AI Visibility Test Prompt Template for Company Visibility
AI_VISIBILITY_TEST_PROMPT = """
Test company visibility in AI platforms for company presence and recognition:

Company: {company_name}
Website: {website_url}
Positioning: {positioning_headline}
Target Audience (ICP): {icp}
Competitors: {competitors}

Based on your understanding of the company, its industry positioning, and competitive landscape, generate the most relevant and effective queries that potential customers, industry professionals, or stakeholders might use to discover or evaluate the company. Select queries that best test the visibility and recognition of the company in AI platforms.

**TASK:**
1. Generate 5-8 strategic test queries covering different search intents and user personas
2. For each query, perform a web search to see what content appears
3. Analyze the search results to identify:
   - Whether company content appears
   - What competitor content appears instead
   - The specific URLs and sources found
   - Patterns in visibility and positioning

**OUTPUT FORMAT:**
Respond with structured JSON following the AiVisibilityWebSearchSchema:
- Platform name and timestamp
- Detailed results for each query tested
- Summary statistics and overall findings
- Cross-platform insights if testing multiple platforms

Focus on testing actual queries with web search to identify gaps in AI visibility for the company's overall presence and market positioning.
"""

# System prompt for AI test prompt generation
AI_TEST_PROMPT_GENERATION_SYSTEM = """You are an expert AI visibility testing specialist focused on company presence and market positioning. Your role is to generate comprehensive, strategically-designed test queries that evaluate how well a company appears in AI platform search results.

Key Responsibilities:
1. **Strategic Query Generation**: Create queries that potential customers and industry professionals would naturally use when searching for companies in the target industry
2. **Competitive Intelligence**: Design queries that reveal how the company's presence competes against competitors in AI search results
3. **Market Positioning Gap Analysis**: Identify specific query patterns where the company should have strong visibility
4. **Stakeholder Simulation**: Generate queries that mirror actual stakeholder search behavior and intent

Guidelines for Query Creation:
- Focus on company-specific terminology and industry positioning
- Include both broad market-awareness queries and specific company-focused queries
- Test variations of how customers might search for solutions the company provides
- Consider different stakeholder personas and their search patterns
- Include competitive comparison queries
- Test both direct company queries and indirect market-based queries

**OUTPUT REQUIREMENTS:**
You must respond with structured JSON output conforming to the AiVisibilityWebSearchSchema. Your response should include:
- Detailed web search results for each query tested
- Specific URLs and sources found in search results
- Analysis of whether company content appears vs competitor content
- Summary statistics and insights about visibility patterns

**SCHEMA:**
```json
{schema}
```

Your output should be comprehensive test queries that effectively evaluate the company's AI visibility across multiple search scenarios and competitive landscapes, with all results structured according to the provided schema."""

# System prompt for the analysis
SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI visibility analyst specializing in company presence and market positioning across AI platforms like ChatGPT and Perplexity. Your role is to analyze how companies appear in AI search results and provide actionable insights for improving visibility.

Analyze the test results and provide detailed recommendations. Respond strictly with JSON output conforming to the schema:
```json
{schema}
```
"""

# User prompt template for the analysis
USER_PROMPT_TEMPLATE = """
As an AI visibility expert, analyze the provided structured web search results to generate a comprehensive company AI visibility report. 

**Company Context:**
{company_context}

**PERPLEXITY PLATFORM RESULTS:**
{perplexity_results}

**CHATGPT PLATFORM RESULTS:**
{chatgpt_results}

**Analysis Requirements:**

1. **Platform Results Analysis:**
   - Extract and analyze query results from the structured web search data
   - Compare company content visibility across both platforms
   - Identify patterns in competitor content that appears instead
   - Assess the quality and relevance of search results for each query

2. **Visibility Gap Identification:**
   - Identify queries where company content should appear but doesn't on either platform
   - Analyze specific company content with high citation potential based on search results
   - Study competitor content patterns that achieve visibility on either platform do not limit to only the competitors listed in the company context.
   - Compare platform-specific visibility gaps and opportunities

3. **Actionable Recommendations:**
   - Provide platform-specific technical optimizations for AI visibility
   - Suggest content improvements to increase citations on both platforms
   - Recommend specific actions to improve search visibility across platforms
   - Address platform-specific optimization opportunities

**Output Format:**
Generate a structured JSON report following the CompanyAiBaselineSchema with:
- Test queries analyzed
- Platform-specific results clearly separated for ChatGPT and Perplexity
- Identified visibility gaps and citation opportunities for each platform
- Actionable recommendations for improvement tailored to each platform's behavior

**Note:** The input results are structured web search data. Extract the relevant information from the query_results arrays and platform-specific data to populate the final analysis schema.

Focus on providing concrete, actionable insights that can directly improve the company's AI visibility across both Perplexity and ChatGPT platforms.
""" 

# --- New ChatGPT Query Generation Schemas ---

class GeneratedQuerySchema(BaseModel):
    query_text: str = Field(description="The query text")

class GeneratedQueriesListSchema(BaseModel):
    queries: List[GeneratedQuerySchema] = Field(description="List of generated queries")

GENERATED_QUERIES_LIST_SCHEMA = GeneratedQueriesListSchema.model_json_schema()

# --- New ChatGPT Query Generation Prompts ---

CHATGPT_QUERY_GENERATION_USER_PROMPT_TEMPLATE = """
Given the following company context, generate a list of 8 queries that users will ask, we will use these to test AI visibility:
- 5 queries should be market/industry related (general to the sector and company positioning)
- 3 queries should be company-specific queries (direct company name searches and feature queries)
Return the queries in a structured JSON list, each with a clear query text.

Company Context:
{company_context}
"""

CHATGPT_QUERY_GENERATION_SYSTEM_PROMPT_TEMPLATE = ""

CHATGPT_SINGLE_QUERY_USER_PROMPT_TEMPLATE = "{single_query}"

CHATGPT_SINGLE_QUERY_SYSTEM_PROMPT_TEMPLATE = "" 