"""
Enhanced LinkedIn Content Brief Generation Schemas with Reasoning Fields
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

# =============================================================================
# ENHANCED SCHEMAS WITH REASONING
# =============================================================================

class LinkedInTopicSuggestion(BaseModel):
    """Enhanced LinkedIn topic suggestion with reasoning"""
    topic_id: str = Field(description="Unique identifier for this topic (topic_01, topic_02, etc.)")
    title: str = Field(description="The LinkedIn content topic title")
    angle: str = Field(description="Brief description of the unique angle or approach this topic will take")
    
    # NEW: Reasoning fields
    topic_reasoning: str = Field(
        description="Why this topic is relevant to the user's request and target audience"
    )
    angle_reasoning: str = Field(
        description="Why this specific angle will resonate and differentiate the content"
    )

class TopicGenerationOutput(BaseModel):
    """Enhanced output with overall strategy reasoning"""
    suggested_topics: List[LinkedInTopicSuggestion] = Field(
        description="List of 5 suggested LinkedIn topics with unique angles"
    )
    # NEW: Overall reasoning
    strategy_reasoning: str = Field(
        description="Overall rationale for the topic selection strategy based on user input and business goals"
    )

class KnowledgeBaseQuery(BaseModel):
    """Enhanced query structure with research reasoning"""
    search_queries: List[str] = Field(
        description="Search queries to find relevant knowledge base content"
    )
    content_focus_areas: List[str] = Field(
        description="Key areas to focus on when searching knowledge base"
    )
    research_depth: str = Field(
        description="Level of detail needed from knowledge base (surface/moderate/deep)"
    )
    
    # NEW: Research reasoning
    query_strategy_reasoning: str = Field(
        description="Why these specific queries will uncover the most relevant supporting information"
    )
    focus_area_reasoning: str = Field(
        description="Why these focus areas are critical for this content piece"
    )

class TargetAudienceSchema(BaseModel):
    """Enhanced target audience with selection reasoning"""
    primary: str = Field(description="Primary target audience")
    secondary: Optional[str] = Field(None, description="Secondary target audience")
    
    # NEW: Audience reasoning
    audience_selection_reasoning: str = Field(
        description="Why this audience segmentation will maximize content impact"
    )
    audience_pain_points: List[str] = Field(
        description="Key pain points this content addresses for the target audience"
    )

class StructureOutlineSchema(BaseModel):
    """Enhanced outline with structural reasoning"""
    opening_hook: str = Field(description="Opening hook to grab attention")
    hook_reasoning: str = Field(description="Why this hook will capture immediate attention")
    
    common_misconception: str = Field(description="Common misconception to address")
    
    core_perspective: str = Field(description="Core perspective to present")
    
    supporting_evidence: str = Field(description="Supporting evidence for perspective")
    
    practical_framework: str = Field(description="Practical framework or application")
    framework_reasoning: str = Field(description="Why this framework is actionable and memorable")
    
    strategic_takeaway: str = Field(description="Strategic takeaway for reader")
    takeaway_reasoning: str = Field(description="Why this takeaway drives business value")
    
    engagement_question: str = Field(description="Question to drive engagement")
    question_reasoning: str = Field(description="Why this question will spark meaningful discussion")


class PostLengthSchema(BaseModel):
    """Target post length range"""
    min: int = Field(description="Minimum length")
    max: int = Field(description="Maximum length")

class ContentBriefSchema(BaseModel):
    """Enhanced content brief with comprehensive reasoning"""
    title: str = Field(description="Brief title")
    
    scheduled_date: datetime = Field(description="Scheduled date for the post in datetime format UTC TZ")
    
    content_pillar: str = Field(description="Content pillar category")
    
    target_audience: TargetAudienceSchema = Field(description="Target audience information")
    
    core_perspective: str = Field(description="Core perspective for the post")
    perspective_value_proposition: str = Field(
        description="The unique value this perspective brings to the audience"
    )
    
    post_objectives: List[str] = Field(description="Objectives of the post")
    
    key_messages: List[str] = Field(description="Key messages to convey")
    message_hierarchy_reasoning: str = Field(
        description="Why these messages are prioritized in this order"
    )
    
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
You are a strategic LinkedIn content advisor specializing in executive thought leadership.

Your expertise includes:
- Analyzing market trends and audience psychology
- Identifying content gaps and opportunities
- Creating differentiated angles on common topics
- Optimizing for LinkedIn's algorithm and engagement patterns
- Balancing thought leadership with practical value

Core Principles:
1. **Audience-First Thinking**: Every topic must solve a real problem or answer a burning question
2. **Unique Perspective**: Leverage the executive's specific experience and insights
3. **Engagement Optimization**: Structure topics for maximum discussion and sharing
4. **Business Alignment**: Connect content to measurable business outcomes
5. **Platform Native**: Respect LinkedIn's professional context and user behavior

For each topic, provide clear reasoning about:
- Why it addresses the user's intent
- How it leverages unique expertise
- What makes the angle fresh
- Expected audience impact
"""

KNOWLEDGE_BASE_QUERY_SYSTEM_PROMPT = """
You are a research strategist specializing in content intelligence gathering.

Your expertise includes:
- Identifying information gaps that need filling
- Creating targeted search strategies
- Prioritizing high-value research areas
- Connecting disparate information sources
- Extracting actionable insights from data

Research Principles:
1. **Relevance Over Volume**: Quality of insights matters more than quantity
2. **Evidence Hierarchy**: Prioritize first-party data, case studies, then industry research
3. **Practical Application**: Focus on information that supports actionable advice
4. **Credibility Building**: Seek data that establishes authority
5. **Story Support**: Find examples that illustrate abstract concepts

For each query, explain:
- What specific information it seeks
- How it supports the content angle
- Why this research matters to the audience
"""

BRIEF_GENERATION_SYSTEM_PROMPT = """
You are a senior content strategist creating comprehensive LinkedIn content briefs.

Your expertise includes:
- Translating strategy into executable content plans
- Structuring content for maximum impact
- Integrating research seamlessly into narratives
- Optimizing for both algorithms and human psychology
- Measuring and predicting content performance

Brief Creation Principles:
1. **Clarity Above All**: Every instruction must be unambiguous and actionable
2. **Strategic Reasoning**: Explain the 'why' behind every recommendation
3. **Evidence-Based**: Ground all suggestions in research or proven practices
4. **Flexibility with Structure**: Provide framework but allow creative interpretation
5. **Measurable Success**: Define clear metrics and success indicators

For each brief element, provide reasoning about:
- Strategic purpose
- Expected impact
- Implementation guidance
- Success measurement
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

TOPIC_GENERATION_USER_PROMPT_TEMPLATE = """
Generate 5 strategic LinkedIn topics based on the following context:

USER'S CONTENT VISION:
{user_input}

EXECUTIVE PROFILE & EXPERTISE:
{executive_profile}

CONTENT STRATEGY & GOALS:
{content_strategy}

REQUIREMENTS FOR EACH TOPIC:

1. **Topic Development**:
   - Create a compelling title that promises value
   - Define a unique angle that differentiates from common advice
   - Explain the reasoning behind the topic selection
   - Describe why this angle will resonate
   - Predict the expected impact on audience and business goals

2. **Strategic Alignment**:
   - Connect to user's original intent
   - Leverage executive's unique expertise
   - Address specific audience pain points
   - Support content strategy objectives

3. **LinkedIn Optimization**:
   - Consider optimal post length and format
   - Plan for algorithm-friendly engagement hooks
   - Include controversy or discussion points where appropriate
   - Balance professional tone with personality

4. **Differentiation Factors**:
   - What makes this topic fresh in a crowded feed?
   - What unique insight only this executive can provide?
   - How does it challenge conventional thinking?

Each topic must include:
- topic_id (topic_01 through topic_05)
- Clear reasoning for selection
- Specific angle reasoning
- Expected impact analysis

Ensure variety across:
- Content depth (tactical vs strategic)
- Audience segments addressed
- Emotional triggers (inspire, educate, challenge)
- Content formats (frameworks, stories, debates)
"""


# New template specifically for topic regeneration
TOPIC_REGENERATION_USER_PROMPT_TEMPLATE = """
Based on user feedback, generate 5 NEW strategic LinkedIn topics.

ORIGINAL CONTENT VISION:
{user_input}

EXECUTIVE CONTEXT:
{executive_profile}

STRATEGY CONTEXT:
{content_strategy}

USER FEEDBACK ON PREVIOUS SUGGESTIONS:
{regeneration_feedback}

CRITICAL ADJUSTMENTS BASED ON FEEDBACK:

1. **Address Specific Concerns**:
   - Directly incorporate feedback points
   - Avoid patterns that didn't resonate
   - Emphasize requested elements
   - Provide reasoning for how each topic addresses feedback

2. **Maintain Quality Standards**:
   - Keep strategic alignment with goals
   - Preserve executive authenticity
   - Ensure LinkedIn best practices
   - Explain improvements over previous suggestions

3. **Fresh Perspectives**:
   - Explore completely different angles
   - Consider alternative frameworks
   - Target different pain points
   - Provide reasoning for new directions

4. **Enhanced Value Proposition**:
   - Clarify the unique value of each topic
   - Strengthen the executive's unique perspective
   - Improve practical applicability
   - Explain why these topics better meet user needs

For each NEW topic, explain:
- How it addresses the feedback
- Why it's better than previous options
- What makes it compelling
- Expected audience response
"""

KNOWLEDGE_BASE_QUERY_USER_PROMPT_TEMPLATE = """
Create targeted research queries for the selected LinkedIn topic.

USER'S ORIGINAL VISION:
{user_input}

SELECTED TOPIC DETAILS:
{selected_topic}

CONTENT STRATEGY CONTEXT:
{content_strategy}

AVAILABLE KNOWLEDGE BASE RESOURCES:
- Company documentation and processes
- Industry research and reports  
- Customer case studies and testimonials
- Product specifications and features
- Previous thought leadership content
- Market analysis and competitive intelligence
- Executive insights and speaking notes

RESEARCH OBJECTIVES:

1. **Primary Research Goals**:
   - Find evidence to support the core perspective
   - Identify compelling examples and case studies
   - Discover surprising statistics or insights
   - Provide reasoning for query selection

2. **Query Strategy**:
   - Create 5-7 specific search queries
   - Mix broad and narrow search terms
   - Target different types of evidence
   - Explain what each query seeks to find

3. **Focus Areas**:
   - Define 3-4 critical content areas to explore
   - Prioritize based on audience needs
   - Balance depth with breadth
   - Provide reasoning for focus area selection

4. **Research Depth Assessment**:
   - Determine appropriate depth (surface/moderate/deep)
   - Consider content format requirements
   - Balance thoroughness with efficiency
   - Explain depth reasoning

For each element, explain:
- Why this research is essential
- How it supports the content angle
- What unique insights it might reveal
- How findings will strengthen the narrative
"""

BRIEF_GENERATION_USER_PROMPT_TEMPLATE = """
Create a comprehensive LinkedIn content brief with strategic reasoning.

USER'S ORIGINAL VISION:
{user_input}

SELECTED TOPIC:
{selected_topic}

EXECUTIVE PROFILE:
{executive_profile}

CONTENT STRATEGY:
{content_strategy}

KNOWLEDGE BASE RESEARCH:
{knowledge_base_research}

BRIEF REQUIREMENTS:

1. **Strategic Foundation**:
   - Title with reasoning for LinkedIn performance
   - Scheduling strategy with timing rationale
   - Content pillar alignment with strategy explanation
   - Target audience with pain point analysis

2. **Content Architecture**:
   - Core perspective with value proposition
   - Structured outline with flow reasoning
   - Key messages with hierarchy explanation
   - Evidence integration with selection rationale

3. **Engagement Optimization**:
   - Multiple hook options with testing strategy
   - Discussion-driving elements with reasoning
   - CTA with behavior prediction
   - Hashtag strategy with reach analysis

4. **Execution Guidance**:
   - Tone and style with audience alignment
   - Length optimization with algorithm consideration
   - Success metrics with measurement plan
   - Research gaps with priority reasoning

For every recommendation, provide:
- Strategic reasoning
- Expected impact
- Implementation tips
- Success indicators

Ensure the brief:
- Directly addresses user's original intent
- Integrates research findings naturally
- Maintains executive authenticity
- Optimizes for LinkedIn's unique environment
- Provides clear, actionable guidance
"""

# =============================================================================
# BRIEF FEEDBACK PROMPTS
# =============================================================================

BRIEF_FEEDBACK_SYSTEM_PROMPT = """
You are a content strategy analyst specializing in brief optimization.

Your expertise includes:
- Interpreting stakeholder feedback
- Prioritizing revision needs
- Identifying missing elements
- Balancing competing requirements
- Maintaining strategic coherence

Analysis Principles:
1. **Preserve Strengths**: Don't fix what isn't broken
2. **Prioritize Impact**: Focus on changes that matter most
3. **Maintain Voice**: Keep executive authenticity intact
4. **Strategic Alignment**: Ensure revisions support goals
5. **Practical Implementation**: Make changes achievable

For each revision recommendation, explain:
- Why it's necessary
- What impact it will have
- How to implement it
- Priority level and reasoning
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
You are a content brief editor implementing strategic revisions.

Your expertise includes:
- Precise content modification
- Maintaining narrative coherence
- Enhancing without overwriting
- Preserving original strengths
- Implementing feedback effectively

Revision Principles:
1. **Surgical Precision**: Change only what needs changing
2. **Enhanced Reasoning**: Strengthen rationale where needed
3. **Coherent Flow**: Maintain logical progression
4. **Strategic Consistency**: Keep aligned with objectives
5. **Quality Improvement**: Every change must add value

For revisions:
- Implement all high-priority changes
- Preserve successful elements
- Enhance reasoning throughout
- Maintain authentic voice
- Improve clarity and impact
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
    """Enhanced feedback analysis with prioritization reasoning"""
    feedback_summary: str = Field(
        description="Summary of the key points in the user feedback"
    )
    
    revision_instructions: List[RevisionInstruction] = Field(
        description="List of specific revision instructions"
    )

    missing_elements: List[str] = Field(
        description="Elements that should be added to the brief based on feedback"
    )
    
    overall_direction: str = Field(
        description="Overall direction for the brief revision based on feedback analysis"
    )
    
    direction_reasoning: str = Field(
        description="Strategic rationale for the recommended revision direction"
    )

# =============================================================================
# OUTPUT SCHEMA DEFINITIONS (for workflow nodes)
# =============================================================================

TOPIC_GENERATION_OUTPUT_SCHEMA = TopicGenerationOutput.model_json_schema()
KNOWLEDGE_BASE_QUERY_OUTPUT_SCHEMA = KnowledgeBaseQuery.model_json_schema()
BRIEF_GENERATION_OUTPUT_SCHEMA = BriefGenerationOutput.model_json_schema()
BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = BriefFeedbackAnalysis.model_json_schema() 