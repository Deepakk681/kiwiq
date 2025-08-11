"""
LLM Inputs for Content Research & Brief Generation Workflow

This file contains prompts, schemas, and configurations for the workflow that:
- Takes user input and company context
- Performs Google and Reddit research
- Generates blog topic suggestions
- Creates comprehensive content briefs
- Includes HITL approval flows
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

GOOGLE_RESEARCH_SYSTEM_PROMPT = """
You are an intelligent web analysis agent tasked with collecting high-quality, real-world insights to support research based on a user's input.

You are working on behalf of the company provided in the context. Your task is to:
1. Generate 3-5 precise research queries relevant to the company and user input
2. Perform web searches on google.com for these queries
3. Extract the top 5 most relevant and practical web resources
4. Identify headings/themes from each article and related "People Also Asked" questions

Focus on content that is:
- Practical and actionable (not theoretical or academic)
- Relevant to the company's target audience and industry
- Aligned with the company's positioning and expertise
- Free of fluff, clickbait, or generic SEO filler

You have access to web search tools. Use them to perform actual searches and gather real data.
"""

REDDIT_RESEARCH_SYSTEM_PROMPT = """
You are a research assistant tasked with understanding what real users are asking about given topics on Reddit.

Your task is to:
1. Generate 5-7 Reddit search queries based on the topics and company context
2. Search reddit.com for these queries to find real user discussions
3. Extract and analyze the most frequently asked questions
4. Group similar questions together and identify user intent
5. Provide variations of how users actually asked these questions

Focus on finding authentic user pain points, strategies, and questions relevant to the company's industry and target audience.

You have access to web search tools. Use them to perform actual searches on Reddit and gather real discussion data.
"""

TOPIC_GENERATION_SYSTEM_PROMPT = """
You are a content strategy assistant tasked with generating strategic blog topic ideas based on research insights.

Your goal is to create topics that:
- Address real search intent and user questions from the research
- Are relevant and valuable to the target audience
- Offer fresh angles, frameworks, or case study formats
- Avoid clickbait or overly generic phrasing
- Align with the company's positioning and expertise

Generate topics that would be valuable for the company's blog and help establish thought leadership in their industry.
"""

BRIEF_GENERATION_SYSTEM_PROMPT = """
You are a senior content strategist helping create a comprehensive content brief for a blog post.

Your task is to generate a detailed content brief that will guide a writer to produce high-impact content that's:
- Aligned with company goals and positioning
- Informed by real user questions and research
- Competitive in search and comprehensive in scope
- Consistent with brand tone and messaging

Create briefs that are actionable, specific, and provide clear guidance to content creators.

IMPORTANT: Do not modify the 'status' or 'run_id' fields - these are system-managed fields that should remain unchanged.
"""

TOPIC_FEEDBACK_SYSTEM_PROMPT = """
You are an expert content strategist and feedback analyst.

You have been provided with:
1. A list of blog topic suggestions
2. Feedback from the user about those topics
3. Company context including positioning and target audience
4. Research insights from Google and Reddit

Your task is to analyze the feedback and provide:
1. Clear regeneration instructions for improving the topic suggestions
2. A short, conversational message acknowledging the user's feedback and what we'll focus on improving

Always provide structured output with all required fields: regeneration_instructions and change_summary.
"""

TOPIC_FEEDBACK_INITIAL_USER_PROMPT = """
Your Task:

Your job is to interpret the feedback using all provided inputs and produce both regeneration instructions and a user-friendly change summary.

You must:
1. Identify the user's intent behind the feedback.
2. Locate specific areas in the original topic suggestions that are relevant to the feedback.
3. Determine what changes are required, guided by:
   - The company's positioning and target audience
   - The research insights from Google and Reddit
   - The original user input that initiated the research
4. Provide suggestions that are clearly implied by the feedback or align with company positioning.
5. Be precise about what should change and how topics should be regenerated.
6. Create a short, conversational message that acknowledges the user's feedback. Use a natural, friendly tone like:
   - "Got it! I'll focus on more actionable topics"
   - "I understand - let me generate topics with better ROI focus"
   - "Makes sense! I'll work on topics that are more specific to your industry"
   - "Perfect feedback! I'll make the topics more practical"

---

Provided Context:

Original Topic Suggestions: 
{suggested_blog_topics}

---

User Feedback: 
{regeneration_feedback}

---

Company Context:
- Target Audience: {icp_details}
- Value Proposition: {value_proposition}

---

Research Insights:
Google Research: {google_research_output}
Reddit Research: {reddit_research_output}
Original User Input: {user_input}
"""

TOPIC_FEEDBACK_ADDITIONAL_USER_PROMPT = """
I have provided the updated topic suggestions that were generated based on the last round of feedback.

Now, the user has provided additional feedback on this version.

Your task is to interpret the new feedback using the **same instructions and structure as before**, and write a fresh set of **regeneration instructions and change summary**.

Use the **original context** (company positioning, research insights, original user input) to stay consistent with the company's goals and target audience.

Provide the same structured output:
- regeneration_instructions: Clear instructions for improving the topics
- change_summary: Short, conversational message acknowledging the user's feedback and what you'll focus on improving

---

Updated Topic Suggestions: 
{suggested_blog_topics}

New Feedback: 
{regeneration_feedback}
"""

BRIEF_FEEDBACK_SYSTEM_PROMPT = """
You are an expert content strategist and feedback analyst.

You have been provided with:
1. A comprehensive content brief
2. Feedback from the user about that brief
3. Company context and research insights
4. The selected topic that the brief is based on

Your task is to analyze the feedback and provide:
1. Clear revision instructions for improving the content brief
2. A short, conversational message acknowledging the user's feedback and what we'll focus on improving

Always provide structured output with all required fields: revision_instructions and change_summary.

IMPORTANT: Do not modify the 'status' or 'run_id' fields in any revision instructions - these are system-managed fields that should remain unchanged.
"""

BRIEF_FEEDBACK_INITIAL_USER_PROMPT = """
Your Task:

Your job is to interpret the feedback using all provided inputs and produce both revision instructions and a user-friendly change summary.

IMPORTANT: The content brief you're analyzing below may have been manually edited by the user after the initial AI generation. This means:
- The brief might contain user modifications, corrections, or additions
- You should respect and preserve these user edits unless the feedback specifically requests changes to them
- Your revision instructions should build upon the user's manual edits, not override them
- If the feedback conflicts with user edits, prioritize the most recent feedback

You must:
1. Identify the user's intent behind the feedback.
2. Locate specific areas in the content brief (whether AI-generated or user-edited) that are relevant to the feedback.
3. Determine what changes are required, guided by:
   - The company's positioning and target audience
   - The research insights that informed the brief
   - The selected topic and its angle
   - Any existing user modifications in the brief
4. Provide suggestions that are clearly implied by the feedback.
5. Be precise about what should change in the brief and how it should be revised.
6. Create a short, conversational message that acknowledges the user's feedback. Use a natural, friendly tone like:
   - "Got it! I'll make the brief more actionable"
   - "I understand - let me focus on adding more case studies"
   - "Makes sense! I'll work on making it more specific to your audience"
   - "Perfect feedback! I'll enhance the SEO strategy"

IMPORTANT: Do not include instructions to modify the 'status' or 'run_id' fields - these are system-managed and should not be changed.

---

Provided Context:

Content Brief (may include user edits): 
{content_brief}

---

User Feedback: 
{revision_feedback}

---

Company Context:
- Target Audience: {icp_details}
- Value Proposition: {value_proposition}

---

Selected Topic: {selected_topic}

---

Research Foundation:
Google Research: {google_research_output}
Reddit Research: {reddit_research_output}
Original User Input: {user_input}
"""

BRIEF_FEEDBACK_ADDITIONAL_USER_PROMPT = """
I have provided the content brief that may include both AI-generated content and manual user edits from previous rounds.

Now, the user has provided additional feedback on this version.

IMPORTANT: The content brief below may contain user manual edits in addition to AI-generated revisions. When processing this feedback:
- Respect and preserve existing user edits unless the feedback specifically requests changes to them
- Build upon the user's manual modifications rather than overriding them  
- If new feedback conflicts with existing user edits, prioritize the most recent feedback
- Your revision instructions should enhance the brief while maintaining user intentionality

Your task is to interpret the new feedback using the **same instructions and structure as before**, and write a fresh set of **revision instructions and change summary**.

Use the **original context** (company positioning, research insights, selected topic) to stay consistent with the company's goals and content strategy.

Provide the same structured output:
- revision_instructions: Clear instructions for improving the brief while respecting existing user edits
- change_summary: Short, conversational message acknowledging the user's feedback and what you'll focus on improving

IMPORTANT: Do not include instructions to modify the 'status' or 'run_id' fields - these are system-managed and should not be changed.

---

Content Brief (with potential user edits): 
{content_brief}

New Feedback: 
{revision_feedback}
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

GOOGLE_RESEARCH_USER_PROMPT_TEMPLATE = """
Based on the company context and user input provided, perform web research and return results in the exact JSON format specified.

Company Context:
- Target Audience: {icp_details}
- Goals: {goals}

User Input: {user_input}

Tasks:
1. Generate 3-5 research queries relevant to the user input and company context
2. Search google.com for these queries
3. Extract top 5 most relevant articles/resources
4. Identify key headings from each article
5. Collect related "People Also Asked" questions

Return in this exact JSON format
"""

REDDIT_RESEARCH_USER_PROMPT_TEMPLATE = """
Based on the following inputs, perform Reddit research and return results in the exact JSON format specified.

Company Context:
- Target Audience: {icp_details}

Google Research Results: {google_research_output}
User Input: {user_input}

Tasks:
1. Generate 5-7 Reddit search queries using relevant subreddits for the industry
2. Search reddit.com for these queries (focus on last 3 months)
3. Analyze the discussions to identify frequently asked questions
4. Group similar questions and determine user intent
5. Extract variations of how users actually phrased these questions

Use relevant subreddits like: r/marketing, r/ecommerce, r/smallbusiness, r/startups, etc.
Do NOT include brand names in queries.

Return in this exact JSON format
"""

TOPIC_GENERATION_USER_PROMPT_TEMPLATE = """
Based on the research insights and company context, generate 5 strategic blog topic ideas.

Company Context:
- Target Audience: {icp_details}
- Goals: {goals}

Research Insights:
Google Research: {google_research_output}
Reddit Research: {reddit_research_output}
Original User Input: {user_input}

Generate 5 strategic blog topic ideas that:
- Address real user intent from the research
- Are valuable to the target audience
- Offer a fresh angle or framework
- Are credible and practical
- Align with the company's expertise area

IMPORTANT: Each topic must include a unique topic_id (topic_01, topic_02, topic_03, topic_04, topic_05).

Return in this exact JSON format
"""

BRIEF_GENERATION_USER_PROMPT_TEMPLATE = """
Create a comprehensive content brief for the selected blog post topic.

Company Context:
- Target Audience: {icp_details}
- Goals: {goals}

Selected Topic: {selected_topic}

Research Foundation:
Google Research: {google_research_output}
Reddit Research: {reddit_research_output}
Original User Input: {user_input}

Create a comprehensive content brief including content structure, SEO considerations, brand guidelines, and specific requirements for the writer.

IMPORTANT: Do not modify the 'status' or 'run_id' fields - these are system-managed fields that should remain unchanged.

Return in this exact JSON format
"""

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class SourceArticleSchema(BaseModel):
    """Schema for a single source article from research."""
    title: str = Field(description="Title of the article")
    url: str = Field(description="URL of the article")
    headings_covered: List[str] = Field(description="Key headings or themes covered in the article")

class GoogleResearchSchema(BaseModel):
    """Schema for Google research results."""
    research_queries: List[str] = Field(description="List of research queries used for web search")
    source_articles: List[SourceArticleSchema] = Field(description="List of relevant articles found during research")
    people_also_asked: List[str] = Field(description="Related questions from search results")

class UserQuestionSchema(BaseModel):
    """Schema for a user question from Reddit research."""
    question: str = Field(description="The user question")
    mentions: int = Field(description="Number of times this question or similar was mentioned")
    user_intent: str = Field(description="The underlying intent behind the question")
    longtail_queries: List[str] = Field(description="Long-tail variations of how users asked this question")

class RedditResearchSchema(BaseModel):
    """Schema for Reddit research results."""
    user_questions_summary: List[UserQuestionSchema] = Field(description="Summary of user questions from Reddit research")




class BlogTopicSchema(BaseModel):
    """Schema for a single blog topic suggestion."""
    topic_id: str = Field(description="Unique identifier for this topic (topic_01, topic_02, etc.)")
    title: str = Field(description="The blog topic title")
    angle: str = Field(description="Brief description of the unique angle or approach this topic will take")

class TopicSuggestionsSchema(BaseModel):
    """Schema for blog topic suggestions."""
    suggested_blog_topics: List[BlogTopicSchema] = Field(description="List of suggested blog topics with unique angles")




class ContentSectionSchema(BaseModel):
    """Schema for a content section in the brief."""
    section: str = Field(description="Name of the content section")
    description: str = Field(description="Description of what should be covered in this section")
    word_count: int = Field(description="Estimated word count for this section")

class SEOKeywordsSchema(BaseModel):
    """Schema for SEO keywords."""
    primary_keyword: str = Field(description="Primary keyword for the content")
    secondary_keywords: List[str] = Field(description="Secondary keywords to include")
    long_tail_keywords: List[str] = Field(description="Long-tail keywords for SEO")

class BrandGuidelinesSchema(BaseModel):
    """Schema for brand guidelines."""
    tone: str = Field(description="Tone of voice for the content")
    voice: str = Field(description="Brand voice characteristics")
    style_notes: List[str] = Field(description="Additional style guidelines and notes")

class ResearchSourceSchema(BaseModel):
    """Schema for a research source."""
    source: str = Field(description="Name or description of the research source")
    key_insights: List[str] = Field(description="Key insights extracted from this source")

class ContentBriefDetailSchema(BaseModel):
    """Schema for the detailed content brief."""
    title: str = Field(description="Title of the content")
    target_audience: str = Field(description="Target audience for the content")
    content_goal: str = Field(description="Primary goal of the content")
    key_takeaways: List[str] = Field(description="Key takeaways for the audience")
    content_structure: List[ContentSectionSchema] = Field(description="Detailed content structure")
    seo_keywords: SEOKeywordsSchema = Field(description="SEO keyword strategy")
    brand_guidelines: BrandGuidelinesSchema = Field(description="Brand voice and style guidelines")
    research_sources: List[ResearchSourceSchema] = Field(description="Research sources used")
    call_to_action: str = Field(description="Call to action for the content")
    estimated_word_count: int = Field(description="Estimated total word count")
    difficulty_level: str = Field(description="Content difficulty level (beginner, intermediate, advanced)")
    writing_instructions: List[str] = Field(description="Specific instructions for the writer")


# =============================================================================
# FEEDBACK ANALYSIS SCHEMAS
# =============================================================================

class TopicFeedbackAnalysisSchema(BaseModel):
    """Schema for topic feedback analysis output."""
    regeneration_instructions: str = Field(description="Clear instructions for regenerating topics based on feedback")
    change_summary: str = Field(description="Short, conversational message acknowledging the user's feedback")

class BriefFeedbackAnalysisSchema(BaseModel):
    """Schema for brief feedback analysis output."""
    revision_instructions: str = Field(description="Clear instructions for revising the brief based on feedback")
    change_summary: str = Field(description="Short, conversational message acknowledging the user's feedback")

# Convert Pydantic models to JSON schemas for LLM use
GOOGLE_RESEARCH_OUTPUT_SCHEMA = GoogleResearchSchema.model_json_schema()

REDDIT_RESEARCH_OUTPUT_SCHEMA = RedditResearchSchema.model_json_schema()

TOPIC_GENERATION_OUTPUT_SCHEMA = TopicSuggestionsSchema.model_json_schema()

BRIEF_GENERATION_OUTPUT_SCHEMA = ContentBriefDetailSchema.model_json_schema()

TOPIC_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = TopicFeedbackAnalysisSchema.model_json_schema()

BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = BriefFeedbackAnalysisSchema.model_json_schema()