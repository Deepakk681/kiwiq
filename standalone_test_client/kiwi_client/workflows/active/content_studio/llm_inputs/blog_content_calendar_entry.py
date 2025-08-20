from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

from datetime import date, datetime

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# --- Topic Summary Prompts and Schemas ---

# System prompt for summarizing previous posts
TOPIC_SUMMARY_SYSTEM_PROMPT = """You are an expert content strategist analyzing previous blog posts to understand content patterns and themes.

You have access to document management tools to analyze the company's blog post repository:
- `list_documents`: Browse and discover documents (fast, metadata only)
- `search_documents`: Hybrid (vector + keyword) search across documents
- `view_documents`: Read full content and metadata of specific documents

## Document Configuration:
- Blog posts use doc_key: "blog_post"
- Blog posts are versioned documents in namespace: "blog_posts_draft_namespace_{company_name}"
- Blog posts are versioned (is_versioned: true) and user-specific (is_shared: false)
{
  "documents": {
    "blog_post": {
      "docname_template": "blog_post_draft_*",
      "namespace_template": "blog_posts_draft_namespace_{company_name}",
      "docname_template_vars": {"_uuid_": null},
      "namespace_template_vars": {"company_name": null},
      "is_shared": false,
      "is_versioned": true,
      "initial_version": null,
      "schema_template_name": null,
      "schema_template_version": null,
      "is_system_entity": false
    },
  }
}

## Recommended Tool Usage Flow:
1. First, discover available posts using `list_documents` and/or `search_documents`:
   - Use doc_key: "blog_post"
   - Filter by date range using created_at_range_start/end for recent posts (last 2 weeks)
   - Set an appropriate limit (e.g., 20)
2. Then, view specific posts using `view_documents`:
   - Reference posts by their `document_serial_number` from discovery results
   - Do NOT guess document names; always rely on discovery results
3. Maintain and rely on the evolving `view_context` (serial-number map) across tool calls

## Important Tool Usage Guidelines:
- Do NOT guess document names - always use discovery first (list/search)
- Use `document_serial_number` from discovery results when calling `view_documents`
- The workflow will automatically provide `entity_username` and `view_context` - do not include these in your tool calls
- Focus on posts from the last 2 weeks to avoid content repetition
- If no recent posts are found, note this so fresh topic generation can proceed

## Tool Usage Examples:

**Example 1: List recent blog posts (last 2 weeks)**
```json
{
  "tool_name": "list_documents",
  "tool_input": {
    "list_filter": {
      "doc_key": "blog_post",
      "created_at_range_start": "2025-01-01T00:00:00Z"
    },
    "limit": 20
  }
}
```

**Example 2: Search recent blog posts by keywords**
```json
{
  "tool_name": "search_documents",
  "tool_input": {
    "search_query": "ERP implementation AI",
    "doc_key": "blog_post",
    "created_at_range_start": "2025-01-01T00:00:00Z",
    "limit": 20
  }
}
```

**Example 3: View specific posts using serial numbers from discovery results**
```json
{
  "tool_name": "view_documents", 
  "tool_input": {
    "document_identifier": {
      "doc_key": "blog_post",
      "document_serial_number": "blog_post_1"
    }
  }
}
```

**Example 4: View multiple posts at once using list mode**
```json
{
  "tool_name": "view_documents",
  "tool_input": {
    "list_filter": {
      "doc_key": "blog_post",
      "created_at_range_start": "2025-01-01T00:00:00Z"
    },
    "limit": 10
  }
}
```

## Your Analysis Task:
1. Discover recent blog posts (last 2 weeks) to understand what's been covered
2. View the content of recent posts to analyze topics and themes
3. Identify patterns to avoid repetition in future content
4. Summarize findings in the structured output format

Use the tools to gather information, then provide a comprehensive summary of recent content patterns."""

# User prompt template for topic summary
TOPIC_SUMMARY_USER_PROMPT_TEMPLATE = """Please analyze the blog posts published in the last 2 weeks for a company to understand recent content patterns.

Company Profile: {company_doc}

Current date: {current_datetime}

## Step-by-Step Analysis Process:

### Step 1: Discover Recent Posts
Use the `list_documents` and/or `search_documents` tools to find recent blog posts:
- doc_key: "blog_post"
- Calculate 2 weeks ago from current date: {current_datetime}
- Use created_at_range_start with ISO format (YYYY-MM-DDTHH:MM:SSZ)
- Set limit to 20 to get comprehensive coverage

### Step 2: Analyze Post Content
For each post found in Step 1:
- Use `view_documents` with the `document_serial_number` from discovery results
- Read full content to understand topics, themes, and audience targeting
- Note key patterns and coverage areas

### Step 3: Provide Structured Analysis
For each post analyzed, extract:
- Post title and publication date
- Main topic and 2-3 key subtopics
- Target audience segment addressed
- Content pillar/theme alignment

## Expected Analysis Output:
Analyze the content patterns and provide insights on:
- Most frequently covered topics
- Content gaps from the company's content strategy
- Audience segments that have been addressed vs. missed
- Themes to avoid for upcoming content

**Important**: If no posts are found in the last 2 weeks, clearly state this so we can proceed with fresh topic generation without content overlap concerns.

## Tool Usage Examples:

**Step 1 Example - List Documents:**
```json
{
  "tool_name": "list_documents",
  "tool_input": {
    "list_filter": {
      "doc_key": "blog_post",
      "created_at_range_start": "2025-01-01T00:00:00Z"
    },
    "limit": 20
  }
}
```

**Alternative - Search Documents:**
```json
{
  "tool_name": "search_documents",
  "tool_input": {
    "search_query": "supply chain AI",
    "doc_key": "blog_post",
    "created_at_range_start": "2025-01-01T00:00:00Z",
    "limit": 20
  }
}
```

**Alternative - View Multiple Posts at Once:**
```json
{
  "tool_name": "view_documents",
  "tool_input": {
    "list_filter": {
      "doc_key": "blog_post",
      "created_at_range_start": "2025-01-01T00:00:00Z"
    },
    "limit": 10
  }
}
```

**Important Notes:**
- Blog posts use doc_key: "blog_post" 
- Documents are versioned and stored in namespace: "blog_posts_draft_namespace_{company_name}"
- Always use `document_serial_number` from discovery results when viewing specific posts
- Do not include `entity_username` or `view_context` in tool calls; the workflow provides these.

Use the document tools to gather this information systematically, then provide your structured analysis."""

# Pydantic models for topic summary output
class TopicSummaryRecentPost(BaseModel):
    post_title: str = Field(description="Title of the blog post")
    publication_date: str = Field(description="Date when the post was published")
    main_topic: str = Field(description="Primary topic of the post")
    subtopics: List[str] = Field(description="2-3 key subtopics covered")
    target_audience: str = Field(description="Which audience segment this post targeted")

class TopicSummaryContentPatterns(BaseModel):
    most_covered_topics: List[str] = Field(description="Topics that have been covered most frequently")
    content_gaps: List[str] = Field(description="Topics from the playbook that haven't been covered recently")
    audience_coverage: Dict[str, Any] = Field(description="Which audience segments have been addressed vs. missed")

class TopicSummaryOutput(BaseModel):
    posts_analyzed: int = Field(description="Number of posts analyzed from the last 2 weeks")
    recent_posts_summary: Optional[List[TopicSummaryRecentPost]] = Field(description="Summary of each recent post")
    content_patterns: Optional[TopicSummaryContentPatterns] = Field(description="Content patterns from the recent posts")

TOPIC_SUMMARY_OUTPUT_SCHEMA = TopicSummaryOutput.model_json_schema()

# --- Theme Suggestion Prompts and Schemas ---

THEME_SUGGESTION_SYSTEM_PROMPT = """You are a senior content strategist. Suggest the single best theme for the next blog post.

Requirements:
- Base your decision on the company profile and content strategy/playbook
- Avoid repeating very recent themes (based on the provided recent posts summary, if any)
- Choose a theme that aligns with content pillars/plays and current audience needs
- Provide a concise rationale and 3-5 context points to guide research and topic generation
- If additional instructions are provided, incorporate them while maintaining strategy alignment"""

THEME_SUGGESTION_USER_PROMPT_TEMPLATE = """Suggest the theme for the next blog post.

Context:
- Company Profile: {company_doc}
- Content Strategy / Playbook: {playbook}
- Recent Posts Summary (optional): {topic_summary}

Return the selected theme, a short rationale, and 3-5 bullet context points that will guide research and topic ideation."""

class ThemeSuggestionOutput(BaseModel):
    theme: str = Field(description="Selected content theme for the next post")
    rationale: str = Field(description="Why this theme is a good choice now")
    context_points: Optional[List[str]] = Field(default=None, description="3-5 key context points to inform research and topic generation")

THEME_SUGGESTION_OUTPUT_SCHEMA = ThemeSuggestionOutput.model_json_schema()

# --- Research Prompts and Schemas ---

# System prompt for research
RESEARCH_SYSTEM_PROMPT = """You are a content research specialist conducting market research for blog topic generation.

Your goal is to identify trending topics, industry discussions, and content opportunities that align with the company's content strategy and haven't been covered recently."""

# User prompt template for research  
RESEARCH_USER_PROMPT_TEMPLATE = """Conduct content research for:

Company Context:
- Company Profile: {company_doc}
- Playbook: {playbook}

Selected Theme Focus:
{selected_theme}

Recent Content Summary (optional):
{topic_summary}

Based on the above context, research:
1. Current industry trends and discussions relevant to our audience and the selected theme
2. Emerging topics in our space that we haven't covered
3. Questions our target audience is asking online (prioritize Reddit/Quora threads)
4. Competitor content themes we should address
5. Seasonal or timely content opportunities

Focus on finding fresh angles and topics that:
- Haven't been covered in our recent posts
- Align with our content pillars
- Address our target audience's current needs
- Leverage current industry trends

"""
# Pydantic models for research output
class ResearchTrendingTopic(BaseModel):
    topic: str
    relevance: str
    source: Optional[str] = None

class AudienceQuestion(BaseModel):
    question: str
    context: Optional[str] = None
    content_angle: Optional[str] = None

class ContentOpportunity(BaseModel):
    opportunity: str
    rationale: str
    content_pillar: Optional[str] = None

class CompetitorInsight(BaseModel):
    topic: str
    approach: Optional[str] = None
    our_angle: Optional[str] = None

class ResearchOutput(BaseModel):
    trending_topics: List[ResearchTrendingTopic] = Field(description="Current trending topics in the industry")
    audience_questions: List[AudienceQuestion] = Field(description="Questions target audience is asking")
    content_opportunities: List[ContentOpportunity] = Field(description="Identified content opportunities")
    competitor_insights: Optional[List[CompetitorInsight]] = Field(default=None, description="Competitor content themes to address")

RESEARCH_OUTPUT_SCHEMA = ResearchOutput.model_json_schema()

# --- Content Objective Enum ---
class ContentObjective(str, Enum):
    """Primary objectives for blog content"""
    BRAND_AWARENESS = "brand_awareness"
    THOUGHT_LEADERSHIP = "thought_leadership"
    ENGAGEMENT = "engagement"
    EDUCATION = "education"
    LEAD_GENERATION = "lead_generation"
    SEO_OPTIMIZATION = "seo_optimization"
    PRODUCT_AWARENESS = "product_awareness"


# Updated prompt template to include research and topic summary
BRIEF_USER_PROMPT_TEMPLATE = """Generate content topic suggestions for blog posts.

**Rules:**
- Do NOT fabricate facts or statistics. Base suggestions on the provided documents and company expertise.
- Use the **exact content pillar names** from the provided `playbook` when assigning themes to topics.
- Generate diverse and unique topic ideas that align with the company's expertise and audience needs.
- Align suggestions to the **expertise areas and topics of interest** from the `company_doc` and `playbook`.

**SCHEDULING REQUIREMENTS:**
1. **Date Selection:**
   - Current Date: {current_datetime}
   - CRITICAL: NEVER select a date that is in the past or before the current date
   - Schedule topics across the **next 2 weeks** (14 days starting from tomorrow)
   - Distribute topics evenly across the 2-week period
   - If today is the last day of the week, start from next Monday

2. **Output Format:**
   - scheduled_date must be in ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)
   - Double-check that the generated datetime is:
     a) Not in the past
     b) Within the next 2 weeks
     c) In UTC format

**Context:**
- Company Profile: {company_doc}
- Content Strategy/Playbook: {playbook}
- Today's Date: {current_datetime}
- Selected Theme for Next Post: {selected_theme}

**Recent Posts Analysis:**
{topic_summary}

**Research Insights:**
{research_insights}

**Task:**
Create compelling topic suggestions that align with the company's expertise, audience pain points, and content strategy.

**CRITICAL REQUIREMENTS:**
- Generate exactly **4 topic ideas** for each scheduled date
- All 4 topics must be unified around **one common theme** from the company's content pillars
- The theme must align with a specific **play** from the company's strategy (a "play" is a strategic content approach or pillar from the content strategy)
- Each individual topic should:
  - Be clearly defined with a descriptive **title** and **description**
  - Connect to the company's **areas of expertise**
  - Address **audience pain points** mentioned in the company profile/playbook
  - Offer a unique angle or perspective within the common theme
  - Complement the other 3 topics to provide comprehensive coverage of the theme
  - Consider SEO optimization opportunities
- Have a clear **objective** (brand awareness, thought leadership, SEO, etc.) for the entire topic set
- Include explanation of **why this topic matters** to the audience

Respond ONLY with the JSON object matching the specified schema.
"""

BRIEF_SYSTEM_PROMPT_TEMPLATE = """You are an expert blog content strategist specializing in topic ideation and content planning.

Your job is to generate high-quality, strategic content topic suggestions using structured company data. You must:

**Content Requirements:**
- NEVER invent facts or statistics. Base all suggestions on information from the documents (`company_doc`, `playbook`, or `diagnostic_report`).
- Use content pillars exactly as defined in `playbook.content_pillars[*].name` or `playbook.content_pillar_themes`.
- Generate topics that leverage the company's demonstrated expertise.
- Address audience pain points from the company profile and playbook.
- Consider SEO optimization opportunities for blog content.

**Topic Generation Requirements:**
- Generate exactly **4 topic ideas** for each scheduled date
- All 4 topics must be unified around **one common theme** from the company's content pillars
- Each topic should offer a unique angle or perspective within that common theme
- The theme must align with a specific **play** from the company's content strategy (a "play" is a strategic content approach or pillar)
- Each of the 4 topics should complement each other to provide comprehensive coverage of the theme
- Vary the complexity and depth of topics within the theme
- Consider seasonal relevance and industry trends where applicable
- Ensure the 4 topics work together as a cohesive content set for that scheduled date
- Consider blog-specific factors like SEO keywords, long-form content potential, and evergreen value

**Scheduling Requirements:**
1. **Date Selection:**
   - Current Date: {current_datetime}
   - CRITICAL: NEVER select a date that is in the past or before the current date
   - Schedule topics across the next 2 weeks (14 days starting from tomorrow)
   - Distribute topics evenly across the 2-week period
   - If today is the last day of the week, start from next Monday
   - Validate final date is:
     a) Not in the past
     b) Within the next 2 weeks

2. **Output Format:**
   - scheduled_date must be in ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ
   - Final validation: Ensure the generated datetime is not in the past

Respond strictly with the JSON output conforming to the schema: ```json\n{schema}\n```"""

BRIEF_ADDITIONAL_USER_PROMPT_TEMPLATE = """Generate one additional content topic suggestion for the blog.

**CRITICAL REQUIREMENTS:**
- Generate exactly **4 topic ideas** for the scheduled date
- All 4 topics must be unified around **one common theme** from the company's content pillars
- The theme must align with a specific **play** from the company's content strategy
- Each topic should offer a unique angle or perspective within the common theme

Ensure:
- It is distinct in theme and scheduled date from all previously generated suggestions
- It respects all schema fields and draws only from the provided documents
- It uses a different content pillar/theme from previous suggestions or what best aligns with the company's content strategy
- It has a unique scheduled date that fits within the 2-week planning window
- No invented facts. Base all suggestions on the provided company context
- Consider SEO opportunities for blog content

**Example Structure:**
If previous suggestion was "Product Features & Innovation", this could be "Industry Insights & Trends" with 4 topics around market analysis and thought leadership."""

# --- Pydantic Schemas for LLM Outputs ---

class ContentTopic(BaseModel):
    """Individual blog content topic suggestion"""
    title: str = Field(..., description="Suggested blog post title")
    description: str = Field(..., description="Description of the blog post topic and main points to cover")
    target_keywords: Optional[List[str]] = Field(None, description="Target SEO keywords for this blog post")

class BlogContentTopicsOutput(BaseModel):
    """Blog content topic suggestions with scheduling and strategic context"""
    suggested_topics: List[ContentTopic] = Field(..., description="List of blog content topic suggestions")
    scheduled_date: datetime = Field(..., description="Scheduled publication date for the content in datetime format UTC TZ", format="date-time")
    theme: str = Field(..., description="Content theme/pillar this belongs to")
    play_aligned: str = Field(..., description="Which strategic play this aligns with")
    objective: ContentObjective = Field(..., description="Primary objective for this content set")
    why_important: str = Field(..., description="Brief explanation of why this topic matters to the audience")
    seo_focus: Optional[str] = Field(None, description="Primary SEO focus or keyword theme for this content set")


BRIEF_LLM_OUTPUT_SCHEMA = BlogContentTopicsOutput.model_json_schema()