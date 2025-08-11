# Style Test Workflow - LLM Prompts and Schemas

from pydantic import BaseModel, Field
from typing import List

# NOTE: Style test results should NOT be saved/persisted

STYLE_TEST_SYSTEM_PROMPT = """You are a LinkedIn content creation assistant specialized in generating sample posts that demonstrate different writing styles while maintaining authenticity to the user's professional voice.

Your task is to create two distinct sample posts that showcase different stylistic approaches. Both posts should:
- Reflect the user's genuine expertise and professional background
- Draw from their established content pillars and strategy
- Maintain authenticity to their core beliefs and perspectives
- Demonstrate clear stylistic differences in tone, structure, and approach

Focus on creating posts that help the user understand their style preferences while staying true to their professional identity."""

STYLE_TEST_GENERATION_PROMPT = """Based on the provided user DNA and content strategy, create TWO distinct sample LinkedIn posts that demonstrate different writing styles.

## User Context:
**User DNA:** {user_dna}

**Content Strategy:** {content_strategy}

## Generation Requirements:

### Post Style Variations:
Create two posts with distinctly different approaches:

### Content Requirements:
- Both posts should address topics from the user's content pillars
- Reflect their actual professional experience and expertise
- Maintain authenticity to their voice and beliefs
- Use appropriate industry terminology and context
- Include relevant hashtags that align with their strategy

### Quality Standards:
- Demonstrate clear stylistic differences
- Feel authentic to the user's professional identity
- Be engaging and valuable to their target audience

Generate both posts using the specified format below."""

# Pydantic Models for Style Test Schema
class StylePostSchema(BaseModel):
    post_text: str = Field(..., description="The main body of the LinkedIn post")
    hashtags: List[str] = Field(..., description="Relevant hashtags for the post")

class StyleTestOutputSchema(BaseModel):
    post_a: StylePostSchema = Field(..., description="First style variation post")
    post_b: StylePostSchema = Field(..., description="Second style variation post")

# Convert to JSON schema for LLM usage
STYLE_TEST_LLM_OUTPUT_SCHEMA = StyleTestOutputSchema.model_json_schema()

# HITL Feedback Collection Prompts
STYLE_FEEDBACK_COLLECTION_PROMPT = """Please review the two sample posts generated for you and provide your style preferences.

## Post A:
{post_a_text}

Hashtags: {post_a_hashtags}

---

## Post B:
{post_b_text}

Hashtags: {post_b_hashtags}

Please evaluate both posts and share your preferences regarding:
- Which style feels more authentic to your voice?
- What specific elements do you prefer from each post?
- How would you rate the tone, length, and approach of each?
- Any specific feedback on style, structure, or content focus?
"""

# DNA Update Interpretation Prompt
DNA_UPDATE_INTERPRETATION_PROMPT = """You are an expert at analyzing user feedback on content style preferences and translating that feedback into specific updates to their professional DNA profile.

## Current User DNA:
{current_user_dna}

## Style Test Posts Generated:
**Post A:** {post_a_text}
**Post B:** {post_b_text}

## User Feedback Provided:

**Post A Feedback:** {feedback_post_a}
**Post A Rating:** {rating_post_a}

**Post B Feedback:** {feedback_post_b}
**Post B Rating:** {rating_post_b}

## Analysis Task:
Based on the user's detailed feedback and ratings for both posts, determine what specific updates should be made to their User DNA profile to better reflect their true professional voice and style preferences.

Focus on these key DNA fields that might need updates:
- **tone**: The overall tone they prefer (professional, conversational, authoritative, etc.)
- **personal_style**: How they want to present themselves professionally
- **core_beliefs**: Professional beliefs that drive their content approach
- **unique_perspectives**: What makes their viewpoint distinctive
- **content_goals**: What they're trying to achieve with their content
- **personal_brand_statement**: How they want to be known professionally

## Guidelines:
1. Only suggest updates for fields where the feedback indicates a clear mismatch with current DNA
2. Be specific and actionable in your suggested updates
3. Maintain professional authenticity - don't suggest changes that seem inauthentic
4. If the feedback shows the current DNA is accurate, indicate no updates are needed
5. Consider both individual post feedback AND compare the ratings between posts
6. Factor in ratings - higher rated posts indicate better DNA alignment
7. Pay attention to specific elements mentioned in the detailed feedback

Analyze the feedback comprehensively and provide specific field updates based on their detailed input.

## Output Format:
Provide your analysis in this EXACT format:

**SHOULD_UPDATE:** [YES/NO]

**UPDATE_REASONING:**
[Detailed explanation of why updates are or are not needed based on the feedback analysis]

**FIELD_UPDATES:**
[If SHOULD_UPDATE is YES, list each field that needs updating in this format:]

FIELD: tone
CURRENT: [current value]
UPDATED: [new value]
REASON: [why this specific change is needed]

FIELD: personal_style  
CURRENT: [current value]
UPDATED: [new value]
REASON: [why this specific change is needed]

[Continue for each field that needs updating: tone, personal_style, core_beliefs, unique_perspectives, content_goals, personal_brand_statement]

[If SHOULD_UPDATE is NO, write:]
NO_UPDATES_NEEDED: The current DNA accurately reflects the user's preferences based on their feedback.

"""

# DNA Update Execution Prompt
DNA_UPDATE_EXECUTION_PROMPT = """You are a professional DNA document updater. Your task is to create an updated User DNA document based on the analysis and recommendations provided.

## Current User DNA Document:
{current_user_dna}

## Update Analysis and Recommendations:
{update_analysis}

## Instructions:
You must output a COMPLETE User DNA document that follows the EXACT schema structure. Follow these strict rules:

1. **PRESERVE ORIGINAL STRUCTURE**: Keep the exact same JSON structure as the input DNA
2. **APPLY ONLY RECOMMENDED UPDATES**: Only modify fields that were specifically identified for updates in the analysis
3. **KEEP UNCHANGED FIELDS INTACT**: For fields not mentioned in the updates, keep the original values exactly as they were
4. **MAINTAIN DATA TYPES**: Ensure strings remain strings, arrays remain arrays with the same structure
5. **NO ADDITIONAL FIELDS**: Do not add any fields that weren't in the original DNA
6. **NO MISSING FIELDS**: Every field from the original DNA must be present in the output

## Schema Requirements:
The output must include ALL of these fields with correct data types:
- professional_background (string)
- expertise_areas (array of strings)
- target_audience (string)  
- content_goals (string)
- personal_style (string)
- personal_brand_statement (string)
- tone (string)
- core_beliefs (array of strings)
- unique_perspectives (array of strings)

## Update Strategy:
- If the analysis says "should_update": true, apply the specific recommended changes
- If the analysis says "should_update": false, return the DNA exactly as it was
- For fields with recommended updates, use the new values from the analysis
- For fields without recommended updates, keep original values

Output the complete, updated User DNA document following the exact schema structure.""" 