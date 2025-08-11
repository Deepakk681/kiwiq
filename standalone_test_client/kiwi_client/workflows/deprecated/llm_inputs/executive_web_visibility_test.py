from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from datetime import datetime
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# Schema definitions for web search results (intermediate output)
class SearchResultDetailSchema(BaseModel):
    """Detailed analysis of individual search result - extract specific data from each URL found"""
    url: str = Field(description="Complete URL of the search result (e.g., https://linkedin.com/in/executive-name)")
    title: str = Field(description="Exact title/headline as it appears in search results (e.g., 'John Smith - CEO at TechCorp | LinkedIn')")
    snippet: str = Field(description="Meta description or preview text shown in search results - copy exact text")
    platform_type: str = Field(description="Platform category: 'linkedin_profile', 'company_blog', 'news_media', 'podcast_platform', 'industry_publication', 'conference_site', 'other'")
    content_type: str = Field(description="Content format: 'profile_page', 'authored_article', 'interview_feature', 'podcast_episode', 'video_content', 'conference_bio', 'news_mention', 'company_about_page'")
    authority_signals: List[str] = Field(description="Specific authority indicators found in title/snippet: ['CEO at CompanyName', 'Keynote Speaker at EventName', 'Forbes 30 Under 30', 'Harvard MBA', 'Author of BookTitle'] - extract exact phrases")
    is_executive_owned: bool = Field(description="True if executive controls this content (their LinkedIn, company blog post by them, their personal website), False if third-party content about them")
    relevance_score: int = Field(description="How well this result matches the search query intent: 10=perfect match, 7-9=highly relevant, 4-6=somewhat relevant, 1-3=barely relevant")

class CompetitorRankingSchema(BaseModel):
        name: str = Field(description="Name of the competitor as it appears in the search result")
        position: int = Field(description="Ranking position of the competitor in the first 10 results (1-10)")
        title: str = Field(description="Title or role of the competitor as found in the search result (e.g., 'CTO at CompanyX')")

class WebSearchQueryResultSchema(BaseModel):
    """Complete results for a single search query - analyze all aspects of search performance"""
    query_text: str = Field(description="Exact search query tested including quotes if used (e.g., 'AI thought leaders 2024' or '\"John Smith\" CEO technology')")
    query_category: str = Field(description="Query type: 'branded_authority' (name + expertise), 'expertise_recognition' (industry expert searches), 'competitive_positioning' (vs other leaders), 'content_discovery' (name + content type)")
    search_engine: str = Field(description="Search platform used: 'google', 'bing', 'linkedin', 'duckduckgo'")
    total_results_count: Optional[int] = Field(description="Total number of results reported by search engine (e.g., 'About 2,450 results') - extract number only")
    first_page_results: List[SearchResultDetailSchema] = Field(description="Analysis of first 10 search results in order - must include all 10 results even if not relevant")
    executive_content_found: bool = Field(description="True if ANY executive-related content appears in first 10 results")
    executive_ranking_positions: List[int] = Field(description="All positions (1-10) where executive content appears - e.g., [1, 4, 7] if executive appears in positions 1, 4, and 7")
    best_executive_ranking: Optional[int] = Field(description="Highest ranking position for executive content (lowest number = best ranking), null if no executive content found")
    competitors_found: List[str] = Field(description="Names of other executives/companies found in first 10 results - extract exact names as they appear")
    competitor_rankings: List[CompetitorRankingSchema] = Field(description="List of competitor ranking data for each competitor in first 10 results")
    authority_signals_discovered: List[str] = Field(description="New authority signals found for executive in this search: ['Speaker at TechConf 2024', 'Featured in Forbes article', 'Podcast guest on ShowName'] - specific instances only")
    content_gaps_identified: List[str] = Field(description="Content types/topics where competitors appear but executive doesn't: ['No podcast appearances found', 'Missing from industry leader lists', 'No recent conference speaking'] - specific gaps")
    query_insights: str = Field(description="2-3 sentence analysis of what this query reveals about executive's digital positioning and opportunities")

class SearchEngineAnalysisSchema(BaseModel):
    """Complete analysis from one search engine - calculate summary metrics across all queries"""
    search_engine: str = Field(description="Search engine name: 'google', 'bing', 'linkedin', etc.")
    queries_with_executive_presence: int = Field(description="Count of queries where executive appeared in first 10 results")
    executive_first_page_dominance: float = Field(description="Calculate: (total executive-owned results across all queries) / (total first page results analyzed) * 100 - percentage of first page results executive controls")
    average_executive_ranking: Optional[float] = Field(description="Calculate average of all executive ranking positions when found - e.g., if executive ranks at positions 1, 3, 5 across queries, average = 3.0")
    top_authority_signals_found: List[str] = Field(description="Most important authority signals discovered across all queries: ['CEO of CompanyName', 'Keynote at MajorConf', 'Featured in TechCrunch'] - specific instances with context")
    main_competitors_identified: List[str] = Field(description="Executives/companies that appear most frequently across queries - rank by frequency of appearance")
    content_theme_gaps: List[str] = Field(description="Content themes where competitors dominate but executive is absent: ['AI ethics discussions', 'Future of work panels', 'Industry prediction articles'] - thematic gaps")
    query_results: List[WebSearchQueryResultSchema] = Field(description="Complete detailed results for each individual query tested")
    platform_summary: str = Field(description="2-3 sentence executive summary of executive's overall search presence on this platform, including strengths and key gaps")

class WebVisibilityWebSearchSchema(BaseModel):
    """Complete web visibility test results for executive - aggregated analysis for LinkedIn report generation"""
    executive_name: str = Field(description="Full name of executive as searched (e.g., 'John Smith' or 'Dr. Jane Doe')")
    search_engine_results: List[SearchEngineAnalysisSchema] = Field(description="Detailed results from each search engine platform tested")
    
    # Summary metrics for LinkedIn report scorecard - calculate from all search data
    overall_web_visibility_score: float = Field(description="Calculate 0-10 score based on: first page dominance (40%), authority signals count (30%), competitive positioning (30%)")
    digital_authority_signals: List[str] = Field(description="Deduplicated list of ALL authority signals found across all searches: ['CEO at CompanyX', 'Harvard MBA', 'TechCrunch featured expert', 'Conference keynote speaker'] - unique instances only")
    followers_count: int = Field(description="Number of followers the executive has on LinkedIn - find exact number, run a dedicated query if needed")
    total_google_mentions: int = Field(description="Highest 'total results count' number found across all Google queries - represents estimated total online mentions")
    first_page_control_percentage: float = Field(description="Calculate: (executive-owned results found) / (total first page results analyzed) * 100 across ALL queries")
    primary_content_platforms: List[str] = Field(description="Platforms where executive content appears most frequently, ranked by frequency: ['linkedin', 'company_blog', 'industry_publications'] - based on platform_type analysis")
    key_competitors_by_search_volume: List[str] = Field(description="Competitors who appear most frequently across all queries, ranked by total appearances - track who dominates executive's target search space")
    biggest_content_gaps: List[str] = Field(description="Most significant content/positioning gaps identified across all searches: ['No podcast presence', 'Missing from industry leader lists', 'Weak conference speaking profile'] - biggest opportunities")
    quick_win_opportunities: List[str] = Field(description="Immediate 30-day opportunities identified: ['Optimize LinkedIn headline for X keyword', 'Submit speaker bio to Y conference', 'Publish article on Z trending topic'] - specific actionable items")
    
    # Strategic insights for LinkedIn content strategy
    brand_strength_assessment: str = Field(description="3-4 sentence assessment of executive's current brand strength in search results - what's working and what's weak")
    competitive_positioning_analysis: str = Field(description="3-4 sentence analysis of how executive ranks vs competitors in search visibility - who dominates and why")
    content_strategy_recommendations: List[str] = Field(description="Top 5 content strategy recommendations based on search gap analysis: ['Create more AI ethics content to compete with Competitor X', 'Increase podcast appearances to match industry standard'] - specific strategic actions")

# Generate schema for the web search results output
WEB_SEARCH_GENERATION_SCHEMA = WebVisibilityWebSearchSchema.model_json_schema()




class SearchResultMetricsSchema(BaseModel):
    """Core search metrics across engines - requires automated search queries"""
    google_total_results: int = Field(description="Total mentions on Google - LLM task: Perform Google searches for '[executive_name]' and '[executive_name] + [company]' and count total results")
    first_page_controlled_results: int = Field(description="Results on page 1 you control (0-10) - LLM task: Analyze first 10 Google results for branded queries and count how many are executive-owned content (LinkedIn, company blog, interviews where executive is primary subject)")
    average_ranking_position: float = Field(description="Average position across key branded queries (executive name + expertise terms)")
    branded_query_dominance: float = Field(description="Percentage of branded queries where executive ranks #1 - LLM task: Test 5-7 branded queries like '[name] AI expert', '[name] CEO', '[name] [industry]' and calculate percentage where executive content ranks position 1")

class DigitalAuthorityMetricsSchema(BaseModel):
    """Web-based digital authority signals for scorecard - requires content analysis and counting"""
    web_visibility_score: float = Field(description="Overall web presence score (0-10) calculated from authority signals strength")
    google_results_count: int = Field(description="Total online mentions - same as google_total_results for consistency")
    first_page_dominance: int = Field(description="Out of 10 first page results you control - same as first_page_controlled_results")
    authority_signals: List[str] = Field(description="Key authority indicators found - LLM task: Scan search results and extract authority signals like 'CEO of [company]', 'Speaker at [event]', 'Featured in [publication]', awards, certifications")
    content_freshness_score: float = Field(description="How recent/updated content is (0-10) - LLM task: Check publication dates of top search results and score based on recency (content within 6 months = 10, 6-12 months = 7, 1-2 years = 4, older = 2)")
    speaking_engagements: int = Field(description="Number of speaking engagements found - LLM task: Search for '[executive_name] speaker' and '[executive_name] keynote' and count unique speaking events mentioned")
    podcast_appearances: int = Field(description="Number of podcast appearances - LLM task: Search for '[executive_name] podcast' and count unique podcast appearances mentioned in results")
    guest_articles: int = Field(description="Number of guest articles published - LLM task: Search for 'by [executive_name]' and '[executive_name] author' and count bylined articles on external publications")
    industry_mentions: int = Field(description="Mentions in industry publications - LLM task: Search for '[executive_name]' on industry-specific sites (TechCrunch, Forbes, VentureBeat, etc.) and count unique mentions")

class CompetitorBenchmarkSchema(BaseModel):
    """Competitor comparison data for gaps analysis - requires comparative analysis"""
    competitor_names: List[str] = Field(description="Top 3-5 industry leaders identified for comparison")
    search_dominance_gaps: List[str] = Field(description="Queries competitors own that executive doesn't - LLM task: Test industry expertise queries like '[industry] thought leader', '[technology] expert' and identify which competitors rank higher")
    content_volume_gap: str = Field(description="Qualitative assessment of content volume vs competitors - LLM task: Compare Google results count and content freshness between executive and top 3 competitors")
    authority_signal_gaps: List[str] = Field(description="Authority signals competitors have that executive lacks - LLM task: Analyze competitor search results and identify authority signals (awards, publications, speaking roles) that executive is missing")
    positioning_advantages: List[str] = Field(description="Areas where executive outperforms competitors in search results")

class WebVisibilityOpportunitiesSchema(BaseModel):
    """Web-focused opportunities categorized by timeline and effort"""
    quick_wins_30_days: List[str] = Field(description="30-day web optimization actions - LLM task: Identify immediate SEO improvements like missing schema markup, incomplete profiles, or obvious content gaps")
    power_moves_90_days: List[str] = Field(description="90-day strategic web initiatives - LLM task: Suggest content creation opportunities, guest posting targets, or speaking engagement pursuits based on gap analysis")
    game_changers_6_months: List[str] = Field(description="6-month authority building moves - LLM task: Recommend major positioning shifts like launching thought leadership content series, pursuing industry awards, or establishing new expertise areas")
    missing_credentials_from_search: List[str] = Field(description="Important qualifications not visible in search results - LLM task: Cross-reference executive's known background with what appears in search results and identify missing elements")
    seo_optimization_opportunities: List[str] = Field(description="Specific SEO improvements needed - LLM task: Identify missing keywords, weak content optimization, or technical SEO issues affecting visibility")

class WebTestQuerySchema(BaseModel):
    """Individual search query testing with competitive analysis"""
    query_text: str = Field(description="Exact search query tested")
    query_type: str = Field(description="Category: branded/expertise/industry/competitor comparison")
    executive_found_in_results: bool = Field(description="Whether executive appears in first 3 pages of results")
    ranking_position: Optional[int] = Field(description="Exact position if found (1-30), null if not found")
    competitor_analysis: str = Field(description="Who ranks above executive for this query - LLM task: Identify competing executives or companies that rank higher and analyze why")
    result_quality_assessment: str = Field(description="Quality of executive's search result (title, snippet, relevance) - LLM task: Evaluate how well the search result represents the executive's expertise")

class WebContentAnalysisSchema(BaseModel):
    """Analysis of executive's web content quality and distribution"""
    primary_content_platforms: List[str] = Field(description="Main platforms hosting executive content - LLM task: Identify where executive's content primarily lives (company blog, LinkedIn, Medium, etc.)")
    content_themes_from_web: List[str] = Field(description="Main topics executive is known for online - LLM task: Analyze search results and extract recurring themes/topics associated with executive")
    brand_consistency_score: float = Field(description="Consistency of messaging across web platforms (0-10) - LLM task: Compare bio, descriptions, and positioning across different platforms and score consistency")
    external_validation_signals: List[str] = Field(description="Third-party credibility indicators - LLM task: Find quotes about executive from others, customer testimonials, peer recognition, media coverage")

class StreamlinedWebVisibilitySchema(BaseModel):
    """Web-only analysis for LinkedIn report generation"""
    # Core metrics for scorecard
    digital_authority_metrics: DigitalAuthorityMetricsSchema = Field(description="Web authority metrics for report scorecard")
    search_result_metrics: SearchResultMetricsSchema = Field(description="Search performance data")
    
    # Content and brand analysis
    web_content_analysis: WebContentAnalysisSchema = Field(description="Analysis of executive's web content quality and themes")
    
    # Competitive analysis for gaps section
    competitor_benchmark: CompetitorBenchmarkSchema = Field(description="Competitor comparison data")
    
    # Opportunity identification for action items
    visibility_opportunities: WebVisibilityOpportunitiesSchema = Field(description="Web-focused actionable opportunities categorized by timeline")
    
    # Testing results
    test_queries: List[WebTestQuerySchema] = Field(description="Results from testing key search queries")
    
    # Overall scoring
    overall_web_visibility_score: float = Field(description="Combined web presence score (0-10) calculated from all above metrics")

# Generate schema for the output
GENERATION_SCHEMA = StreamlinedWebVisibilitySchema.model_json_schema()

# Web Visibility Test Prompt Template for Executive Content
WEB_VISIBILITY_TEST_PROMPT = """
Test executive web visibility and digital authority presence for comprehensive LinkedIn analysis report:

Executive Profile:
- Name: {full_name}
- LinkedIn Profile: {profile_url}
- Persona Tags: {persona_tags}

**PRIMARY OBJECTIVE:**
Conduct comprehensive web visibility testing to gather data for executive's LinkedIn analysis report. Focus on measuring digital authority, search dominance, and competitive positioning that will inform content strategy recommendations.

**CRITICAL SEARCH CATEGORIES TO TEST:**

1. **Branded Authority Queries** (Test 3-4):
   - "[name] [expertise area]"
   - "[name] [current title]"
   - "[name] [industry] thought leader"

2. **Expertise Recognition Queries** (Test 2-3):
   - "[industry] thought leaders 2024"
   - "best [expertise area] experts"
   - "[technology/domain] industry leaders"

3. **Competitive Positioning Queries** (Test 2-3):
   - "[expertise area] vs [competitor name]"
   - "top [industry] CEOs"
   - "[domain] expert comparison"

4. **Content Discovery Queries** (Test 1-2):
   - "[name] articles" or "[name] interviews"
   - "[name] speaking" or "[name] podcast"

**SEARCH EXECUTION REQUIREMENTS:**
- Test each query on Google and LinkedIn (minimum)
- Record first 10 results for each query
- Identify executive-owned vs competitor content
- Note authority signals (titles, credentials, media mentions)
- Track content freshness and engagement indicators

**FOCUS AREAS FOR ANALYSIS:**
- First page dominance (how many of top 10 results executive controls)
- Authority signal extraction (speaking, media, awards)
- Competitor gap identification
- Content theme recognition
- Search ranking positions
"""

# System prompt for web test prompt generation
WEB_TEST_PROMPT_GENERATION_SYSTEM = """You are a web visibility analyst specializing in executive digital authority measurement. Your role is to conduct strategic web searches that provide comprehensive data for LinkedIn content strategy analysis.

**CORE RESPONSIBILITIES:**
1. **Authority Signal Detection**: Find speaking engagements, media mentions, awards, certifications, industry recognition
2. **Competitive Intelligence**: Identify which competitors dominate expertise-based searches
3. **Content Gap Analysis**: Discover what content themes and topics the executive should be associated with but isn't
4. **Search Dominance Measurement**: Calculate first-page control and ranking positions
5. **Digital Footprint Mapping**: Map all platforms where executive has presence and authority

**QUERY STRATEGY:**
- Branded queries: Test name recognition and association strength
- Expertise queries: Test thought leadership positioning
- Competitive queries: Benchmark against industry leaders
- Content discovery: Find existing authority content
- Industry positioning: Test category leadership claims

**ANALYSIS DEPTH REQUIREMENTS:**
For each search result, extract:
- URL and platform type
- Content type (profile, article, interview, etc.)
- Authority indicators present
- Publish date and content freshness
- Engagement signals if visible
- Competitive context (who else appears)

**QUALITY STANDARDS:**
- Test minimum 8-12 strategic queries
- Cover all major search engines (Google, LinkedIn mandatory)
- Provide specific URLs and detailed content analysis
- Include quantitative metrics (rankings, counts, scores)
- Generate actionable insights for content strategy

**SCHEMA:**
```json
{schema}
```
"""

# System prompt for the analysis
SYSTEM_PROMPT_TEMPLATE = """
You are an expert web visibility analyst specializing in executive thought leadership performance across search engines and web platforms. Your role is to analyze how executive content appears in web search results and provide actionable insights for improving online visibility.

Analyze the web search results and provide detailed recommendations. Respond strictly with JSON output conforming to the schema:
```json
{schema}
```
"""

# User prompt template for the analysis
USER_PROMPT_TEMPLATE = """
As a web visibility expert, analyze the provided structured web search results to generate a comprehensive executive web visibility report. 

**Executive Context:**
{company_context}

**WEB SEARCH RESULTS:**
{web_search_results}

**Analysis Requirements:**

1. **Search Engine Performance Analysis:**
   - Extract and analyze query results from the structured web search data
   - Evaluate ranking positions across different search engines
   - Assess content freshness and authority signals
   - Analyze brand consistency across platforms
   - Determine search volume and visibility metrics

2. **Web Presence Assessment:**
   - Identify primary platforms where executive has presence
   - Evaluate content quality and engagement metrics
   - Assess authority signals and credibility markers
   - Analyze social media integration and cross-platform consistency

3. **Competitive Positioning:**
   - Compare executive's web visibility with competitor executives
   - Identify ranking gaps and opportunities
   - Analyze content volume and quality differences
   - Assess authority and credibility positioning

4. **Visibility Opportunities:**
   - Identify platform-specific optimization opportunities
   - Recommend content optimization strategies
   - Suggest SEO improvements for better ranking
   - Provide authority building recommendations

**Output Format:**
Generate a structured JSON report following the ExecutiveWebVisibilityTestSchema with:
- Test queries analyzed with actual search results
- Search engine performance metrics and rankings
- Web presence analysis across platforms
- Competitive comparison with industry executives
- Actionable visibility improvement opportunities
- Overall web visibility score and assessment

**Note:** The input results are structured web search data. Extract the relevant information from the query_results arrays and platform-specific data to populate the final analysis schema.

Focus on providing concrete, actionable insights that can directly improve the executive's web visibility across search engines and professional platforms.
""" 