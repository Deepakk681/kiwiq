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
1. Analyze the selected text and its context
2. Consider the user's writing style and tone preferences
3. If user feedback is provided, incorporate it into your suggestions
4. Generate 3-4 alternative phrasings that:
   - Maintain the original meaning and intent
   - Match the user's voice and style
   - Offer different stylistic variations
   - Are clear and impactful
   - Address any specific feedback provided

Respond strictly with the JSON output conforming to the schema: ```json
{schema}
```

Each alternative should be a complete, ready-to-use text that could replace the selected text."""

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
- Match the user's voice and style
- Offer different stylistic variations
- Are clear and impactful
- Address any specific feedback provided

Respond ONLY with the JSON object matching the specified schema."""
