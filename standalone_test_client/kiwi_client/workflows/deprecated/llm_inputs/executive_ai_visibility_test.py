from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from datetime import datetime
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

class AISearchQueryResultSchema(BaseModel):
    """Individual AI platform search query result"""
    query_text: str = Field(description="The exact query that was searched")
    ai_platform: str = Field(description="AI platform used (ChatGPT, Perplexity, Claude, Gemini)")
    search_results: List[str] = Field(description="List of URLs/sources found in AI response")
    executive_mentioned: bool = Field(description="Whether executive was mentioned in AI response")
    executive_context_in_response: str = Field(description="How executive was described/positioned in AI response")
    executive_ranking_vs_competitors: int = Field(description="Position executive appeared vs other experts mentioned (1=first, 0=not mentioned)")
    competitors_mentioned: List[str] = Field(description="Names of competing executives/experts mentioned")
    competitor_positioning: str = Field(description="How competitors were described vs executive")
    authority_signals_recognized: List[str] = Field(description="Authority signals AI recognized for executive (title, achievements, etc.)")
    expertise_areas_recognized: List[str] = Field(description="Specific expertise areas AI associated with executive")
    information_accuracy_score: float = Field(description="Accuracy of information about executive (0-10)")
    thought_leadership_indicators: List[str] = Field(description="Signs AI recognizes executive as thought leader")
    citation_sources: List[str] = Field(description="Sources AI cited when mentioning executive")
    visibility_quality: str = Field(description="Quality of executive's mention: 'prominent', 'moderate', 'minimal', 'none'")
    response_completeness: str = Field(description="AI response completeness and depth about executive")

class AIPlatformAnalysisSchema(BaseModel):
    """Complete analysis from one AI platform"""
    ai_platform: str = Field(description="Name of AI platform (ChatGPT, Perplexity, Claude, Gemini)")
    total_queries_tested: int = Field(description="Total number of queries tested")
    queries_with_executive_mention: int = Field(description="Queries where executive was mentioned")
    executive_recognition_rate: float = Field(description="Percentage of queries where executive appeared")
    average_executive_ranking: Optional[float] = Field(description="Average ranking position when executive appears")
    top_expertise_areas_recognized: List[str] = Field(description="Most recognized expertise areas")
    main_competitors_surfaced: List[str] = Field(description="Key competitors mentioned by AI")
    biographical_accuracy_issues: List[str] = Field(description="Inaccurate information AI has about executive")
    authority_recognition_strength: List[str] = Field(description="Strong authority signals AI recognizes")
    thought_leadership_gaps: List[str] = Field(description="Areas where AI doesn't recognize executive as expert")
    query_results: List[AISearchQueryResultSchema] = Field(description="Detailed results for each query")
    platform_specific_insights: str = Field(description="Key insights specific to this AI platform")

class AIVisibilityWebSearchSchema(BaseModel):
    """Complete AI visibility test results across platforms"""
    executive_name: str = Field(description="Full name of executive tested")
    test_timestamp: str = Field(description="When the test was conducted")
    total_queries_across_platforms: int = Field(description="Total queries tested across all AI platforms")
    ai_platform_results: List[AIPlatformAnalysisSchema] = Field(description="Results from each AI platform")
    
    # Cross-platform summary metrics
    overall_ai_recognition_rate: float = Field(description="Overall recognition rate across all platforms")
    most_recognized_expertise_areas: List[str] = Field(description="Expertise areas most consistently recognized")
    consistently_mentioned_competitors: List[str] = Field(description="Competitors mentioned across multiple platforms")
    cross_platform_accuracy_issues: List[str] = Field(description="Biographical inaccuracies found across platforms")
    strongest_authority_signals: List[str] = Field(description="Authority signals recognized across platforms")
    biggest_thought_leadership_gaps: List[str] = Field(description="Biggest gaps in thought leadership recognition")
# Generate schema for the web search results output
WEB_SEARCH_GENERATION_SCHEMA = AIVisibilityWebSearchSchema.model_json_schema()

# Schema definitions adapted for executive AI visibility testing
class AIRecognitionMetricsSchema(BaseModel):
    """Core AI recognition metrics for LinkedIn report scorecard"""
    overall_ai_recognition_score: float = Field(description="Combined AI visibility score (0-10) - for report scorecard")
    expert_query_performance: float = Field(description="Performance when AI asked about expertise (0-10) - for report scorecard")
    biographical_accuracy_score: float = Field(description="How accurately AI knows executive (0-10) - for report scorecard")
    thought_leadership_recognition: float = Field(description="AI recognition as thought leader (0-10) - for report scorecard")
    name_recognition_rate: float = Field(description="Percentage of platforms that recognize executive's name")

class PlatformSpecificRecognitionSchema(BaseModel):
    """Recognition metrics for individual AI platforms"""
    chatgpt_recognition_score: float = Field(description="ChatGPT recognition score (0-10)")
    perplexity_recognition_score: float = Field(description="Perplexity recognition score (0-10)")
    claude_recognition_score: float = Field(description="Claude recognition score (0-10)")
    gemini_recognition_score: float = Field(description="Gemini recognition score (0-10)")
    platform_consistency_score: float = Field(description="Consistency of recognition across platforms (0-10)")
    best_performing_platform: str = Field(description="Platform where executive has strongest recognition")
    weakest_platform: str = Field(description="Platform where executive needs most improvement")

class AICompetitiveAnalysisSchema(BaseModel):
    """AI recognition competitive analysis for report gap section"""
    ai_recognition_vs_competitors: str = Field(description="How executive's AI recognition compares to competitors")
    competitors_with_better_ai_visibility: List[str] = Field(description="Competitors who rank higher in AI recognition")
    executive_ai_advantages: List[str] = Field(description="Areas where executive outperforms competitors in AI")
    missing_from_ai_knowledge: List[str] = Field(description="Important credentials/achievements AI doesn't know")
    competitor_ai_strategies_to_emulate: List[str] = Field(description="What competitors do better in AI recognition")

class AIVisibilityOpportunitiesSchema(BaseModel):
    """AI-focused opportunities for the 3 action items in report"""
    quick_wins_30_days: List[str] = Field(description="30-day AI optimization actions (structured content, bio updates)")
    power_moves_90_days: List[str] = Field(description="90-day strategic AI visibility initiatives (content series, expertise positioning)")
    game_changers_6_months: List[str] = Field(description="6-month AI authority building moves (thought leadership campaigns)")
    content_optimization_for_ai: List[str] = Field(description="Specific content changes to improve AI recognition")
    biographical_updates_needed: List[str] = Field(description="Bio/credential information to update for AI platforms")
    expertise_positioning_gaps: List[str] = Field(description="Expertise areas to establish stronger AI recognition")

class ExpertiseRecognitionTestSchema(BaseModel):
    """Testing AI recognition of executive expertise"""
    expertise_query: str = Field(description="Query testing expertise recognition")
    platforms_tested: List[str] = Field(description="AI platforms tested for this query")
    executive_mentioned_count: int = Field(description="Number of platforms that mentioned executive")
    average_ranking_vs_competitors: float = Field(description="Average ranking vs other experts mentioned")
    accuracy_of_executive_information: float = Field(description="Accuracy of information about executive (0-10)")
    thought_leadership_indicators_found: List[str] = Field(description="Thought leadership signals AI recognized")

class StreamlinedAIVisibilityTestSchema(BaseModel):
    """AI visibility analysis results for LinkedIn report generation"""
    # Core metrics for report scorecard
    ai_recognition_metrics: AIRecognitionMetricsSchema = Field(description="AI recognition scores for LinkedIn report")
    platform_recognition: PlatformSpecificRecognitionSchema = Field(description="Platform-specific recognition analysis")
    
    # Competitive analysis for report gap section
    competitive_analysis: AICompetitiveAnalysisSchema = Field(description="AI recognition vs competitors")
    
    # Opportunity identification for report action items
    improvement_opportunities: AIVisibilityOpportunitiesSchema = Field(description="AI-focused improvement opportunities")
    
    # Testing results
    expertise_recognition_tests: List[ExpertiseRecognitionTestSchema] = Field(description="Results of expertise recognition tests")
    
    # Gap analysis for report
    missing_credentials: List[str] = Field(description="Important credentials AI doesn't recognize")
    biographical_gaps: List[str] = Field(description="Key bio info missing from AI knowledge")
    thought_leadership_topic_gaps: List[str] = Field(description="Topics where executive should be recognized but isn't")

# Generate schema for the output
GENERATION_SCHEMA = StreamlinedAIVisibilityTestSchema.model_json_schema()

# AI Visibility Test Prompt Template for Executive Content
AI_VISIBILITY_TEST_PROMPT = """
Test executive visibility and recognition across AI platforms for comprehensive LinkedIn analysis report:

Executive Profile:
- Name: {full_name}
- LinkedIn Profile: {profile_url}
- Persona Tags: {persona_tags}
- Primary Goal: {primary_goal}
- Secondary Goal: {secondary_goal}

**PRIMARY OBJECTIVE:**
Conduct comprehensive AI platform testing to measure executive recognition, expertise positioning, and competitive standing that will inform LinkedIn content strategy recommendations.

**CRITICAL QUERY CATEGORIES TO TEST:**

1. **Expert Recognition Queries** (Test 3-4):
   - "Who are the top [industry] experts?"
   - "Best [expertise area] thought leaders"
   - "[technology/domain] industry experts"
   - "Leading [field] authorities"

2. **Direct Executive Queries** (Test 2-3):
   - "[executive name] expertise"
   - "[executive name] background"
   - "What is [executive name] known for?"

3. **Competitive Comparison Queries** (Test 2-3):
   - "[executive name] vs [competitor name]"
   - "Compare [executive name] to other [industry] leaders"
   - "[industry] thought leader rankings"

4. **Topic Authority Queries** (Test 2-3):
   - "[specific expertise topic] experts"
   - "Who should I follow for [domain] insights?"
   - "[technology] implementation leaders"

**AI PLATFORM TESTING REQUIREMENTS:**
- Test each query on ChatGPT, Perplexity, Claude, and Gemini (minimum)
- Record complete AI responses for analysis
- Note executive mentions, positioning, and ranking vs competitors
- Track authority signals AI recognizes
- Identify biographical accuracy and gaps

**FOCUS AREAS FOR ANALYSIS:**
- Expert recognition rate across platforms
- Thought leadership positioning
- Competitive ranking and context
- Authority signal recognition
- Biographical accuracy assessment
- Missing credentials identification
"""

# System prompt for AI test prompt generation
AI_TEST_PROMPT_GENERATION_SYSTEM = """You are an AI visibility analyst specializing in executive thought leadership recognition across AI platforms. Your role is to conduct strategic AI platform queries that provide comprehensive data for LinkedIn content strategy analysis.

**CORE RESPONSIBILITIES:**
1. **Expert Recognition Testing**: Verify if AI platforms recognize executive as industry expert
2. **Thought Leadership Positioning**: Assess how executive is positioned vs competitors
3. **Authority Signal Recognition**: Identify what credentials/achievements AI platforms know
4. **Biographical Accuracy Assessment**: Check accuracy of executive information in AI responses
5. **Competitive Intelligence**: Map executive's standing vs industry leaders in AI responses

**QUERY STRATEGY:**
- Expert recognition queries: Test thought leadership positioning
- Direct executive queries: Test name recognition and association strength
- Competitive queries: Benchmark against industry leaders
- Topic authority queries: Test domain expertise recognition
- Comparative queries: Understand relative positioning

**ANALYSIS DEPTH REQUIREMENTS:**
For each AI response, extract:
- Whether executive is mentioned and how
- Ranking/positioning vs competitors
- Authority signals recognized
- Expertise areas associated
- Biographical accuracy
- Thought leadership indicators
- Citation sources if any

**QUALITY STANDARDS:**
- Test minimum 10-12 strategic queries
- Cover all major AI platforms (ChatGPT, Perplexity, Claude, Gemini)
- Provide complete AI response analysis
- Include quantitative scoring (recognition rates, rankings)
- Generate actionable insights for content strategy

**SCHEMA:**
```json
{schema}
```
"""
# System prompt for the analysis
SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI visibility analyst specializing in executive thought leadership performance across AI platforms. Your role is to analyze how executives are recognized and positioned in AI responses and provide actionable insights for improving AI visibility.

Analyze the test results and provide detailed recommendations for LinkedIn content strategy. Respond strictly with JSON output conforming to the StreamlinedAIVisibilityTestSchema.

Focus on:
1. **Recognition Scoring**: Calculate accurate scores for AI recognition metrics
2. **Competitive Analysis**: Compare executive positioning vs competitors in AI responses  
3. **Gap Identification**: Find missing credentials, expertise areas, and biographical info
4. **Opportunity Mapping**: Identify specific actions to improve AI recognition
5. **Platform Optimization**: Provide platform-specific recommendations

Your analysis should directly inform the LinkedIn report sections:
- AI Recognition Score for scorecard
- Competitive gaps for analysis section  
- Specific opportunities for 3 action items
```json
{schema}
```
"""

# User prompt template for the analysis
USER_PROMPT_TEMPLATE = """
As an AI visibility expert, analyze the provided AI platform search results to generate a comprehensive executive AI recognition report for LinkedIn strategy.

**Executive Context:**
{company_context}

**Perplexity Platform SEARCH RESULTS:**
{perplexity_results}

**ChatGPT Platform SEARCH RESULTS:**
{chatgpt_results}

**Analysis Requirements:**

1. **Recognition Metrics Calculation:**
   - Calculate overall AI recognition score based on mention frequency and quality
   - Assess expert query performance across platforms
   - Evaluate biographical accuracy and completeness
   - Score thought leadership recognition strength

2. **Platform-Specific Analysis:**
   - Compare recognition strength across ChatGPT, Perplexity, Claude, Gemini
   - Identify platform-specific strengths and weaknesses
   - Analyze consistency of information across platforms

3. **Competitive Intelligence:**
   - Map executive positioning vs competitors mentioned in AI responses
   - Identify competitors with stronger AI recognition
   - Analyze what makes competitors more visible to AI platforms

4. **Gap Analysis:**
   - Identify missing credentials and biographical information
   - Find expertise areas where executive should be recognized but isn't
   - Spot thought leadership topics with recognition gaps

5. **Opportunity Prioritization:**
   - Quick wins: Immediate bio/content optimizations
   - Power moves: Strategic positioning initiatives  
   - Game changers: Long-term thought leadership campaigns

**Output Format:**
Generate structured JSON following StreamlinedAIVisibilityTestSchema with:
- Quantified recognition metrics for LinkedIn report scorecard
- Competitive analysis for gap identification
- Categorized opportunities for 3 action items
- Platform-specific insights and recommendations

Focus on providing concrete, measurable insights that directly improve the executive's AI platform recognition and support LinkedIn content strategy development.
"""

# --- New ChatGPT Query Generation Schemas ---

class GeneratedQuerySchema(BaseModel):
    query_text: str = Field(description="The query text")

class GeneratedQueriesListSchema(BaseModel):
    queries: List[GeneratedQuerySchema] = Field(description="List of generated queries")

GENERATED_QUERIES_LIST_SCHEMA = GeneratedQueriesListSchema.model_json_schema()

# --- New ChatGPT Query Generation Prompts ---

CHATGPT_QUERY_GENERATION_USER_PROMPT_TEMPLATE = """
Given the following executive context, generate a list of 8 queries that users will ask, we will use these to test AI visibility:
- 5 queries should be industry/expertise related (general thought leadership and expert recognition queries)
- 3 queries should be executive-specific queries (direct name searches and biographical queries)
Return the queries in a structured JSON list, each with a clear query text.

Executive Context:
{executive_context}
"""

CHATGPT_QUERY_GENERATION_SYSTEM_PROMPT_TEMPLATE = ""

CHATGPT_SINGLE_QUERY_USER_PROMPT_TEMPLATE = "{single_query}"

CHATGPT_SINGLE_QUERY_SYSTEM_PROMPT_TEMPLATE = ""