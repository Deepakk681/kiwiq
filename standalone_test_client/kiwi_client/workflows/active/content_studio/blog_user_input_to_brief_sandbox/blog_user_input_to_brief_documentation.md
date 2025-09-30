# Blog User Input to Brief Generation Workflow

## Variables and Important Configuration

### Input Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `company_name` | str | Yes | Name of the company for document operations. Used to load company profile and content strategy documents. |
| `user_input` | str | Yes | User's content ideas, brainstorm, or transcript. This is the raw input that will be transformed into a structured blog brief. |
| `brief_uuid` | str | Yes | Unique identifier for the brief being generated. Used for tracking and versioning the brief throughout the workflow. |
| `initial_status` | str | No (default: "draft") | Initial status of the workflow. Typically "draft" until the brief is finalized. |
| `load_additional_user_files` | list | No (default: []) | Optional list of additional user files to load for context. Each item must include 'namespace', 'docname', and 'is_shared' fields. |

### Setup Documents Required

#### 1. Company Profile Document
- **When Loaded**: At the beginning of the workflow in the context loading stage
- **Purpose**: Provides company information including value proposition, offerings, ICPs, and goals
- **Usage**: Used during Google and Reddit research to provide company context, referenced in topic generation to align suggestions with company expertise, and incorporated into brief generation for brand-aligned content
- **Required Fields**: name, website_url, value_proposition, company_offerings, icps, goals

#### 2. Content Strategy/Playbook Document
- **When Loaded**: At the beginning of the workflow alongside company profile
- **Purpose**: Contains content strategy guidelines and playbook for content creation
- **Usage**: Referenced during topic generation to ensure topics align with content strategy, used in brief generation to incorporate strategic content elements
- **Required Fields**: name, content_strategy

### HITL Configuration

#### Topic Selection Node (`topic_selection_hitl`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_action` | enum | Yes | User's decision on topic selection |
| `selected_topic_id` | str | Conditional | ID of the selected topic (required if action is complete) |
| `user_instructions_on_selected_topic` | str | No | Additional instructions or context for the selected topic |
| `revision_feedback` | str | Conditional | Feedback for topic regeneration (required if action is provide_feedback) |
| `load_additional_user_files` | list | No | Additional files to provide context for topic selection |

**User Actions Explained:**
- **complete**: Choose this when you've found a suitable topic from the suggestions. You must specify the `selected_topic_id` to indicate which topic to use for brief generation.
- **provide_feedback**: Select this to regenerate topics with specific guidance. Provide detailed feedback about what kind of topics you're looking for.
- **cancel_workflow**: Exit the workflow without generating a brief.

**Topic Selection Best Practices:**
- Review all suggested topics carefully, considering SEO potential and audience relevance
- Use `user_instructions_on_selected_topic` to add specific angles or focus areas
- If topics don't match your vision, provide clear feedback about desired direction

#### Brief Approval Node (`brief_approval_hitl`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_brief_action` | enum | Yes | User's decision on brief approval |
| `revision_feedback` | str | Conditional | Feedback for brief revision (required if action is provide_feedback) |
| `updated_content_brief` | dict | Yes | The current version of the content brief, including any manual edits |
| `load_additional_user_files` | list | No | Additional files for brief revision context |

**User Actions Explained:**
- **complete**: Approve the brief as final. This saves the brief with a "complete" status for use in content creation.
- **provide_feedback**: Request specific revisions to the brief. The system will analyze feedback and regenerate accordingly.
- **draft**: Save current version as draft and continue editing. Useful for iterative refinement.
- **cancel_workflow**: Exit without saving the brief. Any drafts created will be deleted.

**Manual Editing Capability:**
The `updated_content_brief` field allows direct editing of:
- Title and content goal
- Target audience definition
- SEO keywords (primary and secondary)
- Content structure and sections
- Key takeaways and call to action
- Brand guidelines and writing instructions
- Word count estimates

### Research Configuration

#### Google Research
- **Purpose**: Gathers authoritative web insights and industry trends
- **Queries Generated**: 3-5 precise research queries
- **Sources Extracted**: Top 5 most relevant web resources
- **Model**: Perplexity Sonar Pro for real-time web search

#### Reddit Research
- **Purpose**: Captures authentic user discussions and pain points
- **Queries Generated**: 5-7 Reddit-specific search queries
- **Platforms Searched**: reddit.com, quora.com, g2.com, trustpilot.com, and other community platforms
- **Model**: Perplexity Sonar Pro with domain filtering

### Configuration Limits

- **Maximum Regeneration Attempts**: Configured via `MAX_REGENERATION_ATTEMPTS` - limits topic regeneration cycles
- **Maximum Revision Attempts**: Configured via `MAX_REVISION_ATTEMPTS` - limits brief revision cycles
- **Maximum Iterations**: Configured via `MAX_ITERATIONS` - overall iteration limit for HITL feedback loops
- **Knowledge Enrichment Iterations**: Configured via `MAX_ITERATIONS` - limits document tool usage cycles

## Workflow Overview and Components

### Overview
This workflow transforms user content ideas into comprehensive blog briefs through research and AI-powered topic generation. It performs Google web search for real-time insights, conducts Reddit research for authentic user discussions, generates strategic blog topics with human selection, enriches content with document tools for domain knowledge, and creates detailed content briefs with iterative refinement capabilities.

### Key Components

#### 1. Context Loading Stage
**Node IDs**:
- Input: `input_node`
- Load Company: `load_company_doc`
- Transform Files: `transform_additional_files_config`
- Load Additional: `load_additional_user_files_node`

**Purpose**: Establishes foundational company and strategy context for all subsequent operations.

**Inputs Required**:
- `company_name`: Name of the company for document operations
- `user_input`: User's content ideas, brainstorm, or transcript
- `brief_uuid`: UUID of the brief being generated
- `initial_status`: Initial status of the workflow (default: "draft")
- `load_additional_user_files`: Optional list of additional user files with namespace, docname, and is_shared fields

**Documents Loaded**:
- **Company Document**: Company profile and positioning information
- **Content Strategy/Playbook**: Content guidelines and strategic direction
- **Additional User Files**: Optional custom documents specified by the user

**Process**:
The workflow begins by loading company context documents in parallel. The `load_company_doc` node retrieves both the company profile and content strategy playbook using company-specific namespaces. If additional files are specified, they undergo transformation to proper configuration format before loading.

#### 2. Google Research Phase
**Node IDs**:
- Prompt Constructor: `construct_google_research_prompt`
- LLM: `google_research_llm`

**Purpose**: Gathers high-quality web insights and industry trends relevant to the user's content ideas.

**Process**:
The system constructs a research prompt combining company context with user input. The LLM then performs intelligent web searches on Google to identify authoritative sources, extract key themes, capture "People Also Asked" questions, and document reasoning for each source selection. The research focuses on generating 3-5 precise queries that yield the most relevant and practical web resources.

**Prompt Configuration**:
- **System Prompt**: `GOOGLE_RESEARCH_SYSTEM_PROMPT`
- **User Template**: `GOOGLE_RESEARCH_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `company_doc`: Company profile and positioning
  - `user_input`: Original user's content ideas
  - `additional_user_files`: Any additional loaded files
  - `topic_hitl_additional_user_files`: Files added during topic selection
- **Output Schema**: `GOOGLE_RESEARCH_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `PERPLEXITY_PROVIDER`
- Model: Configured via `PERPLEXITY_MODEL`
- Temperature: Configured via `PERPLEXITY_TEMPERATURE`
- Max Tokens: Configured via `PERPLEXITY_MAX_TOKENS`

#### 3. Reddit Research Phase
**Node IDs**:
- Prompt Constructor: `construct_reddit_research_prompt`
- LLM: `reddit_research_llm`

**Purpose**: Understands real user pain points, questions, and discussion patterns from Reddit and similar communities.

**Process**:
Building on Google research insights, the system generates 5-7 Reddit-specific search queries. It searches across multiple discussion platforms (reddit.com, quora.com, g2.com, and others) to extract frequently asked questions, group similar queries by user intent, and capture variations in how users express their needs. This provides authentic user voice and real-world problem contexts.

**Prompt Configuration**:
- **System Prompt**: `REDDIT_RESEARCH_SYSTEM_PROMPT`
- **User Template**: `REDDIT_RESEARCH_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `company_doc`: Company profile information
  - `google_research_output`: Results from Google research
  - `user_input`: Original user requirements
  - `additional_user_files`: Additional context files
  - `topic_hitl_additional_user_files`: Topic selection files
- **Output Schema**: `REDDIT_RESEARCH_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `PERPLEXITY_PROVIDER`
- Model: Configured via `PERPLEXITY_MODEL`
- Temperature: Configured via `PERPLEXITY_TEMPERATURE`
- Max Tokens: Configured via `PERPLEXITY_MAX_TOKENS`
- Domain Filter: reddit.com, quora.com, g2.com, slashdot.org, trustpilot.com, and others

#### 4. Topic Generation Stage
**Node IDs**:
- Prompt Constructor: `construct_topic_generation_prompt`
- LLM: `topic_generation_llm`
- HITL: `topic_selection_hitl`
- Router: `route_topic_selection`
- Filter: `filter_selected_topic`

**Purpose**: Creates strategic blog topic ideas that address both SEO opportunities and user needs.

**Process**:
The system analyzes insights from both Google and Reddit research to generate 3-5 blog topic suggestions. Each topic is aligned with company expertise and content strategy, provides clear reasoning connected to research findings, offers fresh angles or frameworks, and avoids clickbait while maintaining engagement potential.

**Prompt Configuration**:
- **System Prompt**: `TOPIC_GENERATION_SYSTEM_PROMPT`
- **User Template**: `TOPIC_GENERATION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `company_doc`: Company profile
  - `content_playbook_doc`: Content strategy
  - `google_research_output`: Google research results
  - `reddit_research_output`: Reddit findings
  - `user_input`: Original requirements
  - `additional_user_files`: Additional context
- **Output Schema**: `TOPIC_GENERATION_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `LLM_PROVIDER`
- Model: Configured via `LLM_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`

#### 5. Human-in-the-Loop Topic Selection
**Node IDs**:
- HITL: `topic_selection_hitl`
- Router: `route_topic_selection`
- Transform Files: `transform_topic_hitl_additional_files_config`
- Load Files: `load_topic_hitl_additional_user_files_node`

**Purpose**: Enables human review and selection of the most appropriate topic with iterative refinement options.

**User Actions Available**:
- **complete**: Accept a specific topic and proceed to brief generation
- **provide_feedback**: Request topic regeneration with specific guidance
- **cancel_workflow**: Exit the workflow without generating a brief

**HITL Output Schema**:
- `user_action`: Required enum for user's decision
- `selected_topic_id`: ID of selected topic (required if action is complete)
- `user_instructions_on_selected_topic`: Optional instructions for the selected topic
- `revision_feedback`: Feedback for regeneration (required if provide_feedback)
- `load_additional_user_files`: Optional additional files for context

**Feedback Processing**:
When feedback is provided, the system:
1. Loads any additional files specified
2. Analyzes feedback using `analyze_topic_feedback` node
3. Constructs regeneration prompt with `construct_topic_regeneration_prompt`
4. Regenerates topics through `topic_generation_llm`
5. Limits iterations to configured max (`MAX_REGENERATION_ATTEMPTS`)

#### 6. Knowledge Enrichment Phase
**Node IDs**:
- Prompt Constructor: `construct_knowledge_enrichment_prompt`
- LLM: `knowledge_enrichment_llm`
- Condition Check: `check_conditions`
- Router: `route_from_conditions`
- Tool Executor: `tool_executor`

**Purpose**: Enriches the selected topic with relevant domain knowledge from available documents using AI-powered document tools.

**Process**:
The knowledge enrichment phase uses an iterative tool-calling pattern with access to three document tools:
- `search_documents`: Search for relevant documents in the knowledge base
- `view_documents`: View specific document contents
- `list_documents`: List available documents

The LLM iteratively calls these tools to gather relevant information. After each response, conditions are checked to determine whether to execute tools, continue iteration, or proceed to brief generation. The process continues until maximum iterations are reached, no more tool calls are needed, or valid structured output is produced.

**Prompt Configuration**:
- **System Prompt**: `KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT`
- **User Template**: `KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `selected_topic`: The chosen topic from selection
  - `google_research_output`: Google research results
  - `reddit_research_output`: Reddit findings
  - `user_instructions_on_selected_topic`: User's topic instructions
  - `additional_user_files`: Additional context files
  - `topic_hitl_additional_user_files`: Topic HITL files
  - `company_name`: Company name for context
- **Output Schema**: `KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `KNOWLEDGE_ENRICHMENT_LLM_PROVIDER`
- Model: Configured via `KNOWLEDGE_ENRICHMENT_LLM_MODEL`
- Temperature: Configured via `KNOWLEDGE_ENRICHMENT_TEMPERATURE`
- Max Tokens: Configured via `KNOWLEDGE_ENRICHMENT_MAX_TOKENS`
- Reasoning Effort: "medium"
- Tool Calling: Enabled with parallel tool calls
- Max Iterations: Configured via `MAX_ITERATIONS`

#### 7. Brief Generation Stage
**Node IDs**:
- Prompt Constructor: `construct_brief_generation_prompt`
- LLM: `brief_generation_llm`
- Save Draft: `save_as_draft_after_brief_generation`

**Purpose**: Creates a comprehensive content brief with all necessary elements for content creation.

**Process**:
Using the selected topic, accumulated research data, and enriched knowledge context, the system generates a structured content brief. The brief includes target audience definition, content goals and key takeaways, detailed section breakdowns with word counts, SEO keyword strategy, brand guidelines and tone specifications, research sources and citations, and call to action strategy. The brief is automatically saved as a draft immediately after generation.

**Prompt Configuration**:
- **System Prompt**: `BRIEF_GENERATION_SYSTEM_PROMPT`
- **User Template**: `BRIEF_GENERATION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `company_doc`: Company profile
  - `content_playbook_doc`: Content strategy
  - `selected_topic`: Chosen topic details
  - `google_research_output`: Google research
  - `reddit_research_output`: Reddit research
  - `knowledge_context`: Enriched knowledge
  - `additional_user_files`: Additional files
  - `topic_hitl_additional_user_files`: Topic HITL files
  - `user_instructions_on_selected_topic`: User instructions
- **Output Schema**: `BRIEF_GENERATION_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `LLM_PROVIDER`
- Model: Configured via `LLM_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`

**Auto-Save Configuration**:
- Document Type: Blog Content Brief
- Versioning: Enabled (`BLOG_CONTENT_BRIEF_IS_VERSIONED`)
- Operation: upsert_versioned
- Status: Set to `initial_status` value

#### 8. Human-in-the-Loop Brief Approval
**Node IDs**:
- HITL: `brief_approval_hitl`
- Router: `route_brief_approval`
- Transform Files: `transform_brief_hitl_additional_files_config`
- Load Files: `load_brief_hitl_additional_user_files_node`

**Purpose**: Allows human review, editing, and approval of the generated brief with revision options.

**User Actions Available**:
- **complete**: Approve the brief as final
- **provide_feedback**: Request revisions with specific instructions
- **draft**: Save current version as draft and continue editing
- **cancel_workflow**: Exit without saving

**Manual Editing Capability**:
Users can directly edit any part of the brief content through the `updated_content_brief` field before approval, including modifying title, sections, word counts, SEO keywords, and writing instructions.

**HITL Output Schema**:
- `user_brief_action`: Required enum for user's decision
- `revision_feedback`: Feedback for revision (required if provide_feedback)
- `updated_content_brief`: Required dict containing edited brief
- `load_additional_user_files`: Optional additional files for revision

**Process Flow**:
Based on user action, the router directs to:
- Save as final if approved
- Check iteration limit and process feedback if revision requested
- Save as draft and loop back if draft selected
- Delete draft and exit if cancelled

#### 9. Feedback Processing Loop
**Node IDs**:
- Check Limit: `check_iteration_limit`
- Router: `route_on_limit_check`
- Feedback Prompt: `construct_brief_feedback_prompt`
- Feedback Analysis: `analyze_brief_feedback`
- Revision Prompt: `construct_brief_revision_prompt`

**Purpose**: Processes user feedback and regenerates the brief incorporating requested changes while maintaining context.

**Process**:
When revision is requested:
1. System checks if iteration limit has been reached
2. If within limits, loads any additional files specified
3. Analyzes feedback to extract specific revision instructions
4. Constructs revision prompt with analyzed instructions
5. Regenerates brief through `brief_generation_llm`
6. Returns to HITL for review

**Iteration Control**:
- Maximum iterations: Configured via `MAX_ITERATIONS`
- Iteration count tracked in `generation_metadata.iteration_count`
- Workflow outputs if limit exceeded to prevent infinite loops

**Feedback Analysis Configuration**:
- **System Prompt**: `BRIEF_FEEDBACK_SYSTEM_PROMPT`
- **User Template**: `BRIEF_FEEDBACK_INITIAL_USER_PROMPT`
- **Template Inputs**:
  - `content_brief`: Current brief version
  - `revision_feedback`: User's feedback
  - `company_doc`: Company context
  - `content_playbook_doc`: Content strategy
  - `selected_topic`: Selected topic
  - `google_research_output`: Google research
  - `reddit_research_output`: Reddit research
  - `brief_hitl_additional_user_files`: Additional files
- **Output Schema**: `BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `FEEDBACK_LLM_PROVIDER`
- Model: Configured via `FEEDBACK_ANALYSIS_MODEL`
- Temperature: Configured via `FEEDBACK_TEMPERATURE`
- Max Tokens: Configured via `FEEDBACK_MAX_TOKENS`

#### 10. Document Storage and Versioning
**Node IDs**:
- Save After Generation: `save_as_draft_after_brief_generation`
- Save as Draft: `save_as_draft`
- Save Final: `save_brief`
- Delete on Cancel: `delete_draft_on_cancel`

**Purpose**: Manages document persistence with proper versioning at multiple save points throughout the workflow.

**Save Points**:
1. **After Brief Generation** (`save_as_draft_after_brief_generation`):
   - Automatically saves initial brief
   - Status: Set to `initial_status`
   - Operation: upsert_versioned

2. **Manual Draft** (`save_as_draft`):
   - Saves when user selects "draft" action
   - Status: Set to user's action
   - Loops back to HITL for continued editing

3. **Final Brief** (`save_brief`):
   - Saves when user approves content
   - Status: Set to "complete"
   - Proceeds to output node

4. **Delete on Cancel** (`delete_draft_on_cancel`):
   - Removes draft if workflow cancelled
   - Returns deletion count to output

**Version Control**:
- All briefs are versioned according to `BLOG_CONTENT_BRIEF_IS_VERSIONED`
- Each save creates a new version while preserving previous versions
- UUID tracking ensures consistent document identification
- Namespace and docname patterns ensure proper organization

**Output Information**:
- For successful completion: Returns `final_paths_processed` with storage details
- For cancellation: Returns `cancelled_draft_deleted_count` with deletion information