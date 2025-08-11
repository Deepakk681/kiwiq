"""
Brief to Blog Generation Workflow - LLM Inputs

This file contains prompts, schemas, and configurations for the workflow that:
- Takes a blog brief document as input
- Enriches the brief with domain knowledge from knowledge base
- Generates final blog content using SEO best practices and company guidelines
- Includes HITL approval flows and feedback processing
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT = """
You are a domain knowledge specialist tasked with enriching a blog content brief with relevant context from the company's knowledge base.

Your task is to:
1. Analyze the provided blog brief to identify all sections/topics covered
2. Search the knowledge_base namespace for documents containing information relevant to each section
3. Extract key insights, data points, examples, and context for each section
4. Return structured output mapping each section to its relevant context

You have access to document search tools to find relevant information in the knowledge base.

Guidelines:
- Only include context that is directly relevant to the brief sections
- If no relevant context is found for a section, mark it as optional (do not make up information)
- Focus on actionable insights, data points, case studies, and examples
- Prioritize recent and authoritative information
- Extract specific quotes, statistics, or examples when available
"""

CONTENT_GENERATION_SYSTEM_PROMPT = """
You are a senior content writer specializing in creating high-quality, SEO-optimized blog content.

Your task is to generate comprehensive blog content using:
- The original blog brief (structure, goals, target audience)
- Enriched domain knowledge context for each section
- SEO best practices document
- Company guidelines and brand voice

Create content that is:
- Well-structured and comprehensive
- SEO-optimized with natural keyword integration
- Aligned with company brand voice and guidelines
- Engaging and valuable to the target audience
- Backed by research and domain expertise

The output should be production-ready blog content that fulfills the brief requirements while incorporating the enriched knowledge context.
"""

FEEDBACK_ANALYSIS_SYSTEM_PROMPT = """
You are a content feedback analyst and improvement specialist.

You have been provided with:
1. Generated blog content
2. User feedback on that content
3. Access to the knowledge base for additional research

Your task is to:
1. Analyze the user feedback to understand specific improvement areas
2. Use knowledge base tools to gather any additional context needed
3. Provide structured update instructions for improving the content

Always provide clear, actionable improvement instructions that address the user's concerns while maintaining content quality and SEO effectiveness.
"""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE = """
Analyze the provided blog brief and enrich it with relevant domain knowledge from the knowledge base.

Blog Brief:
{blog_brief}

Your task:
1. Identify all sections/topics mentioned in the brief
2. Search the knowledge_base namespace for relevant documents
3. Extract context, insights, and examples for each section
4. Return structured output mapping sections to their relevant context

Use the document search tools available to find relevant information. Focus on actionable insights and specific examples.

Return the results in the specified JSON format.
"""

CONTENT_GENERATION_USER_PROMPT_TEMPLATE = """
Generate comprehensive blog content based on the provided inputs.

Original Blog Brief:
{blog_brief}

Enriched Knowledge Context:
{knowledge_context}

SEO Best Practices:
{seo_best_practices}

Company Guidelines:
{company_guidelines}

Instructions:
1. Create well-structured, comprehensive blog content
2. Integrate the enriched knowledge context naturally
3. Follow SEO best practices for keyword integration
4. Maintain company brand voice and guidelines
5. Ensure content is engaging and valuable to the target audience

IMPORTANT: MAIN_CONTENT field is most important field to generate.

Generate production-ready blog content that fulfills all brief requirements.

Return the results in the specified JSON format.
"""

FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze the user feedback and provide structured improvement instructions.

Original Blog Content:
{blog_content}

User Feedback:
{user_feedback}

Instructions:
1. Understand the specific areas the user wants improved
2. Use knowledge base tools if additional research is needed
3. Provide clear, actionable update instructions
4. Focus on addressing user concerns while maintaining quality

Return structured update instructions in the specified JSON format.
"""

CONTENT_UPDATE_USER_PROMPT_TEMPLATE = """
Update the blog content based on the feedback analysis and update instructions.

Original Blog Content:
{original_content}

Update Instructions:
{update_instructions}

Please generate improved blog content that addresses all the feedback points while maintaining quality and SEO effectiveness.

Return the updated content in the same JSON format as the original content generation.
"""

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class SectionContextSchema(BaseModel):
    """Schema for context information for a content section."""
    section_name: str = Field(description="Name of the content section")
    relevant_context: Optional[str] = Field(description="Relevant context and insights for this section, or null if no relevant information found")
    key_points: List[str] = Field(description="List of key points, data, or examples relevant to this section")

class KnowledgeEnrichmentSchema(BaseModel):
    """Schema for knowledge enrichment output."""
    enriched_sections: List[SectionContextSchema] = Field(description="List of content sections with their enriched context")

class BlogContentSchema(BaseModel):
    """Schema for generated blog content."""
    title: str = Field(description="SEO-optimized blog post title")
    main_content: str = Field(description="Main blog content with proper formatting and structure")

class ContentUpdateInstructionSchema(BaseModel):
    """Schema for content update instructions."""
    section_to_update: str = Field(description="Specific section or part of content to update")
    update_instruction: str = Field(description="Detailed instruction for how to update this section")
    additional_context: str = Field(description="Additional context for the update instruction")

class FeedbackAnalysisSchema(BaseModel):
    """Schema for feedback analysis output."""
    update_instructions: List[ContentUpdateInstructionSchema] = Field(description="List of specific update instructions")

# =============================================================================
# WORKFLOW CONTROL SCHEMA
# =============================================================================

# Convert Pydantic models to JSON schemas for LLM use
KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA = KnowledgeEnrichmentSchema.model_json_schema()
CONTENT_GENERATION_OUTPUT_SCHEMA = BlogContentSchema.model_json_schema()
FEEDBACK_ANALYSIS_OUTPUT_SCHEMA = FeedbackAnalysisSchema.model_json_schema()
