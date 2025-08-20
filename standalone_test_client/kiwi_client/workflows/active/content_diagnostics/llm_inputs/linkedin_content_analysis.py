from typing import List, Union, Dict, Any
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
    confidence_score: float = Field(..., description="Confidence score (0 to 100) for the theme assignment.")

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
- For each post, provide its ID -- Don't generate it, use the post URN from the 'urn' field from the input post data, its a number and will be the post_id, the assigned theme ID or "Other", a confidence score (0-100), and a brief reasoning.

Follow the instructions precisely and respond only with the JSON output conforming to the schema: ```json\n{schema}\n```
"""
# assign theme Other if not a good fit to any themes!
# - Assign a theme to a post even if confidence is low, but reflect it in the score.


from typing import List
from pydantic import BaseModel, Field

# ---------- Sub-schemas ----------
class Citation(BaseModel):
    post_id: str = Field(..., description="Unique identifier of the source post")
    post_date: str = Field(..., description="Date of the cited post")
    excerpt: str = Field(..., description="Relevant excerpt from the post (max 200 chars)")

# ---------- Content Quality Metrics ----------

class ContentQualityMetrics(BaseModel):
    readability_score: float = Field(..., description="Flesch Reading Ease score or similar (0-100)")
    clarity_score: float = Field(..., description="Message clarity rating (0-100)")
    uniqueness_score: float = Field(..., description="Content originality score (0-100)")
    value_proposition_strength: float = Field(..., description="How clearly value is communicated (0-100)")
    quality_summary: str = Field(..., description="Overall content quality assessment")
    citations: List[Citation] = Field(..., description="Examples of high and low quality posts")

# ---------- Narrative and Storytelling ----------

class StorytellingMetrics(BaseModel):
    story_usage_pct: float = Field(..., description="Percentage of posts using storytelling")
    story_types: List[str] = Field(..., description="Types of stories used (personal, case study, analogy, etc.)")
    avg_story_engagement_lift: float = Field(..., description="Engagement boost from storytelling posts")
    best_story_example: Citation = Field(..., description="Most engaging story post")
    storytelling_summary: str = Field(..., description="Analysis of storytelling effectiveness")

# ---------- Call-to-Action Analysis ----------

class CTATypeDistribution(BaseModel):
    """OpenAI-compatible alternative to Dict[str, float] for CTA type distribution."""
    cta_type: str = Field(..., description="Type of CTA (comment, share, link, etc.)")
    percentage: float = Field(..., description="Percentage of posts using this CTA type")

class CTAMetrics(BaseModel):
    cta_usage_pct: float = Field(..., description="Percentage of posts with clear CTAs")
    cta_types: List[CTATypeDistribution] = Field(..., description="Distribution of CTA types as list of type-percentage pairs")
    avg_cta_conversion: float = Field(..., description="Average CTA response rate")
    most_effective_cta: str = Field(..., description="Highest performing CTA type")
    cta_examples: List[Citation] = Field(..., description="Examples of effective CTAs")
    cta_summary: str = Field(..., description="CTA strategy effectiveness analysis")

# ---------- Keywords and Topics ----------

class KeywordAnalysis(BaseModel):
    top_keywords: List[str] = Field(..., description="Most frequent keywords with frequency and engagement")
    trending_keywords: List[str] = Field(..., description="Keywords gaining traction recently")
    keyword_density: float = Field(..., description="Average keyword density percentage")
    keyword_performance: str = Field(..., description="Analysis of keyword impact on engagement")
    citations: List[Citation] = Field(..., description="Posts with effective keyword usage")

# ---------- Hashtag Analysis ----------

class HashtagMetrics(BaseModel):
    avg_hashtags_per_post: float
    hashtag_reach_impact: float = Field(..., description="Estimated reach increase from hashtags (%)")
    optimal_hashtag_count: int = Field(..., description="Number of hashtags for best engagement")
    hashtag_strategy: str = Field(..., description="Assessment of hashtag usage effectiveness")
    citations: List[Citation] = Field(..., description="Posts with effective hashtag strategies")

# ---------- Enhanced Format Metrics ----------

class FormatMetrics(BaseModel):
    format_type: str = Field(..., description="Content format (Text-only, Image, Document, Video, Carousel, Poll, etc.).")
    usage_pct: float = Field(..., description="Percentage of theme posts using this format (0 to 100).")
    avg_engagement: float = Field(..., description="Average engagement rate for posts in this format.")
    avg_reach: float = Field(..., description="Average reach for this format")
    format_trend: str = Field(..., description="Whether usage is increasing, stable, or decreasing")
    best_example: Citation = Field(..., description="Top performing post in this format")

class StructureAnalysisSchema(BaseModel):
    top_formats: List[FormatMetrics]
    avg_word_count: float = Field(..., description="Mean word count of posts in this theme.")
    avg_read_time_sec: float = Field(..., description="Estimated reading time in seconds.")
    bullet_point_usage: float = Field(..., description="Percentage of posts using bullet points")
    structure_summary: str = Field(..., description="Explanation of structural patterns and how they affect performance.")
    citations: List[Citation] = Field(..., description="Examples of effective structures")

# ---------- Enhanced Hook Analysis ----------

class HookMetrics(BaseModel):
    hook_type: str = Field(..., description="Opening device (e.g., Question, Bold Claim, Statistic, Story Snippet).")
    usage_pct: float = Field(..., description="Usage percentage (0 to 100)")
    avg_engagement: float
    avg_hook_length: int = Field(..., description="Average character count of hook")
    effectiveness_score: float = Field(..., description="Hook effectiveness rating (0-100)")

class HookAnalysisSchema(BaseModel):
    top_hooks: List[HookMetrics]
    best_hook_example: str = Field(..., description="Short example of the highest-performing hook in this theme.")
    worst_hook_example: str = Field(..., description="Example of ineffective hook for learning")
    hook_diversity_score: float = Field(..., description="Variety in hook usage (0-100)")
    hook_summary: str = Field(..., description="Why these hooks work and when to use them.")
    citations: List[Citation] = Field(..., description="Posts with notable hooks")

# ---------- Enhanced Engagement Performance ----------

class EngagementPerformanceSchema(BaseModel):
    avg_likes: float
    avg_comments: float
    avg_reposts: float
    avg_impressions: float = Field(..., description="Average post impressions")
    engagement_rate: float = Field(..., description="(likes + comments + reposts) ÷ followers, averaged across posts (0 to 100).")
    virality_score: float = Field(..., description="Measure of content spread beyond immediate network (0-100)")
    comment_sentiment: float = Field(..., description="Average sentiment of comments received (0-100)")
    top_post_engagement: float
    bottom_post_engagement: float
    engagement_variance: float = Field(..., description="Consistency of engagement across posts")
    performance_summary: str = Field(..., description="Key drivers of engagement and any anomalies to note.")
    top_performers: List[Citation] = Field(..., description="Highest engagement posts")
    low_performers: List[Citation] = Field(..., description="Lowest engagement posts for comparison")

# ---------- Audience Analysis ----------

class AudienceInsights(BaseModel):
    primary_audience_segments: List[str] = Field(..., description="Main audience categories engaging with content")
    evidence: List[Citation] = Field(..., description="Posts attracting target audience")

# ---------- Enhanced Timing and Cadence ----------

class TimingCadenceMetrics(BaseModel):
    posting_frequency_days: float = Field(..., description="Average number of days between posts in this theme.")
    peak_days: List[str] = Field(..., description="Weekdays that earn above-average engagement (e.g., ['Tuesday', 'Thursday']).")
    peak_hours: List[int] = Field(..., description="Hours of day with highest engagement (0-23)")
    engagement_lift_at_peaks: float = Field(..., description="Percentage lift in engagement during peak windows (0 to 100).")
    consistency_score: float = Field(..., description="How consistent the posting schedule is (0-100)")
    optimal_frequency: str = Field(..., description="Recommended posting frequency based on data")
    timing_summary: str = Field(..., description="Interpretation of cadence and timing insights.")

# ---------- Enhanced Asset Usage ----------

class AssetTypeMetrics(BaseModel):
    asset_type: str = Field(..., description="Asset category (Image, Video, Document, Infographic, GIF, None, etc.).")
    usage_pct: float = Field(..., description="Usage percentage (0 to 100)")
    avg_engagement: float
    production_effort: str = Field(..., description="Estimated effort level (Low, Medium, High)")
    roi_score: float = Field(..., description="Return on investment score considering effort vs engagement (0-100)")

class AssetUsageSchema(BaseModel):
    asset_distribution: List[AssetTypeMetrics]
    visual_consistency_score: float = Field(..., description="Brand consistency in visual assets (0-100)")
    asset_quality_score: float = Field(..., description="Average quality rating of assets (0-100)")
    asset_summary: str = Field(..., description="How different asset types contribute to engagement.")
    best_assets: List[Citation] = Field(..., description="Most effective asset examples")

class RecentTopicSchema(BaseModel):
    date: str
    topic: str
    engagement_rate: float
    reach: int
    sentiment_score: float
    short_summary: str
    post_citation: Citation

# ---------- Actionable Recommendations ----------

class Recommendation(BaseModel):
    priority: str = Field(..., description="Priority level (High, Medium, Low)")
    category: str = Field(..., description="Category (Content, Timing, Format, Engagement, etc.)")
    recommendation: str = Field(..., description="Specific actionable recommendation")
    expected_impact: str = Field(..., description="Expected outcome if implemented")
    implementation_difficulty: str = Field(..., description="Ease of implementation (Easy, Medium, Hard)")
    supporting_data: List[Citation] = Field(..., description="Data supporting this recommendation")

# ---------- Main Theme-level Diagnostics ----------

class ContentThemeAnalysisSchema(BaseModel):
    """
    Comprehensive diagnostics for a single content theme after classifying and analyzing LinkedIn posts.
    Includes detailed metrics, citations, and actionable insights for content optimization.
    """
    # Core Theme Information
    theme_name: str
    theme_description: str
    analysis_date: str = Field(..., description="Date of analysis")
    total_posts_analyzed: int
    
    # Content Analysis Sections
    content_quality: ContentQualityMetrics
    structure_analysis: StructureAnalysisSchema
    hook_analysis: HookAnalysisSchema
    storytelling_analysis: StorytellingMetrics
    cta_analysis: CTAMetrics
    
    # Discovery and Optimization
    keyword_analysis: KeywordAnalysis
    hashtag_metrics: HashtagMetrics
    
    # Performance Metrics
    engagement_performance: EngagementPerformanceSchema
    audience_insights: AudienceInsights
    timing_cadence: TimingCadenceMetrics
    asset_usage: AssetUsageSchema
    
    # Strategic Analysis
    recent_topics: List[RecentTopicSchema]
    
    # Actionable Insights
    key_findings: List[str] = Field(..., description="Top 5-7 most important findings")
    recommendations: List[Recommendation] = Field(..., description="Prioritized actionable recommendations")
    success_factors: List[str] = Field(..., description="What's working well that should continue")
    risk_factors: List[str] = Field(..., description="Potential issues to address")
    
    # Metadata
    confidence_score: float = Field(..., description="Overall confidence in analysis (0-100)")
    data_completeness: float = Field(..., description="Completeness of available data (0-100)")
    analysis_limitations: List[str] = Field(..., description="Any limitations or caveats in the analysis")


# ---------- Enhanced Prompt Templates ----------

THEME_ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze the following set of LinkedIn posts comprehensively, all belonging to the same theme.

The group focuses on the theme '{theme_name}' ({theme_id}).
Theme Description: {theme_description}

Perform a deep analysis covering:
1. Content quality and readability
2. Writing patterns, tone, and style consistency
3. Structure, formatting, and visual presentation
4. Engagement patterns and audience response
5. Keyword and hashtag effectiveness
6. Storytelling and CTA usage
7. Competitive positioning
8. Trends over time

For each finding, provide specific citations from the posts to support your analysis.
Return your analysis with actionable insights and prioritized recommendations.

[Posts] in this theme group (under 'mapped_posts'):
```json
{theme_group_json}
```
"""

THEME_ANALYSIS_SYSTEM_PROMPT_TEMPLATE = """
You are an expert social media content strategist specializing in LinkedIn optimization, with deep expertise in:
- Content analysis and quality assessment
- Engagement psychology and audience behavior
- Data-driven content strategy
- Competitive intelligence
- Performance optimization

You are analyzing a set of LinkedIn posts grouped by a specific theme. Your analysis must be:

1. **Evidence-Based**: Every claim must be supported by citations from actual posts
2. **Comprehensive**: Cover all aspects of content performance and quality
3. **Actionable**: Provide specific, implementable recommendations
4. **Quantitative**: Use metrics and scores wherever possible
5. **Strategic**: Consider both tactical improvements and strategic positioning

For the given theme, analyze:

**Content Quality & Messaging**
- Readability, clarity, and value proposition
- Message consistency and brand alignment
- Unique insights vs. generic content

**Tone & Voice**
- Emotional resonance and authenticity
- Professional vs. conversational balance
- Consistency across posts

**Structure & Format**
- Post length optimization
- Visual hierarchy and scannability
- Format variety and effectiveness

**Engagement Mechanics**
- Hook effectiveness
- Storytelling impact
- Call-to-action performance
- Comment-driving techniques

**Discovery & Reach**
- Keyword optimization
- Hashtag strategy
- Timing and frequency

**Audience & Community**
- Audience quality and relevance
- Community engagement patterns
- Influencer interactions

**Competitive Position**
- Performance vs. industry benchmarks
- Unique differentiators
- Gaps and opportunities

**Trends & Evolution**
- Performance trajectory
- Content evolution
- Emerging opportunities

Provide:
- Key findings with supporting evidence
- Prioritized recommendations (High/Medium/Low)
- Success factors to maintain
- Risk factors to address
- Clear next steps

Always cite specific posts as evidence using post IDs, dates, and relevant excerpts.

Respond only with the JSON output conforming to the schema: ```json\n{schema}\n```
"""

EXTRACTED_THEMES_SCHEMA = ExtractedThemesOutput.model_json_schema()

BATCH_CLASSIFICATION_SCHEMA = BatchClassificationOutput.model_json_schema()

THEME_ANALYSIS_REPORT_SCHEMA = ContentThemeAnalysisSchema.model_json_schema()

