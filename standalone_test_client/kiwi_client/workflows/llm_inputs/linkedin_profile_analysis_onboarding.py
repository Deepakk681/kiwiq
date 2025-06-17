from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


### PROFILE ANALYSIS SCHEMA ###

class ProfileInsightsSchema(BaseModel):
    """Key insights extracted from LinkedIn profile"""
    user_full_name: str = Field(description="Full name of the user")
    location: str = Field(description="Location of the user")
    current_position: str = Field(description="Current job title and company")
    industry: str = Field(description="Industry of the user, keep it short and concise")
    experience_years: int = Field(description="Years of professional experience")
    top_skills: List[str] = Field(description="Top 5 skills from profile")
    career_highlights: List[str] = Field(description="Key career achievements and transitions")
    education: str = Field(description="Educational background summary")

PROFILE_INSIGHTS_SCHEMA = ProfileInsightsSchema.model_json_schema()


### PERSONALIZED QUESTIONS SCHEMA ###

class QuestionSchema(BaseModel):
    """Individual question structure"""
    question: str = Field(description="The personalized question text - keep it concise, max 1-2 sentences")
    
class PersonalizedQuestionsSchema(BaseModel):
    """Personalized questions based on profile analysis"""
    content_goals: List[QuestionSchema] = Field(description="Questions about content creation goals and objectives")

PERSONALIZED_QUESTIONS_SCHEMA = PersonalizedQuestionsSchema.model_json_schema()


### TARGET AUDIENCE FRAMEWORK SCHEMA ###

class AudienceSegmentSchema(BaseModel):
    """Individual target audience segment"""
    audience_type: str = Field(description="Type of audience (e.g., 'Fellow Founders', 'Potential Investors')")
    description: str = Field(description="Brief description of this audience segment")

class TargetAudienceFrameworkSchema(BaseModel):
    """Target audience framework with multiple segments"""
    audience_segments: List[AudienceSegmentSchema] = Field(description="3-4 target audience segments", min_items=3, max_items=4)

TARGET_AUDIENCE_FRAMEWORK_SCHEMA = TargetAudienceFrameworkSchema.model_json_schema()


### PROFILE ANALYSIS PROMPT TEMPLATES ###

PROFILE_ANALYSIS_SYSTEM_PROMPT = """
You are an expert LinkedIn profile analyst. Extract key insights from LinkedIn profiles to inform content strategy.

Extract and analyze:
- Professional background and expertise
- Career progression and achievements  
- Industry of user

Respond with valid JSON only:

```json
{profile_insights_schema}
```
"""

PROFILE_ANALYSIS_USER_PROMPT = """
Analyze this LinkedIn profile and extract key insights:

LINKEDIN PROFILE DATA:
{linkedin_profile_data}

Extract:
1. Current professional position and industry
2. Years of experience and career progression
3. Top skills and areas of expertise
4. Notable career highlights and achievements
5. Educational background
6. Number of followers that user has

Focus on extracting actionable insights that will help create personalized onboarding questions.
"""


### PERSONALIZED QUESTIONS GENERATION PROMPT TEMPLATES ###

QUESTIONS_GENERATION_SYSTEM_PROMPT = """
You are an expert onboarding specialist creating questions for content creators. Your goal is to generate relevant questions that will help understand their content creation goals.

Generate questions that are:
1. Personalized based on available profile information (industry, role, experience)
2. Adaptable to limited information by focusing on universal content creation aspects
3. Designed to uncover their value proposition and expertise
4. Focused on understanding their content creation objectives

Generate questions for:
- Content Goals and Objectives (3 questions)

IMPORTANT: 
- Do NOT generate questions about target audience, as target audience identification is handled separately
- When profile information is available, incorporate it naturally into questions
- When information is limited, focus on their role/industry while keeping questions adaptable
- Balance between personalization and universal content creation aspects

**FORMATTING REQUIREMENTS:**
- Keep question_text concise (max 1-2 sentences)
- Focus on clarity and impact over length
- Use available profile information naturally without forcing it

Respond strictly with the JSON output conforming to the schema:

```json
{questions_schema}
```
"""

QUESTIONS_GENERATION_USER_PROMPT = """
Based on this LinkedIn profile data, generate onboarding questions:

LINKEDIN PROFILE DATA:
{linkedin_profile_data}

Generate questions that will help us understand how to create an effective content strategy. Use available profile information to add relevant context while keeping questions adaptable.

The questions should help uncover:
- Their content creation goals and objectives
- What success looks like through their content
- Their preferred content approach and style

Focus on creating questions about:
- Content Goals: Questions about their content creation objectives, desired outcomes, and what they want to achieve through their content

**IMPORTANT GUIDELINES:**
- Use available profile information (industry, role, experience) to add relevant context
- If certain profile information is missing, focus on universal content creation aspects
- Balance between personalization and general content strategy questions
- Keep question_text concise (max 1-2 sentences)
- Focus on clarity and impact over length

IMPORTANT: Do NOT ask about target audience, as we handle target audience identification separately. Focus only on their content creation goals, success metrics, content preferences, and strategic objectives.
"""


### TARGET AUDIENCE FRAMEWORK PROMPT TEMPLATES ###

TARGET_AUDIENCE_SYSTEM_PROMPT = """
Based on the LinkedIn profile data, create 3-4 distinct target audience segments. Provide specific examples relevant to their role and industry.

For each audience segment, include:
- Audience type and detailed description
- Why this audience would be interested in their content
- Specific examples of individuals/roles within this segment
- Content topics that would resonate with this audience
- Potential engagement patterns and preferences

Use the professional context to make realistic, actionable audience recommendations. The segments should be complementary but distinct, covering different aspects of their expertise and network.

Respond strictly with the JSON output conforming to the schema:

```json
{target_audience_schema}
```
"""

TARGET_AUDIENCE_USER_PROMPT = """
Based on this LinkedIn profile data, create 3-4 distinct target audience segments:

LINKEDIN PROFILE DATA:
{linkedin_profile_data}

Create 3-4 target audience segments that this person could effectively reach through their content. Consider their professional background, industry, and expertise when recommending suitable audiences. The segments should be complementary but distinct, covering different networking circles and professional interests.

For each audience segment, provide:
1. Clear audience type and description of who they are
2. Why this person's content would be valuable to them
3. Specific examples of roles/individuals in this segment
4. Content topics that would resonate
5. How this audience typically engages with content

**IMPORTANT FORMATTING REQUIREMENTS:**
- Keep audience_type concise (max 1-2 words)
- Keep description concise (max 1-2 sentences)
- Focus on clarity and impact over length

Focus on identifying diverse audience segments that align with different aspects of their professional expertise and content creation potential.
""" 