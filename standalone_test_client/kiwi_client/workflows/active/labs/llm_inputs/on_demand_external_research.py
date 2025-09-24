"""
On-Demand External Research Workflow - LLM Inputs

This file contains prompts, schemas, and configurations for the workflow that:
- Conducts comprehensive external research using Perplexity deep research models
- Generates research names using GPT-5-mini with structured output
- Includes HITL approval flows and feedback processing
- Supports iteration limits to prevent infinite loops
- Enables flexible document storage with UUID-based naming
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

DEFAULT_RESEARCH_SYSTEM_PROMPT = """You are an expert researcher with access to web search capabilities. 
Your task is to conduct thorough, comprehensive research on the given topic and provide well-structured, 
detailed insights with proper citations.

Please:
1. Search for current and relevant information from reliable sources
2. Analyze multiple perspectives and viewpoints on the topic
3. Provide clear, structured insights with detailed explanations
4. Include specific examples, data, statistics, and case studies when available
5. Cite your sources appropriately with URLs and publication details
6. Organize your findings in a logical, easy-to-follow structure
7. Highlight key findings and actionable insights
8. Address potential limitations or gaps in the research

Use your web search tools effectively to conduct comprehensive research across multiple sources and domains."""

RESEARCH_NAME_GENERATION_SYSTEM_PROMPT = """You are an expert at creating concise, descriptive names for research reports. 
Generate a clear, professional name that captures the essence of the research topic in 5-15 words."""

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

DEFAULT_RESEARCH_USER_PROMPT_TEMPLATE = """Please conduct comprehensive research on the following topic:

**Research Context:** {research_context}

{additional_user_files}

Please provide a detailed research report that includes:

1. **Executive Summary** - Key findings and insights (2-3 paragraphs)
2. **Background & Context** - Historical context and current state
3. **Key Findings** - Main research insights organized by themes
4. **Data & Statistics** - Relevant metrics, trends, and quantitative insights
5. **Expert Perspectives** - Quotes and insights from industry experts
6. **Case Studies & Examples** - Real-world applications and examples
7. **Future Outlook** - Trends, predictions, and implications
8. **Sources & References** - Complete list of sources with URLs and dates
9. **Research Limitations** - Any gaps or limitations in available information

Please ensure all findings are current (within the last 2 years when possible) and from credible sources. 
Include direct quotes where relevant and provide specific data points to support your analysis.

If additional context files have been provided above, incorporate relevant insights from them into your research."""

RESEARCH_NAME_GENERATION_USER_PROMPT_TEMPLATE = """Based on the following research context, generate a concise, professional name for this research report.

Research Context: {research_context}

The name should be:
- 5-15 words long
- Clear and descriptive
- Professional and suitable for a research report title
- Capture the key essence of the research topic
- Use title case formatting"""

FEEDBACK_REVISION_USER_PROMPT_TEMPLATE = "**Revision Request:**\n{revision_feedback}\n\n{hitl_additional_user_files}\n\nPlease address the above feedback and improve the research accordingly. If additional context files have been provided above, incorporate relevant insights from them into your revised research."

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ResearchNameOutput(BaseModel):
    """Output schema for research name generation."""
    research_name: str = Field(
        ..., 
        description="A concise, professional name for the research report (5-15 words)"
    )

# =============================================================================
# JSON SCHEMAS FOR LLM USE
# =============================================================================

# Generate JSON schema from Pydantic model
RESEARCH_NAME_OUTPUT_SCHEMA = ResearchNameOutput.model_json_schema()


# =============================================================================
# CODE RUNNER CONFIGURATIONS
# =============================================================================

# UUID concatenation code for code runner
SAVE_CONFIG_GENERATION_CODE = '''
import uuid

# Get inputs
research_name = INPUT.get("research_name", "research_report")
asset_name = INPUT.get("asset_name", "default_asset")
input_namespace = INPUT.get("namespace")
input_docname = INPUT.get("docname")
input_is_shared = INPUT.get("is_shared")

# Generate a UUID suffix
uuid_suffix = str(uuid.uuid4())[:8]  # Use first 8 characters for readability

# Clean the research name (remove special chars but keep spaces and case)
import re
clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', research_name)  # Remove special chars
clean_name = " ".join(clean_name.split()[:10])

# Process namespace
if input_namespace:
    if "{item}" in input_namespace:
        namespace = input_namespace.replace("{item}", asset_name)
    else:
        namespace = input_namespace
else:
    # Default namespace with asset name
    namespace = f"external_research_reports_{asset_name}"

# Process docname
if input_docname:
    if "{item}" in input_docname:
        # Replace {item} with just the uuid suffix
        docname = input_docname.replace("{item}", uuid_suffix)
    else:
        # Just attach suffix to provided docname
        docname = f"{input_docname}_{uuid_suffix}"
else:
    # Generate docname from clean research name and suffix
    docname = f"{clean_name}_{uuid_suffix}"

# Process is_shared (default to False if not provided or None)
is_shared = bool(input_is_shared) if input_is_shared is not None else False

# Generate save config
# save_config = {
#     "namespace": namespace,
#     "docname": docname,
#     "is_shared": is_shared
# }

save_config = [
    {
        "input_field_path": "research_content",
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
