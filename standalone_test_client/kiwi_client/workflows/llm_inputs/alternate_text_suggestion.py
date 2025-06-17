from typing import List, Optional
from pydantic import BaseModel, Field

class AlternativeSuggestionsResponse(BaseModel):
    """Schema for the response containing a list of alternative text suggestions"""
    alternatives: List[str] = Field(..., description="List of alternative text suggestions")

# Schema for generation
GENERATION_SCHEMA = AlternativeSuggestionsResponse.model_json_schema()

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """You are an expert copywriter tasked with providing alternative phrasings for selected text while maintaining the user's voice and intent.

Your task is to:
1. Carefully analyze the selected text within the context of the complete post
2. Ensure each alternative maintains narrative flow and consistency with surrounding content
3. Consider the user's writing style and tone preferences
4. If user feedback is provided, incorporate it into your suggestions
5. Generate 3-4 alternative phrasings that:
   - Maintain the original meaning and intent
   - Seamlessly integrate with the complete post's flow and style
   - Match the user's voice and style
   - Offer different stylistic variations while preserving context
   - Are clear and impactful
   - Address any specific feedback provided
   - Ensure smooth transitions with surrounding text

Respond strictly with the JSON output conforming to the schema: ```json
{schema}
```

Each alternative should be a complete, ready-to-use text that could replace the selected text while maintaining perfect alignment with the rest of the post."""

# User prompt template
USER_PROMPT_TEMPLATE = """Generate alternative phrasings for the following text:

**Selected Text:**
{selected_text}

**Context:**
{content_draft}

**User's Style and Tone Preferences:**
{user_dna}

**User Feedback:**
{feedback_section}

**Task:**
Generate multiple alternatives that:
- Maintain the original meaning and intent
- Seamlessly integrate with the complete post's flow and style
- Match the user's voice and style
- Offer different stylistic variations while preserving context
- Are clear and impactful
- Address any specific feedback provided
- Ensure smooth transitions with surrounding text

Pay special attention to:
1. How the selected text connects with the content before and after it
2. Maintaining consistent tone and style throughout the post
3. Ensuring each alternative reads naturally within the complete context

Respond ONLY with the JSON object matching the specified schema."""
