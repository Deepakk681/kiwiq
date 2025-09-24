"""
File Summarization Workflow - LLM Inputs

This file contains prompts, schemas, and configurations for the workflow that:
- Summarizes user-uploaded documents using GPT-5
- Generates summary names using GPT-5-mini with structured output
- Includes HITL approval flows and feedback processing
- Supports iteration limits to prevent infinite loops
- Enables flexible document storage with UUID-based naming
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

DEFAULT_SUMMARIZATION_SYSTEM_PROMPT = """You are an expert document analyst and summarization specialist. 
Your task is to analyze and summarize the provided documents to create comprehensive, well-structured summaries 
that capture the key information and insights.

Please:
1. Read and analyze all provided documents thoroughly
2. Identify the main themes, key points, and important details
3. Extract relevant data, statistics, and factual information
4. Organize information in a logical, coherent structure
5. Create clear, concise summaries that maintain accuracy
6. Highlight key findings and actionable insights
7. Preserve important context and relationships between information
8. Ensure the summary is comprehensive yet accessible

Focus on creating summaries that are both informative and easy to understand, maintaining the essential value of the original documents."""

SUMMARY_NAME_GENERATION_SYSTEM_PROMPT = """You are an expert at creating concise, descriptive names for document summaries. 
Generate a clear, professional name that captures the essence of the summarized content in 5-15 words."""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

DEFAULT_SUMMARIZATION_USER_PROMPT_TEMPLATE = """Please analyze and summarize the following documents:

**Summary Context:** {summary_context}

{additional_user_files}

Please provide a comprehensive summary that includes:

1. **Executive Summary** - Key findings and main insights (2-3 paragraphs)
2. **Document Overview** - Brief description of the documents and their purpose
3. **Key Points** - Main themes and important information organized by topic
4. **Data & Statistics** - Relevant metrics, numbers, and quantitative insights
5. **Important Details** - Critical information, dates, names, and specific facts
6. **Conclusions & Insights** - Main takeaways and implications
7. **Action Items** - Any tasks, recommendations, or next steps mentioned
8. **Document References** - Brief mention of source documents and their relevance
9. **Summary Limitations** - Any gaps or areas that need additional information

Please ensure the summary is accurate, comprehensive, and maintains the essential information from the original documents. 
Include specific details and data points where relevant to support your analysis.

If additional context files have been provided above, incorporate relevant insights from them into your summary."""

SUMMARY_NAME_GENERATION_USER_PROMPT_TEMPLATE = """Based on the following summary context, generate a concise, professional name for this document summary.

Summary Context: {summary_context}

The name should be:
- 5-15 words long
- Clear and descriptive
- Professional and suitable for a document summary title
- Capture the key essence of the summarized content
- Use title case formatting"""

FEEDBACK_REVISION_USER_PROMPT_TEMPLATE = "**Revision Request:**\n{revision_feedback}\n\n{hitl_additional_user_files}\n\nPlease address the above feedback and improve the summary accordingly. If additional context files have been provided above, incorporate relevant insights from them into your revised summary."

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class SummaryNameOutput(BaseModel):
    """Output schema for summary name generation."""
    summary_name: str = Field(
        ..., 
        description="A concise, professional name for the document summary (5-15 words)"
    )

# =============================================================================
# JSON SCHEMAS FOR LLM USE
# =============================================================================

# Generate JSON schema from Pydantic model
SUMMARY_NAME_OUTPUT_SCHEMA = SummaryNameOutput.model_json_schema()


# =============================================================================
# CODE RUNNER CONFIGURATIONS
# =============================================================================

# UUID concatenation code for code runner
SAVE_CONFIG_GENERATION_CODE = '''
import uuid

# Get inputs
summary_name = INPUT.get("summary_name", "document_summary")
asset_name = INPUT.get("asset_name", "default_asset")
input_namespace = INPUT.get("namespace")
input_docname = INPUT.get("docname")
input_is_shared = INPUT.get("is_shared")

# Generate a UUID suffix
uuid_suffix = str(uuid.uuid4())[:8]  # Use first 8 characters for readability

# Clean the summary name (remove special chars but keep spaces and case)
import re
clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', summary_name)  # Remove special chars
clean_name = " ".join(clean_name.split()[:10])

# Process namespace
if input_namespace:
    if "{item}" in input_namespace:
        namespace = input_namespace.replace("{item}", asset_name)
    else:
        namespace = input_namespace
else:
    # Default namespace with asset name
    namespace = f"document_summary_reports_{asset_name}"

# Process docname
if input_docname:
    if "{item}" in input_docname:
        # Replace {item} with just the uuid suffix
        docname = input_docname.replace("{item}", uuid_suffix)
    else:
        # Just attach suffix to provided docname
        docname = f"{input_docname}_{uuid_suffix}"
else:
    # Generate docname from clean summary name and suffix
    docname = f"{clean_name}_{uuid_suffix}"

# Process is_shared (default to False if not provided or None)
is_shared = bool(input_is_shared) if input_is_shared is not None else False

# Generate save config
save_config = [
    {
        "input_field_path": "summary_content",
        "target_path": {
            "filename_config": {
                "static_namespace": namespace,
                "static_docname": docname
            }
        },
        "is_shared": is_shared
    }
]

# Set result
RESULT = {
    "save_config": save_config,
    "final_docname": docname,
    "uuid_suffix": uuid_suffix,
    "clean_name": clean_name
}
'''
