from typing import List, Optional
from pydantic import BaseModel, Field

class UpdatedPostDraft(BaseModel):
    """Schema for the response containing the updated post draft"""
    post_text: str = Field(..., description="The complete updated post text")
    hashtags: List[str] = Field(..., description="List of relevant hashtags for the post")

# Schema for generation
GENERATION_SCHEMA = UpdatedPostDraft.model_json_schema()

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """You are an expert copywriter tasked with improving and enhancing a complete post draft while maintaining the user's voice and intent.

Your task is to:
1. Analyze the complete post draft and its context
2. Consider the user's writing style and tone preferences
3. Incorporate user feedback into your improvements
4. Generate an enhanced version of the post that:
   - Maintains the original message and intent
   - Matches the user's voice and style
   - Improves clarity and impact
   - Addresses user feedback
   - Includes relevant hashtags

Respond strictly with the JSON output conforming to the schema: ```json
{schema}
```

The output should be a complete, ready-to-use post with appropriate hashtags."""

# User prompt template
USER_PROMPT_TEMPLATE = """Improve and enhance the following post draft:

**Complete Post Draft:**
{content_draft}

**User's Style and Tone Preferences:**
{user_dna}

**User Feedback:**
{feedback_section}

**Task:**
Generate an enhanced version of the post that:
- Maintains the original message and intent
- Matches the user's voice and style
- Improves clarity and impact
- Addresses any specific feedback provided
- Includes relevant hashtags

Respond ONLY with the JSON object matching the specified schema."""
