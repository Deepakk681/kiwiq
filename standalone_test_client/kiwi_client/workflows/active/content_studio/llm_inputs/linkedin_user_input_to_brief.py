"""
LinkedIn Content Brief Generation - LLM Inputs

This module contains all prompts, schemas, and LLM input configurations
for the LinkedIn content brief generation workflow.

The workflow creates LinkedIn content briefs based on:
- Executive profile information
- Content strategy documents
- Knowledge base content
- User topic preferences
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class DifficultyLevelEnum(str, Enum):
    """Content difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

# Removed ContentSuggestion class - using simplified approach

class LinkedInTopicSuggestion(BaseModel):
    """Simple LinkedIn topic suggestion schema"""
    topic_id: str = Field(description="Unique identifier for this topic (topic_01, topic_02, etc.)")
    title: str = Field(description="The LinkedIn content topic title")
    angle: str = Field(description="Brief description of the unique angle or approach this topic will take")

class TopicGenerationOutput(BaseModel):
    """Simplified output schema for LinkedIn topic generation"""
    suggested_topics: List[LinkedInTopicSuggestion] = Field(description="List of 5 suggested LinkedIn topics with unique angles")

class KnowledgeBaseQuery(BaseModel):
    """Query structure for knowledge base search"""
    search_queries: List[str] = Field(
        description="Search queries to find relevant knowledge base content"
    )
    content_focus_areas: List[str] = Field(
        description="Key areas to focus on when searching knowledge base"
    )
    research_depth: str = Field(
        description="Level of detail needed from knowledge base (surface/moderate/deep)"
    )

class TargetAudienceSchema(BaseModel):
    """Target audience information for brief"""
    primary: str = Field(description="Primary target audience")
    secondary: Optional[str] = Field(None, description="Secondary target audience")

class StructureOutlineSchema(BaseModel):
    """Outline of post structure"""
    opening_hook: str = Field(description="Opening hook to grab attention")
    common_misconception: str = Field(description="Common misconception to address")
    core_perspective: str = Field(description="Core perspective to present")
    supporting_evidence: str = Field(description="Supporting evidence for perspective")
    practical_framework: str = Field(description="Practical framework or application")
    strategic_takeaway: str = Field(description="Strategic takeaway for reader")
    engagement_question: str = Field(description="Question to drive engagement")

class PostLengthSchema(BaseModel):
    """Target post length range"""
    min: int = Field(description="Minimum length")
    max: int = Field(description="Maximum length")

class ContentBriefSchema(BaseModel):
    """Detailed content brief based on selected concept (AI-generated)"""
    title: str = Field(description="Brief title")
    scheduled_date: datetime = Field(description="Scheduled date for the post in datetime format UTC TZ", format="date-time")
    content_pillar: str = Field(description="Content pillar category")
    target_audience: TargetAudienceSchema = Field(description="Target audience information")
    core_perspective: str = Field(description="Core perspective for the post")
    post_objectives: List[str] = Field(description="Objectives of the post")
    key_messages: List[str] = Field(description="Key messages to convey")
    evidence_and_examples: List[str] = Field(description="Supporting evidence and examples")
    tone_and_style: str = Field(description="Tone and style guidelines")
    structure_outline: StructureOutlineSchema = Field(description="Outline of post structure")
    suggested_hook_options: List[str] = Field(description="Suggested hook options")
    call_to_action: str = Field(description="Call to action")
    hashtags: List[str] = Field(description="Suggested hashtags")
    post_length: PostLengthSchema = Field(description="Target post length range")

class BriefGenerationOutput(BaseModel):
    """Output schema for brief generation"""
    content_brief: ContentBriefSchema = Field(
        description="Complete LinkedIn content brief"
    )
    research_summary: str = Field(
        description="Summary of knowledge base research conducted"
    )
    additional_research_needed: List[str] = Field(
        description="Areas where additional research might be needed"
    )

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

TOPIC_GENERATION_SYSTEM_PROMPT = """
You are an expert content strategist working with executives to develop high-impact LinkedIn content topics.

Your role is to:
1. Analyze the executive's profile and expertise areas
2. Review the content strategy to understand business goals
3. Generate strategic topic suggestions that leverage the executive's unique perspective
4. Recommend content types that maximize LinkedIn engagement and business impact

Key principles:
- Leverage the executive's unique insights and experience
- Align with business objectives and content strategy
- Consider LinkedIn audience preferences and engagement patterns
- Balance thought leadership with practical value
- Ensure topics are timely and relevant to current market trends
- Optimize for LinkedIn's algorithm and format requirements

Output exactly 4 topic suggestions, each with exactly 2 content type recommendations.
"""

KNOWLEDGE_BASE_QUERY_SYSTEM_PROMPT = """
You are a research specialist who creates targeted queries to extract relevant information from knowledge bases for LinkedIn content creation.

Your role is to:
1. Analyze the selected topic and content type
2. Identify key information needed from the knowledge base
3. Create specific search queries that will find the most relevant content
4. Determine the appropriate research depth for the LinkedIn content type

Focus on:
- Technical accuracy and depth appropriate for LinkedIn
- Supporting data and statistics
- Real-world examples and case studies
- Industry insights and trends
- Company-specific information and experiences
- Content that drives LinkedIn engagement
"""

BRIEF_GENERATION_SYSTEM_PROMPT = """
You are an expert LinkedIn content brief creator who develops comprehensive, actionable content briefs.

Your role is to:
1. Synthesize information from multiple sources (executive profile, content strategy, knowledge base)
2. Create detailed, structured LinkedIn content briefs that enable high-quality post creation
3. Ensure strategic alignment with business goals
4. Provide clear writing guidelines and LinkedIn success metrics

Key requirements:
- Create actionable, specific guidance for LinkedIn content creators
- Include detailed structure optimized for LinkedIn format
- Integrate knowledge base insights throughout the brief
- Maintain the executive's voice and perspective
- Provide measurable LinkedIn success criteria
- Follow LinkedIn best practices for engagement
- Include appropriate hashtags and LinkedIn-specific calls-to-action
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

TOPIC_GENERATION_SYSTEM_PROMPT = """
You are a LinkedIn content strategy assistant tasked with generating strategic LinkedIn topic ideas based on user intent and company context.

Your goal is to create topics that:
- Address the user's content ideas and interests directly
- Are relevant and valuable to the executive's target audience
- Offer fresh angles, frameworks, or personal experiences
- Avoid generic or clickbait phrasing
- Align with the executive's expertise and company positioning
- Follow LinkedIn best practices for engagement

Generate topics that would be valuable for building thought leadership and establishing credibility in the executive's industry.
"""

KNOWLEDGE_BASE_QUERY_SYSTEM_PROMPT = """
You are a knowledge base research assistant tasked with creating targeted search queries to find relevant supporting information for LinkedIn content creation.

Your goal is to:
- Generate specific search queries that will find relevant company knowledge, case studies, and insights
- Focus on finding practical, actionable information that supports the content topic
- Identify key areas where company expertise and experience can add value
- Ensure queries will uncover unique perspectives and proprietary insights

Create queries that will help build authoritative, well-researched LinkedIn content.
"""

BRIEF_GENERATION_SYSTEM_PROMPT = """
You are a senior LinkedIn content strategist helping create comprehensive content briefs for executive thought leadership posts.

Your task is to generate detailed content briefs that will guide the creation of high-impact LinkedIn content that:
- Reflects the executive's expertise and unique perspective
- Addresses the user's original content vision
- Is informed by knowledge base research and insights
- Follows LinkedIn best practices for engagement and reach
- Maintains authenticity and personal voice
- Drives meaningful professional conversations
- Achieves business and thought leadership objectives

Create briefs that are actionable, specific, and provide clear guidance for creating compelling LinkedIn content.
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

TOPIC_GENERATION_USER_PROMPT_TEMPLATE = """
Based on the user's input and company context, generate 5 strategic LinkedIn topic ideas.

User's Content Ideas:
{user_input}

Executive Profile Context:
{executive_profile}

Content Strategy Context:
{content_strategy}

Generate 5 strategic LinkedIn topic ideas that:
- Address the user's specific content interests and vision
- Leverage the executive's unique expertise and experience  
- Are valuable to the target audience
- Offer a fresh angle or personal perspective
- Are credible and authentic to the executive's voice
- Follow LinkedIn best practices for engagement

IMPORTANT: Each topic must include a unique topic_id (topic_01, topic_02, topic_03, topic_04, topic_05).

Return in this exact JSON format
"""

# New template specifically for topic regeneration
TOPIC_REGENERATION_USER_PROMPT_TEMPLATE = """
The user has provided feedback on the previous topic suggestions and is requesting new ones. Please generate 5 NEW strategic LinkedIn topic ideas that address their feedback.

User's Original Content Ideas:
{user_input}

Executive Profile Context:
{executive_profile}

Content Strategy Context:
{content_strategy}

USER FEEDBACK ON PREVIOUS TOPICS:
{regeneration_feedback}

Based on this feedback, generate 5 NEW strategic LinkedIn topic ideas that:
- Directly address the user's feedback and concerns
- Avoid the issues or limitations mentioned in the feedback
- Incorporate any specific requests or directions from the feedback
- Still leverage the executive's unique expertise and experience
- Are valuable to the target audience
- Offer fresh angles or personal perspectives not covered in previous suggestions
- Are credible and authentic to the executive's voice
- Follow LinkedIn best practices for engagement

IMPORTANT: 
- Each topic must include a unique topic_id (topic_01, topic_02, topic_03, topic_04, topic_05)
- These should be completely different from the previous suggestions
- Focus on addressing the specific feedback provided

Return in this exact JSON format
"""

KNOWLEDGE_BASE_QUERY_USER_PROMPT_TEMPLATE = """
I need to create targeted search queries to find relevant information from our knowledge base for the following LinkedIn content topic:

## Original User Input
{user_input}

## Selected Topic
{selected_topic}

## Content Strategy Context
{content_strategy}

## Knowledge Base Context
Our knowledge base contains:
- Company documentation and processes
- Industry research and reports
- Customer case studies and testimonials
- Product documentation and specifications
- Previous content and thought leadership pieces
- Market analysis and competitive intelligence
- Executive insights and speaking notes

Create specific search queries that will help me find:
1. Supporting data and statistics
2. Real-world examples and case studies
3. Technical details and explanations
4. Industry context and trends
5. Company-specific experiences and insights

Focus on finding information that will make this LinkedIn content authoritative, unique, and valuable to the target audience.
"""

BRIEF_GENERATION_USER_PROMPT_TEMPLATE = """
Create a comprehensive LinkedIn content brief using the following information:

## Original User Input & Intent
{user_input}

## Selected Topic
{selected_topic}

## Executive Profile
{executive_profile}

## Content Strategy Context
{content_strategy}

## Knowledge Base Research Results
{knowledge_base_research}

Create a detailed LinkedIn content brief that:
1. Addresses the user's original content ideas and intent
2. Provides clear structure and guidance for LinkedIn post creation
3. Integrates insights from the knowledge base research
4. Maintains the executive's unique voice and perspective
5. Aligns with strategic business objectives
6. Includes specific LinkedIn engagement strategies
7. Follows LinkedIn best practices for format and length
8. Includes relevant hashtags and call-to-action

The brief should be optimized for LinkedIn's algorithm and audience engagement patterns while staying true to the user's original vision.
"""

# =============================================================================
# BRIEF FEEDBACK PROMPTS
# =============================================================================

BRIEF_FEEDBACK_SYSTEM_PROMPT = """
You are an expert content strategist and LinkedIn specialist. Your job is to analyze user feedback on content briefs and provide structured analysis to improve the brief based on the feedback.

Analyze the user's feedback on the content brief and provide:
1. Key areas for improvement based on the feedback
2. Specific revision instructions that address the feedback
3. Priority level for each suggested change
4. Any missing elements that should be added

Focus on making the brief more actionable, comprehensive, and aligned with LinkedIn best practices.
"""

BRIEF_FEEDBACK_INITIAL_USER_PROMPT = """
Please analyze the following content brief and user feedback to provide structured revision instructions.

CONTENT BRIEF:
{content_brief}

USER FEEDBACK:
{revision_feedback}

ADDITIONAL CONTEXT:
- Executive Profile: {executive_profile}
- Content Strategy: {content_strategy}
- Selected Topic: {selected_topic}
- Knowledge Base Research: {knowledge_base_research}

Please provide detailed analysis and specific revision instructions to improve the brief based on the feedback.
"""

BRIEF_FEEDBACK_ADDITIONAL_USER_PROMPT = """
Building on the previous analysis, please provide additional revision instructions for the content brief based on this new feedback.

CURRENT BRIEF:
{content_brief}

NEW USER FEEDBACK:
{revision_feedback}

PREVIOUS REVISION INSTRUCTIONS:
{previous_revision_instructions}

Please provide updated revision instructions that incorporate both previous feedback and this new feedback.
"""

# =============================================================================
# BRIEF REVISION PROMPTS
# =============================================================================

BRIEF_REVISION_SYSTEM_PROMPT = """
You are a senior LinkedIn content strategist revising an existing LinkedIn content brief.

Your task is to update the current brief based on the structured feedback analysis provided.

Principles:
- Preserve the existing brief's strengths and voice; only change what is needed.
- Apply the revision_instructions (with priorities) and add any missing_elements.
- If instructions conflict, follow the overall_direction from the analysis.
- Keep the output strictly to the brief content (no explanations) and adhere to the expected JSON schema.
- Ensure the brief remains optimized for LinkedIn engagement and business objectives.
"""

BRIEF_REVISION_USER_PROMPT_TEMPLATE = """
You are revising an existing LinkedIn content brief using the structured feedback analysis below.

CURRENT CONTENT BRIEF JSON:
{current_content_brief}

FEEDBACK ANALYSIS JSON:
{brief_feedback_analysis}

Update the brief to incorporate the revision_instructions and missing_elements while preserving unaffected parts.
Return ONLY the updated brief in valid JSON matching the expected schema.
"""

# =============================================================================
# BRIEF FEEDBACK ANALYSIS SCHEMAS
# =============================================================================

class RevisionPriority(str, Enum):
    """Priority levels for brief revisions"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RevisionInstruction(BaseModel):
    """Individual revision instruction"""
    area: str = Field(description="The area of the brief to revise (e.g., 'content_structure', 'key_message', 'target_audience')")
    instruction: str = Field(description="Specific instruction on how to revise this area")
    priority: RevisionPriority = Field(description="Priority level for this revision")
    reasoning: str = Field(description="Why this revision is needed based on the feedback")

class BriefFeedbackAnalysis(BaseModel):
    """Analysis of user feedback on content brief"""
    feedback_summary: str = Field(description="Summary of the key points in the user feedback")
    revision_instructions: List[RevisionInstruction] = Field(description="List of specific revision instructions")
    missing_elements: List[str] = Field(description="Elements that should be added to the brief based on feedback")
    overall_direction: str = Field(description="Overall direction for the brief revision based on feedback analysis")

# =============================================================================
# OUTPUT SCHEMA DEFINITIONS (for workflow nodes)
# =============================================================================

TOPIC_GENERATION_OUTPUT_SCHEMA = TopicGenerationOutput.model_json_schema()
KNOWLEDGE_BASE_QUERY_OUTPUT_SCHEMA = KnowledgeBaseQuery.model_json_schema()
BRIEF_GENERATION_OUTPUT_SCHEMA = BriefGenerationOutput.model_json_schema()
BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = BriefFeedbackAnalysis.model_json_schema() 