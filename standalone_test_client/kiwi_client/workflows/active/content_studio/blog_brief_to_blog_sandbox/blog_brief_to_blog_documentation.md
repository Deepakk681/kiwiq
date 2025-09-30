# Blog Brief to Blog Generation Workflow

## Variables and Important Configuration

### Input Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `company_name` | str | Yes | Name of the company for document operations. Used to load company-specific documents and create proper namespaces for saving content. |
| `brief_docname` | str | Yes | Document name of the blog brief being used for content generation. This brief contains all the specifications for the blog post to be created. |
| `post_uuid` | str | Yes | Unique identifier for the blog post being generated. Used for tracking and versioning the content throughout the workflow. |
| `initial_status` | str | No (default: "draft") | Initial status when saving drafts. Typically set to "draft" and updated to "complete" upon final approval. |
| `load_additional_user_files` | list | No (default: []) | Optional list of additional user files to load for enrichment. Each item must include 'namespace', 'docname', and 'is_shared' fields. |

### Setup Documents Required

#### 1. Blog Content Brief
- **When Loaded**: At the beginning of the workflow in the context loading stage
- **Purpose**: Provides the complete specifications for the blog post including title, target audience, key takeaways, SEO keywords, content structure, and writing instructions
- **Usage**: Referenced during knowledge enrichment to understand what domain knowledge is needed, and used as the primary input for content generation
- **Required Fields**: title, content_goal, seo_keywords, key_takeaways, target_audience, content_structure, writing_instructions

#### 2. Company Guidelines Document
- **When Loaded**: At the beginning of the workflow in the context loading stage
- **Purpose**: Contains company-specific writing guidelines, brand voice, and style preferences
- **Usage**: Ensures the generated content aligns with company standards and maintains consistent brand voice throughout the blog post
- **Required Fields**: name, value_proposition, company_offerings, brand_guidelines

#### 3. SEO Best Practices (System Document)
- **When Loaded**: At the beginning of the workflow in the context loading stage
- **Purpose**: System-level document containing SEO optimization rules and best practices
- **Usage**: Incorporated into the content generation system prompt to ensure the blog post follows SEO best practices for better search visibility
- **System Entity**: This is a shared system document available across all companies

### HITL Configuration

#### Content Approval Node (`content_approval`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_action` | enum | Yes | User's decision on the generated content |
| `revision_feedback` | str | Conditional | Feedback for content improvement (required if action is provide_feedback) |
| `updated_content_draft` | dict | Yes | The current version of the blog content, including any manual edits made by the user |
| `load_additional_user_files` | list | No | Additional files to load for feedback analysis. Each item should have 'namespace', 'docname', and 'is_shared' fields |

**User Actions Explained:**
- **complete**: Select this when you are satisfied with the blog content and want to finalize it. This will save the content with a "complete" status.
- **provide_feedback**: Choose this to request revisions. You must provide specific feedback about what changes are needed. The system will analyze your feedback and regenerate the content.
- **draft**: Use this to save the current version as a draft and continue editing later. The workflow will loop back to allow further modifications.
- **cancel_workflow**: Select this to exit the workflow without saving the final version. Any drafts created will be deleted.

**Manual Editing Capability:**
The `updated_content_draft` field allows you to directly edit any part of the generated blog post before submitting your decision. Common edits include:
- Adjusting the tone or style of specific sections
- Adding or removing content
- Modifying headlines or subheadings
- Updating statistics or examples
- Refining the introduction or conclusion

### Configuration Limits

- **Maximum LLM Iterations**: Configured via `MAX_LLM_ITERATIONS` - limits the number of tool-calling iterations during knowledge enrichment
- **Tool Call Limit**: Configured via `MAX_TOOL_CALLS` - maximum number of document tool calls per iteration
- **Temperature Settings**: Controls creativity vs consistency in content generation
- **Token Limits**: Maximum tokens for different LLM operations (content generation, tool calling)

## Workflow Overview and Components

### Overview
This workflow transforms a blog content brief into a fully developed blog post with knowledge enrichment capabilities. It leverages document tools for domain knowledge acquisition, provides comprehensive content generation with SEO optimization, includes human-in-the-loop approval for content review and iterative feedback, and maintains proper version control through multiple save points.

### Key Components

#### 1. Context Loading Stage
**Node IDs**:
- Input: `input_node`
- Load Context: `load_all_context_docs`
- Transform Additional Files: `transform_additional_files_config`
- Load Additional Files: `load_additional_user_files_node`

**Purpose**: Establishes the foundational context by loading all necessary documents including the blog brief, company guidelines, SEO best practices, and any optional user-specified files.

**Inputs Required**:
- `company_name`: Name of the company for document operations
- `brief_docname`: Document name of the brief being used for drafting
- `post_uuid`: UUID of the post being generated
- `initial_status`: Initial status for saving drafts (default: "draft")
- `load_additional_user_files`: Optional list of additional user files with namespace, docname, and is_shared fields

**Documents Loaded**:
- **Blog Content Brief**: Loaded using company-specific namespace and provided brief docname
- **Company Guidelines**: Static document containing company-specific writing guidelines
- **SEO Best Practices**: System-level document with SEO optimization rules
- **Additional User Files**: Optional custom documents specified by the user

**Process**:
The workflow begins by loading all contextual documents in parallel. The `load_all_context_docs` node uses configured load paths to retrieve the blog brief, company guidelines, and SEO best practices. If additional user files are specified, they are first transformed to the proper configuration format and then loaded through a separate node.

#### 2. Knowledge Enrichment Phase
**Node IDs**:
- Prompt Constructor: `construct_knowledge_enrichment_prompt`
- LLM: `knowledge_enrichment_llm`
- Condition Check: `check_conditions`
- Router: `route_from_conditions`
- Tool Executor: `tool_executor`

**Purpose**: Enriches the content generation process by gathering relevant domain knowledge from available documents using AI-powered document tools.

**Process**:
The knowledge enrichment phase employs an iterative tool-calling pattern. The LLM is provided with access to three document tools:
- `search_documents`: Search for relevant documents in the knowledge base
- `view_documents`: View specific document contents
- `list_documents`: List available documents

The system constructs a knowledge enrichment prompt and sends it to the LLM with tool-calling capabilities. After each LLM response, conditions are checked to determine whether to execute tools, continue iteration, or proceed to content generation. The iteration continues until either the maximum iteration limit is reached, no more tool calls are needed, or valid structured output is produced.

**Prompt Configuration**:
- **System Prompt**: `KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT`
- **User Template**: `KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `blog_brief`: The loaded blog brief content
  - `company_name`: Company name for context
- **Output Schema**: `KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `TOOLCALL_LLM_PROVIDER`
- Model: Configured via `TOOLCALL_LLM_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`
- Reasoning Effort: "medium"
- Tool Calling: Enabled with parallel tool calls
- Max Iterations: Configured via `MAX_LLM_ITERATIONS`
- Tool Call Limit: Configured via `MAX_TOOL_CALLS`

#### 3. Content Generation Stage
**Node IDs**:
- Prompt Constructor: `construct_content_generation_prompt`
- LLM: `content_generation_llm`
- Store Draft: `store_draft`

**Purpose**: Generates the complete blog content based on the brief, enriched knowledge context, and SEO guidelines.

**Process**:
Once knowledge enrichment is complete, the system constructs a comprehensive content generation prompt that includes:
- The original blog brief
- Enriched knowledge context from the previous phase
- SEO best practices from the loaded system document
- Any additional user files that were loaded

The content generation LLM produces structured blog content following the brief requirements and incorporating the gathered knowledge. Immediately after generation, the content is automatically saved as an initial draft with version tracking.

**Prompt Configuration**:
- **System Prompt**: `CONTENT_GENERATION_SYSTEM_PROMPT`
- **User Template**: `CONTENT_GENERATION_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `blog_brief`: Original blog brief
  - `knowledge_context`: Enriched knowledge from previous phase
  - `additional_user_files`: Any additional loaded files (default: empty string)
  - `seo_best_practices`: SEO guidelines from system document
- **Output Schema**: `CONTENT_GENERATION_OUTPUT_SCHEMA`

**Model Configuration**:
- Provider: Configured via `DEFAULT_LLM_PROVIDER`
- Model: Configured via `DEFAULT_LLM_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`

**Auto-Save Configuration**:
- Document Type: Blog Post
- Versioning: Enabled with "draft_v1" initial version
- Operation: Initialize for first save, then upsert_versioned
- Namespace Pattern: `BLOG_POST_NAMESPACE_TEMPLATE`
- Document Name Pattern: `BLOG_POST_DOCNAME`

#### 4. Human-in-the-Loop Approval
**Node IDs**:
- HITL: `content_approval`
- Router: `route_content_approval`

**Purpose**: Enables human review, editing, and approval of the generated content with support for iterative refinement.

**User Actions Available**:
- **complete**: Approve the content as final
- **provide_feedback**: Request revisions with specific feedback
- **draft**: Save current version as draft and continue editing
- **cancel_workflow**: Exit workflow and delete draft

**Manual Editing Capability**:
Users can directly edit the generated content through the `updated_content_draft` field. All edits are preserved and carried forward through the workflow. Users can also specify additional files to load for the feedback processing phase.

**HITL Output Schema**:
- `user_action`: Required enum field for user's decision
- `revision_feedback`: Optional feedback text (required if action is provide_feedback)
- `updated_content_draft`: Required dict containing the edited blog content
- `load_additional_user_files`: Optional list of additional files to load for feedback analysis

**Process Flow**:
Based on the user's action, the router directs the workflow to:
- Save as final draft if approved
- Check iteration limit and process feedback if revision requested
- Save as draft and loop back to HITL if draft action selected
- Delete draft and exit if cancelled

#### 5. Feedback Processing Loop
**Node IDs**:
- Check Iteration: `check_iteration_limit`
- Router: `route_on_limit_check`
- Transform Files: `transform_hitl_additional_files_config`
- Load Files: `load_hitl_additional_user_files_node`
- Feedback Analysis Prompt: `construct_feedback_analysis_prompt`
- Feedback Analysis LLM: `feedback_analysis_llm`
- Content Update Prompt: `construct_content_update_prompt`

**Purpose**: Processes user feedback and regenerates content incorporating the requested changes while maintaining context from previous iterations.

**Process**:
When feedback is provided, the system first checks if the iteration limit has been reached. If within limits:
1. Any additional files specified during HITL are loaded
2. Feedback is analyzed to extract specific update instructions
3. Update instructions are used to regenerate the content
4. The regenerated content flows back to the HITL for review

**Iteration Control**:
- Maximum iterations: Configured via `MAX_LLM_ITERATIONS`
- Iteration count tracked in `generation_metadata.iteration_count`
- Workflow outputs if limit exceeded to prevent infinite loops

**Feedback Analysis Configuration**:
- **System Prompt**: `FEEDBACK_ANALYSIS_SYSTEM_PROMPT`
- **User Template**: `FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `blog_content`: Current blog content
  - `user_feedback`: Revision feedback from user
  - `hitl_additional_user_files`: Any additional files loaded
- **Output Schema**: `FEEDBACK_ANALYSIS_OUTPUT_SCHEMA`

**Content Update Configuration**:
- **User Template**: `CONTENT_UPDATE_USER_PROMPT_TEMPLATE`
- **Template Inputs**:
  - `original_content`: Current blog content
  - `update_instructions`: Analyzed feedback instructions
  - `hitl_additional_user_files`: Additional context files

**Model Configuration**:
- Provider: Configured via `DEFAULT_LLM_PROVIDER`
- Model: Configured via `DEFAULT_LLM_MODEL`
- Temperature: Configured via `TEMPERATURE`
- Max Tokens: Configured via `MAX_TOKENS`

#### 6. Document Storage and Versioning
**Node IDs**:
- Store Initial Draft: `store_draft`
- Save Manual Draft: `save_draft`
- Save Final Draft: `save_final_draft`
- Delete on Cancel: `delete_draft_on_cancel`

**Purpose**: Manages document persistence with proper versioning at multiple save points throughout the workflow.

**Save Points**:
1. **Initial Draft** (`store_draft`): Automatically saves after first content generation
   - Version: "draft_v1"
   - Status: Set to `initial_status` value

2. **Manual Draft** (`save_draft`): Saves when user chooses "draft" action in HITL
   - Operation: upsert_versioned
   - Status: Maintains `initial_status` value
   - Loops back to HITL for continued editing

3. **Final Draft** (`save_final_draft`): Saves when user approves content
   - Operation: upsert_versioned
   - Status: Set to user's selected action (typically "complete")
   - Proceeds to output node

4. **Delete on Cancel** (`delete_draft_on_cancel`): Removes draft if workflow cancelled
   - Deletes all draft versions created during the session
   - Returns deletion details to output

**Version Control**:
- All blog posts are versioned according to `BLOG_POST_IS_VERSIONED` configuration
- Each save creates a new version while preserving previous versions
- UUID tracking ensures consistent document identification across versions
- Namespace and docname patterns ensure proper document organization

**Output Information**:
- For successful completion: Returns `final_blog_post_paths` with storage details
- For cancellation: Returns `cancelled_drafts_deleted` count and `cancelled_draft_details`