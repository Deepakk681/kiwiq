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
2. Search the knowledge base for documents containing information relevant to each section
3. Extract key insights, data points, examples, and context for each section
4. Return structured output mapping each section to its relevant context

You have access to the following document tools:
1) view_documents — Read full content of specific documents or list with content
2) list_documents — Fast browsing by type/namespace (metadata only)
3) search_documents — Hybrid (vector + keyword) search across documents

Tool usage guidelines:
- Do not guess document names. First discover (list/search), then view the specific docs using returned serial numbers
- Keep tool calls purposeful and minimal; batch discovery where possible
- Maintain and rely on the evolving view_context (serial-number map)
- Prefer recent and higher-quality sources; cite quotes/data verbatim when used

Document Config Mapping (use only these for this workflow):
{
  "documents": {
    "blog_uploaded_files": {
      "docname_template": "",
      "namespace_template": "blog_uploaded_files_{company_name}",
      "docname_template_vars": {},
      "namespace_template_vars": {"company_name": null},
      "is_shared": false,
      "is_versioned": false,
      "initial_version": null,
      "schema_template_name": null,
      "schema_template_version": null,
      "is_system_entity": false
    }
  }
}

Additional guidance:
- When discovering documents, prefer list_documents with namespace scoping to the company
- When multiple candidates are found, pick the most relevant few to view, not all
- If no relevant context is found for a section, return it as empty rather than inventing content
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

Context for tools:
- Company name (entity scope): {company_name}
- Primary doc_key to use: blog_uploaded_files
- Namespace pattern to search: blog_uploaded_files_{company_name}

Your task:
1. Identify all sections/topics mentioned in the brief
2. Use list_documents/search_documents to discover relevant files under the namespace above
3. Use view_documents to read specific documents (selected via serial numbers)
4. Extract context, insights, concrete data points, quotes, and examples for each section
5. Return structured output mapping sections to their relevant context, leaving any section empty when nothing relevant is found

Tool usage requirements:
- Do not guess document names. First use list/search tools, then view specific docs via serial numbers
- Prefer recent or higher-quality sources when multiple are available
- Keep total tool calls minimal and purposeful; batch discovery where possible

Return the results strictly in the provided JSON schema.
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
2. Integrate the enriched knowledge context naturally (cite specific data/quotes inline where appropriate)
3. Follow SEO best practices for keyword integration and formatting (H1/H2/H3)
4. Maintain company brand voice and guidelines
5. Ensure content is engaging and valuable to the target audience
6. Ensure MAIN_CONTENT is the most complete and detailed section

IMPORTANT: MAIN_CONTENT field is most important field to generate.

Generate production-ready blog content that fulfills all brief requirements.

Return the results strictly in the specified JSON schema.
"""

FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze the user feedback and provide structured improvement instructions.

Original Blog Content:
{blog_content}

User Feedback:
{user_feedback}

Instructions:
1. Identify specific improvement areas from the feedback
2. If additional facts/examples are needed, propose targeted lookups (but do not execute edits here)
3. Provide clear, actionable update instructions, referencing the portions to change
4. Maintain SEO and brand voice alignment in the guidance

Return structured update instructions in the specified JSON schema.
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
