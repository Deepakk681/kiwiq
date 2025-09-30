# On-Demand External Research Workflow

## Variables and Important Configuration

### Input Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `research_context` | str | Yes | The research topic or context to investigate. This defines the focus and scope of the external research. Example: "Latest trends in AI-powered sales automation" or "Best practices for SaaS customer retention". |
| `asset_name` | str | Yes | Asset name used for namespace and docname placeholder replacement. Helps organize and identify research reports. |
| `namespace` | str | No (default: EXTERNAL_RESEARCH_REPORT_NAMESPACE_TEMPLATE) | Namespace for saving the research report. Use {item} placeholder for asset name insertion. |
| `docname` | str | No | Document name for saving the research. If not provided, a name will be auto-generated based on the research context. Use {item} for random UUID suffix insertion. |
| `is_shared` | bool | No (default: False) | Flag to determine if the research report should be shared across users or kept private. |
| `load_additional_user_files` | list | No (default: []) | Optional list of additional files to provide context for the research. Each item must have 'namespace', 'docname', and 'is_shared' fields. |

### Setup Documents Required

#### 1. Additional Context Files (Optional)
- **When Loaded**: At the beginning if provided, or during HITL feedback
- **Purpose**: Provide supplementary context or existing research that should inform the new investigation
- **Usage**: Incorporated into research prompts to ensure the external research builds upon or complements existing knowledge
- **Structure**: Each file must specify namespace, docname, and is_shared status

### HITL Configuration

#### Research Approval Node (`research_approval`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_action` | enum | Yes | User's decision on the research report |
| `revision_feedback` | str | Conditional | Feedback for research improvements (required if action is request_revisions) |
| `load_additional_user_files` | list | No (default: []) | Additional files to provide context for research revision |

**User Actions Explained:**
- **approve**: Accept the research as comprehensive and accurate. The report adequately covers the research context with reliable sources.
- **request_revisions**: Request improvements with specific feedback. Use when the research needs deeper investigation, different sources, or adjusted focus.
- **cancel**: Exit the workflow without finalizing. The draft research will remain but won't be marked as complete.

**Revision Feedback Best Practices:**
- Specify areas that need deeper investigation or clarification
- Request additional sources or different types of sources if needed
- Indicate if the research should focus more on practical applications vs theory
- Ask for specific data points, statistics, or case studies if missing
- Request different perspectives or viewpoints on controversial topics

### Research Configuration

#### Perplexity Deep Research
The workflow leverages Perplexity's advanced research capabilities:
- **Real-Time Web Search**: Accesses current information from across the web
- **Source Diversity**: Gathers insights from multiple authoritative sources
- **Citation Tracking**: Maintains references to all sources for verification
- **Comprehensive Coverage**: Explores multiple angles and perspectives on the topic

#### Research Report Structure
Generated reports typically include:
- **Executive Summary**: High-level overview of key findings
- **Detailed Analysis**: In-depth exploration of the research topic
- **Key Insights**: Actionable takeaways and important discoveries
- **Citations**: Web search result citations for all claims and data
- **Trends and Patterns**: Identified themes across multiple sources

#### Name Generation
When no docname is provided:
- **Automatic Naming**: GPT-5-mini generates a descriptive name based on research context
- **UUID Suffix**: Ensures unique identification of each research report
- **Context-Aware**: Names reflect the specific research focus and scope

### Model Configuration

#### Research Generation
- **Model**: Perplexity's research model for comprehensive web investigation
- **Provider**: Configured via `PERPLEXITY_LLM_PROVIDER`
- **Model Version**: Configured via `PERPLEXITY_LLM_MODEL`
- **Temperature**: Configured via `TEMPERATURE` - balances thoroughness with focus
- **Max Tokens**: Configured via `MAX_TOKENS` - controls research report length

#### Name Generation (when needed)
- **Model**: GPT-5-mini for efficient name generation
- **Provider**: Configured via `GPT_MINI_PROVIDER`
- **Model Version**: Configured via `GPT_MINI_MODEL`
- **Temperature**: Configured via `TEMPERATURE`
- **Max Tokens**: Configured via `RESEARCH_NAME_MAX_TOKENS`
- **Reasoning Effort**: "low" - optimized for quick name generation

### Configuration Limits

- **Maximum LLM Iterations**: Configured via `MAX_LLM_ITERATIONS` - prevents infinite revision loops
- **Iteration Tracking**: Stored in `generation_metadata.iteration_count`
- **Message History**: Maintained across iterations for context continuity
- **Web Search Results**: Captured in `web_search_result` field with citations
- **Save Configuration**: Generated dynamically with UUID support for unique naming

### Research Quality Controls

- **Source Verification**: All claims are backed by web search citations
- **Multi-Source Validation**: Information is cross-referenced across sources
- **Recency Priority**: Focuses on current and recent information
- **Bias Mitigation**: Seeks diverse perspectives on topics
- **Depth Control**: Balances comprehensive coverage with focused analysis

## Workflow Overview and Components

### Overview
This workflow enables comprehensive external research using Perplexity's deep research models for web-based investigation. It automatically generates research report names using GPT-5-mini, provides UUID-based unique document naming, includes human-in-the-loop approval for research review and refinement, and implements iteration limits to ensure controlled feedback processing.

The workflow is designed for on-demand research tasks where users need comprehensive, real-time information from web sources, with the ability to review and refine the research output through iterative feedback.

### Key Components

#### 1. Context Loading and Input Validation
**Node IDs**:
- Input: `input_node`
- Check Docname: `check_docname_provided`
- Router: `route_docname_check`
- Transform Files: `transform_additional_files_config`
- Load Additional: `load_additional_user_files_node`

**Purpose**: Establishes research context, validates input parameters, and loads supplementary documents for enhanced research.

**Inputs Required**:
- `research_context`: The research topic or context to investigate
- `asset_name`: Asset name for namespace and docname placeholder replacement
- `namespace`: Optional namespace for saving (default: `EXTERNAL_RESEARCH_REPORT_NAMESPACE_TEMPLATE`)
- `docname`: Optional docname for saving (uses UUID suffix if not provided)
- `is_shared`: Optional sharing flag (default: False)
- `load_additional_user_files`: Optional list of additional files with namespace, docname, and is_shared fields

**Process**:
The workflow begins by checking if a docname is provided. If not, it routes to generate a research report name automatically. Additional user files are transformed to proper configuration format if provided. The system validates all inputs and prepares the context for research execution.

#### 2. Research Name Generation
**Node IDs**:
- Prompt Constructor: `construct_research_name_prompt`
- LLM: `generate_research_name`

**Purpose**: Automatically generates descriptive names for research reports when not provided by the user.

**Process**:
When no docname is specified, the system constructs a prompt using the research context. GPT-5-mini analyzes the context and generates a concise, descriptive name that accurately represents the research topic.

**Prompt Configuration**:
- **System Prompt**: `RESEARCH_NAME_GENERATION_SYSTEM_PROMPT`
- **User Template**: `RESEARCH_NAME_GENERATION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `research_context`: The research topic for name generation
- **Output Schema**: `RESEARCH_NAME_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `GPT_MINI_PROVIDER`
- Model: Configured via `GPT_MINI_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `RESEARCH_NAME_MAX_TOKENS`
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

#### 4. External Research Phase
**Node IDs**:
- Prompt Constructor: `construct_research_prompt`
- LLM: `conduct_research`
- Save Draft: `save_research_draft`

**Purpose**: Performs comprehensive web-based research using Perplexity's deep research capabilities.

**Process**:
The system constructs a research prompt combining the research context with any additional loaded documents. Perplexity's research model conducts deep web searches, gathering information from multiple sources. The LLM synthesizes findings into a comprehensive research report with citations. After generation, the research is automatically saved as a draft.

**Prompt Configuration**:
- **System Prompt**: `DEFAULT_RESEARCH_SYSTEM_PROMPT`
- **User Template**: `DEFAULT_RESEARCH_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `research_context`: The research topic to investigate
  - `additional_user_files`: Optional loaded document contents

**Model Configuration**:
- Provider: Configured via `PERPLEXITY_LLM_PROVIDER`
- Model: Configured via `PERPLEXITY_LLM_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`

**Save Configuration**:
- Uses dynamically generated save configuration
- Stores research content with proper document structure
- Includes citations from web search results

#### 5. Human-in-the-Loop Approval
**Node IDs**:
- HITL: `research_approval`
- Router: `route_research_approval`
- Transform HITL Files: `transform_hitl_additional_files_config`
- Load HITL Files: `load_hitl_additional_user_files_node`

**Purpose**: Enables human review and approval of the research report with revision capabilities.

**User Actions Available**:
- **approve**: Accept the research report as final
- **request_revisions**: Request improvements with specific feedback
- **cancel**: Exit workflow without finalizing

**HITL Output Schema**:
- `user_action`: Required enum for user's decision
- `revision_feedback`: Feedback for improvements (required if request_revisions)
- `load_additional_user_files`: Optional additional files for revision context

**Process**:
The generated research report is presented for human review. Users can approve the content, request revisions with specific feedback, or cancel the workflow. If additional files are specified during HITL, they are loaded and incorporated into the revision process.

#### 6. Feedback Processing Loop
**Node IDs**:
- Check Limit: `check_iteration_limit`
- Router: `route_iteration_check`
- Feedback Prompt: `construct_feedback_prompt`

**Purpose**: Processes revision feedback and regenerates research while preventing infinite loops.

**Process**:
When revisions are requested:
1. System checks if iteration limit has been reached
2. If within limits, constructs feedback prompt with revision instructions
3. Regenerates research incorporating the feedback
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

The feedback prompt is used with the same Perplexity research model configuration, maintaining message history for context continuity across iterations.

#### 7. Output and Finalization
**Node IDs**:
- Output: `output_node`

**Purpose**: Finalizes the workflow and returns results based on the completion path.

**Output Information**:
- **On Approval**: Returns final research content with citations and storage paths
- **On Cancellation**: Returns partial results with cancellation status
- **On Iteration Limit**: Returns last research version with limit reached status

**Data Returned**:
- `research_content`: The final or latest research report including:
  - `report`: The main research content
  - `citations`: Web search result citations
- `final_research_paths`: Storage paths for the saved document
- Metadata including iteration count and completion status

### State Management

The workflow maintains state through `$graph_state` with the following key fields:
- `research_context`: Research topic throughout the workflow
- `messages_history`: Conversation history for iterations (reducer: "add_messages")
- `generation_metadata`: LLM metadata including iteration tracking
- `save_config`: Dynamically generated save configuration
- `research_content`: Current research report with citations
- `revision_feedback`: Latest revision feedback from user
- `hitl_load_additional_user_files`: Additional files from HITL (reducer: "replace")
- `web_search_result`: Citations and sources from Perplexity's web search

The state management ensures context preservation across iterations, proper tracking of research evolution through revisions, and maintains citations from web searches for transparency and verification.