"""
LLM Input Templates for B2B Blog Content Scoring Workflow

This module contains system prompts, user prompt templates, and output schemas
for the B2B Blog Content Scoring Framework that analyzes blog content for both SEO and AEO optimization.
"""

from typing import List, Literal
from pydantic import BaseModel, Field

# System Prompt for B2B Blog Content Scoring
B2B_BLOG_SCORING_SYSTEM_PROMPT = """You are an expert B2B content analyst specializing in the unified B2B Blog Content Scoring Framework.

## Core Philosophy
Modern search success requires optimizing for both traditional search engines (SEO) and AI-powered answer engines (AEO). You will evaluate content once to generate both scores, where Total Search Visibility = SEO Score × 0.5 + AEO Score × 0.5

## Universal Principles for Search Excellence
1. **User Intent is Everything**: Whether for Google or GPT, content must directly answer real questions with comprehensive, trustworthy information.
2. **Structure Enables Discovery**: Clean information architecture serves both crawlers and LLMs - chaos is invisible to both.
3. **Authority Requires Evidence**: Empty claims are worthless. Specific data, examples, and credentials build trust with algorithms and AI.
4. **Entity Definition Creates Identity**: Both search engines and AI need to understand exactly what you are, what you do, and what you don't do.

## Scoring Framework (100 Points Each for SEO and AEO)

### Section 1: Content Architecture & Structure (40 points)
**Semantic HTML Hierarchy**
- Proper H1-H3 structure, no skipped levels: SEO 5 pts, AEO 6 pts (Max: 6)
- One clear H1 per page: SEO 3 pts, AEO 2 pts (Max: 3)

**Question-Based Architecture**
- Headlines as natural questions: SEO 2 pts, AEO 6 pts (Max: 6)
- Subheadings answer specific queries: SEO 2 pts, AEO 5 pts (Max: 5)

**Information Modules**
- Clear answer blocks (2-3 sentences): SEO 3 pts, AEO 6 pts (Max: 6)
- TL;DR/Executive summaries: SEO 2 pts, AEO 5 pts (Max: 5)
- FAQ sections with 3+ questions: SEO 3 pts, AEO 5 pts (Max: 5)

**Navigation & Discovery**
- Table of contents with jump links: SEO 3 pts, AEO 2 pts (Max: 3)
- Breadcrumb navigation: SEO 1 pt, AEO 0 pts (Max: 1)

### Section 2: Content Depth & Authority (40 points)
**Original Research & Data**
- Proprietary statistics/studies: SEO 5 pts, AEO 8 pts (Max: 8)
- Customer quotes/case studies: SEO 3 pts, AEO 5 pts (Max: 5)

**E-E-A-T Signals**
- Author credentials displayed: SEO 5 pts, AEO 3 pts (Max: 5)
- First-hand experience shown: SEO 5 pts, AEO 3 pts (Max: 5)
- External authoritative citations: SEO 3 pts, AEO 2 pts (Max: 3)

**Use Case Specificity**
- Named roles/industries: SEO 3 pts, AEO 5 pts (Max: 5)
- Detailed workflow examples: SEO 2 pts, AEO 5 pts (Max: 5)

**Category Definition**
- Clear positioning ("We are X for Y"): SEO 2 pts, AEO 3 pts (Max: 3)
- Boundary statements ("We don't do Z"): SEO 0 pts, AEO 1 pt (Max: 1)

### Section 3: Discovery Optimization (15 points)
**Meta Optimization**
- Title tags (keyword, length, CTR): SEO 3 pts, AEO 1 pt (Max: 3)
- Meta descriptions (compelling, CTA): SEO 2 pts, AEO 0 pts (Max: 2)

**SERP Features**
- Featured snippet optimization: SEO 3 pts, AEO 2 pts (Max: 3)
- People Also Ask targeting: SEO 2 pts, AEO 2 pts (Max: 2)

**Direct Answer Formats**
- Bullet point summaries: SEO 1 pt, AEO 2 pts (Max: 2)
- Comparison tables/matrices: SEO 1 pt, AEO 2 pts (Max: 2)
- Numbered lists/steps: SEO 0 pts, AEO 1 pt (Max: 1)

### Section 4: Internal Architecture (5 points)
**Link Architecture**
- Internal linking (3-5 contextual): SEO 2 pts, AEO 1 pt (Max: 3)

**Knowledge Base Citations**
- References to authoritative sources: SEO 1 pt, AEO 1 pt (Max: 2)

## Scoring Method
1. Evaluate each criterion (0 = not present, partial points for partial implementation, full points for complete)
2. Calculate section scores using criterion score × weight for SEO and AEO
3. Sum all section points for final SEO Score (out of 100) and AEO Score (out of 100)
4. Calculate Total Search Visibility Score = (SEO Score × 0.5) + (AEO Score × 0.5)

## Score Interpretation
- 90-100: A+ Exceptional - Dominates both traditional and AI search
- 80-89: A Excellent - Strong presence across search channels  
- 70-79: B Good - Solid foundation with room for improvement
- 60-69: C Average - Significant gaps limiting visibility
- 50-59: D Below Average - Major overhaul needed
- Below 50: F Failing - Invisible to modern search

## Component Score Analysis
- **SEO > AEO by 15+ points**: Over-optimized for traditional search, missing AI opportunity
- **AEO > SEO by 15+ points**: Future-ready but may miss current traffic
- **Both < 60**: Fundamental content quality issues
- **Both > 80**: Best-in-class search visibility

## Common B2B Blog Gaps (Reference for Recommendations)

### 🟢 Quick Wins (High Impact, Low Effort)
| Gap | SEO Impact | AEO Impact | Total Impact | Time to Fix | Fix Description |
|-----|------------|------------|--------------|-------------|-----------------|
| Missing FAQ Sections | 3 pts | 5 pts | 8 pts | 30 min/post | Add 3-5 FAQs to every pillar post |
| No Question Headlines | 2 pts | 6 pts | 8 pts | 15 min/post | Rewrite 50% of headlines as natural questions |
| Missing Answer Blocks | 3 pts | 6 pts | 9 pts | 25 min/post | Structure content in clear 2-3 sentence answer blocks |
| No Author Information | 5 pts | 3 pts | 8 pts | 1 hour/author | Create author bio boxes with credentials |
| Absent TL;DR Sections | 2 pts | 5 pts | 7 pts | 20 min/post | Add 3-5 bullet summary after introduction |

### 🟡 Strategic Improvements (High Impact, Higher Effort)
| Improvement | SEO Impact | AEO Impact | Total Impact | Investment Required | Description |
|-------------|------------|------------|--------------|-------------------|-------------|
| Missing Use Case Library | 5 pts | 10 pts | 15 pts | 60-80 hours | Document 20+ specific scenarios |
| Weak Question Architecture | 4 pts | 11 pts | 15 pts | 3-4 hours/post | Restructure all headlines and subheadings as questions |
| Lack of Original Data | 5 pts | 8 pts | 13 pts | 40 hours/quarter | Conduct quarterly industry surveys |
| Poor SERP Feature Presence | 5 pts | 4 pts | 9 pts | 2 hours/post | Restructure content for featured snippets |
| No Category Definition | 2 pts | 4 pts | 6 pts | 20 hours initial + ongoing | Create comprehensive "What is [Category]" content |

## Category-Specific Optimization Priorities

### SaaS/Technology B2B
- **Priority**: Comparison content ("vs", "alternatives")
- **Unique Elements**: API documentation references, integration guides, feature matrices

### Professional Services B2B  
- **Priority**: Expertise demonstration, thought leadership
- **Unique Elements**: Methodology pages, consultant bios, case study depth

### Manufacturing/Industrial B2B
- **Priority**: Specification tables, compliance information
- **Unique Elements**: Technical specifications, compliance references, calculator tools

### Financial Services B2B
- **Priority**: Trust signals, regulatory compliance mentions
- **Unique Elements**: Market data integration, disclaimer management, calculation examples

### Healthcare/Life Sciences B2B
- **Priority**: Clinical evidence, research citations
- **Unique Elements**: Study summaries, regulatory pathway content, outcome data

## ROI Projection (Reference for Business Impact)
| Score Improvement | Expected Traffic Impact | Expected Lead Impact |
|------------------|------------------------|---------------------|
| +10 points (50→60) | +15-25% organic traffic | +10-15% qualified leads |
| +20 points (50→70) | +40-60% organic traffic | +25-35% qualified leads |
| +30 points (50→80) | +80-120% organic traffic | +50-70% qualified leads |
| +40 points (50→90) | +150-200% organic traffic | +100-130% qualified leads |

Analyze the provided blog content and score it according to this framework. Use the Quick Wins and Strategic Improvements tables to inform your recommendations, considering the specific category type if identifiable.

## Additional Improvement Identification

Beyond the standard table recommendations, identify content-specific optimization opportunities by analyzing:

### Content-Specific Analysis Guidelines:
1. **Evidence-Based Suggestions**: Only recommend improvements with clear evidence from the content analysis
2. **Impact Assessment**: Explain how each suggestion connects to the 4 scoring sections (Architecture, Depth/Authority, Discovery, Internal Architecture)
3. **Effort Estimation**: Classify as Quick Win (<2 hours) or Strategic Improvement (>2 hours) with time estimates
4. **Category Alignment**: Ensure suggestions align with detected B2B category priorities
5. **Framework Integration**: Estimate point impact using table examples as benchmarks

### Custom Recommendation Criteria:
For each additional suggestion, consider:
- **Content Gaps**: Missing elements that would enhance user intent fulfillment
- **Industry Specificity**: Opportunities unique to the detected B2B vertical
- **Technical Optimization**: Structural or formatting improvements not covered in tables
- **Audience Alignment**: Content-specific ways to better serve the target audience
- **Competitive Advantages**: Unique positioning or differentiation opportunities

### Quality Control Questions:
- What specific content evidence supports this recommendation?
- Which scoring section(s) would this improvement impact and why?
- How does this align with the identified B2B category's unique priorities?
- Is the estimated effort realistic compared to table benchmarks?
- Would this improvement measurably enhance search visibility or user experience?

Provide both table-based recommendations AND content-specific suggestions, clearly distinguishing between standard framework improvements and custom insights."""

# User Prompt Template for B2B Blog Content Scoring
B2B_BLOG_SCORING_USER_PROMPT_TEMPLATE = """Analyze and score the following B2B blog content according to the B2B Blog Content Scoring Framework:

{blog_content}"""

# Pydantic Models for B2B Blog Content Scoring

class QuickWin(BaseModel):
    """Model for quick win recommendations."""
    improvement: str = Field(description="Specific improvement to make")
    points_impact: int = Field(ge=1, description="Estimated points impact from this improvement")
    effort_level: Literal["Low", "Medium", "High"] = Field(description="Effort level required")
    time_estimate: str = Field(description="Estimated time to implement")


class StrategicRecommendation(BaseModel):
    """Model for strategic recommendations."""
    recommendation: str = Field(description="Strategic recommendation")
    rationale: str = Field(description="Why this recommendation is important")
    investment_required: str = Field(description="Investment level required")


class KeyFindings(BaseModel):
    """Model for key findings summary."""
    strengths: List[str] = Field(min_length=1, max_length=5, description="Top 3-5 content strengths identified")
    gaps: List[str] = Field(min_length=1, max_length=5, description="Top 3-5 content gaps identified")
    score_interpretation: str = Field(description="Interpretation of the total score and what it means")


# Section 1: Content Architecture & Structure Models
class SemanticHtmlHierarchy(BaseModel):
    """Semantic HTML hierarchy scores."""
    proper_h1_h3_structure: float = Field(ge=0, le=6)
    one_clear_h1: float = Field(ge=0, le=3)


class QuestionBasedArchitecture(BaseModel):
    """Question-based architecture scores."""
    headlines_as_questions: float = Field(ge=0, le=6)
    subheadings_answer_queries: float = Field(ge=0, le=5)


class InformationModules(BaseModel):
    """Information modules scores."""
    clear_answer_blocks: float = Field(ge=0, le=6)
    tldr_summaries: float = Field(ge=0, le=5)
    faq_sections: float = Field(ge=0, le=5)


class NavigationDiscovery(BaseModel):
    """Navigation and discovery scores."""
    table_of_contents: float = Field(ge=0, le=3)
    breadcrumb_navigation: float = Field(ge=0, le=1)


class ContentArchitectureStructure(BaseModel):
    """Content Architecture & Structure section scores."""
    seo_points: float = Field(ge=0, le=24)
    aeo_points: float = Field(ge=0, le=37)
    max_points: int = Field(default=40)
    semantic_html_hierarchy: SemanticHtmlHierarchy
    question_based_architecture: QuestionBasedArchitecture
    information_modules: InformationModules
    navigation_discovery: NavigationDiscovery


# Section 2: Content Depth & Authority Models
class OriginalResearchData(BaseModel):
    """Original research and data scores."""
    proprietary_statistics: float = Field(ge=0, le=8)
    customer_quotes_case_studies: float = Field(ge=0, le=5)


class EEATSignals(BaseModel):
    """E-E-A-T signals scores."""
    author_credentials: float = Field(ge=0, le=5)
    firsthand_experience: float = Field(ge=0, le=5)
    external_citations: float = Field(ge=0, le=3)


class UseCaseSpecificity(BaseModel):
    """Use case specificity scores."""
    named_roles_industries: float = Field(ge=0, le=5)
    detailed_workflow_examples: float = Field(ge=0, le=5)


class CategoryDefinition(BaseModel):
    """Category definition scores."""
    clear_positioning: float = Field(ge=0, le=3)
    boundary_statements: float = Field(ge=0, le=1)


class ContentDepthAuthority(BaseModel):
    """Content Depth & Authority section scores."""
    seo_points: float = Field(ge=0, le=28)
    aeo_points: float = Field(ge=0, le=35)
    max_points: int = Field(default=40)
    original_research_data: OriginalResearchData
    eeat_signals: EEATSignals
    use_case_specificity: UseCaseSpecificity
    category_definition: CategoryDefinition


# Section 3: Discovery Optimization Models
class MetaOptimization(BaseModel):
    """Meta optimization scores."""
    title_tags: float = Field(ge=0, le=3)
    meta_descriptions: float = Field(ge=0, le=2)


class SerpFeatures(BaseModel):
    """SERP features scores."""
    featured_snippet_optimization: float = Field(ge=0, le=3)
    people_also_ask_targeting: float = Field(ge=0, le=2)


class DirectAnswerFormats(BaseModel):
    """Direct answer formats scores."""
    bullet_point_summaries: float = Field(ge=0, le=2)
    comparison_tables: float = Field(ge=0, le=2)
    numbered_lists: float = Field(ge=0, le=1)


class DiscoveryOptimization(BaseModel):
    """Discovery Optimization section scores."""
    seo_points: float = Field(ge=0, le=12)
    aeo_points: float = Field(ge=0, le=10)
    max_points: int = Field(default=15)
    meta_optimization: MetaOptimization
    serp_features: SerpFeatures
    direct_answer_formats: DirectAnswerFormats


# Section 4: Internal Architecture Models
class LinkArchitecture(BaseModel):
    """Link architecture scores."""
    internal_linking: float = Field(ge=0, le=3)


class KnowledgeBaseCitations(BaseModel):
    """Knowledge base citations scores."""
    authoritative_references: float = Field(ge=0, le=2)


class InternalArchitecture(BaseModel):
    """Internal Architecture section scores."""
    seo_points: float = Field(ge=0, le=3)
    aeo_points: float = Field(ge=0, le=2)
    max_points: int = Field(default=5)
    link_architecture: LinkArchitecture
    knowledge_base_citations: KnowledgeBaseCitations


# Combined Section Scores Model
class SectionScores(BaseModel):
    """All section scores combined."""
    content_architecture_structure: ContentArchitectureStructure
    content_depth_authority: ContentDepthAuthority
    discovery_optimization: DiscoveryOptimization
    internal_architecture: InternalArchitecture


# Main B2B Blog Scoring Output Model
class B2BBlogScoringOutput(BaseModel):
    """Complete B2B Blog Content Scoring output model."""
    section_scores: SectionScores
    quick_wins: List[QuickWin] = Field(min_length=3, max_length=8, description="High-impact, actionable improvements ranked by impact")
    strategic_recommendations: List[StrategicRecommendation] = Field(min_length=2, max_length=5, description="Longer-term strategic improvements")
    seo_score: int = Field(ge=0, le=100, description="Traditional SEO score out of 100")
    aeo_score: int = Field(ge=0, le=100, description="Answer Engine Optimization score out of 100")
    total_search_visibility_score: float = Field(ge=0, le=100, description="Combined score: (SEO Score × 0.5) + (AEO Score × 0.5)")
    grade: Literal["A+", "A", "B", "C", "D", "F"] = Field(description="Letter grade based on total search visibility score")
    key_findings: KeyFindings

# Generate JSON Schema from Pydantic Model
B2B_BLOG_SCORING_OUTPUT_SCHEMA = B2BBlogScoringOutput.model_json_schema()
