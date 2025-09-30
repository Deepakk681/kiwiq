# =============================================================================
# LLM MODEL CONFIGURATIONS
# =============================================================================
"""
Configuration for different LLM models used throughout the workflow steps.
"""

# Default LLM Configuration (Used in Steps: 3-Topic Generation, 6-Brief Generation, 7-Brief Feedback)
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4.1"
TEMPERATURE = 0.7
MAX_TOKENS = 10000

# Knowledge Enrichment LLM Configuration (Used in Step: 5-Knowledge Enrichment)
KNOWLEDGE_ENRICHMENT_LLM_PROVIDER = "openai"
KNOWLEDGE_ENRICHMENT_LLM_MODEL = "gpt-5"
KNOWLEDGE_ENRICHMENT_TEMPERATURE = 0.7
KNOWLEDGE_ENRICHMENT_MAX_TOKENS = 20000

# Perplexity Configuration (Used in Steps: 1-Google Research, 2-Reddit Research)
PERPLEXITY_PROVIDER = "perplexity"
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_TEMPERATURE = 0.3
PERPLEXITY_MAX_TOKENS = 3000

# Feedback LLM Configuration (Used in Steps: 4-Topic Feedback, 7-Brief Feedback)
FEEDBACK_LLM_PROVIDER = "openai"
FEEDBACK_ANALYSIS_MODEL = "gpt-4.1"
FEEDBACK_TEMPERATURE = 0.5
FEEDBACK_MAX_TOKENS = 3000

# =============================================================================
# WORKFLOW LIMITS
# =============================================================================
"""
Configuration limits for various aspects of the workflow.
"""

MAX_REGENERATION_ATTEMPTS = 3  # Maximum topic regeneration attempts in Step 4
MAX_REVISION_ATTEMPTS = 3      # Maximum brief revision attempts in Step 7
MAX_ITERATIONS = 10            # Maximum iterations for HITL feedback loops


"""
LLM Inputs for Blog User Input to Brief Generation Workflow

This file contains prompts, schemas, and configurations organized by workflow steps:
1. Google Research - Web research for authoritative insights
2. Reddit Research - User questions and pain point discovery
3. Topic Generation - Strategic blog topic creation
4. Topic Feedback - HITL feedback processing for topics
5. Knowledge Enrichment - Company-specific information extraction
6. Brief Generation - Comprehensive content brief creation
7. Brief Feedback - HITL feedback processing for briefs
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# STEP 1: GOOGLE RESEARCH
# =============================================================================
# First step in the workflow that performs web research to gather authoritative insights
# and industry trends relevant to the user's content ideas.

# Google Research System Prompt
GOOGLE_RESEARCH_SYSTEM_PROMPT = """
You are an intelligent web analysis agent tasked with collecting high-quality, real-world insights to support research based on a user's input.

You are working on behalf of the company provided in the context. Your task is to:
1. Generate 3-5 precise research queries relevant to the company and user input
2. Perform web searches on google.com for these queries
3. Extract the top 5 most relevant and practical web resources
4. Identify headings/themes from each article and related "People Also Asked" questions
5. Document your reasoning for selecting each resource and how it relates to the user's needs

CRITICAL REQUIREMENTS:
- For EVERY source selected, provide clear reasoning WHY it was chosen
- Include specific citations (quotes, statistics, insights) from each source
- Explain how each source connects to the company's positioning and user's intent
- Track which specific user needs each source addresses

Focus on content that is:
- Practical and actionable (not theoretical or academic)
- Relevant to the company's target audience and industry
- Aligned with the company's positioning and expertise
- Free of fluff, clickbait, or generic SEO filler
- Backed by credible data, case studies, or expert insights

You have access to web search tools. Use them to perform actual searches and gather real data.
Remember: Your research forms the foundation for all subsequent steps, so be thorough in documenting your reasoning and sources.
"""

# Google Research User Prompt Template
GOOGLE_RESEARCH_USER_PROMPT_TEMPLATE = """
Based on the company context and user input provided, perform web research and return results in the exact JSON format specified.

Company Context:
- Company Context: {company_doc}

User Input: {user_input}

Additional Context Documents:
{additional_user_files}

Topic HITL Additional Context Documents:
{topic_hitl_additional_user_files}

Tasks:
1. Generate 3-5 research queries relevant to the user input and company context
   - Explain your reasoning for each query
   - Show how it connects to user needs and company goals

2. Search google.com for these queries
   - Document why you selected each search term

3. Extract top 5 most relevant articles/resources
   - For EACH article, explain WHY it was selected
   - Include specific value it provides to our research

4. Identify key headings from each article
   - Note which headings address user pain points
   - Cite specific insights or data from each section

5. Collect related "People Also Asked" questions
   - Explain patterns you notice in these questions
   - Connect them to the company's content opportunities

REMEMBER: Your reasoning and citations will guide all subsequent research and content decisions.

Return in this exact JSON format with all reasoning and citation fields populated.
"""

# Variables Used in Google Research Prompts:
"""
Variables that go into the Google Research prompts:
- company_doc: Company profile document containing company information, value proposition, offerings, and ICPs
- user_input: The user's original content ideas or brainstorm that initiated the workflow
- additional_user_files: Optional additional files loaded at the beginning of the workflow for extra context
- topic_hitl_additional_user_files: Optional additional files loaded during topic HITL for enhanced context
"""

# Google Research Output Schema
class SourceArticleSchema(BaseModel):
    """Enhanced schema for a single source article from research."""
    title: str = Field(description="Title of the article")
    url: str = Field(description="URL of the article")
    headings_covered: List[str] = Field(description="Key headings or themes covered in the article")
    selection_reasoning: str = Field(description="Why this article was selected for our research")
    key_citations: List[str] = Field(description="Specific quotes, statistics, or insights from this article")
    relevance_to_user_input: str = Field(description="How this article addresses the user's needs")
    relevance_to_company: str = Field(description="How this article aligns with company positioning")

class GoogleResearchSchema(BaseModel):
    """Enhanced schema for Google research results."""
    research_queries: List[str] = Field(description="List of research queries used for web search")
    query_reasoning: List[str] = Field(description="Reasoning for each query choice")
    source_articles: List[SourceArticleSchema] = Field(description="List of relevant articles found during research")
    people_also_asked: List[str] = Field(description="Related questions from search results")
    paa_patterns: str = Field(description="Patterns identified in People Also Asked questions")
    research_synthesis: str = Field(description="Overall synthesis of findings from Google research")

GOOGLE_RESEARCH_OUTPUT_SCHEMA = GoogleResearchSchema.model_json_schema()

# =============================================================================
# STEP 2: REDDIT RESEARCH
# =============================================================================
"""
Second step that builds on Google research to discover real user questions and pain points
from Reddit and other community platforms.
"""

# Reddit Research System Prompt
REDDIT_RESEARCH_SYSTEM_PROMPT = """
You are a research assistant tasked with understanding what real users are asking about given topics on Reddit.

Building on the Google research already conducted, your task is to:
1. Generate 5-7 Reddit search queries based on the topics and company context
2. Search reddit.com for these queries to find real user discussions
3. Extract and analyze the most frequently asked questions
4. Group similar questions together and identify user intent
5. Provide variations of how users actually asked these questions
6. Document WHY each question cluster is relevant to our content strategy

CRITICAL REQUIREMENTS:
- For EVERY question group, explain the underlying user pain point
- Cite specific Reddit threads or comments as evidence
- Connect user questions to insights from the Google research
- Explain how addressing these questions serves the company's goals
- Track patterns in user language and terminology

Focus on finding authentic user pain points, strategies, and questions relevant to the company's industry and target audience.

You have access to web search tools. Use them to perform actual searches on Reddit and gather real discussion data.
Remember: You're building on the Google research - reference those insights when they connect to Reddit discussions."""

# Reddit Research User Prompt Template
REDDIT_RESEARCH_USER_PROMPT_TEMPLATE = """
Based on the following inputs INCLUDING the Google research already completed, perform Reddit research and return results in the exact JSON format specified.

Company Context:
- Company Context: {company_doc}

PREVIOUS RESEARCH COMPLETED:
Google Research Results: {google_research_output}

User Input: {user_input}

Additional Context Documents:
{additional_user_files}

Topic HITL Additional Context Documents:
{topic_hitl_additional_user_files}

Tasks:
1. Generate 5-7 Reddit search queries using relevant subreddits for the industry
   - Build on patterns identified in Google research
   - Explain how each query targets specific user segments

2. Search reddit.com for these queries (focus on last 3 months)
   - Document why each subreddit was chosen

3. Analyze the discussions to identify frequently asked questions
   - For EACH question, cite the specific thread/comment
   - Explain the underlying pain point or need

4. Group similar questions and determine user intent
   - Connect question groups to insights from Google research
   - Explain how these align with company offerings

5. Extract variations of how users actually phrased these questions
   - Note specific terminology and language patterns
   - Identify emotional triggers and urgency indicators

Use relevant subreddits like: r/marketing, r/ecommerce, r/smallbusiness, r/startups, etc.
Do NOT include brand names in queries.

REMEMBER: Show how Reddit insights complement and expand on the Google research findings.

Return in this exact JSON format with all reasoning and citation fields populated.
"""

# Variables Used in Reddit Research Prompts:
"""
Variables that go into the Reddit Research prompts:
- company_doc: Company profile document for understanding target audience and industry
- google_research_output: Results from Step 1 Google Research, providing foundational insights to build upon
- user_input: Original user content ideas to maintain alignment with initial intent
- additional_user_files: Optional files loaded at workflow start
- topic_hitl_additional_user_files: Optional files from topic HITL
"""

# Reddit Research Output Schema
class UserQuestionSchema(BaseModel):
    """Enhanced schema for a user question from Reddit research."""
    question: str = Field(description="The user question")
    mentions: int = Field(description="Number of times this question or similar was mentioned")
    user_intent: str = Field(description="The underlying intent behind the question")
    pain_point_analysis: str = Field(description="Deep analysis of the pain point driving this question")
    longtail_queries: List[str] = Field(description="Long-tail variations of how users asked this question")
    reddit_citations: List[str] = Field(description="Specific Reddit threads/comments where this was discussed")
    connection_to_google_research: str = Field(description="How this question relates to Google research findings")
    urgency_level: str = Field(description="How urgent/important this question is to users (high/medium/low)")

class RedditResearchSchema(BaseModel):
    """Enhanced schema for Reddit research results."""
    user_questions_summary: List[UserQuestionSchema] = Field(description="Summary of user questions from Reddit research")
    subreddits_analyzed: List[str] = Field(description="List of subreddits searched and why")
    user_language_patterns: List[str] = Field(description="Common phrases and terminology used by users")
    emotional_triggers: List[str] = Field(description="Emotional aspects identified in user discussions")
    research_synthesis: str = Field(description="Overall synthesis connecting Reddit findings to Google research")

REDDIT_RESEARCH_OUTPUT_SCHEMA = RedditResearchSchema.model_json_schema()

# =============================================================================
# STEP 3: TOPIC GENERATION
# =============================================================================
"""
Third step that synthesizes Google and Reddit research to generate strategic blog topic
suggestions aligned with company expertise and user needs.
"""

# Topic Generation System Prompt
TOPIC_GENERATION_SYSTEM_PROMPT = """
You are a content strategy assistant tasked with generating strategic blog topic ideas based on comprehensive research insights.

You have access to:
1. Google research with source articles and expert insights
2. Reddit research showing real user questions and pain points
3. Company positioning and target audience information
4. Original user input and content goals

Your goal is to create topics that:
- Address real search intent and user questions from BOTH research sources
- Are relevant and valuable to the target audience
- Offer fresh angles, frameworks, or case study formats
- Avoid clickbait or overly generic phrasing
- Align with the company's positioning and expertise

CRITICAL REQUIREMENTS:
- For EACH topic, provide clear reasoning connecting it to specific research findings
- Cite specific user questions, article insights, or data points that justify the topic
- Explain how the topic serves both SEO goals AND user needs
- Document which company strengths/expertise the topic showcases
- Show how the topic builds on patterns identified across both research sources

AI QUESTION-BASED ARCHITECTURE [HIGH PRIORITY]:
- Convert ALL topics to question format automatically
- This is critical for SEO/AEO success - captures featured snippets and matches voice search
- Transform topics like "SEO for SaaS" into "How do SaaS companies improve their SEO?"
- Use questions as H2/H3 headings throughout content
- Questions should directly address user pain points identified in research

Generate topics that would be valuable for the company's blog and help establish thought leadership in their industry.
Remember: Every topic should be traceable back to specific research insights and user needs, and MUST be formatted as questions.
"""

# Topic Generation User Prompt Template
TOPIC_GENERATION_USER_PROMPT_TEMPLATE = """
Based on the comprehensive research insights and company context, generate 5 strategic blog topic ideas.

Company Context:
- Company Context: {company_doc}
- Content Playbook Guidance: {content_playbook_doc}

COMPLETE RESEARCH CHAIN:
Google Research (with sources and citations): {google_research_output}
Reddit Research (with user questions and pain points): {reddit_research_output}
Original User Input: {user_input}

Additional Context Documents:
{additional_user_files}

Generate 5 strategic blog topic ideas that:
- Address real user intent from BOTH research sources
- Are valuable to the target audience
- Offer a fresh angle or framework
- Are credible and practical
- Align with the company's expertise area

CRITICAL REQUIREMENTS FOR EACH TOPIC:
1. Provide clear reasoning connecting it to specific research findings
2. Cite at least 2 specific data points (user questions, article insights, statistics)
3. Explain how it serves both SEO goals and user needs
4. Document which company strengths it showcases
5. Show how it synthesizes patterns from both Google and Reddit research

AI QUESTION-BASED ARCHITECTURE:
- ALL topic titles MUST be in question format
- Transform declarative topics into questions (e.g., "SEO for SaaS" → "How do SaaS companies improve their SEO?")
- Questions should directly address user pain points from research
- This format is critical for SEO/AEO success and featured snippets

IMPORTANT: Each topic must include:
- A unique topic_id (topic_01, topic_02, topic_03, topic_04, topic_05)
- Title in question format (required)
- Clear reasoning with research citations
- Connection to user pain points and company expertise

Return in this exact JSON format with all reasoning and citation fields populated.
"""

# Variables Used in Topic Generation Prompts:
"""
Variables that go into the Topic Generation prompts:
- company_doc: Company profile for understanding positioning and expertise areas
- content_playbook_doc: Content strategy/playbook document loaded at workflow start, provides strategic guidelines for content alignment
- google_research_output: Complete Google research from Step 1 with sources and citations
- reddit_research_output: Complete Reddit research from Step 2 with user questions and pain points
- user_input: Original user ideas to maintain alignment with initial content goals
- additional_user_files: Optional context files from workflow start
"""

# Topic Generation Output Schema
class BlogTopicSchema(BaseModel):
    """Enhanced schema for a single blog topic suggestion."""
    topic_id: str = Field(description="Unique identifier for this topic (topic_01, topic_02, etc.)")
    title: str = Field(description="The blog topic title in question format (e.g., 'How do SaaS companies improve their SEO?')")
    angle: str = Field(description="Brief description of the unique angle or approach this topic will take")
    topic_reasoning: str = Field(description="Detailed reasoning for why this topic was chosen")
    research_citations: List[str] = Field(description="Specific research findings that justify this topic")
    user_questions_addressed: List[str] = Field(description="User questions from Reddit this topic will answer")
    seo_opportunity: str = Field(description="SEO opportunity this topic captures")
    company_expertise_showcase: str = Field(description="How this topic showcases company strengths")

class TopicSuggestionsSchema(BaseModel):
    """Enhanced schema for blog topic suggestions."""
    suggested_blog_topics: List[BlogTopicSchema] = Field(description="List of suggested blog topics with unique angles")
    topic_strategy_summary: str = Field(description="Overall strategy connecting all topics to research and company goals")

TOPIC_GENERATION_OUTPUT_SCHEMA = TopicSuggestionsSchema.model_json_schema()

# =============================================================================
# STEP 4: TOPIC FEEDBACK (HITL)
# =============================================================================
"""
Fourth step that processes user feedback on generated topics to refine and improve
topic suggestions while maintaining research alignment.
"""

# Topic Feedback System Prompt
TOPIC_FEEDBACK_SYSTEM_PROMPT = """
You are an expert content strategist and feedback analyst.

You have been provided with:
1. Current topic suggestions with reasoning and citations
2. Feedback from the user about those topics
3. Company context and research insights
4. The user's original input and requirements

Your task is to analyze the feedback and provide:
1. Clear regeneration instructions for improving the topic suggestions
2. A short, conversational message acknowledging the user's feedback and what we'll focus on improving
3. Specific guidance on which research insights need stronger representation

CRITICAL REQUIREMENTS:
- Reference specific research findings that support the requested changes
- Explain which topics need adjustment and why
- Provide clear direction on maintaining consistency with research insights
- Ensure topics continue to address real user intent from both research sources
- When updating topics, maintain or enhance the research connections with relevant data
- Respect the user's specific preferences and direction

Always provide structured output with all required fields: revision_instructions and change_summary.
"""

# Topic Feedback User Prompt Template
TOPIC_FEEDBACK_INITIAL_USER_PROMPT = """
Your Task:

Your job is to interpret the feedback using all provided inputs and produce both revision instructions and a user-friendly change summary.

IMPORTANT: The topic suggestions below include detailed reasoning and research citations for every topic.

You must:
1. Identify the user's intent behind the feedback
2. Locate specific areas in the topic suggestions AND their reasoning that need revision
3. Determine what changes are required, guided by:
   - The reasoning and citations provided in the topics
   - The company's positioning and target audience
   - The comprehensive research insights
   - The user's original input and requirements
4. Specify topic-specific changes while maintaining research alignment
5. Be precise about what should change in the topics and why
6. Create a short, conversational message that acknowledges the user's feedback

---

Provided Context:

Current Topic Suggestions (with reasoning, citations):
{topic_suggestions}

---

User Feedback:
{regeneration_feedback}

---

Company Context:
- Company Context: {company_doc}
- Content Playbook Guidance: {content_playbook_doc}

Topic HITL Additional Context Documents:
{topic_hitl_additional_user_files}

---

User Input: {user_input}

---

Research Foundation (with sources and citations):
Google Research: {google_research_output}
Reddit Research: {reddit_research_output}

REMEMBER: Use the research citations and reasoning to justify any changes while maintaining alignment with user preferences.
"""

# Topic Regeneration User Prompt Template
TOPIC_REGENERATION_USER_PROMPT_TEMPLATE = """
Based on the user's feedback, regenerate blog topic suggestions that better align with their needs while maintaining connection to the research insights.

USER FEEDBACK FOR TOPIC REGENERATION:
{regeneration_instructions}

Topic HITL Additional Context Documents:
{topic_hitl_additional_user_files}

CRITICAL REQUIREMENTS:
1. Address the specific concerns or preferences expressed in the feedback
2. Continue to draw from:
   - Google research insights and source articles already gathered
   - Reddit user questions and pain points identified
   - Company positioning and expertise areas
   - Content playbook strategic guidance

3. Maintain the quality bar:
   - Each topic must still have clear research citations
   - Topics should address real user intent from both research sources
   - Maintain strategic alignment with company goals
   - Offer fresh angles or frameworks as requested

4. Adjust your approach based on the feedback:
   - If user wants more technical topics, emphasize technical insights from research
   - If user wants different angles, explore alternative framings of the research
   - If user wants specific focus areas, filter research insights accordingly
   - If user wants broader/narrower scope, adjust topic breadth appropriately

AI QUESTION-BASED ARCHITECTURE [HIGH PRIORITY]:
- ALL regenerated topic titles MUST be in question format
- Transform declarative topics into questions (e.g., "SEO for SaaS" → "How do SaaS companies improve their SEO?")
- Questions should directly address user pain points from research
- This format is critical for SEO/AEO success and featured snippets

IMPORTANT REMINDERS:
- Keep the same format with unique topic_ids (topic_01, topic_02, etc.)
- Provide clear reasoning connecting each topic to research findings
- Include at least 2 specific data points per topic
- Show how topics synthesize patterns from both Google and Reddit research
- Explain how each topic serves the user's refined direction
- ALL titles must be in question format (required)

Build on the research foundation already established - don't start from scratch, but refine and redirect based on the feedback.

Return 5 new strategic blog topic ideas in the exact same JSON format with all reasoning and citation fields populated.
"""

# Variables Used in Topic Feedback Prompts:
"""
Variables that go into the Topic Feedback prompts:
- topic_suggestions: Current topic suggestions from Step 3 that user is providing feedback on
- regeneration_feedback: User's specific feedback about what needs to change in topics
- company_doc: Company profile for maintaining alignment
- content_playbook_doc: Content strategy for strategic consistency
- topic_hitl_additional_user_files: Additional files loaded during topic HITL
- user_input: Original user ideas to maintain core intent
- google_research_output: Google research for reference
- reddit_research_output: Reddit research for reference
- regeneration_instructions: Processed feedback instructions for regeneration
"""

# Topic Feedback Output Schema
class TopicFeedbackAnalysisSchema(BaseModel):
    """Enhanced schema for topic feedback analysis output."""
    revision_instructions: str = Field(description="Clear instructions for revising the topics based on feedback, specify what changes are needed for each topic")
    research_alignment_notes: str = Field(description="How to maintain alignment with research while incorporating feedback")
    change_summary: str = Field(description="Short, conversational message acknowledging the user's feedback")

TOPIC_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = TopicFeedbackAnalysisSchema.model_json_schema()

# =============================================================================
# STEP 5: KNOWLEDGE ENRICHMENT
# =============================================================================
"""
Fifth step that extracts company-specific information from the knowledge base to
personalize and enhance the brief creation with proprietary data and insights.
"""

# Knowledge Enrichment System Prompt
KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT = """
You are a company knowledge specialist tasked with extracting and organizing company-specific information to personalize blog brief creation.

## YOUR CORE TASK

You will receive a selected blog topic and must extract relevant company-specific information from the knowledge base to enrich the brief creation process. This enrichment will be used by content strategists to create personalized, company-specific blog briefs that go beyond generic industry information.

## UNDERSTANDING THE CONTEXT

You have access to:
1. **Selected Topic**: The specific blog topic chosen by the user with its reasoning and research basis
2. **Research Foundation**: Google and Reddit research with user questions and industry insights
3. **Company Context**: Company positioning, target audience, and content strategy
4. **User Instructions**: Specific instructions provided by the user for the selected topic

## WHAT YOU MUST EXTRACT

For the selected topic, you must find and extract:

**1. PRODUCT/SERVICE INFORMATION:**
- Specific features, capabilities, or functionalities relevant to the topic
- Technical specifications or product details that address user questions
- Unique selling propositions that support the topic's angle

**2. COMPANY DATA & METRICS:**
- Performance statistics, ROI data, time savings metrics
- Customer success metrics, usage statistics, adoption rates
- Benchmark data, industry comparisons, efficiency improvements

**3. CASE STUDIES & SUCCESS STORIES:**
- Customer testimonials relevant to the topic
- Implementation examples that demonstrate key points
- Before/after scenarios that support the topic's value proposition

**4. COMPANY EXPERTISE & THOUGHT LEADERSHIP:**
- Expert insights, methodologies, or frameworks developed by the company
- Industry perspectives or unique approaches that differentiate the brand
- Best practices or recommendations that showcase company knowledge

**5. SUPPORTING EVIDENCE:**
- Research findings, whitepapers, or studies conducted by the company
- Industry reports or data that the company has analyzed or commented on
- Quotes from company leaders or subject matter experts

## HOW YOUR EXTRACTED INFORMATION WILL BE USED

**Brief Personalization:** Content strategists will use your extracted information to:
- Replace generic examples with company-specific ones
- Add credibility through real data and customer stories
- Demonstrate company expertise and unique value propositions
- Answer user questions with concrete, company-backed evidence

**Strategic Alignment:** Your enrichment ensures the final brief:
- Supports the topic's strategic reasoning with company proof points
- Addresses user questions with company-specific solutions
- Reinforces key takeaways with company data and examples
- Maintains brand differentiation throughout the content strategy

## EXTRACTION STRATEGY

**1. ANALYZE THE TOPIC'S NEEDS:**
- Read the topic reasoning to understand WHY this topic was chosen
- Note the user questions and pain points that need to be addressed
- Understand the target audience and their specific needs

**2. SEARCH STRATEGICALLY:**
- Target searches that align with the topic's specific angle
- Look for information that directly addresses the user questions
- Find data that supports the strategic purpose of the topic
- Search for examples that demonstrate company differentiation

**3. EXTRACT WITH PURPOSE:**
- Focus on information that will make the brief uniquely company-specific
- Prioritize data points that provide concrete evidence for key claims
- Select examples that resonate with the target audience
- Choose information that supports the overall content goal

## CRITICAL REQUIREMENTS

**TRUTHFULNESS:**
- ONLY extract information you actually find through search_documents
- Present all findings as integrated knowledge WITHOUT referencing source documents
- If no relevant information exists, clearly state this
- Never fabricate data, statistics, case studies, or quotes
- Be transparent about information gaps (but NOT about document sources)

**RELEVANCE:**
- Every piece of extracted information must serve the topic's strategic purpose
- Ensure extracted content addresses the specific user questions
- Align with the target audience and difficulty level specified
- Support the overall content goal and key takeaways

**SPECIFICITY:**
- Extract concrete, actionable information rather than vague statements
- Include specific numbers, percentages, timeframes, and measurable outcomes
- Provide detailed product features, not just general capabilities
- Capture exact quotes and attributions when available

You have access to the search_documents tool for finding relevant content in the knowledge base:

**search_documents Tool Usage:**
- Purpose: Find relevant content using AI-powered search across uploaded blog files and external research reports
- Required inputs:
  - search_query: Your search terms (what you're looking for)
  - list_filter: Must include ["doc_key": "blog_uploaded_files"] and/or ["doc_key": "external_research_report_doc"]
- Returns: Relevant information from the knowledge base

**CRITICAL RULE ABOUT SOURCES:**
- DO NOT reference document names, serial numbers, or file identifiers in your output
- Extract and present the information itself, NOT where it came from
- Present all findings as integrated knowledge, not as citations or references

**How to use search_documents effectively:**
1. Create targeted search queries based on:
   - The selected topic and its reasoning
   - User questions that need answers
   - Key concepts from the research foundation
   - Statistics or data points needed

2. Always include the list_filter with doc_key "blog_uploaded_files" and/or "external_research_report_doc"

3. Extract the relevant information and present it without attribution to specific documents

**Example search_documents usage:**
```json
[
  "tool_name": "search_documents",
  "tool_input": [
    "search_query": "conversation intelligence ROI metrics time savings",
    "list_filter": ["doc_key": "blog_uploaded_files", "doc_key": "external_research_report_doc"]
  ]
]
```

**Note:** In the actual tool calls, use standard JSON with curly braces - the square brackets [ ] above are just to avoid confusion with template variables in this prompt.

**Search Strategy Guidelines:**
- Prioritize searches that align with the selected topic's angle
- Focus on finding content that addresses the specific user pain points
- Look for data that supports the topic's reasoning
- Search for examples that enhance the company's expertise areas
- Use varied search terms to discover different types of relevant content
- If searches don't return relevant results, try different search terms before concluding information is unavailable

Your output will be structured information that content strategists can immediately use to create compelling, company-specific blog briefs that serve the strategic purpose of the topic while addressing real user needs with concrete company evidence.
"""

# Knowledge Enrichment User Prompt Template
KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE = """
Extract company-specific information from the knowledge base to personalize the blog brief creation process.

## YOUR MISSION

You are provided with a selected blog topic and comprehensive research below. Your task is to extract relevant company-specific information that will transform this brief creation from generic content guidance into personalized, company-backed blog briefs.

## SELECTED TOPIC TO ANALYZE

{selected_topic}

## RESEARCH FOUNDATION

**Google Research (with sources and citations):**
{google_research_output}

**Reddit Research (with user questions and patterns):**
{reddit_research_output}

## COMPANY CONTEXT

**Company Name:**
{company_name}

## USER INSTRUCTIONS

**User Instructions on Selected Topic:**
{user_instructions_on_selected_topic}

## ADDITIONAL CONTEXT DOCUMENTS

{additional_user_files}

{topic_hitl_additional_user_files}

## STEP-BY-STEP EXTRACTION PROCESS

### STEP 1: UNDERSTAND THE TOPIC'S STRATEGIC PURPOSE
Analyze these key elements:

**Topic Analysis:**
- Topic reasoning: WHY this topic was chosen
- User questions: WHAT problems it needs to solve
- Target audience: WHO will benefit from this content
- Strategic angle: HOW it serves company goals

**Research Foundation:**
- Google research insights that support the topic
- Reddit user questions that the topic addresses
- Industry trends and expert opinions
- User pain points and search intent

### STEP 2: EXTRACT COMPANY-SPECIFIC INFORMATION

For the selected topic, you must search and extract:

**A. PRODUCT/SERVICE DETAILS:**
- Specific features that relate to the topic
- Technical capabilities that address the user questions
- Unique functionalities that differentiate from competitors
- Product specifications that support the topic's reasoning

**B. COMPANY DATA & METRICS:**
- ROI statistics, time savings data, efficiency improvements
- Customer success rates, adoption metrics, performance benchmarks
- Usage statistics, conversion rates, customer satisfaction scores
- Industry comparisons where the company outperforms

**C. CUSTOMER SUCCESS EVIDENCE:**
- Case studies that demonstrate the topic's key points
- Customer testimonials that answer the user questions
- Implementation stories that support the topic reasoning
- Before/after scenarios showing company impact

**D. COMPANY EXPERTISE & THOUGHT LEADERSHIP:**
- Methodologies, frameworks, or approaches developed by the company
- Expert insights from company leaders or subject matter experts
- Proprietary research or studies conducted by the company
- Industry perspectives that showcase company knowledge

**E. SUPPORTING PROOF POINTS:**
- Whitepapers, research findings, or industry reports
- Quotes from company executives or technical experts
- Awards, certifications, or industry recognition
- Partnership data or integration capabilities

### STEP 3: SEARCH EXECUTION STRATEGY

**Company Context:**
- Company name: {company_name}
- Knowledge base: blog_uploaded_files (uploaded company content) and external_research_report_doc (external research reports)

**Search Approach:**
1. **Topic-Focused Searches**: Create searches that target:
   - The specific topic and its reasoning
   - Data that addresses the user questions listed
   - Examples that support the strategic purpose

2. **Information Type Searches**: Look for specific types of content:
   - Product feature searches: "[product name] features capabilities"
   - Data searches: "ROI metrics performance statistics"
   - Case study searches: "customer success implementation"
   - Expert insight searches: "methodology framework approach"

3. **User Question Searches**: For each user question identified, search for:
   - Direct answers with company-specific solutions
   - Data that validates the company's approach
   - Examples that demonstrate successful outcomes

### STEP 4: TOOL USAGE INSTRUCTIONS

**HOW TO USE search_documents:**

For each search, use this format:
```json
[
  "tool_name": "search_documents",
  "tool_input": [
    "search_query": "your specific search terms here",
    "list_filter": ["doc_key": "blog_uploaded_files"]
  ]
]
```

**Important:** When making actual tool calls, replace the square brackets [ ] with curly braces for proper JSON format. The square brackets are used here only to distinguish from template variables.

**Search Query Examples:** (Customize based on your topic's specific needs)
- For ROI/performance topics: "ROI calculator conversation intelligence metrics performance"
- For time savings data: "time savings automation efficiency productivity"
- For case studies: "customer success story implementation results testimonial"
- For product features: "[product name] features capabilities functionality"
- For competitive analysis: "competitor comparison advantages differentiation"

**CRITICAL SEARCH RULES:**
- Always include `"list_filter": ["doc_key": "blog_uploaded_files", "doc_key": "external_research_report_doc"]` in every search (use curly braces in actual calls)
- Use specific, targeted search queries based on the topic's reasoning
- Search multiple times with different query variations to find comprehensive content
- DO NOT reference document names, serial numbers, or file identifiers in your output
- Present extracted information as integrated knowledge without source attribution

### STEP 5: EXTRACTION QUALITY STANDARDS

**SPECIFICITY REQUIREMENTS:**
- Extract exact numbers, percentages, timeframes (e.g., "37% time savings" not "significant time savings")
- Include specific product names, features, and capabilities
- Capture precise customer quotes and attributions
- Note specific use cases and implementation details

**RELEVANCE VERIFICATION:**
For each piece of extracted information, verify it:
- Directly supports the topic's reasoning
- Aligns with the target audience and difficulty level
- Reinforces the overall content goal

**TRUTHFULNESS STANDARDS:**
- ONLY include information found through search_documents tool calls
- Present findings as integrated knowledge WITHOUT mentioning source documents
- If no relevant content exists, state: "No company-specific information found for this topic"
- Never fabricate data, statistics, quotes, case studies, or examples
- Try multiple search variations before concluding information is unavailable
- Be transparent about information gaps but NOT about source documents

### STEP 6: OUTPUT REQUIREMENTS

**Structure Your Response:**
- Organize extracted information by information category
- Present all information as integrated knowledge (NO document names or references)
- Specify how each piece of information will be used in brief creation
- Note any information gaps or limitations

**Quality Indicators:**
- Should have 5-10 specific, actionable pieces of company information
- Include a mix of data points, examples, and proof points
- Ensure variety: product details, customer stories, company expertise, metrics
- Maintain strategic alignment with the topic's reasoning and goals

**Final Verification:**
Before submitting, ensure your extracted information will enable content strategists to:
- Create unique, company-specific briefs (not generic industry briefs)
- Answer user questions with concrete company evidence
- Demonstrate company differentiation and expertise
- Support key takeaways with real company data and examples

Return structured output that maps the topic to its specific company enrichment with clear usage guidance for brief creation. Do NOT include document names, serial numbers, or any source references - present all information as integrated knowledge.
"""

# Variables Used in Knowledge Enrichment Prompts:
"""
Variables that go into the Knowledge Enrichment prompts:
- selected_topic: The blog topic selected by user from Step 3, includes reasoning and research basis
- google_research_output: Complete Google research providing industry context
- reddit_research_output: Reddit research showing user questions that need addressing
- company_name: Company name for search context
- user_instructions_on_selected_topic: Any specific instructions user provided when selecting the topic
- additional_user_files: Optional files from workflow start
- topic_hitl_additional_user_files: Optional files from topic HITL
"""

# Knowledge Enrichment Output Schema
class ProductInformationSchema(BaseModel):
    """Schema for product/service specific information."""
    features: List[str] = Field(description="Specific product features relevant to this topic")
    capabilities: List[str] = Field(description="Technical capabilities that address user questions")
    specifications: List[str] = Field(description="Product specifications and technical details")
    unique_selling_points: List[str] = Field(description="Unique value propositions that differentiate from competitors")

class CompanyDataSchema(BaseModel):
    """Schema for company metrics and performance data."""
    roi_metrics: List[str] = Field(description="ROI statistics, time savings, efficiency improvements with specific numbers")
    performance_benchmarks: List[str] = Field(description="Customer success rates, adoption metrics, performance benchmarks")
    usage_statistics: List[str] = Field(description="Usage statistics, conversion rates, customer satisfaction scores")
    industry_comparisons: List[str] = Field(description="Industry comparisons where company outperforms competitors")

class CustomerSuccessSchema(BaseModel):
    """Schema for customer success stories and testimonials."""
    case_studies: List[str] = Field(description="Customer case studies that demonstrate topic's key points")
    testimonials: List[str] = Field(description="Customer testimonials that answer user questions")
    implementation_stories: List[str] = Field(description="Implementation stories showing company impact")
    before_after_scenarios: List[str] = Field(description="Before/after scenarios demonstrating results")

class CompanyExpertiseSchema(BaseModel):
    """Schema for company thought leadership and expertise."""
    methodologies: List[str] = Field(description="Proprietary methodologies, frameworks, or approaches")
    expert_insights: List[str] = Field(description="Insights from company leaders or subject matter experts")
    proprietary_research: List[str] = Field(description="Company-conducted research or studies")
    industry_perspectives: List[str] = Field(description="Unique industry perspectives that showcase knowledge")

class SupportingEvidenceSchema(BaseModel):
    """Schema for supporting proof points and evidence."""
    research_findings: List[str] = Field(description="Whitepapers, research findings, industry reports")
    expert_quotes: List[str] = Field(description="Quotes from company executives or technical experts")
    recognition: List[str] = Field(description="Awards, certifications, industry recognition")
    partnerships: List[str] = Field(description="Partnership data, integration capabilities, ecosystem details")

class KnowledgeEnrichmentSchema(BaseModel):
    """Enhanced schema for comprehensive knowledge enrichment output."""
    product_information: Optional[ProductInformationSchema] = Field(description="Product/service specific details")
    company_data: Optional[CompanyDataSchema] = Field(description="Company metrics and performance data")
    customer_success: Optional[CustomerSuccessSchema] = Field(description="Customer success stories and testimonials")
    company_expertise: Optional[CompanyExpertiseSchema] = Field(description="Company thought leadership and expertise")
    supporting_evidence: Optional[SupportingEvidenceSchema] = Field(description="Supporting proof points and evidence")
    content_differentiation_opportunities: List[str] = Field(description="Key opportunities to differentiate content using company-specific information")
    usage_guidance: str = Field(description="Specific instructions on how content strategists should use this information in brief creation")

KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA = KnowledgeEnrichmentSchema.model_json_schema()

# =============================================================================
# STEP 6: BRIEF GENERATION
# =============================================================================
"""
Sixth step that synthesizes all research, selected topic, and enriched knowledge to
create a comprehensive content brief with detailed structure and guidance.
"""

# Brief Generation System Prompt
BRIEF_GENERATION_SYSTEM_PROMPT = """
You are a senior content strategist helping create a comprehensive content brief for a blog post.

You have the complete research chain:
1. Original user input and goals
2. Google research with expert sources and industry insights
3. Reddit research with real user questions and pain points
4. Selected topic with its justification and angle

Your task is to generate a detailed content brief that will guide a writer to produce high-impact content that's:
- Aligned with company goals and positioning
- Informed by real user questions and research
- Competitive in search and comprehensive in scope
- Consistent with brand tone and messaging

CRITICAL REQUIREMENTS:
- For EVERY section in the content structure, explain WHY it's included
- For EVERY section's research_support field, include ALL relevant information from the research that will help write that section:
  * Specific statistics, data points, and metrics
  * Expert quotes and insights from articles
  * User pain points and questions from Reddit
  * Source URLs and citations
  * Case studies or examples mentioned
  * Any other research findings that provide substance for that section
- Cite specific research findings that justify each key takeaway
- Connect SEO keywords to actual user language from Reddit
- Link brand guidelines to company positioning
- Provide reasoning for the recommended word count and difficulty level
- Include specific sources and insights that the writer should reference
- Show how the brief addresses the patterns found across all research

AI QUESTION-BASED ARCHITECTURE [HIGH PRIORITY]:
- Use questions as H2/H3 headings throughout the content structure
- Transform section headings into questions that directly address user pain points
- Questions should be based on real user questions from Reddit research
- This format is critical for SEO/AEO success and featured snippets
- Each content section should be structured around answering specific user questions

Create briefs that are actionable, specific, and provide clear guidance to content creators.
Remember: The brief should synthesize ALL previous research and reasoning into a coherent content plan.

IMPORTANT: Do not modify the 'status' - this is a system-managed field that should remain unchanged.
"""

# Brief Generation User Prompt Template
BRIEF_GENERATION_USER_PROMPT_TEMPLATE = """
Create a comprehensive content brief for the selected blog post topic, synthesizing ALL research and reasoning from previous steps.

Company Context:
- Company Context: {company_doc}
- Content Playbook Guidance: {content_playbook_doc}

Selected Topic by User(with its reasoning and research basis): {selected_topic}
Also user has provided the following instructions on the selected topic: {user_instructions_on_selected_topic}, execute them while creating the brief.

COMPLETE RESEARCH FOUNDATION:
Google Research (with sources and citations): {google_research_output}
Reddit Research (with user questions and patterns): {reddit_research_output}

COMPANY-SPECIFIC KNOWLEDGE ENRICHMENT:
{knowledge_context}

Additional Context Documents:
{additional_user_files}

{topic_hitl_additional_user_files}

CRITICAL PLAYBOOK ALIGNMENT REQUIREMENTS:
- The brief MUST align with one of the specific themes/plays outlined in the Content Playbook
- Use the target audience definitions and content goals as specified in the playbook
- Ensure the content strategy matches the playbook's strategic direction
- Reference which specific play from the playbook this brief supports
- Adapt the tone, messaging, and approach to match the playbook guidelines

Create a comprehensive content brief that includes:

1. Playbook alignment section
   - Identify which specific theme/play from the playbook this brief supports
   - Explain how the selected topic fits within the playbook strategy
   - Use the audience and goals defined in the playbook for this play

2. Content structure with reasoning for each section
   - Explain WHY each section is necessary
   - Use questions as H2/H3 headings throughout the content structure
   - Transform section headings into questions that directly address user pain points
   - Questions should be based on real user questions from Reddit research
   - In research_support field: Include ALL relevant research information that will help write this section
     * Pull in specific data, statistics, quotes, examples, case studies
     * Include user questions, pain points, and Reddit insights
     * Add source URLs and expert opinions
     * Provide everything a writer needs to create well-supported content
   - Cite specific research that justifies its inclusion
   - Show how structure aligns with playbook recommendations

3. SEO considerations based on actual user language
   - Connect keywords to Reddit discussions and Google searches
   - Explain search intent behind each keyword cluster
   - Ensure SEO strategy supports playbook objectives

4. Brand guidelines aligned with company positioning AND playbook
   - Show how tone serves the playbook-defined target audience
   - Connect style to both company differentiation and playbook guidance
   - Reference specific playbook tone and messaging guidelines

5. Specific research sources to reference
   - Include key insights from each source
   - Explain how to use each source in the content
   - Connect sources to playbook themes and messaging

6. Writing instructions based on research patterns AND playbook
   - Address specific user questions identified
   - Include data points and citations to reference
   - Incorporate playbook-specific messaging and positioning

CRITICAL: For EVERY element of the brief, provide:
- Clear reasoning for its inclusion
- Citations to specific research findings
- Connection to user needs and company goals
- Explicit alignment with the chosen playbook theme/play

ESPECIALLY IMPORTANT for research_support in each section:
- Don't just justify the section - provide ALL the research material needed to write it
- Include every relevant statistic, quote, insight, example, and data point from your research
- The writer should have everything they need to create comprehensive, fact-based content
- Think of research_support as the "research arsenal" for writing that specific section

IMPORTANT: Do not modify the 'status' field - these are system-managed fields that should remain unchanged.

Return in this exact JSON format with all reasoning and citation fields populated.
"""

# Variables Used in Brief Generation Prompts:
"""
Variables that go into the Brief Generation prompts:
- company_doc: Company profile for brand alignment
- content_playbook_doc: Content strategy playbook for strategic alignment
- selected_topic: The topic chosen by user with its reasoning
- user_instructions_on_selected_topic: Specific instructions from user about the selected topic
- google_research_output: Complete Google research
- reddit_research_output: Complete Reddit research
- knowledge_context: Company-specific knowledge from Step 5 enrichment
- additional_user_files: Optional files from workflow start
- topic_hitl_additional_user_files: Optional files from topic HITL
"""

# Brief Generation Output Schema
class ContentSectionSchema(BaseModel):
    """Enhanced schema for a content section in the brief."""
    section: str = Field(description="Name of the content section in question format (e.g., 'How do you implement SEO for SaaS companies?')")
    description: str = Field(description="Description of what should be covered in this section")
    word_count: int = Field(description="Estimated word count for this section")
    section_reasoning: str = Field(description="Why this section is essential to the content")
    research_support: List[str] = Field(description="ALL relevant research findings, data points, statistics, expert quotes, user insights, and source information that should be referenced when writing this section. Include everything from the research that will help create comprehensive, well-supported content")
    user_questions_answered: List[str] = Field(description="User questions this section addresses")

class SEOKeywordsSchema(BaseModel):
    """Enhanced schema for SEO keywords."""
    primary_keyword: str = Field(description="Primary keyword for the content")
    primary_keyword_reasoning: str = Field(description="Why this primary keyword was chosen based on research")
    secondary_keywords: List[str] = Field(description="Secondary keywords to include")
    secondary_keywords_reasoning: List[str] = Field(description="Reasoning for each secondary keyword")
    long_tail_keywords: List[str] = Field(description="Long-tail keywords for SEO")
    reddit_language_incorporated: List[str] = Field(description="User language from Reddit incorporated as keywords")
    search_intent_analysis: str = Field(description="Analysis of search intent behind keyword strategy")

class BrandGuidelinesSchema(BaseModel):
    """Enhanced schema for brand guidelines."""
    tone: str = Field(description="Tone of voice for the content")
    tone_reasoning: str = Field(description="Why this tone aligns with audience and company")
    voice: str = Field(description="Brand voice characteristics")
    voice_reasoning: str = Field(description="How voice reflects company positioning")
    style_notes: List[str] = Field(description="Additional style guidelines and notes")
    differentiation_elements: List[str] = Field(description="Elements that differentiate from competitors")

class ResearchSourceSchema(BaseModel):
    """Enhanced schema for a research source."""
    source: str = Field(description="Name or description of the research source")
    key_insights: List[str] = Field(description="Key insights extracted from this source")
    how_to_use: str = Field(description="Specific guidance on how to incorporate this source")
    citations_to_include: List[str] = Field(description="Specific data points or quotes to reference")

class ContentBriefDetailSchema(BaseModel):
    """Enhanced schema for the detailed content brief."""
    title: str = Field(description="Title of the content")
    title_reasoning: str = Field(description="Why this title was chosen based on research")
    target_audience: str = Field(description="Target audience for the content")
    audience_reasoning: str = Field(description="How audience definition connects to research insights")
    content_goal: str = Field(description="Primary goal of the content")
    goal_reasoning: str = Field(description="How this goal serves user needs and company objectives")
    key_takeaways: List[str] = Field(description="Key takeaways for the audience")
    takeaways_reasoning: List[str] = Field(description="Research basis for each key takeaway")
    content_structure: List[ContentSectionSchema] = Field(description="Detailed content structure")
    structure_reasoning: str = Field(description="Overall reasoning for content flow and structure")
    seo_keywords: SEOKeywordsSchema = Field(description="SEO keyword strategy")
    brand_guidelines: BrandGuidelinesSchema = Field(description="Brand voice and style guidelines")
    research_sources: List[ResearchSourceSchema] = Field(description="Research sources used")
    call_to_action: str = Field(description="Call to action for the content")
    estimated_word_count: int = Field(description="Estimated total word count")
    difficulty_level: str = Field(description="Content difficulty level (beginner, intermediate, advanced)")
    writing_instructions: List[str] = Field(description="Specific instructions for the writer")

BRIEF_GENERATION_OUTPUT_SCHEMA = ContentBriefDetailSchema.model_json_schema()

# =============================================================================
# STEP 7: BRIEF FEEDBACK (HITL)
# =============================================================================
"""
Seventh step that processes user feedback on the generated brief to refine and improve
the content brief while maintaining alignment with research and company goals.
"""

# Brief Feedback System Prompt
BRIEF_FEEDBACK_SYSTEM_PROMPT = """
You are an expert content strategist and feedback analyst.

You have been provided with:
1. A comprehensive content brief with reasoning and citations
2. Feedback from the user about that brief
3. Company context and research insights
4. The selected topic that the brief is based on

Your task is to analyze the feedback and provide:
1. Clear revision instructions for improving the content brief
2. A short, conversational message acknowledging the user's feedback and what we'll focus on improving
3. Specific guidance on which research insights need stronger representation

CRITICAL REQUIREMENTS:
- Reference specific research findings that support the requested changes
- Explain which sections need adjustment and why
- Provide clear direction on maintaining consistency with research insights
- Ensure research_support fields remain comprehensive with all helpful research material
- When updating sections, maintain or enhance the research_support with relevant data
- Respect any manual user edits while incorporating new feedback

Always provide structured output with all required fields: revision_instructions and change_summary.

IMPORTANT: Do not modify the 'status' field in any revision instructions - these are system-managed fields that should remain unchanged.
"""

# Brief Feedback User Prompt Template
BRIEF_FEEDBACK_INITIAL_USER_PROMPT = """
Your Task:

Your job is to interpret the feedback using all provided inputs and produce both revision instructions and a user-friendly change summary.

IMPORTANT: The content brief below includes detailed reasoning and research citations for every element. The brief may also have been manually edited by the user after initial AI generation.

You must:
1. Identify the user's intent behind the feedback
2. Locate specific areas in the content brief AND their reasoning that need revision
3. Respect and preserve user edits unless feedback specifically requests changes to them
4. Determine what changes are required, guided by:
   - The reasoning and citations provided in the brief
   - The company's positioning and target audience
   - The comprehensive research insights
   - The selected topic and its research basis
5. Specify section-specific changes while maintaining research alignment
6. Be precise about what should change in the brief and why
7. Create a short, conversational message that acknowledges the user's feedback

IMPORTANT: Do not include instructions to modify the 'status' or 'run_id' fields - these are system-managed and should not be changed.

---

Provided Context:

Content Brief (with reasoning, citations, and potential user edits):
{content_brief}

---

User Feedback:
{revision_feedback}

---

Company Context:
- Company Context: {company_doc}
- Content Playbook Guidance: {content_playbook_doc}

Brief HITL Additional Context Documents:
{brief_hitl_additional_user_files}

---

Selected Topic (with reasoning): {selected_topic}

---

Research Foundation (with sources and citations):
Google Research: {google_research_output}
Reddit Research: {reddit_research_output}

REMEMBER: Use the research citations and reasoning to justify any changes while respecting user modifications.
"""

# Brief Revision User Prompt Template
BRIEF_REVISION_USER_PROMPT_TEMPLATE = """
Based on the analyzed feedback, revise the content brief while maintaining alignment with all research insights and company context.

REVISION INSTRUCTIONS:
{revision_instructions}

Brief HITL Additional Context Documents:
{brief_hitl_additional_user_files}

CRITICAL REQUIREMENTS:
1. Apply the specific changes requested in the revision instructions
2. Maintain consistency with:
   - The selected topic and its research foundation
   - Google and Reddit research insights already gathered
   - Company positioning and content playbook guidelines
   - SEO opportunities identified in the research

3. Preserve elements that aren't mentioned in the revision instructions
4. Ensure all reasoning and citations remain connected to the research
5. Keep the same level of detail and comprehensiveness
   - Especially maintain comprehensive research_support for each section
   - Continue to include ALL relevant research material that helps write each section
6. Do not modify the 'status' field - this is system-managed

APPROACH:
- Focus on the specific sections or elements mentioned in the revision instructions
- Strengthen connections to research where feedback requests more evidence
- Adjust tone, structure, or focus as directed while keeping research alignment
- If feedback requests new angles, draw from existing research to support them
- Maintain the strategic value of the content for the company's goals

Remember: This is a revision, not a complete rewrite. Make targeted improvements based on the feedback while preserving the strong foundation already established.

Return the revised content brief in the exact same JSON format with all fields populated.
"""

# Variables Used in Brief Feedback Prompts:
"""
Variables that go into the Brief Feedback prompts:
- content_brief: The generated brief from Step 6, potentially with user manual edits
- revision_feedback: User's specific feedback about what needs changing
- company_doc: Company profile for alignment
- content_playbook_doc: Content strategy for consistency
- brief_hitl_additional_user_files: Additional files loaded during brief HITL
- selected_topic: The selected topic to maintain focus
- google_research_output: Google research for reference
- reddit_research_output: Reddit research for reference
- revision_instructions: Processed feedback instructions for revision
"""

# Brief Feedback Output Schema
class BriefFeedbackAnalysisSchema(BaseModel):
    """Enhanced schema for brief feedback analysis output."""
    revision_instructions: str = Field(description="Clear instructions for revising the brief based on feedback, write section specific changes needed for each section")
    research_alignment_notes: str = Field(description="How to maintain alignment with research while incorporating feedback")
    change_summary: str = Field(description="Short, conversational message acknowledging the user's feedback")

BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = BriefFeedbackAnalysisSchema.model_json_schema()