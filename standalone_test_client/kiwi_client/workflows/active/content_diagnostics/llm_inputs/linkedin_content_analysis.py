from typing import List, Union
# --- Pydantic Schemas for LLM Outputs (Examples) ---
from pydantic import BaseModel, Field

from enum import Enum
class JoinType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
# --- End Mock ---


class ThemeSchema(BaseModel):
    """Schema for a single extracted theme."""
    theme_id: str = Field(..., description="Unique identifier for the theme (e.g., 'theme_1', 'theme_2').")
    theme_name: str = Field(
        description="A clear, specific name for the identified theme (e.g., 'Founder Lessons')."
    )
    theme_description: str = Field(
        description="A structured, human-readable description with clear bullet points explaining: (1) the main topics covered, (2) the purpose or intent behind these posts, and (3) any recurring patterns or characteristics that define this theme."
    )

class ExtractedThemesOutput(BaseModel):
    themes: List[ThemeSchema] = Field(
        description="A list of 5 key content themes extracted from the user's LinkedIn posts."
    )


THEME_EXTRACTION_USER_PROMPT_TEMPLATE = """
Here is a set of LinkedIn posts written by a single user.

Your task is to analyze these posts and return exactly 5 key content themes. Each theme must have a name and a detailed description.

Posts:
```json
{posts_json}
```

Respond ONLY with the JSON object matching the specified schema.
"""

THEME_EXTRACTION_SYSTEM_PROMPT_TEMPLATE = """
You are an expert content strategist specializing in social media analysis.

Your task is to analyze a series of LinkedIn posts and identify exactly 5 key content themes that represent the user's recurring focus areas. Each theme should be unique, clearly named, and reflect distinct patterns in tone, topic, or objective across the posts.

Guidelines:
- Identify **exactly 5 themes**, no more or less
- Each theme must have a **concise, specific name** (e.g., "Startup Lessons", not "Business")
- For each theme, write a **structured, human-readable description** using clear bullet points that cover: (1) main topics, (2) purpose or intent, and (3) recurring patterns or characteristics
- Do not infer the user's goals — base your themes only on the text content provided
- Be as concrete and precise as possible; avoid vague or generic labels

Respond only with the JSON output conforming to the schema: ```json\n{schema}\n```
"""


class PostClassificationSchema(BaseModel):
    """Schema for classifying a single post."""
    post_id: str = Field(..., description="The unique identifier (URN) of the post being classified.")
    reasoning: str = Field(..., description="Brief explanation for why the theme was assigned.")
    assigned_theme_id: str = Field(..., description="The theme_id from the provided list that best fits this post. Must match one of the 5 extracted themes or be 'Other'.")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0) for the theme assignment.")

class BatchClassificationOutput(BaseModel):
    """Schema for the output of the batch classification LLM."""
    classifications: List[PostClassificationSchema] = Field(..., description="List of classifications for each post in the batch.")


POST_CLASSIFICATION_USER_PROMPT_TEMPLATE = """
You are given a list of LinkedIn posts and 5 predefined themes.

Assign each post to its most relevant theme. If no theme fits well, label it as "Other".

[THEMES]
```json
{themes_json}
```

Posts Batch (use 'urn' as the ID for classification):
```json
{posts_batch_json}
```
"""

POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE = """
You are a classification model trained in content categorization and social media tagging.

Your task is to classify each LinkedIn post into the **most relevant theme** from a predefined list of 5 themes. Each post must belong to one — and only one — theme. If none of the themes are a good match, assign it to "Other".

Guidelines:
- Use the theme descriptions provided to make accurate assignments
- Do not make up new themes
- Preserve all original post data (e.g., post text, ID)
- Include the name of the matched theme alongside the original post ID
- Be consistent in your classifications: similar posts should be grouped under the same theme
- For each post, provide its ID -- Don't generate it, use the post URN from the 'urn' field from the input post data, its a number and will be the post_id, the assigned theme ID or "Other", a confidence score (0.0-1.0), and a brief reasoning.

Follow the instructions precisely and respond only with the JSON output conforming to the schema: ```json\n{schema}\n```
"""
# assign theme Other if not a good fit to any themes!
# - Assign a theme to a post even if confidence is low, but reflect it in the score.


from typing import List
from pydantic import BaseModel, Field

# ---------- Sub-schemas ----------

class SentimentMetrics(BaseModel):
    label: str = Field(..., description="Overall sentiment label: Positive, Neutral, or Negative.")
    average_score: float = Field(..., description="Mean polarity score across the theme’s posts (-1.0 – 1.0).")

class ToneAnalysisSchema(BaseModel):
    dominant_tones: List[str] = Field(..., description="Most common emotional tones (e.g., Encouraging, Analytical).")
    sentiment: SentimentMetrics
    tone_summary: str = Field(..., description="Narrative summary of tonal patterns and their potential impact.")

class FormatMetrics(BaseModel):
    format_type: str = Field(..., description="Content format (Text-only, Image, Document, Video, Carousel, Poll, etc.).")
    usage_pct: float = Field(..., description="Percentage of theme posts using this format.")
    avg_engagement: float = Field(..., description="Average engagement rate for posts in this format.")

class StructureAnalysisSchema(BaseModel):
    top_formats: List[FormatMetrics]
    avg_word_count: float = Field(..., description="Mean word count of posts in this theme.")
    avg_read_time_sec: float = Field(..., description="Estimated reading time in seconds.")
    structure_summary: str = Field(..., description="Explanation of structural patterns and how they affect performance.")

class HookMetrics(BaseModel):
    hook_type: str = Field(..., description="Opening device (e.g., Question, Bold Claim, Statistic, Story Snippet).")
    usage_pct: float
    avg_engagement: float

class HookAnalysisSchema(BaseModel):
    top_hooks: List[HookMetrics]
    best_hook_example: str = Field(..., description="Short example of the highest-performing hook in this theme.")
    hook_summary: str = Field(..., description="Why these hooks work and when to use them.")

class EngagementPerformanceSchema(BaseModel):
    avg_likes: float
    avg_comments: float
    avg_reposts: float
    engagement_rate: float = Field(..., description="(likes + comments + reposts) ÷ followers, averaged across posts.")
    top_post_engagement: float
    performance_summary: str = Field(..., description="Key drivers of engagement and any anomalies to note.")

class TimingCadenceMetrics(BaseModel):
    posting_frequency_days: float = Field(..., description="Average number of days between posts in this theme.")
    peak_days: List[str] = Field(..., description="Weekdays that earn above-average engagement (e.g., ['Tuesday', 'Thursday']).")
    peak_hours_24h: List[int] = Field(..., description="Hours (0-23) that earn above-average engagement.")
    engagement_lift_at_peaks: float = Field(..., description="Percentage lift in engagement during peak windows.")
    timing_summary: str = Field(..., description="Interpretation of cadence and timing insights.")

class AssetTypeMetrics(BaseModel):
    asset_type: str = Field(..., description="Asset category (Image, Video, Document, None, etc.).")
    usage_pct: float
    avg_engagement: float

class AssetUsageSchema(BaseModel):
    asset_distribution: List[AssetTypeMetrics]
    asset_summary: str = Field(..., description="How different asset types contribute to engagement.")

class RecentTopicSchema(BaseModel):
    date: str
    topic: str
    engagement_rate: float
    short_summary: str

# ---------- Main Theme-level Diagnostics ----------

class ContentThemeAnalysisSchema(BaseModel):
    """
    Diagnostics for a single content theme after classifying and analysing the executive's LinkedIn posts.
    The focus is on actionable, channel-specific insights rather than writing-style minutiae.
    """
    theme_name: str
    theme_description: str

    tone_analysis: ToneAnalysisSchema
    structure_analysis: StructureAnalysisSchema
    hook_analysis: HookAnalysisSchema
    engagement_performance: EngagementPerformanceSchema
    timing_cadence: TimingCadenceMetrics
    asset_usage: AssetUsageSchema

    recent_topics: List[RecentTopicSchema]


THEME_ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze the following set of LinkedIn posts, all belonging to the same theme.

The group focuses on the theme '{theme_name}' ({theme_id}).
Theme Description: {theme_description}

Identify writing patterns, tone, structure, and engagement insights. Return your analysis and actionable suggestions.

[Posts] in this theme group (under 'mapped_posts'):
```json
{theme_group_json}
```
"""

THEME_ANALYSIS_SYSTEM_PROMPT_TEMPLATE = """
You are a social media content analyst with expertise in tone, structure, writing style, and audience engagement patterns.

You are analyzing a set of LinkedIn posts grouped by a specific theme. Your job is to identify how the user writes within this theme and extract actionable insights.

For the given theme:
- Analyze **tone** (dominant tones, emotional expression, sentiment trends)
- Evaluate **structure** (common formats, conciseness, length patterns)
- Examine **hooks** (opening lines, question usage, statistics, storytelling)
- Describe **linguistic style** (formality, use of emojis, jargon, formatting)
- Identify **frequent topics**
- Comment on **engagement trends** (what post types get more interaction)
- End with **3–5 recommendations** to improve performance or consistency within this theme

Be clear, concrete, and specific. Use examples where useful, but don't repeat full post texts. Your goal is to make the insights easy to apply.

Respond only with the JSON output conforming to the schema: ```json\n{schema}\n```
"""

EXTRACTED_THEMES_SCHEMA = ExtractedThemesOutput.model_json_schema()

BATCH_CLASSIFICATION_SCHEMA = BatchClassificationOutput.model_json_schema()

THEME_ANALYSIS_REPORT_SCHEMA = ContentThemeAnalysisSchema.model_json_schema()

