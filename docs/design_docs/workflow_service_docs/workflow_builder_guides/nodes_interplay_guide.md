# Guide: Making Workflow Nodes Work Together

This guide explains how different nodes in the workflow system connect and interact to create automated processes. Understanding how data flows and how nodes are configured is key to building effective workflows.

## 1. The Big Picture: Workflows as Graphs

Think of a workflow as a flowchart or a graph:

-   **Nodes:** These are the individual steps or actions in your workflow. Each node performs a specific task, like getting input, calling an AI, filtering data, waiting for human review, or producing output.
-   **Edges:** These are the connections or arrows between nodes. They define the sequence of steps and, crucially, how data is passed from one node to the next.

The entire structure – the nodes and their connections – is defined in a configuration file called the **`GraphSchema`**. This schema is the blueprint for your workflow.

## 2. Nodes: The Building Blocks

Each node in your workflow needs to be defined within the `GraphSchema`'s `nodes` section.

```json
{
  "nodes": {
    "a_unique_node_id": {  // <<< You choose a unique ID for this specific instance
      "node_id": "a_unique_node_id", // <<< Must match the key above
      "node_name": "type_of_node",   // <<< Specifies the node's function (see below)
      "node_config": { /* ... specific settings for this node ... */ }
    },
    "another_node_id": { /* ... definition for another node ... */ }
    // ... more nodes
  },
  // ... edges, input/output node definitions ...
}
```

-   **`node_id`**: This is a unique name *you give* to this specific instance of a node in your workflow (e.g., `get_user_email`, `summarize_report`, `human_approval_step`). It must match the key used in the `nodes` dictionary.
-   **`node_name`**: This tells the system *what kind* of node it is. It corresponds to a registered node type. You must use the correct `node_name` for the node to function as intended.
-   **`node_config`**: This dictionary holds the specific settings required by that particular `node_name`. For example, an `llm` node needs model details, a `filter_data` node needs filter conditions, etc. Refer to the specific node's guide for its configuration options.

**Advanced Node Configuration Options:**

All nodes also support these optional advanced settings for controlling execution behavior:

-   **`private_input_mode` / `private_output_mode` (Boolean)**: Enable private data modes for parallel processing with `map_list_router_node`. When enabled, nodes receive/send data directly rather than through the shared central state.
-   **`private_output_passthrough_data_to_central_state_keys` (List[String])**: Keys from the node's **input state** to preserve in central state and pass to subsequent private mode nodes. This serves dual purposes: (1) preserving context data (like unique IDs, batch metadata) in central state for aggregation, and (2) creating a passthrough data chain that flows alongside main processing. **Critical insight**: This preserves data from the node's *input* (what it received), not its *output* (what it produced).
-   **`private_output_to_central_state_node_output_key` (String)**: Key name for node output when writing to central state with passthrough data (default: "output").
-   **`output_private_output_to_central_state` (Boolean)**: Send private output to central state for debugging purposes.
-   **`read_private_input_passthrough_data_to_input_field_mappings` (Object)**: Maps passthrough data keys to input field names. Supports dot notation for nested paths (e.g., `{"user.profile.name": "display_name"}`).
-   **`write_to_private_output_passthrough_data_from_output_mappings` (Object)**: Maps output field names to passthrough data keys. Supports dot notation for nested paths (e.g., `{"result.user_id": "context.user.id"}`).
-   **`dynamic_input_schema` / `dynamic_output_schema` (Object)**: Explicit schema definitions for dynamic nodes.
-   **`enable_node_fan_in` / `defer_node` (Boolean)**: Advanced execution control settings.

**Available Node Types (`node_name`)**

Here are the core node types available for building workflows (refer to their individual guides for detailed configuration):

*   **Core & Flow:**
    *   `input_node`: Defines the starting point and initial data requirements. ([Guide](nodes/core_dynamic_nodes_guide.md))
    *   `output_node`: Defines the final output structure. ([Guide](nodes/core_dynamic_nodes_guide.md))
    *   `filter_data`: Selectively keeps or removes data based on conditions. ([Guide](nodes/filter_node_guide.md))
    *   `if_else_condition`: Evaluates conditions to decide between `true_branch` or `false_branch` outputs (used with a Router). ([Guide](nodes/if_else_node_guide.md))
    *   `hitl_node__default` (or other `hitl_*`): Pauses for human input or review. ([Guide](nodes/hitl_node_guide.md))
*   **Routing:**
    *   `router_node`: Routes workflow to different next steps based on simple data equality checks. ([Guide](nodes/dynamic_router_node_guide.md))
    *   `map_list_router_node`: Distributes items from a list to other nodes for individual processing (often in parallel). Supports batching items before sending and optionally wrapping them in a named field. ([Guide](nodes/map_list_router_node_guide.md))
*   **Data Operations:**
    *   `transform_data`: Restructures or renames data fields. ([Guide](nodes/transform_node_guide.md))
    *   `data_join_data`: Combines data from different sources based on matching keys. ([Guide](nodes/data_join_node_guide.md))
    *   `merge_aggregate`: Merges multiple data objects based on configurable strategies for mapping, conflict resolution, and transformation. Supports sequential transformations on non-dictionary results. ([Guide](nodes/merge_aggregate_node_guide.md))
*   **Data Storage:**
    *   `load_customer_data`: Fetches existing data records from storage using static or dynamic path resolution (including patterns based on input metadata). ([Guide](nodes/load_customer_data_node_guide.md))
    *   `store_customer_data`: Saves workflow data back into storage using static or dynamic path resolution (including patterns based on input metadata). ([Guide](nodes/store_customer_data_node_guide.md))
    *   `load_multiple_customer_data`: Lists and loads multiple documents based on criteria like namespace, shared status, and pagination. ([Guide](nodes/load_multiple_customer_node_guide.md))
*   **LLM & Prompts:**
    *   `prompt_constructor`: Builds text prompts using templates and variables. Can define templates statically (`template`) or load them dynamically from the database (`template_load_config`). Supports sourcing variables via input paths (`construct_options`) or direct mappings. ([Guide](nodes/prompt_constructor_node_guide.md))
    *   `llm`: Interacts with Large Language Models (like GPT, Claude, Gemini), supporting text/structured output, tool calling, and web search. ([Guide](nodes/llm_node_guide.md))
*   **External Services:**
    *   `linkedin_scraping`: Executes configured scraping `jobs` (like profile fetch, post search) via an external service. Uses `InputSource` for dynamic parameters, supports `expand_list` for batch jobs, and has a `test_mode`. Consumes API credits. ([Guide](nodes/linkedin_scraping_node_guide.md))
*   *Deprecated:* `load_prompt_templates` (Functionality merged into `prompt_constructor`).

*(Refer to `services/workflow_service/services/db_node_register.py` for the authoritative list of registered nodes.)*

## 3. Edges: Connecting Nodes and Passing Data

Edges define how nodes are connected and how data flows between them. Edges can be defined in two ways: in the global `edges` list of the `GraphSchema` or directly within node configurations.

### 3.1. Global Edge Definition

```json
{
  // ... nodes definition ...
  "edges": [
    {
      "src_node_id": "node_that_produces_data", // ID of the node sending data
      "dst_node_id": "node_that_needs_data",   // ID of the node receiving data
      "mappings": [ // Instructions on WHICH data to send
        {
          "src_field": "output_field_name", // Name of the data field from the source node's output
          "dst_field": "input_field_name"   // Name this data should have in the target node's input
        },
        // --- NEW: Advanced Dot Notation Examples ---
        {
          "src_field": "api_response.data.user.profile.contact.email", // Deep nested extraction
          "dst_field": "contact_info.primary_email" // Create nested structure
        },
        {
          "src_field": "search_results.0.metadata.relevance_score", // Array element access
          "dst_field": "analysis.primary_result.score"
        }
      ]
    },
    { /* ... definition for another edge ... */ }
  ],
  // ... input/output node definitions ...
}
```

### 3.2. Node-Level Edge Declaration (NEW FEATURE)

You can now declare edges directly within node configurations for better organization:

```json
{
  "nodes": {
    "data_processor": {
      "node_id": "data_processor",
      "node_name": "transform_data",
      "node_config": { /* ... */ },
      "edges": [ // Edges originating FROM this node
        {
          "dst_node_id": "analysis_node",
          "mappings": [
            {
              "src_field": "processed_results.summary.key_findings",
              "dst_field": "analysis_input.findings"
            },
            {
              "src_field": "processed_results.metadata.processing_time",
              "dst_field": "performance_metrics.duration"
            }
          ]
        }
      ]
    }
  }
}
```

### 3.3. Edge Field Reference

-   **`src_node_id`**: The `node_id` of the node where the data originates.
-   **`dst_node_id`**: The `node_id` of the node that will receive the data.
-   **`mappings`**: This optional list is crucial for controlling data flow. Each item (`EdgeMapping`) specifies:
    *   **`src_field`**: The name of a field in the `src_node_id`'s output data. **Now supports full dot notation** for accessing nested structures, arrays, and complex API responses.
    *   **`dst_field`**: The name that this data should have when it arrives as input for the `dst_node_id`. **Now supports full dot notation** for creating nested input structures. Can also include template-specific syntax (`TEMPLATE_ID.VARIABLE_NAME`) for `PromptConstructorNode`.

### 3.4. Dot Notation Capabilities (NEW FEATURE)

The edge mapping system now provides comprehensive support for nested data access:

**Syntax Examples:**
```json
// Object property access
{ "src_field": "user.profile.settings.theme", "dst_field": "ui_config.theme" }

// Array element access by index  
{ "src_field": "results.0.title", "dst_field": "primary_result" }

// Deep nesting with mixed object/array access
{ "src_field": "api_data.users.0.permissions.roles.2.name", "dst_field": "access_control.primary_role" }

// Complex API response handling
{ "src_field": "linkedin_response.profile.experience.0.company.industry", "dst_field": "lead_analysis.industry_context" }
```

**Practical Use Cases:**
- **API Response Processing**: Extract specific values from complex nested API responses without intermediate processing nodes
- **Data Restructuring**: Transform flat data into organized nested structures for downstream consumption  
- **Array Element Selection**: Access specific array elements (first, last, specific index) directly in mappings
- **Structured Input Creation**: Build organized input data for nodes that expect specific nested formats

### 3.6. Data-Only Edges: Efficient Non-Flow Data Transfer (ADVANCED FEATURE)

**Data-only edges** provide a powerful optimization for passing data between nodes without affecting execution flow. This feature helps reduce memory usage and avoid unnecessary central state storage.

#### How Data-Only Edges Work

A **data-only edge** transfers data from a source node to a destination node **without creating an execution dependency**:

```json
{
  "src_node_id": "data_source_node",
  "dst_node_id": "data_target_node", 
  "data_only_edge": true,  // Makes this edge data-only
  "mappings": [
    { "src_field": "large_dataset.results", "dst_field": "analysis_input" },
    { "src_field": "metadata.source_info", "dst_field": "context_data" }
  ]
}
```

#### Key Characteristics

1. **No Execution Trigger**: `data_target_node` does NOT execute because of this edge
2. **Data Availability**: When `data_target_node` does execute (via regular edges), it has access to the mapped data
3. **Memory Efficient**: Data flows directly without being stored in central state
4. **Supports All Features**: Full dot notation support, node-level or global declaration

#### Practical Example: Large Dataset Processing

```json
{
  "nodes": {
    "load_customer_profiles": {
      "node_id": "load_customer_profiles",
      "node_name": "load_customer_data",
      "node_config": { /* loads 200MB customer dataset */ }
    },
    "validate_data_structure": {
      "node_id": "validate_data_structure", 
      "node_name": "filter_data",
      "node_config": { /* quick validation */ }
    },
    "generate_insights": {
      "node_id": "generate_insights",
      "node_name": "llm", 
      "node_config": { /* analyzes customer patterns */ }
    }
  },
  "edges": [
    // Regular execution flow: load → validate → insights
    { "src_node_id": "load_customer_profiles", "dst_node_id": "validate_data_structure", "mappings": [
      { "src_field": "dataset_summary", "dst_field": "summary_to_validate" }
    ]},
    { "src_node_id": "validate_data_structure", "dst_node_id": "generate_insights", "mappings": [
      { "src_field": "validation_status", "dst_field": "data_quality_info" }
    ]},
    
    // Data-only edge: Pass full dataset directly to insights node
    // without storing 200MB in central state
    {
      "src_node_id": "load_customer_profiles",
      "dst_node_id": "generate_insights", 
      "data_only_edge": true,
      "mappings": [
        { "src_field": "customer_profiles", "dst_field": "full_dataset" }
      ]
    }
  ]
}
```

#### Benefits for Node Interactions

1. **Memory Optimization**: Large datasets aren't duplicated in workflow state
2. **Selective Data Distribution**: Different downstream nodes can receive different data subsets
3. **Clean Separation**: Execution flow vs data flow are clearly separated
4. **Performance**: Direct node output reuse without copying

#### Data-Only Edges vs Central State Patterns

| Pattern | When to Use | Memory Impact | Complexity |
|---------|-------------|---------------|------------|
| **Data-Only Edge** | Large data, specific targets | Low (direct reuse) | Medium |
| **Central State** | Small data, multiple access | Higher (stored copy) | Simple |
| **Direct Mapping** | Sequential flow | Low (immediate transfer) | Simple |

#### Advanced Pattern: Mixed Edge Types

A single node can use both regular and data-only edges for different purposes:

```json
{
  "load_analysis_data": {
    "node_id": "load_analysis_data",
    "node_name": "load_customer_data",
    "edges": [
      // Regular edge: Controls execution flow + passes metadata
      {
        "dst_node_id": "validation_step",
        "mappings": [
          { "src_field": "load_status", "dst_field": "status_to_check" }
        ]
      },
      // Data-only edge: Passes large dataset directly to analysis
      {
        "dst_node_id": "deep_analysis", 
        "data_only_edge": true,
        "mappings": [
          { "src_field": "full_dataset", "dst_field": "analysis_data" }
        ]
      },
      // Data-only edge: Passes different subset to reporting
      {
        "dst_node_id": "summary_report",
        "data_only_edge": true, 
        "mappings": [
          { "src_field": "dataset_summary", "dst_field": "report_data" }
        ]
      }
    ]
  }
}
```

### 3.7. What if `mappings` is empty or omitted?

This often implies that the connection is primarily for control flow (ensuring one node runs after another) or that the destination node might read data from a central workflow state or use internal mechanisms (like `construct_options` in `PromptConstructorNode`) to find its data. However, explicit mappings with dot notation now make most data transfer scenarios clear and efficient.

### 3.5. Central Workflow State with Dot Notation (`"$graph_state"`)

Think of the workflow having a shared **memory** or **scratchpad** that nodes can write to and read from throughout the process. This shared memory is accessed using the special node ID `"$graph_state"` and now fully supports dot notation for organized data storage.

**Writing to Shared Memory with Nested Structures:**
```json
// Save complex analysis results in organized structure
{
  "src_node_id": "analysis_processor",
  "dst_node_id": "$graph_state",
  "mappings": [
    { "src_field": "results.quality_score", "dst_field": "lead_analysis.quality.score" },
    { "src_field": "results.confidence_level", "dst_field": "lead_analysis.quality.confidence" },
    { "src_field": "metadata.processing_duration", "dst_field": "workflow_metrics.timing.analysis_duration" },
    { "src_field": "source_data.lead_info.company", "dst_field": "lead_profile.employment.company_name" }
  ]
}
```

**Reading from Shared Memory with Nested Access:**
```json
// Retrieve specific nested values for downstream processing
{
  "src_node_id": "$graph_state", 
  "dst_node_id": "notification_service",
  "mappings": [
    { "src_field": "lead_analysis.quality.score", "dst_field": "alert_data.score" },
    { "src_field": "lead_profile.employment.company_name", "dst_field": "alert_data.company" },
    { "src_field": "workflow_metrics.timing", "dst_field": "debug_info.performance" }
  ]
}
```

**Benefits of Nested Central State:**
- **Organized Data Storage**: Group related data logically (e.g., `lead_analysis.quality.*`, `workflow_metrics.timing.*`)
- **Selective Access**: Read only the specific nested values needed by each node
- **Conflict Avoidance**: Reduce key name conflicts by using hierarchical organization
- **Better Debugging**: Easier to understand data flow with structured state organization

**Key Points:**
- **Dot Notation Support**: Both reading from and writing to central state support full dot notation
- **Automatic Structure Creation**: Writing to nested paths automatically creates required intermediate objects
- **Efficient Access**: Reading specific nested values avoids transferring unnecessary data
- **Execution Flow**: Edges from `"$graph_state"` provide data access only - they don't trigger node execution

## 4. Data Schemas: Defining Input and Output

Every node expects data in a certain format (its **input schema**) and produces data in a certain format (its **output schema**).

-   **Static Schemas:** Many nodes have fixed, predefined schemas. For example, the `llm` node always expects inputs like `user_prompt` or `messages_history` and produces known outputs like `content` and `metadata`. You need to use `EdgeMapping` to map data *to* these expected input names and *from* these known output names.
-   **Statically Defined Structured Output:** Some nodes, like `llm`, can be configured to produce *structured* output (JSON) instead of just text. You define the desired structure in the node's `node_config` (using `output_schema`), and the node attempts to format its response accordingly. You then map *from* the fields within this structured output (e.g., `src_field: "structured_output"` - accessing nested fields within `structured_output` via edge mappings might have limitations, check node documentation).
-   **Dynamic Schemas:** Some nodes are flexible and adapt their schemas based on how they are used:
    *   **`InputNode`**: Its *output* schema is defined by the `src_field` names in the `EdgeMapping`s of edges *originating from it*. These `src_field`s become the required inputs for the entire workflow.
    *   **`OutputNode`**: Its *input* schema is defined by the `dst_field` names in the `EdgeMapping`s of edges *pointing to it*. These `dst_field`s define the final output structure of the workflow.
    *   **`HITLNode`**: Similar to Input/Output, its input (data shown to human) and output (data provided by human) schemas are often defined by incoming and outgoing edge mappings, respectively.
    *   **`TransformerNode`**: Its output schema is explicitly constructed based *only* on the `destination_path` fields defined in its `node_config.mappings`. Its input schema is implicitly defined by the `source_path` fields it needs.
    *   **`PromptConstructorNode`**: Its input schema is dynamic, determined by variables marked `null` in config `variables`, fields needed for `template_load_config`, fields needed for `construct_options` path lookups, and fields mapped directly (globally or template-specific). Its output *dictionary* contains fields named after the template `id`s defined in its config for successfully constructed prompts, and *always* includes a `prompt_template_errors` list (which is empty if no errors occurred). The final *validated output object* passed downstream depends on the node's `dynamic_output_schema` definition in the `GraphSchema`, which should include the expected template `id` fields and can optionally include `prompt_template_errors` if downstream nodes need to access it robustly via the validated schema. Explicitly defining `dynamic_input_schema` and `dynamic_output_schema` is highly recommended.
    *   *Deprecated:* `PromptTemplateLoaderNode` (Functionality merged into `prompt_constructor`).
    *   **Other Nodes:** Nodes like `FilterNode`, `IfElseConditionNode`, `RouterNode`, `LoadCustomerDataNode`, `StoreCustomerDataNode`, `DataJoinNode` often adapt based on the field paths (`field`, `input_path`, `source_path`, etc.) mentioned in their `node_config`. They implicitly require these paths to exist in their input data.

**Key Takeaway for Dynamic Nodes:** The `EdgeMapping`s you create connecting *to* or *from* dynamic nodes, along with configurations like `construct_options` or `template_load_config`, play a critical role in defining what data they expect or produce. Explicitly defining `dynamic_input_schema` and `dynamic_output_schema` for such nodes is highly recommended.

## 5. Configuring the Workflow (`GraphSchema`)

The `GraphSchema` brings everything together:

```json
{
  // 1. Define all node instances
  "nodes": {
    "input_node": { "node_id": "input_node", "node_name": "input_node", "node_config": {} },
    "transform_step": { "node_id": "transform_step", "node_name": "transform_data", "node_config": { /* mappings... */ } },
    "output_node": { "node_id": "output_node", "node_name": "output_node", "node_config": {} }
    // ... other nodes
  },
  // 2. Define all connections and data flow
  "edges": [
    {
      "src_node_id": "input_node",
      "dst_node_id": "transform_step",
      "mappings": [ { "src_field": "raw_data", "dst_field": "data_to_transform" } ]
    },
    {
      "src_node_id": "transform_step",
      "dst_node_id": "output_node",
      "mappings": [ { "src_field": "transformed_data", "dst_field": "final_result" } ]
    }
    // ... other edges
  ],
  // 3. Specify the official start and end points
  "input_node_id": "input_node",
  "output_node_id": "output_node",
  // 4. Optional metadata (e.g., for central state reducers)
  "metadata": { /* ... */ }
}
```

-   Ensure every `node_id` used in `edges`, `input_node_id`, or `output_node_id` exists as a key in the `nodes` dictionary.
-   Make sure the `node_name` corresponds to a valid, registered node type.
-   Carefully define `EdgeMapping`s to ensure data flows correctly between nodes, matching source output fields to destination input fields. Consider all input sources for complex nodes like `PromptConstructorNode` (direct mappings, `construct_options` paths).

## 6. Common Interaction Patterns

Here are examples of how nodes work together:

-   **Simple Data Transformation:**
    `InputNode` -> `TransformerNode` -> `OutputNode`
    *   `InputNode` defines workflow inputs (e.g., `raw_customer_data`).
    *   Edge maps `raw_customer_data` from `InputNode` to the `TransformerNode`.
    *   `TransformerNode` config maps fields from `raw_customer_data` to a new structure (e.g., `simplified_profile`).
    *   Edge maps `transformed_data` (output of transformer) to `OutputNode`.
    *   `OutputNode` defines the final output (e.g., `simplified_profile`).

-   **Conditional Routing:**
    `SomeNode` -> `IfElseConditionNode` -> `RouterNode` -> (`BranchA_Node` OR `BranchB_Node`)
    *   `IfElseConditionNode` evaluates complex conditions based on data from `SomeNode`.
    *   Edge maps `IfElseConditionNode`'s `branch` output (either `"true_branch"` or `"false_branch"`) to `RouterNode`.
    *   `RouterNode` config checks the incoming `branch` value and routes to `BranchA_Node` if `"true_branch"`, else to `BranchB_Node`.
    *   Edges exist from `RouterNode` to both `BranchA_Node` and `BranchB_Node`, but only one path is taken per run (unless `allow_multiple: true`).

-   **AI Content Generation & Review Loop:**
    `InputNode` -> `AIGeneratorNode` -> `HumanReviewNode` -> `ApprovalRouterNode` --(yes)--> `FinalProcessorNode`
                     ^                                                |
                     |-------------------(no)--------------------------|
    *   `AIGeneratorNode` (often an `llm` node) generates content (potentially using `PromptConstructorNode` first). It might produce text or structured output.
    *   `HumanReviewNode` (HITL) presents content, gets `approved` status ("yes"/"no") and `review_comments`.
    *   `ApprovalRouterNode` checks the `approved` status.
    *   If "yes", routes to `FinalProcessorNode`.
    *   If "no", routes back to `AIGeneratorNode` (passing `review_comments` potentially via the central state `"$graph_state"`).

-   **Loading Prompts and Generating Content:**
    `InputNode` -> `PromptConstructorNode` -> `LLMNode`
    *   `InputNode` provides data needed for template variables and/or dynamic template loading/`construct_options` paths (as defined in `PromptConstructorNode`'s `dynamic_input_schema`).
    *   `PromptConstructorNode` defines templates statically (`template`) *or* configures dynamic loading (`template_load_config`) and sources variables according to its priority rules (construct options, direct mappings, defaults). It outputs constructed prompts (named by template `id`) and a `prompt_template_errors` list.
    *   Edge maps the constructed prompt output field(s) (e.g., `src_field: "final_user_prompt"`) to the `LLMNode` (e.g., `dst_field: "user_prompt"`).
    *   Edge can optionally map the `prompt_template_errors` field to another node for error handling.
    *   Edges provide necessary inputs to `PromptConstructorNode`.
    *   `LLMNode` executes the prompt.

-   **Fetching External Data with Nested Access (LinkedIn Example):**
    `InputNode` -> `LinkedInScrapingNode` -> `ProfileAnalysisNode`
    *   `InputNode` provides necessary inputs (e.g., `list_of_usernames`, `company_target`).
    *   Edges map these inputs to the `LinkedInScrapingNode`.
    *   `LinkedInScrapingNode` produces complex nested results with profile data, experience, skills, etc.
    *   **Using dot notation**, edges extract specific values:
        ```json
        {
          "src_node_id": "linkedin_scraper",
          "dst_node_id": "profile_analysis", 
          "mappings": [
            { "src_field": "scraping_results.profiles.0.basic_info.name", "dst_field": "analysis_input.lead_name" },
            { "src_field": "scraping_results.profiles.0.experience.0.company.name", "dst_field": "analysis_input.current_company" },
            { "src_field": "scraping_results.profiles.0.experience.0.position.title", "dst_field": "analysis_input.job_title" },
            { "src_field": "scraping_results.profiles.0.skills", "dst_field": "analysis_input.technical_skills" }
          ]
        }
        ```

-   **Fetching and Combining Data:**
    `InputNode` -> `LoadCustomerDataNode` -> `DataJoinNode` -> `OutputNode`
    *   `InputNode` provides an ID (e.g., `user_id`).
    *   `LoadCustomerDataNode` uses `user_id` to fetch `user_profile` and maybe `user_orders` documents.
    *   `DataJoinNode` config joins `user_orders` onto the `user_profile` based on `user_id`.
    *   Edge maps the `mapped_data` (output of joiner) to the `OutputNode`.

-   **Processing List Items:**
    `LoadCustomerDataNode` -> `MapListRouterNode` -> (`ProcessItemNode` & `LogItemNode`)
    *   `LoadCustomerDataNode` fetches a list (e.g., `product_list`).
    *   `MapListRouterNode` config specifies `source_path: "product_list"` and `destinations: ["ProcessItemNode", "LogItemNode"]`. May also specify `batch_size` and `batch_field_name`.
    *   Crucially, edges from `MapListRouterNode` to `ProcessItemNode` and `LogItemNode` define how *each item* is mapped (e.g., sending `item.id` and `item.price` to `ProcessItemNode`).
    *   `ProcessItemNode` and `LogItemNode` likely run with `private_input_mode: true` to handle items/batches independently/in parallel.

-   **Processing List Items with ID/Metadata Preservation (Most Common Pattern):**
    `InputNode` -> `MapListRouterNode` -> `LLMProcessingNode` (with passthrough data)
    
    **Real-World Usage Pattern from Example Workflows:**
    
    1. **Input Setup**: Input node provides list of items with `id`, `name`, and content fields.
    
    2. **Parallel Distribution**: `MapListRouterNode` distributes individual items to processing nodes.
    
    3. **Individual Processing**: Processing node configuration:
        ```json
        {
          "node_name": "llm",
          "private_input_mode": true,  // Receive data directly from router
          "output_private_output_to_central_state": true,  // Send results to central state
          "private_output_passthrough_data_to_central_state_keys": ["id", "name"],  // Preserve item metadata
          "private_output_to_central_state_node_output_key": "output",  // LLM result key
          "node_config": {
            "llm_config": {"model_spec": {"provider": "openai", "model": "gpt-4o-mini"}},
            "default_system_prompt": "Process the user prompt..."
          }
        }
        ```
        - **Receives**: Individual item data (id, name, user_prompt) from router
        - **Processes**: LLM generates response to the content
        - **Preserves**: `id` and `name` from INPUT state for result tracking
        - **Outputs**: `{output: "LLM response", id: "item_1", name: "Item Title"}`
    
    4. **Central State Collection**: Results aggregated with preserved metadata:
        ```json
        [
          {"output": "LLM response 1", "id": "item_1", "name": "Python Tutorial"},
          {"output": "LLM response 2", "id": "item_2", "name": "ML Basics"}
        ]
        ```
    
    **Multi-Stage Pipeline Pattern (Lead Scoring Example):**
    
    For sequential processing steps, each stage preserves previous context:
    
    ```json
    {
      "step1_node": {
        "private_output_passthrough_data_to_central_state_keys": ["Company", "firstName", "lastName", "emailId"],
        "write_to_private_output_passthrough_data_from_output_mappings": {
          "structured_output": "qualification_result"
        }
      },
      "step2_node": {
        "private_output_passthrough_data_to_central_state_keys": [
          "Company", "firstName", "lastName", "emailId", "qualification_result"  // Preserve previous context
        ],
        "write_to_private_output_passthrough_data_from_output_mappings": {
          "text_content": "content_analysis"  // Add new results
        }
      }
    }
    ```
    
    **Key Benefits**: Simple ID tracking, metadata preservation, clean aggregation, validation support.

-   **Merging Multiple Data Sources:**
    (`SourceANode` & `SourceBNode`) -> `MergeAggregateNode` -> `OutputNode`
    *   `SourceANode` and `SourceBNode` produce data objects (e.g., `crm_data`, `activity_data`).
    *   Edges map these outputs to the `MergeAggregateNode`.
    *   `MergeAggregateNode` `node_config` defines one or more `operations` with `select_paths` pointing to the input data (`crm_data`, `activity_data`).
    *   The `merge_strategy` within the operation specifies how to map fields, resolve conflicts (e.g., keep newest, sum values, extend lists), and potentially transform the result (including sequential non-dictionary transforms).
    *   Edge maps the desired output field from `MergeAggregateNode`'s `merged_data` (e.g., `src_field: "merged_data.consolidated_record"`) to the `OutputNode`.

## 7. Tips for Building Workflows

### General Design Principles
-   **Plan Your Flow:** Sketch out the steps and decisions like a flowchart before configuring the `GraphSchema`.
-   **Use Clear IDs:** Give your `node_id`s meaningful names (e.g., `summarize_meeting_notes`, `check_if_urgent`).
-   **Start Simple, Iterate:** Build a basic version of your workflow first, test it, and then add complexity.
-   **Consult Node Guides:** Each node type has specific configuration options and behaviors. Always refer to the relevant guide (linked above).
-   **Test with Examples:** Run your workflow with different kinds of input data to ensure it handles various scenarios correctly.

### Data Mapping with Dot Notation (NEW)
-   **Leverage Dot Notation Extensively:** Replace transformation nodes with direct edge mappings when possible. Use patterns like `api_response.data.items.0.metadata.score` to extract specific values without intermediate processing.
-   **Map Data Carefully:** Double-check `src_field` and `dst_field` paths in your `EdgeMapping`s. Verify the source data structure and ensure destination paths create the expected nested structure.
-   **Structure Your Inputs:** Use dot notation in `dst_field` to create organized input data for downstream nodes (e.g., `analysis_input.candidate.profile.skills`).
-   **API Response Handling:** For complex API responses, use dot notation to extract multiple nested values in a single edge mapping rather than processing the entire response object.
-   **Array Access Patterns:** When accessing arrays, consider data availability - `results.0.title` assumes at least one result exists. Handle edge cases appropriately.

### Advanced Patterns
```json
// Example: Comprehensive API response processing
{
  "src_node_id": "api_caller",
  "dst_node_id": "data_analyzer",
  "mappings": [
    // Extract multiple nested values from complex API response
    { "src_field": "api_response.data.user_profile.personal.full_name", "dst_field": "analysis.subject.name" },
    { "src_field": "api_response.data.user_profile.professional.current_role.title", "dst_field": "analysis.subject.job_title" },
    { "src_field": "api_response.data.user_profile.professional.current_role.company.name", "dst_field": "analysis.subject.company" },
    { "src_field": "api_response.data.activity_summary.recent_posts.0.engagement.like_count", "dst_field": "analysis.engagement.top_post_likes" },
    { "src_field": "api_response.metadata.request_timestamp", "dst_field": "analysis.metadata.data_collection_time" }
  ]
}
```

### Central State Organization
-   **Organize Central State with Dot Notation:** Use hierarchical structure in central state keys (e.g., `lead_analysis.quality.score`, `workflow_metrics.timing.duration`) to avoid naming conflicts and improve organization.
-   **Selective Central State Access:** Read only the specific nested values needed by each node rather than transferring entire objects.

### Edge Declaration and Optimization Strategies
-   **Choose Edge Declaration Style:** Use node-level `edges` fields for nodes with many outgoing connections to keep configuration organized. Use global `edges` list for complex multi-source patterns.
-   **Maintain Consistency:** Don't mix edge declaration styles for the same node - choose either node-level or global.
-   **Optimize with Data-Only Edges:** Use `data_only_edge: true` for large datasets or when you need to pass data to non-consecutive nodes without affecting execution flow. This reduces memory usage and avoids central state duplication.
-   **Mix Edge Types Strategically:** A single node can have both regular and data-only outgoing edges - use regular edges for execution control and data-only edges for efficient data distribution.

### Node-Specific Best Practices
-   **Use `PromptConstructorNode` for Prompts:** Prefer using the `PromptConstructorNode` for defining static prompts, loading/constructing dynamic prompts, and sourcing variables from various inputs.
-   **Understand Dynamic Nodes:** For Input, Output, HITL, and PromptConstructor nodes, the connected edges and explicit schema definitions (`dynamic_input_schema`, `dynamic_output_schema`) are crucial for defining their data requirements and outputs.

### Private Mode and Parallel Processing
-   **Leverage Passthrough Data for Context:** When using `MapListRouterNode` and private modes, use passthrough data mappings with dot notation to preserve complex context structures that need to flow through parallel branches.
-   **Understand `private_output_passthrough_data_to_central_state_keys`:** This field creates both central state preservation AND a passthrough data chain. It preserves keys from the node's *input state* (not output), making them available to subsequent private input mode nodes.
-   **Use Simple Patterns First:** Start with basic ID/metadata preservation patterns like `["id", "name"]`. Most real workflows just need simple field lists to track items through processing.
-   **Progressive Context Building:** For multi-stage pipelines, each step can preserve all previous context plus add new results using `write_to_private_output_passthrough_data_from_output_mappings` with dot notation support.
-   **Debug with Central State Output:** Enable `output_private_output_to_central_state: true` on nodes in private mode to see their outputs in the central state for debugging purposes.

### Performance and Error Handling
-   **Memory Optimization with Data-Only Edges:** For large datasets (>10MB), use data-only edges instead of central state to prevent memory duplication. This is especially important for workflows processing customer data, file uploads, or API responses with large payloads.
-   **Storage Efficiency:** Data-only edges reduce workflow state storage requirements in the database, leading to faster checkpointing and recovery operations.
-   **Error Handling:** The dot notation system automatically handles missing paths gracefully, but design workflows to handle cases where expected data might not exist.
-   **Path Validation:** While the system is robust, extremely deep nesting (10+ levels) may impact performance. Consider data structure optimization for very complex nested paths.
-   **Test Edge Cases:** Verify your dot notation paths work with various data structures, including empty arrays, missing properties, and null values.

By understanding how nodes, edges, mappings, and schemas work together within the `GraphSchema`, you can build powerful and flexible automated workflows. Remember to consult the individual node guides for specific configuration details.
