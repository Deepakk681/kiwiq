# =============================================================================
# LLM MODEL CONFIGURATIONS
# =============================================================================
# Configuration for different LLM models used throughout the workflow steps.

# Maximum iterations for HITL feedback loops
MAX_LLM_ITERATIONS = 10

# Step 1: Summary Name Generation
GPT_MINI_PROVIDER = "openai"
GPT_MINI_MODEL = "gpt-5-mini"
SUMMARY_NAME_MAX_TOKENS = 500

# Steps 2 & 4: Document Summarization and Feedback Revision
GPT_5_PROVIDER = "openai"
GPT_5_MODEL = "gpt-5"

# General LLM Configuration
TEMPERATURE = 0.7
MAX_TOKENS = 8000


# =============================================================================
# LLM Inputs for File Summarisation Workflow
# =============================================================================
# This file contains prompts, schemas, and configurations organized by workflow steps:
# 1. Summary Name Generation - Auto-generate descriptive names for synthesis reports
# 2. Document Summarization - Create task-specific synthesis from documents
# 3. Summary Approval (HITL) - Human review and feedback processing
# 4. Feedback Revision - Apply feedback to improve summary

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =============================================================================
# STEP 1: SUMMARY NAME GENERATION (OPTIONAL)
# =============================================================================
# First optional step that generates a descriptive name for the synthesis report
# when no docname is provided by the user. Uses GPT-5-mini for efficient name generation.

# Summary Name Generation System Prompt
SUMMARY_NAME_GENERATION_SYSTEM_PROMPT = """You are an expert at creating concise, descriptive names for task-specific document synthesis reports.
Generate a clear, professional name that captures both the task context and the essence of the synthesized content in 5-15 words.
The name should reflect that this is a focused synthesis created for a specific task, not a general document summary."""

# Summary Name Generation User Prompt Template
SUMMARY_NAME_GENERATION_USER_PROMPT_TEMPLATE = """Based on the following task context, generate a concise, professional name for this task-specific document synthesis report.

Task Context: {summary_context}

The name should be:
- 5-15 words long
- Clear and descriptive of both the task and the synthesized content
- Professional and suitable for a task-focused synthesis report title
- Capture the key essence of the task and the relevant synthesized information
- Reflect that this is a focused synthesis created for a specific task
- Use title case formatting

Examples of good names:
- "AI Healthcare Impact Analysis Synthesis"
- "Blog Post Research Context Report"
- "Marketing Strategy Document Synthesis"
- "Product Launch Research Summary" """

# Variables Used in Summary Name Generation:
# - summary_context: The specific task context provided by the user that defines what information should be extracted

# Summary Name Output Schema
class SummaryNameOutput(BaseModel):
    """Output schema for summary name generation."""
    summary_name: str = Field(
        ...,
        description="A concise, professional name for the document summary (5-15 words)"
    )

SUMMARY_NAME_OUTPUT_SCHEMA = SummaryNameOutput.model_json_schema()

# =============================================================================
# STEP 2: DOCUMENT SUMMARIZATION
# =============================================================================
# Main step that analyzes and synthesizes documents based on task-specific context,
# filtering out irrelevant information and creating focused, actionable synthesis.

# Default Summarization System Prompt
DEFAULT_SUMMARIZATION_SYSTEM_PROMPT = """You are an expert document analyst and summarization specialist.
Your task is to analyze and summarize the provided documents to create a focused, high-quality synthesis report that will serve as crisp, relevant context for a specific task or project.

**CRITICAL INSTRUCTIONS:**
- You are NOT creating a general summary of all document content
- You are creating a TASK-SPECIFIC synthesis that filters out noise and irrelevant information
- Focus ONLY on information that is directly relevant to the provided task context
- Extract and synthesize only the insights, data, and details that will be useful for the specific task
- Remove or de-emphasize information that doesn't contribute to the task objectives
- Create a focused, actionable summary that serves as high-quality context for the task

**Your Process:**
1. Carefully read the task context to understand what information is needed
2. Analyze all provided documents with the task context in mind
3. Identify and extract ONLY information relevant to the specific task
4. Filter out noise, tangential details, and irrelevant content
5. Synthesize the relevant information into a coherent, task-focused summary
6. Organize the information to maximize its utility for the specific task
7. Ensure the summary provides crisp, high-quality context that directly supports the task

**Quality Standards:**
- Every piece of information in the summary should be relevant to the task
- The summary should be immediately actionable for the specific task
- Focus on insights, data, and details that directly contribute to task success
- Maintain accuracy while prioritizing relevance over comprehensiveness
- Create a synthesis that eliminates the need to re-read the original documents for task-relevant information"""

# Default Summarization User Prompt Template
DEFAULT_SUMMARIZATION_USER_PROMPT_TEMPLATE = """**TASK CONTEXT:** {summary_context}

**DOCUMENTS TO ANALYZE:**
{additional_user_files}

**YOUR MISSION:**
Create a focused synthesis report that will serve as high-quality context for the specific task described above.
This is NOT a general document summary - you are filtering and extracting ONLY the information that is directly
relevant to the task at hand.

**FILTERING CRITERIA:**
- Include ONLY information that directly supports or relates to the task context
- Exclude tangential details, background information, or content that doesn't contribute to the task
- Focus on actionable insights, relevant data, and specific details that will be useful for the task
- Prioritize information that helps achieve the task objectives

**REQUIRED SYNTHESIS STRUCTURE:**

1. **Task-Relevant Executive Summary** - Key insights directly applicable to the task (2-3 paragraphs)
2. **Relevant Key Points** - Main themes and information organized by relevance to the task
3. **Task-Specific Data & Statistics** - Metrics, numbers, and quantitative insights that support the task
4. **Critical Task Details** - Specific facts, dates, names, and information needed for the task
5. **Actionable Insights** - Takeaways and implications that directly support task completion
6. **Task-Supporting Evidence** - Specific examples, case studies, or data points relevant to the task
7. **Implementation Considerations** - Any practical details, recommendations, or next steps that help with the task

**QUALITY REQUIREMENTS:**
- Every section should contain information directly relevant to the task context
- Filter out noise and irrelevant content completely
- Ensure the synthesis provides crisp, actionable context for the task
- Include specific details and data points that directly support the task objectives
- Create a summary that eliminates the need to re-read original documents for task-relevant information

**IMPORTANT:** This synthesis will be used as context for the specific task described above. Focus on creating
maximum value for that task by including only the most relevant and actionable information."""

# Variables Used in Document Summarization:
# - summary_context: The task-specific context that defines what information should be extracted
# - additional_user_files: The loaded documents to be analyzed and synthesized

# =============================================================================
# STEP 3: SUMMARY APPROVAL (HITL)
# =============================================================================
# Human-in-the-loop step where users review the generated synthesis and can
# approve, request revisions, or cancel the workflow.

# HITL configuration is handled through the workflow, but feedback processing
# uses the revision prompt below.

# =============================================================================
# STEP 4: FEEDBACK REVISION
# =============================================================================
# Step that processes user feedback to improve the synthesis while maintaining
# task focus and filtering for relevance.

# Feedback Revision User Prompt Template
FEEDBACK_REVISION_USER_PROMPT_TEMPLATE = """**REVISION REQUEST:**\n{revision_feedback}\n\n**ADDITIONAL CONTEXT FILES:**\n{hitl_additional_user_files}\n\n**REVISION INSTRUCTIONS:**
Please address the above feedback while maintaining focus on the original task context. Remember that this synthesis
report is designed to serve as high-quality context for a specific task, so:

1. **Maintain Task Focus** - Ensure all revisions continue to support the original task objectives
2. **Filter for Relevance** - When incorporating new information, include only what's directly relevant to the task
3. **Preserve Quality** - Keep the synthesis crisp, actionable, and focused on task-relevant information
4. **Address Feedback** - Incorporate the requested changes while maintaining the task-specific filtering approach
5. **Eliminate Noise** - Continue to exclude tangential or irrelevant information that doesn't support the task

If additional context files have been provided above, incorporate only the insights that are directly relevant to
the task context and the revision feedback. Maintain the high-quality, focused nature of the synthesis report."""

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