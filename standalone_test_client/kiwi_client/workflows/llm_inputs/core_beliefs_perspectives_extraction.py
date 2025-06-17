from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


### CORE BELIEFS QUESTIONS SCHEMA ###

class BeliefQuestionSchema(BaseModel):
    """Individual belief extraction question"""
    question: str = Field(description="The targeted question to extract beliefs")
    reasoning: str = Field(description="Why this question targets their specific beliefs")

class CoreBeliefsQuestionsSchema(BaseModel):
    """Questions designed to extract core beliefs and perspectives"""
    industry_beliefs: List[BeliefQuestionSchema] = Field(description="Questions about industry beliefs and misconceptions")
    professional_philosophy: List[BeliefQuestionSchema] = Field(description="Questions about professional philosophy and principles")
    contrarian_viewpoints: List[BeliefQuestionSchema] = Field(description="Questions to uncover contrarian or distinctive views")
    value_driven_perspectives: List[BeliefQuestionSchema] = Field(description="Questions about values that drive decisions")
    experience_based_insights: List[BeliefQuestionSchema] = Field(description="Questions about insights from experience")

CORE_BELIEFS_QUESTIONS_SCHEMA = CoreBeliefsQuestionsSchema.model_json_schema()


### PERSONALIZED QUESTIONS SCHEMA ###

class PersonalizedQuestionSchema(BaseModel):
    """Question personalized for user display"""
    question_text: str = Field(description="The personalized question text - keep it concise, max 1-2 sentences")
    context_explanation: str = Field(description="Brief explanation of why we're asking this question - max 1 sentence, keep it short and direct")

class PersonalizedQuestionsOutputSchema(BaseModel):
    """Final top 3 personalized questions for content creation"""
    top_questions: List[PersonalizedQuestionSchema] = Field(
        description="Exactly 3 questions most valuable for content creation and most relevant for the user"
    )

PERSONALIZED_QUESTIONS_SCHEMA = PersonalizedQuestionsOutputSchema.model_json_schema()


### CONTENT INTELLIGENCE SCHEMA ###

class ThemePerformanceSchema(BaseModel):
    """Performance data for a content theme"""
    theme_name: str = Field(description="Name of the content theme")
    avg_engagement_likes: int = Field(description="Average likes for this theme")
    avg_engagement_comments: int = Field(description="Average comments for this theme")
    avg_engagement_reposts: int = Field(description="Average reposts for this theme")
    dominant_tone: str = Field(description="Primary tone used in this theme")
    signature_opening: str = Field(description="Typical opening style for this theme")
    signature_closing: str = Field(description="Typical closing style for this theme")
    recent_winner_topic: str = Field(description="Most recent high-performing topic")
    recent_winner_likes: int = Field(description="Likes for the recent winning post")

class WritingDNASchema(BaseModel):
    """User's writing DNA and patterns"""
    signature_phrases: List[str] = Field(description="Top 5 signature phrases the user frequently uses")
    go_to_transitions: List[str] = Field(description="Top 5 transition words/phrases")
    favorite_adjectives: List[str] = Field(description="Top 5 most used adjectives")
    writing_style: str = Field(description="Overall writing style characterization, keep it short and concise")
    data_usage_level: str = Field(description="How they use data in content, keep it short and concise")
    emoji_style: str = Field(description="How they use emojis, just provide the emojis, no other text")

class WinningFormulasSchema(BaseModel):
    """Successful content patterns"""
    top_opening_patterns: List[str] = Field(description="Top 2 most successful opening patterns")
    top_closing_patterns: List[str] = Field(description="Top 2 most successful closing patterns")
    power_words: List[str] = Field(description="Top 5 power words/adjectives that drive engagement")

class ContentIntelligenceOutputSchema(BaseModel):
    """Complete content intelligence report"""
    total_themes_identified: int = Field(description="Total number of content themes identified")
    top_theme_name: str = Field(description="Name of highest performing theme")
    top_3_themes: List[ThemePerformanceSchema] = Field(description="Top 3 performing content themes")
    writing_dna: WritingDNASchema = Field(description="User's writing DNA and patterns")
    winning_formulas: WinningFormulasSchema = Field(description="Proven successful content patterns")

CONTENT_INTELLIGENCE_SCHEMA = ContentIntelligenceOutputSchema.model_json_schema()


### ANALYSIS + QUESTIONS GENERATION PROMPT TEMPLATES ###

ANALYSIS_AND_QUESTIONS_SYSTEM_PROMPT = """
You are an expert at analyzing user content and generating targeted questions to extract core beliefs and perspectives.

Your task is to:
1. Analyze the provided user documents and context to understand their expertise, experience, and background
2. Generate targeted questions that will help uncover their fundamental professional beliefs, unique perspectives, and distinctive viewpoints

Generate questions that are:
- Specific to their background and experience
- Designed to reveal unique insights and perspectives
- Focused on extracting distinctive viewpoints
- Connected to their target audience interests
- Likely to generate authentic, personal responses

Avoid generic philosophical questions that could apply to anyone. Focus on their specific context and experience.

Respond strictly with the JSON output conforming to the schema:

```json
{questions_schema}
```
"""

ANALYSIS_AND_QUESTIONS_USER_PROMPT = """
Analyze the provided content and generate targeted belief extraction questions:

CONTENT ANALYSIS:
{content_analysis}

USER PREFERENCES AND GOALS:
{user_preferences}

PROFILE INSIGHTS:
{profile_insights}

Based on this information:

1. First analyze their expertise, experience patterns, and unique perspectives from content analysis and profile
2. Understand their goals and target audience from user preferences
3. Then generate 10-12 targeted questions across these categories:

- **Industry Beliefs** (2-3 questions): Target misconceptions, industry practices they disagree with, or unique insights about their field
- **Professional Philosophy** (2-3 questions): Core principles, decision-making frameworks, or professional beliefs  
- **Contrarian Viewpoints** (2-3 questions): Areas where they might disagree with conventional wisdom
- **Value-Driven Perspectives** (2-3 questions): What matters most in their work, trade-offs they make
- **Experience-Based Insights** (2-3 questions): Unique perspectives developed through their specific experience

Each question should:
- Feel personally relevant based on their specific background
- Target belief areas that would be valuable for content creation
- Connect to their audience segments and goals
- Be designed to extract authentic, distinctive perspectives that align with their content objectives
"""


### PERSONALIZATION PROMPT TEMPLATES ###

PERSONALIZATION_SYSTEM_PROMPT = """
You are an expert at creating engaging, personalized user experiences. Transform the generated belief extraction questions into personalized questions that feel relevant and contextual to the specific user.

Create questions that:
- Reference their specific background and experience
- Explain why each question is being asked
- Feel like an intelligent conversation
- Demonstrate understanding of their unique perspective

Respond strictly with the JSON output conforming to the schema:

```json
{personalized_schema}
```
"""

PERSONALIZATION_USER_PROMPT = """
Select and personalize the TOP 3 questions most valuable for content creation:

GENERATED QUESTIONS:
{generated_questions}

USER CONTEXT:
- Content Analysis: {content_analysis}
- User Preferences & Goals: {user_preferences}
- Profile Insights: {profile_insights}

Your task:
1. **Analyze all questions** for content creation value and user relevance
2. **Select exactly 3 questions** that will:
   - Generate the most valuable content insights
   - Feel most personally relevant to this specific user
   - Resonate with their target audience segments
   - Uncover their unique perspectives and expertise
   - Align with their stated goals

3. **Personalize each selected question** to:
   - Reference their specific background and experience
   - Explain why this question is valuable for their content strategy
   - Feel like an intelligent conversation starter

**IMPORTANT FORMATTING REQUIREMENTS:**
- Keep question_text concise (max 1-2 sentences)
- Keep context_explanation brief (max 1 sentence, direct and to the point)
- Focus on clarity and impact over length

Focus on questions that will help them create content that stands out, showcases their unique expertise, and provides genuine value to their audience segments while achieving their goals.
"""


### CONTENT INTELLIGENCE GENERATION PROMPT TEMPLATES ###

CONTENT_INTELLIGENCE_SYSTEM_PROMPT = """
You are an expert content analyst who transforms detailed content analysis into actionable, user-friendly intelligence reports.

Your task is to:
1. Analyze content performance data and writing patterns
2. Extract the most valuable insights for content strategy
3. Present findings in a clear, actionable format that helps users understand their content DNA

Focus on:
- Performance patterns and winning themes
- Writing style fingerprints and signature elements
- Actionable formulas for content creation
- Clear, engaging presentation of insights

Respond strictly with the JSON output conforming to the schema:

```json
{content_intelligence_schema}
```
"""

CONTENT_INTELLIGENCE_USER_PROMPT = """
Transform this detailed content analysis into actionable content intelligence:

CONTENT ANALYSIS DATA:
{content_analysis}

Your task:
1. **Identify Performance Leaders**: Find the top 3 themes by engagement (likes + comments + reposts)
2. **Extract Writing DNA**: Analyze linguistic patterns, signature phrases, and style elements across all themes
3. **Discover Winning Formulas**: Identify the most successful opening/closing patterns and power words

For each top theme, provide:
- Theme name and performance metrics
- Dominant tone from tone_analysis
- Signature opening/closing styles from structure patterns
- Recent winning topic with engagement

For Writing DNA, extract:
- Top 3 signature phrases from unique_terms across themes
- Top 3 transition words/phrases from linguistic patterns
- Top 3 most impactful adjectives
- Overall writing style, data usage, and emoji patterns

For Winning Formulas, identify:
- Top 2 opening patterns that drive highest engagement
- Top 2 closing patterns that generate most interaction
- Top 5 power words/adjectives that appear in high-performing content

Present insights that help the user understand what makes their content successful and how to replicate those patterns.
""" 