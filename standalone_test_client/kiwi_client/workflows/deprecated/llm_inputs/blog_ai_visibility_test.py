from typing import List
# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

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

# Schema definitions as requested
class ChatGptResultsSchema(BaseModel):
    """Results from ChatGPT testing"""
    blog_content_mentioned: bool = Field(description="Whether any blog content was referenced")
    specific_posts_cited: List[str] = Field(description="List of blog post URLs cited")
    citation_context: str = Field(description="How blog content was used in response")
    user_intent: str = Field(description="User intent covered in the response")
    competitors_mentioned: List[str] = Field(description="Competitor content cited instead")
    visibility_gaps: List[str] = Field(description="Use the information from the search results to identify gaps where company content should appear but doesn't")
    citation_opportunities: List[str] = Field(description="Blog posts that have high potential for AI citation")

class PerplexityResultsSchema(BaseModel):
    """Results from Perplexity testing"""
    blog_content_mentioned: bool = Field(description="Whether any blog content was referenced")
    specific_posts_cited: List[str] = Field(description="List of blog post URLs cited")
    citation_context: str = Field(description="How blog content was used in response")
    user_intent: str = Field(description="User intent covered in the response")
    competitors_mentioned: List[str] = Field(description="Competitor content cited instead")
    visibility_gaps: List[str] = Field(description="Use the information from the search results to identify gaps where company content should appear but doesn't")
    citation_opportunities: List[str] = Field(description="Blog posts that have high potential for AI citation")

class BlogAiVisibilityTestSchema(BaseModel):
    """Documentation of AI platform queries testing blog content visibility"""
    chatgpt_results: List[ChatGptResultsSchema] = Field(description="Results from ChatGPT testing")
    perplexity_results: List[PerplexityResultsSchema] = Field(description="Results from Perplexity testing")
    

# Generate schema for the output
GENERATION_SCHEMA = BlogAiVisibilityTestSchema.model_json_schema()

# AI Visibility Test Prompt Template
AI_VISIBILITY_TEST_PROMPT = """
Test company visibility in AI platforms for blog content:

Company: {company_name}
Website: {website_url}
Target Audience: {icps}
Competitors: {competitors}

Based on your understanding of the company, its industry, and its blog content, generate the most relevant and effective queries that a potential customer or industry professional might 
use to discover the company's expertise or solutions. Select queries that best test the visibility and citation of the company's blog content in AI platforms.

**TASK:**
1. Generate 5-8 strategic test queries covering different search intents and user personas
2. For each query, perform a web search to see what content appears
3. Analyze the search results to identify:
   - Whether company blog content appears
   - What competitor content appears instead
   - The specific URLs and sources found
   - Patterns in visibility and positioning

**OUTPUT FORMAT:**
Respond with structured JSON following the AiVisibilityWebSearchSchema:
- Platform name and timestamp
- Detailed results for each query tested
- Summary statistics and overall findings
- Cross-platform insights if testing multiple platforms

Focus on testing actual queries with web search to identify gaps in AI visibility for the company's blog content.
"""

# System prompt for AI test prompt generation
AI_TEST_PROMPT_GENERATION_SYSTEM = """You are an expert AI visibility testing specialist. Your role is to generate comprehensive, strategically-designed test queries that evaluate how well a company's blog content appears in AI platform search results.

Key Responsibilities:
1. **Strategic Query Generation**: Create queries that potential customers would naturally use when searching for solutions in the company's industry
2. **Competitive Intelligence**: Design queries that reveal how the company's content competes against competitors in AI search results
3. **Content Gap Analysis**: Identify specific query patterns where the company should have strong visibility
4. **Real-World Simulation**: Generate queries that mirror actual user search behavior and intent

Guidelines for Query Creation:
- Focus on industry-specific terminology and pain points from the ICP data
- Include both broad awareness-stage queries and specific solution-focused queries based on content distribution mix
- Test variations of how customers might describe their problems using ICP pain points
- Consider different buyer personas and their search patterns from the ICP data
- Include competitive comparison queries against the listed competitors
- Test both direct company/product queries and indirect topic-based queries
- Leverage the company's positioning and target industry information for query relevance

**OUTPUT REQUIREMENTS:**
You must respond with structured JSON output conforming to the AiVisibilityWebSearchSchema. Your response should include:
- Detailed web search results for each query tested
- Specific URLs and sources found in search results
- Analysis of whether company content appears vs competitor content
- Summary statistics and insights about visibility patterns
"""


# System prompt for the analysis
SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI visibility analyst specializing in blog content performance across AI platforms like ChatGPT and Perplexity. Your role is to analyze how company blog content appears in AI search results and provide actionable insights for improving visibility.

Analyze the test results and provide detailed recommendations. Respond strictly with JSON output conforming to the schema:
```json
{schema}
```
"""

# User prompt template for the analysis
USER_PROMPT_TEMPLATE = """
As an AI visibility expert, analyze the provided structured web search results to generate a comprehensive blog AI visibility report. 

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
   - Analyze specific blog posts with high citation potential based on search results
   - Study competitor content patterns that achieve visibility on either platform do not limit to only the competitors listed in the company context.
   - Compare platform-specific visibility gaps and opportunities

3. **Actionable Recommendations:**
   - Provide platform-specific technical optimizations for AI visibility
   - Suggest content improvements to increase citations on both platforms
   - Recommend specific actions to improve search visibility across platforms
   - Address platform-specific optimization opportunities

**Output Format:**
Generate a structured JSON report following the BlogAiVisibilityTestSchema with:
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
- 5 queries should be market/industry related (general to the sector)
- 3 queries should be company-specific blog post queries
Return the queries in a structured JSON list, each with a clear query text.

Company Context:
{company_context}
"""

CHATGPT_QUERY_GENERATION_SYSTEM_PROMPT_TEMPLATE = ""

CHATGPT_SINGLE_QUERY_USER_PROMPT_TEMPLATE = "{single_query}"

CHATGPT_SINGLE_QUERY_SYSTEM_PROMPT_TEMPLATE = ""