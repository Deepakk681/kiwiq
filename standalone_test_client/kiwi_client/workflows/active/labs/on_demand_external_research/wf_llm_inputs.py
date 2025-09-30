# =============================================================================
# LLM MODEL CONFIGURATIONS
# =============================================================================
# Configuration for different LLM models used throughout the workflow steps.

# Maximum iterations for HITL feedback loops
MAX_LLM_ITERATIONS = 10

# Step 1: Research Name Generation
GPT_MINI_PROVIDER = "openai"
GPT_MINI_MODEL = "gpt-5-mini"
RESEARCH_NAME_MAX_TOKENS = 500

# Step 2 & 4: External Research and Feedback Revision
PERPLEXITY_LLM_PROVIDER = "perplexity"
PERPLEXITY_LLM_MODEL = "sonar-pro"
# NOTE: while replacing this with deep researcher, also modify max tokens in override config!

# General LLM Configuration
TEMPERATURE = 0.7
MAX_TOKENS = 8000


# =============================================================================
# LLM Inputs for On-Demand External Research Workflow
# =============================================================================
# This file contains prompts, schemas, and configurations organized by workflow steps:
# 1. Research Name Generation - Auto-generate descriptive names for research reports
# 2. External Research - Conduct targeted external research using Perplexity
# 3. Research Approval (HITL) - Human review and feedback processing
# 4. Feedback Revision - Apply feedback to improve research

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# STEP 1: RESEARCH NAME GENERATION (OPTIONAL)
# =============================================================================
# First optional step that generates a descriptive name for the research report
# when no docname is provided by the user. Uses GPT-5-mini for efficient name generation.

# Research Name Generation System Prompt
RESEARCH_NAME_GENERATION_SYSTEM_PROMPT = """You are an expert at creating concise, descriptive names for context-specific external research reports.
Generate a clear, professional name that captures both the research context and the value-added external research in 5-15 words.
The name should reflect that this is targeted external research designed to enhance a specific research context, not general research on a broad topic."""

# Research Name Generation User Prompt Template
RESEARCH_NAME_GENERATION_USER_PROMPT_TEMPLATE = """Based on the following research context, generate a concise, professional name for this context-specific external research report.

Research Context: {research_context}

The name should be:
- 5-15 words long
- Clear and descriptive of both the research context and the external research value
- Professional and suitable for a context-specific research report title
- Capture the key essence of the research context and the external research contribution
- Reflect that this is targeted external research designed to enhance the specific research context
- Use title case formatting

Examples of good names:
- "AI Healthcare Market Research Enhancement"
- "Blog Content Strategy External Validation"
- "Product Launch Market Intelligence Report"
- "Marketing Campaign Research Context Extension" """

# Variables Used in Research Name Generation:
# - research_context: The specific research context that defines what external research is needed

# Research Name Output Schema
class ResearchNameOutput(BaseModel):
    """Output schema for research name generation."""
    research_name: str = Field(
        ...,
        description="A concise, professional name for the research report (5-15 words)"
    )

RESEARCH_NAME_OUTPUT_SCHEMA = ResearchNameOutput.model_json_schema()

# =============================================================================
# STEP 2: EXTERNAL RESEARCH
# =============================================================================
# Main step that conducts comprehensive external research using Perplexity's
# deep research models to find targeted, context-specific information.

# Default Research System Prompt
DEFAULT_RESEARCH_SYSTEM_PROMPT = """You are an expert researcher with access to web search capabilities.
Your task is to conduct focused, context-specific external research that adds maximum value to the provided research context.

**CRITICAL INSTRUCTIONS:**
- You are NOT conducting general research on a broad topic
- You are conducting TARGETED research that directly supports and enhances the specific research context
- Focus ONLY on information that adds value, fills gaps, or provides new insights relevant to the research context
- Prioritize research that directly contributes to the goals and objectives outlined in the research context
- Filter out tangential information, general background, or content that doesn't enhance the specific context
- Create research that serves as high-value, actionable intelligence for the specific research purpose

**Your Research Process:**
1. Carefully analyze the research context to understand what specific information is needed
2. Identify knowledge gaps, missing perspectives, or areas that need additional external validation
3. Conduct targeted searches for information that directly supports the research context
4. Focus on current, relevant data that adds new insights or validates existing information
5. Prioritize sources and information that provide actionable value for the specific research purpose
6. Synthesize findings to create a focused research report that enhances the original context
7. Ensure every piece of research directly contributes to the research context objectives

**Quality Standards:**
- Every research finding should directly support or enhance the research context
- Focus on information that provides new insights, validation, or actionable intelligence
- Prioritize current, credible sources that add maximum value to the specific research purpose
- Create research that eliminates the need for additional external validation on the topic
- Ensure the research report serves as a comprehensive, value-added extension of the original context"""

# Default Research User Prompt Template
DEFAULT_RESEARCH_USER_PROMPT_TEMPLATE = """**RESEARCH CONTEXT:** {research_context}

**EXISTING CONTEXT FILES:**
{additional_user_files}

**YOUR MISSION:**
Conduct targeted external research that adds maximum value to the research context above. This is NOT general research
on a broad topic - you are conducting focused research to enhance, validate, and add new insights to the specific
research context provided.

**RESEARCH OBJECTIVES:**
- Identify knowledge gaps in the existing research context that need external validation
- Find current, relevant information that directly supports or enhances the research context
- Discover new insights, data, or perspectives that add value to the specific research purpose
- Validate existing information with external sources and current data
- Provide actionable intelligence that directly contributes to the research context goals

**REQUIRED RESEARCH STRUCTURE:**

1. **Context-Enhancing Executive Summary** - Key external findings that add value to the research context (2-3 paragraphs)
2. **Value-Added Key Findings** - External research insights organized by relevance to the research context
3. **Supporting Data & Statistics** - Current metrics, trends, and quantitative insights that validate or enhance the context
4. **Expert Validation & Perspectives** - External expert quotes and insights that support the research context
5. **Context-Supporting Case Studies** - Real-world examples that directly relate to the research context
6. **Current Market Intelligence** - Latest trends, developments, and implications relevant to the research context
7. **Actionable External Insights** - New information that provides actionable value for the research context
8. **Sources & References** - Complete list of external sources with URLs and dates
9. **Research Gaps Identified** - Areas where additional external research might be needed

**QUALITY REQUIREMENTS:**
- Every research finding should directly enhance, validate, or add new insights to the research context
- Focus on current information (within the last 2 years when possible) from credible sources
- Prioritize research that provides actionable intelligence for the specific research purpose
- Include specific data points, quotes, and examples that directly support the research context
- Create research that serves as a comprehensive, value-added extension of the existing context

**IMPORTANT:** This external research will be integrated with the existing research context to create a comprehensive
research report. Focus on finding information that adds maximum value and fills knowledge gaps in the specific
research context provided above."""

# Variables Used in External Research:
# - research_context: The specific research context that defines what external research is needed
# - additional_user_files: The loaded documents that provide existing context

# =============================================================================
# STEP 3: RESEARCH APPROVAL (HITL)
# =============================================================================
# Human-in-the-loop step where users review the generated research and can
# approve, request revisions, or cancel the workflow.

# HITL configuration is handled through the workflow, but feedback processing
# uses the revision prompt below.

# =============================================================================
# STEP 4: FEEDBACK REVISION
# =============================================================================
# Step that processes user feedback to improve the research while maintaining
# context focus and value addition.

# Feedback Revision User Prompt Template
FEEDBACK_REVISION_USER_PROMPT_TEMPLATE = """**REVISION REQUEST:**\n{revision_feedback}\n\n**ADDITIONAL CONTEXT FILES:**\n{hitl_additional_user_files}\n\n**REVISION INSTRUCTIONS:**
Please address the above feedback while maintaining focus on the original research context. Remember that this external
research is designed to add maximum value to a specific research context, so:

1. **Maintain Context Focus** - Ensure all revisions continue to support and enhance the original research context
2. **Filter for Value Addition** - When incorporating new information, include only what directly adds value to the research context
3. **Preserve Research Quality** - Keep the research focused, actionable, and directly relevant to the research context
4. **Address Feedback** - Incorporate the requested changes while maintaining the context-specific research approach
5. **Enhance Context Value** - Continue to prioritize research that provides maximum value for the specific research purpose

If additional context files have been provided above, incorporate only the insights that directly enhance the research
context and address the revision feedback. Maintain the high-value, context-focused nature of the external research."""

# Variables Used in Feedback Revision:
# - revision_feedback: The user's specific feedback about what needs to be improved
# - hitl_additional_user_files: Additional files loaded during HITL for enhanced context

# =============================================================================
# SAVE CONFIGURATION GENERATION (CODE RUNNER)
# =============================================================================
# Code runner that generates dynamic save configuration with UUID-based naming
# for unique document identification when docname is not provided.

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
clean_name = re.sub(r'[^a-zA-Z0-9\\s]', '', research_name)  # Remove special chars
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