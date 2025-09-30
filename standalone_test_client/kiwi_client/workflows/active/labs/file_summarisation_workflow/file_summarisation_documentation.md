# File Summarisation Workflow

## Variables and Important Configuration

### Input Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `summary_context` | str | Yes | The specific task context for which the document synthesis is being created. This defines what information should be extracted and what should be filtered out. Example: "Creating a blog post about AI in healthcare" or "Developing a marketing strategy for a new product launch". |
| `asset_name` | str | Yes | Asset name used for namespace and docname placeholder replacement. This helps organize and identify the generated summaries. |
| `namespace` | str | No (default: DOCUMENT_SUMMARY_REPORT_NAMESPACE_TEMPLATE) | Namespace for saving the document summary. Use {item} placeholder for asset name insertion. |
| `docname` | str | No | Document name for saving the summary. If not provided, a name will be auto-generated. Use {item} for random UUID suffix insertion. |
| `is_shared` | bool | No (default: False) | Flag to determine if the document summary should be shared across users or kept private. |
| `load_additional_user_files` | list | Yes | List of documents to be summarized. Each item must have 'namespace', 'docname', and 'is_shared' fields. These are the primary documents that will be analyzed and synthesized. |

### Setup Documents Required

#### 1. Documents to Summarize
- **When Loaded**: After input validation and before summarization begins
- **Purpose**: These are the primary documents that need to be synthesized based on the task context
- **Usage**: The LLM analyzes these documents through the lens of the specific task context, extracting relevant information and filtering out noise
- **Required Structure**: Each document in the list must specify namespace, docname, and is_shared status

#### 2. Additional Context Files (Optional)
- **When Loaded**: Can be loaded during HITL feedback if user specifies additional files
- **Purpose**: Provide supplementary context or information that might enhance the synthesis
- **Usage**: Incorporated into revision prompts when user requests improvements with additional context

### HITL Configuration

#### Summary Approval Node (`summary_approval`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_action` | enum | Yes | User's decision on the document summary |
| `revision_feedback` | str | Conditional | Feedback for summary improvements (required if action is request_revisions) |
| `load_additional_user_files` | list | No (default: []) | Additional files to load for enhanced context during revision |

**User Actions Explained:**
- **approve**: Accept the synthesis as final. The summary accurately captures the relevant information for your task context.
- **request_revisions**: Request improvements with specific feedback. Use this when the summary needs adjustments in focus, detail level, or coverage.
- **cancel**: Exit the workflow without finalizing. The draft summary will remain but won't be marked as complete.

**Revision Feedback Best Practices:**
- Be specific about what information is missing or incorrectly emphasized
- Indicate if the summary is too detailed or too high-level for your needs
- Specify if certain documents should be weighted more heavily
- Request inclusion of specific data points or examples if needed

### Synthesis Configuration

#### Task-Specific Filtering
The workflow excels at intelligent noise reduction based on your task context:
- **Relevance Filtering**: Only information pertinent to the specified task is extracted
- **Detail Level**: Automatically adjusts detail level based on task requirements
- **Cross-Document Synthesis**: Combines insights from multiple documents coherently
- **Actionable Output**: Creates summaries optimized for immediate use in your task

#### Name Generation
When no docname is provided:
- **Automatic Naming**: GPT-5-mini generates a descriptive name based on the summary context
- **UUID Suffix**: A unique identifier is appended to ensure no naming conflicts
- **Descriptive Format**: Names clearly indicate the content and purpose of the synthesis

### Model Configuration

#### Summary Generation
- **Model**: GPT-5 for high-quality synthesis
- **Temperature**: Configured via `TEMPERATURE` - balances creativity with accuracy
- **Max Tokens**: Configured via `MAX_TOKENS` - controls summary length
- **System Prompt**: Task-focused synthesis instructions

#### Name Generation (when needed)
- **Model**: GPT-5-mini for efficient name generation
- **Temperature**: Configured via `TEMPERATURE`
- **Max Tokens**: Configured via `SUMMARY_NAME_MAX_TOKENS`
- **Reasoning Effort**: "low" - optimized for quick name generation

### Configuration Limits

- **Maximum LLM Iterations**: Configured via `MAX_LLM_ITERATIONS` - prevents infinite revision loops
- **Iteration Tracking**: Stored in `generation_metadata.iteration_count`
- **Message History**: Maintained across iterations for context continuity
- **Save Configuration**: Generated dynamically with UUID support for unique naming

## Workflow Overview and Components

### Overview
This workflow enables task-specific document synthesis with intelligent noise filtering. It uses GPT-5 for intelligent document analysis and task-focused summarization, automatically generates synthesis report names using GPT-5-mini, provides UUID-based unique document naming, includes human-in-the-loop approval for synthesis review, and implements iteration limit checking to prevent infinite feedback loops.

The workflow excels at extracting only information relevant to specific task contexts while removing tangential details and irrelevant content, creating crisp, actionable synthesis reports ideal for scenarios like blog post research where multiple documents contain relevant context mixed with noise.

### Key Components

#### 1. Context Loading and Input Validation
**Node IDs**:
- Input: `input_node`
- Check Docname: `check_docname_provided`
- Router: `route_docname_check`
- Transform Files: `transform_additional_files_config`
- Load Additional: `load_additional_user_files_node`

**Purpose**: Establishes task context, validates input parameters, and loads necessary documents for summarization.

**Inputs Required**:
- `summary_context`: The specific task context defining what information should be extracted
- `asset_name`: Asset name for namespace and docname placeholder replacement
- `namespace`: Optional namespace for saving (default: `DOCUMENT_SUMMARY_REPORT_NAMESPACE_TEMPLATE`)
- `docname`: Optional docname for saving (uses UUID suffix if not provided)
- `is_shared`: Optional sharing flag (default: False)
- `load_additional_user_files`: List of files to summarize with namespace, docname, and is_shared fields

**Process**:
The workflow begins by checking if a docname is provided. If not, it routes to generate a summary name automatically. Additional user files undergo transformation to proper configuration format before loading. The system validates all inputs and prepares the context for summarization.

#### 2. Summary Name Generation
**Node IDs**:
- Prompt Constructor: `construct_summary_name_prompt`
- LLM: `generate_summary_name`

**Purpose**: Automatically generates descriptive names for synthesis reports when not provided by the user.

**Process**:
When no docname is provided, the system constructs a prompt using the summary context to generate an appropriate name. GPT-5-mini analyzes the context and produces a concise, descriptive name for the synthesis report.

**Prompt Configuration**:
- **System Prompt**: `SUMMARY_NAME_GENERATION_SYSTEM_PROMPT`
- **User Template**: `SUMMARY_NAME_GENERATION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `summary_context`: The task context for name generation
- **Output Schema**: `SUMMARY_NAME_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `GPT_MINI_PROVIDER`
- Model: Configured via `GPT_MINI_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `SUMMARY_NAME_MAX_TOKENS`
- Reasoning Effort: "low"

#### 3. Save Configuration Generation
**Node IDs**:
- Code Runner: `generate_save_config`

**Purpose**: Generates the complete save configuration including UUID-based unique naming when needed.

**Process**:
The code runner executes `SAVE_CONFIG_GENERATION_CODE` to create a structured save configuration. It handles placeholder replacement for asset names, generates UUIDs for unique document identification, and prepares the complete configuration for document storage.

**Code Runner Configuration**:
- Timeout: 30 seconds
- Memory: 256 MB
- Code: `SAVE_CONFIG_GENERATION_CODE`
- Fail on Error: True

#### 4. Document Summarization Phase
**Node IDs**:
- Prompt Constructor: `construct_summary_prompt`
- LLM: `conduct_summarization`
- Save Draft: `save_summary_draft`

**Purpose**: Performs intelligent document analysis and creates task-focused synthesis reports.

**Process**:
The system constructs a summarization prompt combining the task context with loaded documents. GPT-5 analyzes the documents through the lens of the specific task, filtering out irrelevant information and extracting only pertinent content. The synthesis focuses on actionable insights relevant to the defined context. After generation, the summary is automatically saved as a draft.

**Prompt Configuration**:
- **System Prompt**: `DEFAULT_SUMMARIZATION_SYSTEM_PROMPT`
- **User Template**: `DEFAULT_SUMMARIZATION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `summary_context`: The task-specific context
  - `additional_user_files`: Loaded document contents

**Model Configuration**:
- Provider: Configured via `GPT_5_PROVIDER`
- Model: Configured via `GPT_5_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`

**Save Configuration**:
- Uses dynamically generated save configuration
- Stores summary content with proper document structure
- Maintains versioning and metadata

#### 5. Human-in-the-Loop Approval
**Node IDs**:
- HITL: `summary_approval`
- Router: `route_summary_approval`
- Transform HITL Files: `transform_hitl_additional_files_config`
- Load HITL Files: `load_hitl_additional_user_files_node`

**Purpose**: Enables human review and approval of the generated synthesis with revision capabilities.

**User Actions Available**:
- **approve**: Accept the synthesis as final
- **request_revisions**: Request improvements with specific feedback
- **cancel**: Exit workflow without saving final version

**HITL Output Schema**:
- `user_action`: Required enum for user's decision
- `revision_feedback`: Feedback for improvements (required if request_revisions)
- `load_additional_user_files`: Optional additional files for revision context

**Process**:
The generated synthesis is presented for human review. Users can approve the content, request revisions with specific feedback, or cancel the workflow. If additional files are specified for revision context, they are loaded and incorporated into the revision process.

#### 6. Feedback Processing Loop
**Node IDs**:
- Check Limit: `check_iteration_limit`
- Router: `route_iteration_check`
- Feedback Prompt: `construct_feedback_prompt`

**Purpose**: Processes revision feedback and regenerates synthesis while preventing infinite loops.

**Process**:
When revisions are requested:
1. System checks if iteration limit has been reached
2. If within limits, constructs feedback prompt with revision instructions
3. Regenerates synthesis incorporating feedback
4. Returns to HITL for review

**Iteration Control**:
- Maximum iterations: Configured via `MAX_LLM_ITERATIONS`
- Iteration count tracked in `generation_metadata.iteration_count`
- Workflow outputs if limit exceeded

**Feedback Prompt Configuration**:
- **User Template**: `FEEDBACK_REVISION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `revision_feedback`: User's revision feedback
  - `hitl_additional_user_files`: Additional context files

The feedback prompt is used with the same LLM configuration as the main summarization, maintaining message history for context continuity.

#### 7. Output and Finalization
**Node IDs**:
- Output: `output_node`

**Purpose**: Finalizes the workflow and returns results based on the completion path.

**Output Information**:
- **On Approval**: Returns final synthesis content and storage paths
- **On Cancellation**: Returns partial results and cancellation status
- **On Iteration Limit**: Returns last synthesis version with limit reached status

**Data Returned**:
- `summary_content`: The final or latest synthesis report
- `final_summary_paths`: Storage paths for the saved document
- Metadata including iteration count and completion status

### State Management

The workflow maintains state through `$graph_state` with the following key fields:
- `summary_context`: Task context throughout the workflow
- `messages_history`: Conversation history for iterations (reducer: "add_messages")
- `generation_metadata`: LLM metadata including iteration tracking
- `save_config`: Dynamically generated save configuration
- `summary_content`: Current synthesis report content
- `revision_feedback`: Latest revision feedback from user
- `hitl_load_additional_user_files`: Additional files from HITL (reducer: "replace")

The state management ensures context preservation across iterations and proper tracking of the synthesis evolution through the revision process.