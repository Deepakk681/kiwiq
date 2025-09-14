# End-to-End Guide: Building Workflows

This guide provides a comprehensive walkthrough on how to design, configure, and build automated workflows using the `GraphSchema`. It covers the fundamental concepts, configuration details, data flow management, runtime context, and provides practical examples.

## 1. Introduction: What is a Workflow?

In this system, a workflow is an automated sequence of tasks designed to achieve a specific goal. Think of it as a digital assembly line or a flowchart where data moves through different processing steps.

-   **Tasks are Nodes:** Each step in the workflow is represented by a **Node**. Nodes perform specific actions like fetching data, transforming it, making decisions, calling AI models, waiting for human input, or storing results.
-   **Connections are Edges:** The sequence and flow of data between nodes are defined by **Edges**. Edges act like wires connecting the output of one node to the input of another.
-   **The Blueprint is `GraphSchema`:** The entire workflow – all its nodes, connections, and overall structure – is defined in a JSON configuration object called the `GraphSchema`. This schema is the master plan that the system reads to execute the workflow.

## 2. Understanding the `GraphSchema` Structure

The `GraphSchema` is the core JSON object defining your workflow. It has several key sections:

```json
// Example GraphSchema Structure
{
  "nodes": {
    // Node definitions go here (Section 3)
  },
  "edges": [
    // Edge definitions go here (Section 4)
  ],
  "input_node_id": "unique_id_for_start_node", // Typically "input_node"
  "output_node_id": "unique_id_for_end_node", // Typically "output_node" or the last processing node
  "runtime_config": {
    // Runtime configuration including database pool settings (Section 2.1)
  },
  "metadata": {
    // Optional graph-level settings (e.g., for central state)
  }
}
```

-   **`nodes` (Object):** A dictionary where you define each individual node (task) in your workflow. The key is the unique `node_id` you assign, and the value is the node's configuration object.
-   **`edges` (List):** A list of objects defining the connections between nodes and how data flows along those connections.
-   **`input_node_id` (String):** Specifies the `node_id` of the node that acts as the entry point for the workflow. This node defines the data the workflow expects when it starts. Conventionally, this is often `"input_node"`.
-   **`output_node_id` (String):** Specifies the `node_id` of the node whose output is considered the final result of the entire workflow. Conventionally, this might be `"output_node"`, but it can be any node in the graph.
-   **`runtime_config` (Object):** Optional section for runtime configuration settings including database connection pool tiers (see Section 2.1).
-   **`metadata` (Object):** Optional section for advanced graph-level configurations, such as defining how data should be combined in the central workflow state (using reducers).

*(See `services/workflow_service/graph/graph.py` for the precise Pydantic model definition.)*

### 2.1. Runtime Configuration: Database Pool Tiers

The `runtime_config` section allows you to optimize database connection pooling based on your workflow's expected load and concurrency requirements. This configuration is now defined using a structured `RuntimeConfig` schema for better validation and type safety.

```json
{
  "runtime_config": {
    "db_concurrent_pool_tier": "medium" // "small" | "medium" | "large"
  }
}
```

**RuntimeConfig Schema**: The runtime configuration is validated against a Pydantic schema that ensures only valid pool tier values are accepted and provides clear defaults.

**Database Pool Tiers:**

-   **`"small"` (Default):** Optimized for lightweight workflows with minimal database usage
    -   Uses default pool settings from global configuration
    -   Best for: Simple workflows, development, testing

-   **`"medium"`:** Balanced configuration for moderate database usage
    -   SQLAlchemy Pool: 10 base connections + 15 overflow = 25 total max connections  
    -   LangGraph Pool: Default worker pool settings
    -   Best for: Production workflows with moderate database operations, batch processing

-   **`"large"`:** High-performance configuration for database-intensive workflows
    -   SQLAlchemy Pool: 20 base connections + 30 overflow = 50 total max connections
    -   LangGraph Pool: 5 max connections for checkpointer operations
    -   Best for: High-concurrency workflows, data-heavy processing, complex multi-step operations

**When to Use Each Tier:**

```json
// Lightweight workflow example (small tier - default)
{
  "runtime_config": {
    "db_concurrent_pool_tier": "small"
  }
  // Good for: Simple LLM calls, basic data lookups, development workflows
}

// Moderate workflow example (medium tier)  
{
  "runtime_config": {
    "db_concurrent_pool_tier": "medium"
  }
  // Good for: Multi-step data processing, moderate parallel operations, 
  //          workflows with 10-25 concurrent database operations
}

// High-intensity workflow example (large tier)
{
  "runtime_config": {
    "db_concurrent_pool_tier": "large"  
  }
  // Good for: Heavy parallel processing, large batch operations,
  //          workflows with 25+ concurrent database operations,
  //          complex data aggregation and analysis workflows
}
```

**Technical Details:**

The pool tier configuration automatically adjusts the underlying database connection pools:

-   **SQLAlchemy Engine Pools:** Used for ORM operations (loading/storing customer data, workflow state management)
-   **LangGraph Checkpointer Pools:** Used for workflow state persistence and recovery
-   **Connection Lifecycle:** Automatic connection recycling, health checks, and timeout management

**Important Considerations:**

-   Higher tiers consume more database resources - use appropriately based on actual workflow needs
-   Pool configurations are applied when the workflow execution begins
-   Changes to pool tier require workflow redeployment to take effect
-   Monitor database connection usage to ensure optimal tier selection

*(See `libs/src/db/session.py` and `libs/src/global_config/settings.py` for implementation details.)*

## 3. Defining Nodes: The Workflow Steps

Each task in your workflow is a node, defined within the `nodes` dictionary of the `GraphSchema`.

```json
// Inside GraphSchema.nodes
"nodes": {
  "get_user_profile": { // <<< This is the unique node_id you choose
    "node_id": "get_user_profile", // <<< Must match the key above
    "node_name": "load_customer_data", // <<< Specifies the TYPE of node (its function)
    "node_config": { // <<< Node-specific configuration
      "load_paths": [
        {
          "filename_config": {
            "static_namespace": "user_profiles",
            "input_docname_field": "user_id" // Get docname from input data field (e.g., mapped from input_node)
          },
          "output_field_name": "profile_document"
        }
      ]
      // Note: User/Org context needed by this node comes from runtime_config (See Section 6)
    },
    // --- Optional Advanced Settings ---
    "private_input_mode": false, // Default: Read from shared state (See Section 9)
    "private_output_mode": false, // Default: Write to shared state (See Section 9)
    "dynamic_input_schema": null, // Usually inferred, see Section 7
    "dynamic_output_schema": null, // Usually inferred, see Section 7
    "enable_node_fan_in": false, // Default: Node runs once per trigger (See advanced docs)
    "defer_node": false,
    // --- Private Mode Passthrough Data Settings (See Section 9.1) ---
    "private_output_passthrough_data_to_central_state_keys": [], // Keys to pass from private output to central state
    "private_output_to_central_state_node_output_key": "output", // Key for node output in central state when using passthrough
    "output_private_output_to_central_state": false, // Send private output to central state for debugging
    "read_private_input_passthrough_data_to_input_field_mappings": null, // Map passthrough data to input fields (supports dot notation)
    "write_to_private_output_passthrough_data_from_output_mappings": null // Map output fields to passthrough data (supports dot notation)  
  },
  "summarize_profile": { /* ... another node definition ... */ }
  // ... more nodes
}
```

**Key Fields for Each Node:**

-   **`node_id` (String, Required):** A unique identifier *you assign* to this specific instance of the node within this workflow (e.g., `fetch_order_details`, `generate_summary_llm`, `wait_for_manager_approval`). This ID is used in edges to refer to this node. It must match the key in the `nodes` dictionary. **Cannot start with `$`**.
-   **`node_name` (String, Required):** Specifies the *type* of node, determining its function and behavior. This must match a registered node type in the system (e.g., `llm`, `filter_data`, `transform_data`, `hitl_node__default`, `router_node`, `prompt_constructor`, `load_customer_data`, `store_customer_data`, `linkedin_scraping`, `merge_aggregate`). Refer to the individual node guides or the `nodes_interplay_guide.md` for a list of available types.
-   **`node_config` (Object, Optional):** A dictionary containing configuration parameters specific to the `node_name`. The structure and required fields within `node_config` vary significantly between node types. **Consult the specific node's guide for details.** Examples:
    *   An `llm` node needs `llm_config` (model, temperature, max_tokens), `output_schema` (for structured output), `tool_calling_config` & `tools` (for tool use), `web_search_options`, etc.
    *   A `filter_data` node needs `targets` defining filter conditions.
    *   A `transform_data` node needs `mappings` defining data restructuring.
    *   A `load_customer_data` node needs `load_paths` specifying which documents to fetch. It implicitly uses the **runtime context** (see Section 6) to determine the user and organization for access control. It supports resolving paths using `input_namespace_field_pattern` and `input_docname_field_pattern` based on other input data.
    *   A `store_customer_data` node needs `store_configs` defining data sources and target locations. It also uses the **runtime context** for access control. It supports resolving paths using `input_namespace_field_pattern` and `input_docname_field_pattern` based on other input data.
    *   A `load_multiple_customer_data` node needs filters (`namespace_filter`, `include_shared`, etc.), pagination (`skip`, `limit`), sorting (`sort_by`, `sort_order`), and an `output_field_name`. It uses runtime context for authorization.
    *   A `prompt_constructor` node needs `prompt_templates` (defining static `template` or dynamic `template_load_config`, `variables` for defaults/requirements, and optionally `construct_options` for path-based variable sourcing) and optionally `global_construct_options` for fallback path sourcing.
    *   A `linkedin_scraping` node needs `jobs` defining scraping tasks (profile info, posts, search). Each job defines parameters (static or dynamic via `InputSource` object, which supports `static_value`, `input_field_path`, and `expand_list`), limits (using system defaults if omitted), and an `output_field_name`. It can be run in `test_mode` to validate configs. See its guide for details on job types, credit consumption, defaults, and the output structure (`execution_summary`, `scraping_results`).
    *   A `merge_aggregate` node needs `operations`. Each operation defines `select_paths` (data sources), an `output_field_name`, and a `merge_strategy` (containing `map_phase`, `reduce_phase`, and optional `post_merge_transformations`) to intelligently combine objects. Supports sequential transformations on non-dictionary results. See its guide for details on strategies and reducers.
    *   *Deprecated:* `load_prompt_templates` node (use `prompt_constructor` with `template_load_config` instead).
-   **`private_input_mode` / `private_output_mode` (Boolean, Optional):** Advanced settings primarily used with `map_list_router_node` for parallel processing. See Section 9.
-   **Private Mode Passthrough Settings (Optional):** Advanced configurations for controlling data flow in private modes:
    -   **`private_output_passthrough_data_to_central_state_keys` (List[String]):** Keys from the current node's private input state to pass through to the central state when the node completes. This serves a dual purpose: (1) It preserves context data (like unique IDs, metadata) from parallel processing branches in the central state for aggregation, and (2) It makes this data available as passthrough data for subsequent private input mode nodes in the processing chain. **Key insight:** This field specifies which keys from the node's *input state* (not output) should be carried forward. **Most common pattern from real workflows:** `["id", "name"]` to preserve item identifiers and descriptive names through parallel processing for result tracking and validation.
    -   **`private_output_to_central_state_node_output_key` (String):** Key name for node output when writing to central state (default: "output").
    -   **`output_private_output_to_central_state` (Boolean):** Whether to send private output to central state for debugging.
    -   **`read_private_input_passthrough_data_to_input_field_mappings` (Object):** Maps passthrough data keys to input field names. Supports dot notation for nested paths (e.g., `{"user.profile.name": "display_name"}`).
    -   **`write_to_private_output_passthrough_data_from_output_mappings` (Object):** Maps output field names to passthrough data keys. Supports dot notation for nested paths (e.g., `{"result.user_id": "context.user.id"}`).
    See Section 9.1 for detailed usage.
-   **`dynamic_input_schema` / `dynamic_output_schema` (Object, Optional):** Advanced settings for explicitly defining expected data structures, often used by dynamic nodes like `InputNode`, `OutputNode`, `HITLNode`, `PromptConstructorNode`. Defining these is highly recommended for dynamic nodes. See Section 7.

## 4. Connecting Nodes with Edges: Defining the Flow

Edges are the arrows in your workflow flowchart. They define the sequence and, crucially, how data is passed between nodes. Edges can be defined in two ways: in the `edges` list of the `GraphSchema` (traditional) or within individual node configurations (new feature).

### 4.1. Traditional Edge Definition

```json
// Inside GraphSchema.edges
"edges": [
  {
    "src_node_id": "node_A", // The ID of the node SENDING data
    "dst_node_id": "node_B", // The ID of the node RECEIVING data
    "mappings": [ // Optional: Instructions for data transfer
      {
        "src_field": "output_field_from_A", // Field name in Node A's output
        "dst_field": "expected_input_field_in_B" // Name this data will have for Node B
      },
      // --- Using Dot Notation for Nested Data (NEW FEATURE) ---
      {
        "src_field": "complex_output.details.primary_email", // Extract deeply nested email
        "dst_field": "contact_info.email" // Store in nested contact_info object
      },
      // --- Array Access with Indices ---
      {
        "src_field": "user_list.0.profile.name", // First user's profile name
        "dst_field": "primary_user.display_name"
      },
      // --- Complex Nested Mapping ---
      {
        "src_field": "api_response.data.results.0.metadata.score",
        "dst_field": "analysis.quality_metrics.primary_score"
      },
      // --- Mapping a whole object ---
      {
        "src_field": "user_settings", // The entire 'user_settings' object from Node A
        "dst_field": "settings_for_B" // Will arrive as 'settings_for_B' in Node B
      },
      // --- Mapping to a template-specific variable (for PromptConstructorNode) ---
      {
         "src_field": "specific_tone_setting",
         "dst_field": "my_prompt_id.tone" // Sets 'tone' variable only for template with id 'my_prompt_id'
      }
    ]
  },
  // --- An edge for control flow (no data mapping needed) ---
  {
    "src_node_id": "node_B",
    "dst_node_id": "node_C"
    // "mappings" is omitted or empty []
  }
]
```

### 4.2. Node-Level Edge Declaration (NEW FEATURE)

You can now declare edges directly within node configurations for better organization:

```json
// Inside GraphSchema.nodes
"nodes": {
  "data_processor": {
    "node_id": "data_processor",
    "node_name": "transform_data", 
    "node_config": { /* ... */ },
    "edges": [ // Edges originating FROM this node
      {
        "dst_node_id": "validation_node",
        "mappings": [
          {
            "src_field": "processed_data.results",
            "dst_field": "input_data"
          }
        ]
      },
      {
        "dst_node_id": "summary_node",
        "mappings": [
          {
            "src_field": "processed_data.metadata.stats",
            "dst_field": "summary_stats.processing"
          }
        ]
      }
    ]
  }
}
```

**Note**: A node can declare edges either in its node configuration OR in the global `edges` list, but not both. The system will automatically convert node-level edge declarations to the standard format during validation.

### 4.3. Edge Field Reference

**Key Fields for Each Edge:**

-   **`src_node_id` (String, Required):** The `node_id` of the node where the connection starts (the data source).
-   **`dst_node_id` (String, Required):** The `node_id` of the node where the connection ends (the data destination).
-   **`mappings` (List[`EdgeMapping`], Optional):** This list defines *which* data fields flow from the source to the destination and what they should be called.
    *   Each object in the `mappings` list requires:
        *   **`src_field` (String):** The name of the field in the output of the `src_node_id`. **Supports full dot notation** for accessing nested data structures.
        *   **`dst_field` (String):** The name the data from `src_field` should have when it becomes input for the `dst_node_id`. **Supports full dot notation** for creating nested structures. Can also use `TEMPLATE_ID.VARIABLE_NAME` format for template-specific inputs (e.g., for `PromptConstructorNode`).

### 4.4. Dot Notation Reference (NEW FEATURE)

The edge mapping system now supports comprehensive dot notation for accessing and setting nested data structures:

**Dot Notation Syntax:**
- **Object Access**: `field.subfield.property`
- **Array Access**: `field.0.property` (using numeric indices)
- **Deep Nesting**: `data.results.0.metadata.user.profile.settings.theme`
- **Mixed Access**: `users.0.preferences.notifications.email.enabled`

**Examples by Use Case:**

```json
// --- Basic Nested Object Access ---
{
  "src_field": "user_profile.contact.email",
  "dst_field": "notification_settings.email_address"
}

// --- Array Element Access ---
{
  "src_field": "search_results.0.title",     // First search result's title
  "dst_field": "primary_result.heading"
}

// --- Deep Nesting with Arrays ---
{
  "src_field": "api_response.data.items.2.metadata.tags.0", // Third item's first tag
  "dst_field": "categorization.primary_tag"
}

// --- Creating Nested Structures ---
{
  "src_field": "simple_score",               // Flat field from source
  "dst_field": "analysis.metrics.quality_score" // Creates nested structure in destination
}

// --- Complex API Response Mapping ---
{
  "src_field": "linkedin_data.profile.experience.0.company.name",
  "dst_field": "lead_info.current_employer.company_name"
}

// --- LLM Structured Output Access ---
{
  "src_field": "structured_output.recommendations.0.priority_level",
  "dst_field": "action_items.highest_priority.level"
}
```

**Advanced Patterns:**

```json
// --- Multiple Fields from Same Nested Source ---
{
  "mappings": [
    {
      "src_field": "customer_data.profile.personal.first_name",
      "dst_field": "personalization.greeting.first_name"
    },
    {
      "src_field": "customer_data.profile.personal.last_name", 
      "dst_field": "personalization.greeting.last_name"
    },
    {
      "src_field": "customer_data.profile.preferences.communication.email",
      "dst_field": "contact.primary_method"
    }
  ]
}

// --- Transforming Array Structure ---
{
  "mappings": [
    {
      "src_field": "raw_leads.0.contact_info.email",
      "dst_field": "processed_leads.primary.email"
    },
    {
      "src_field": "raw_leads.0.company_info.name",
      "dst_field": "processed_leads.primary.company"  
    }
  ]
}
```

### 4.5. Why are Mappings Important?

Nodes are often developed independently and have specific expectations for their input data names. Mappings act as adapters, ensuring the output data from one node matches the input requirements of the next. With dot notation support, you can now:

- **Extract specific values** from complex nested structures without preprocessing
- **Create structured inputs** for nodes that expect organized data
- **Avoid data transformation nodes** for simple field restructuring
- **Handle API responses directly** without custom parsing logic

### 4.6. Data-Only Edges: Efficient Non-Flow Data Passing (ADVANCED FEATURE)

**Data-only edges** provide an efficient way to pass data between nodes without affecting the workflow's execution flow. This is a powerful optimization feature for complex workflows.

#### What are Data-Only Edges?

A data-only edge passes data from a source node to a destination node **without creating an execution dependency**. The destination node receives the data but is not triggered to execute by this edge.

```json
{
  "src_node_id": "data_producer",
  "dst_node_id": "data_consumer", 
  "data_only_edge": true,  // KEY: This makes it a data-only edge
  "mappings": [
    { "src_field": "analysis_results", "dst_field": "background_data" },
    { "src_field": "metadata.processing_time", "dst_field": "performance_info.duration" }
  ]
}
```

#### How Data-Only Edges Work

1. **Execution Flow**: The edge does NOT affect when nodes execute. `data_consumer` will only execute when triggered by regular (non-data-only) edges.

2. **Data Availability**: When `data_consumer` does execute, it will have access to the data mapped from `data_producer` via the data-only edge.

3. **No Central State Copy**: The data flows directly from source to destination without being stored in the central workflow state, saving memory and storage.

#### When to Use Data-Only Edges

**Use data-only edges when:**
- You need to pass data to a node that's not immediately next in the execution sequence
- You want to avoid storing large datasets in central state  
- Multiple downstream nodes need access to the same data from a source node
- You want to optimize memory usage in complex workflows

**Example Use Case:**
```json
{
  "nodes": {
    "load_large_dataset": {
      "node_id": "load_large_dataset",
      "node_name": "load_customer_data", 
      "node_config": { /* loads 100MB dataset */ }
    },
    "quick_validation": {
      "node_id": "quick_validation",
      "node_name": "filter_data",
      "node_config": { /* validates dataset structure */ }
    },
    "detailed_analysis": {
      "node_id": "detailed_analysis", 
      "node_name": "llm",
      "node_config": { /* analyzes full dataset */ }
    },
    "summary_report": {
      "node_id": "summary_report",
      "node_name": "transform_data",
      "node_config": { /* generates summary */ }
    }
  },
  "edges": [
    // Regular execution flow
    { "src_node_id": "load_large_dataset", "dst_node_id": "quick_validation", "mappings": [...] },
    { "src_node_id": "quick_validation", "dst_node_id": "summary_report", "mappings": [...] },
    
    // Data-only edge: Pass large dataset directly to detailed_analysis 
    // without storing in central state or affecting execution order
    {
      "src_node_id": "load_large_dataset", 
      "dst_node_id": "detailed_analysis",
      "data_only_edge": true,
      "mappings": [
        { "src_field": "large_dataset", "dst_field": "analysis_data" }
      ]
    },
    
    // Regular execution flow continues (detailed_analysis runs after summary_report)
    { "src_node_id": "summary_report", "dst_node_id": "detailed_analysis", "mappings": [...] }
  ]
}
```

#### Data-Only Edges vs Central State

| Approach | Memory Usage | Execution Control | Best For |
|----------|--------------|-------------------|----------|
| **Data-Only Edge** | Efficient (direct reuse) | Precise flow control | Large data, specific destinations |
| **Central State** | Higher (stored copy) | Simple access | Small data, multiple access points |

#### Performance Benefits

1. **Memory Efficiency**: Large datasets aren't duplicated in central state
2. **Storage Optimization**: Reduces workflow state storage requirements  
3. **Direct Data Reuse**: Node outputs are reused directly without copying
4. **Selective Data Flow**: Only targeted nodes receive specific data

#### Important Notes

- **Execution Order**: Data-only edges do NOT trigger node execution
- **Data Availability**: Data is only available when the destination node executes via regular edges
- **Dot Notation Support**: Data-only edges support full dot notation in mappings
- **Node-Level Declaration**: Can be declared in node `edges` configuration or global `edges` list
- **Mixed Edge Types**: A node can have both regular and data-only outgoing edges

### 4.7. What if `mappings` is empty?

An edge without mappings primarily defines execution order: `dst_node_id` will run after `src_node_id`. The `dst_node_id` might not need direct data from the `src_node_id` (perhaps it reads from the central state or uses mechanisms like `construct_options`), or it might process the entire state passed along implicitly. However, relying on implicit data flow is less clear than using explicit mappings.

## 5. Handling Data Flow

Data is the lifeblood of the workflow. Understanding how it moves is critical. With dot notation support and data-only edges, data flow has become much more flexible, efficient, and powerful.

**Data Flow Methods:**
1. **Direct Edge Mappings**: Sequential node-to-node data transfer
2. **Central Workflow State**: Shared memory for multi-node access  
3. **Data-Only Edges**: Efficient direct data passing without execution flow (NEW - Section 4.6)

### 5.1. Basic Data Passing via Mappings

`EdgeMapping`s are the standard way to pass specific data fields:

```json
// Node A produces: { "result_summary": "...", "status_code": 200 }
// Node B expects: { "summary_text": "...", "outcome": "..." }

// Edge from A to B:
{
  "src_node_id": "node_A",
  "dst_node_id": "node_B",
  "mappings": [
    { "src_field": "result_summary", "dst_field": "summary_text" },
    // Note: status_code is not mapped, so Node B doesn't receive it directly via this edge.
  ]
}
```

### 5.2. Accessing Nested Data with Dot Notation

Use dot notation (`.`) in `src_field` and `dst_field` to access data within nested objects or lists:

```json
// Node A produces: { 
//   "report": { 
//     "details": { 
//       "author": "John Smith", 
//       "tags": ["urgent", "internal"],
//       "metrics": { "score": 95, "confidence": 0.8 }
//     } 
//   } 
// }
// Node C expects: { "report_author": "...", "first_tag": "...", "quality_metrics": {...} }

// Edge from A to C:
{
  "src_node_id": "node_A",
  "dst_node_id": "node_C",
  "mappings": [
    { "src_field": "report.details.author", "dst_field": "report_author" },
    { "src_field": "report.details.tags.0", "dst_field": "first_tag" }, // Get the first tag
    { "src_field": "report.details.metrics.score", "dst_field": "quality_metrics.primary_score" },
    { "src_field": "report.details.metrics.confidence", "dst_field": "quality_metrics.confidence_level" }
  ]
}
```

### 5.3. Complex Data Structure Handling

The dot notation system handles complex nested structures seamlessly:

```json
// Example: Processing LinkedIn API Response
// Node A produces: {
//   "linkedin_response": {
//     "profile": {
//       "basic_info": { "first_name": "Jane", "last_name": "Doe" },
//       "experience": [
//         {
//           "company": { "name": "TechCorp", "industry": "Software" },
//           "position": { "title": "Senior Engineer", "level": "Senior" }
//         }
//       ],
//       "skills": ["Python", "Machine Learning", "APIs"]
//     }
//   }
// }

// Edge mapping to structure for LLM processing:
{
  "src_node_id": "linkedin_scraper",
  "dst_node_id": "profile_analyzer", 
  "mappings": [
    { 
      "src_field": "linkedin_response.profile.basic_info.first_name", 
      "dst_field": "analysis_input.candidate.personal.first_name" 
    },
    { 
      "src_field": "linkedin_response.profile.basic_info.last_name", 
      "dst_field": "analysis_input.candidate.personal.last_name" 
    },
    { 
      "src_field": "linkedin_response.profile.experience.0.company.name", 
      "dst_field": "analysis_input.candidate.current_role.company" 
    },
    { 
      "src_field": "linkedin_response.profile.experience.0.position.title", 
      "dst_field": "analysis_input.candidate.current_role.title" 
    },
    { 
      "src_field": "linkedin_response.profile.skills", 
      "dst_field": "analysis_input.candidate.technical_skills" 
    }
  ]
}
```

### 5.4. Error Handling and Validation

The dot notation system includes robust error handling:

- **Path Not Found**: If a nested path doesn't exist, the system logs a warning and skips the mapping
- **Index Out of Bounds**: Array access with invalid indices is handled gracefully
- **Type Mismatches**: Attempting to access nested properties on primitive values is caught
- **Automatic Structure Creation**: Destination nested structures are created automatically as needed

### 5.5. Central Workflow State (`"$graph_state"`)

Workflows often need a shared **memory** or **scratchpad** accessible by multiple nodes throughout the execution. This allows data to persist across steps that aren't directly connected or to manage state during loops (like tracking `iteration_count` from an `LLMNode`'s metadata). This shared memory is accessed using the special node ID `"$graph_state"`.

**Writing to Central State with Dot Notation:**
An edge *from* a regular node *to* `"$graph_state"` saves data into the shared memory, with full dot notation support:

    ```json
// Example: Storing nested analysis results
    {
  "src_node_id": "calculate_score", 
  "dst_node_id": "$graph_state",
      "mappings": [
    { "src_field": "analysis_results.quality_score", "dst_field": "lead_analysis.quality.score" },
    { "src_field": "analysis_results.confidence_level", "dst_field": "lead_analysis.quality.confidence" },
    { "src_field": "metadata.processing_time", "dst_field": "workflow_stats.processing_times.scoring" }
      ]
    }
    ```

**Reading from Central State with Dot Notation:**
An edge *from* `"$graph_state"` *to* a regular node retrieves data from the shared memory:

    ```json
// Example: Retrieving nested analysis data
    {
  "src_node_id": "$graph_state",
  "dst_node_id": "send_notification",
      "mappings": [
    { "src_field": "lead_analysis.quality.score", "dst_field": "notification_data.score" },
    { "src_field": "lead_analysis.quality.confidence", "dst_field": "notification_data.confidence" },
    { "src_field": "workflow_stats.processing_times", "dst_field": "debug_info.timing" }
      ]
    }
    ```

**Complex Central State Operations:**

```json
// Example: Multi-stage workflow with progressive state building
{
  "mappings": [
    // Store multiple analysis results in organized structure
    { "src_field": "linkedin_analysis.company_info", "dst_field": "lead_profile.employment.current_company" },
    { "src_field": "linkedin_analysis.experience_summary", "dst_field": "lead_profile.employment.background" },
    { "src_field": "web_research.company_news.0.headline", "dst_field": "lead_profile.context.latest_company_news" },
    { "src_field": "sentiment_analysis.overall_score", "dst_field": "lead_profile.analysis.sentiment_score" }
  ]
}
```

**Important Notes:**
- **Execution Flow**: Edges originating *from* `"$graph_state"` are solely for **data retrieval**. They **do not** trigger the execution of the destination node.
- **Dot Notation**: Both reading from and writing to central state support full dot notation for nested structures
- **Automatic Structure Creation**: Writing to nested paths in central state automatically creates the required structure
- **Reducers (Advanced)**: When multiple nodes write to the *same key* in the central state, you can define how data is combined using "reducers" in `GraphSchema.metadata`. Common reducers include `replace` (default), `add_messages`, and `append_list`.

## 6. Accessing Runtime Context

Beyond the data explicitly passed via edges or stored in the central state (`$graph_state`), nodes often need access to information about the *current execution environment* and *shared services*. This is provided through the **runtime configuration** (`runtime_config`).

**What is `runtime_config`?**

When a workflow is executed (e.g., via the `workflow_execution_flow` in `worker.py`), the system prepares a special `runtime_config` dictionary. This dictionary is automatically passed to the `process` method of every node when it runs. It contains crucial context that nodes can use without requiring explicit mappings in the `GraphSchema`.

**Key Context Items:**

-   **`APPLICATION_CONTEXT_KEY` (`"application_context"`):** This key holds a dictionary containing information specific to the current workflow run.
    *   **`workflow_run_job` (`WorkflowRunJobCreate`):** Contains details like the current `run_id`, `workflow_id`, `owner_org_id`, `triggered_by_user_id`, the initial `inputs` provided to the workflow, and `thread_id`.
    *   **`user` (`User` model):** The fully loaded user object corresponding to `triggered_by_user_id`. This allows nodes to perform actions based on user roles, permissions, or preferences.

-   **`EXTERNAL_CONTEXT_MANAGER_KEY` (`"external_context_manager"`):** This key holds an instance of the `ExternalContextManager`. This manager provides managed access to shared external resources and services.
    *   **Database Connections:** Access to the asynchronous database pool (`db`).
    *   **Service Clients:** Ready-to-use clients for interacting with other services, such as `customer_data_service` (for MongoDB interactions), `rabbit` (for message queue publishing), etc.
    *   **Registries:** Access to registries like `db_registry` (for schema templates, etc.).

**How Nodes Use Runtime Context:**

Nodes needing this information (like `load_customer_data` or `store_customer_data`) retrieve it directly from the `runtime_config` passed to their `process` method.

```python
# Simplified example inside a node's process method
# from workflow_service.config.constants import APPLICATION_CONTEXT_KEY, EXTERNAL_CONTEXT_MANAGER_KEY
# from kiwi_app.auth.models import User
# from kiwi_app.workflow_app.schemas import WorkflowRunJobCreate

async def process(self, input_data, runtime_config, *args, **kwargs):
    if not runtime_config:
        self.logger.error("Missing runtime_config.")
        return # Handle error

    # Retrieve the specific context dictionaries
    app_context = runtime_config.get("configurable", {}).get(APPLICATION_CONTEXT_KEY)
    ext_context = runtime_config.get("configurable", {}).get(EXTERNAL_CONTEXT_MANAGER_KEY)

    if not app_context or not ext_context:
        self.logger.error("Missing required keys in runtime_config.")
        return # Handle error

    # Access information from Application Context
    user: Optional[User] = app_context.get("user")
    run_job: Optional[WorkflowRunJobCreate] = app_context.get("workflow_run_job")

    if not user or not run_job:
        self.logger.error("Missing user or run_job in application context.")
        return # Handle error

    org_id = run_job.owner_org_id
    user_id = user.id
    self.logger.info(f"Node running for Org: {org_id}, User: {user_id}")

    # Access services from External Context Manager
    customer_data_service = ext_context.customer_data_service
    # rabbit_client = ext_context.rabbit

    # Example: Use the service with implicit org/user context
    # (The service uses the provided 'user' object for permission checks)
    try:
        # No need to pass org_id/user_id explicitly to the node config!
        # The service method receives the 'user' object for context.
        document = await customer_data_service.get_unversioned_document(
            org_id=org_id, # org_id is required by the service method signature
            namespace="some_namespace",
            docname="some_doc",
            is_shared=False, # Example flag
            user=user # Pass the user object for authorization checks
        )
        # ... process document ...
    except Exception as e:
        self.logger.error(f"Failed to load document: {e}")

    # ... rest of node logic ...
```

**Benefits of Runtime Context:**

-   **Simpler Graph Schemas:** You don't need to clutter your `GraphSchema` by explicitly passing `user_id`, `org_id`, or service connection details through edges.
-   **Security:** Nodes automatically operate within the correct organizational and user context, simplifying permission enforcement.
-   **Maintainability:** Centralizes access to external services, making it easier to manage connections and configurations.

## 7. Working with Dynamic Schemas

Some nodes don't have fixed input/output structures but adapt based on connections or configuration.

-   **`InputNode`:** Its *output* is defined by the `src_field`s on its outgoing edges. These become the workflow's initial required inputs.
    ```json
    // Edge from InputNode:
    { "src_node_id": "input_node", "dst_node_id": "some_node", "mappings": [ { "src_field": "user_query", "dst_field": "query" } ] }
    // This means the workflow requires an input named "user_query".
    ```
-   **`OutputNode`:** Its *input* is defined by the `dst_field`s on its incoming edges. These define the workflow's final output structure.
    ```json
    // Edge to OutputNode:
    { "src_node_id": "some_node", "dst_node_id": "output_node", "mappings": [ { "src_field": "result", "dst_field": "final_answer" } ] }
    // This means the workflow will output a field named "final_answer".
    ```
-   **`HITLNode`:** Its input (data shown) and output (data provided) schemas are often defined by incoming/outgoing edge mappings.
-   **`LLMNode` with `output_schema`:** While the base `LLMNode` has static I/O fields (`user_prompt`, `content`, `metadata`, etc.), configuring `output_schema` in its `node_config` causes it to produce an additional `structured_output` field whose *content* structure matches your definition. You may map in the future *from* this structured data using `structured_output.field_name`. NOTE: currently mapping is only possible with first level fields in edges, so this type of notation can go in some node's configs to access subfields, but not directly via edges as of now!
-   **`PromptConstructorNode`:** Its input schema is dynamic, derived from several sources: fields needed for `construct_options` path lookups (e.g., if a path is `user.profile.name`, it needs the `user` field mapped), fields needed for dynamic template loading (`input_name_field_path`, `input_version_field_path`), fields mapped directly via edges (globally like `variable_name` or template-specific like `template_id.variable_name`), and variables marked `null` in its config. Its output dictionary *always* contains fields matching the `id` of each successfully constructed template, plus a `prompt_template_errors` list (empty if no errors). The structure of the final *validated output object* passed downstream is determined by the `dynamic_output_schema` defined for the node in the `GraphSchema`. This schema should list the expected template `id` fields and can optionally include `prompt_template_errors`. **It is highly recommended to explicitly define `dynamic_input_schema` and `dynamic_output_schema` for this node in the `GraphSchema` for clarity and validation.**
-   *Deprecated:* `PromptTemplateLoaderNode` (Functionality merged into `prompt_constructor`).
-   **Other Config-Driven Nodes:** Nodes like `FilterNode`, `IfElseConditionNode`, `RouterNode`, `Load/StoreCustomerDataNode`, `DataJoinNode`, `TransformerNode`, `MergeAggregateNode`, and `LinkedInScrapingNode` determine required inputs and/or shape their outputs based on values within their `node_config`. Ensure data for necessary input paths (e.g., `field`, `input_path`, `source_path`, `input_field_path`, `select_paths`) is available via edges or central state. For `LinkedInScrapingNode`, the output structure under `scraping_results` is determined by the `output_field_name` in each configured `job`. For `MergeAggregateNode`, the output structure under `merged_data` is determined by the `output_field_name` in each configured `operation`. Many of these nodes (especially `Load/StoreCustomerDataNode`) also rely on the **runtime context** (see Section 6) for permissions and service access.

## 8. Advanced Pattern: Conditional Logic

Workflows often need to make decisions. This is typically done using an `IfElseConditionNode` combined with a `RouterNode`.

1.  **Evaluate Conditions:** The `IfElseConditionNode` evaluates complex conditions (potentially multiple sets combined with AND/OR logic) based on its input data. See its guide for detailed configuration.
2.  **Output Decision:** It produces an output field named `branch`, whose value will be either the string `"true_branch"` or `"false_branch"`.
3.  **Map Decision to Router:** An edge connects the `IfElseConditionNode` to a `RouterNode`, mapping the `branch` output field to an input field the router will check.
    ```json
    {
      "src_node_id": "my_if_else_node",
      "dst_node_id": "my_router_node",
      "mappings": [ { "src_field": "branch", "dst_field": "decision_result" } ]
    }
    ```
4.  **Configure Router:** The `RouterNode` is configured (see its guide) to check the value of the mapped field (`decision_result` in this case). It defines which `choice_id` (downstream node ID) corresponds to the `"true_branch"` value and which corresponds to the `"false_branch"` value.
    ```json
    // Inside my_router_node node_config:
    "choices_with_conditions": [
      { "choice_id": "node_for_true_path", "input_path": "decision_result", "target_value": "true_branch" },
      { "choice_id": "node_for_false_path", "input_path": "decision_result", "target_value": "false_branch" }
    ]
    ```
5.  **Connect Router Outputs:** Define edges from the `RouterNode` to both potential downstream nodes (`node_for_true_path` and `node_for_false_path`). The execution engine will only follow the path chosen by the router based on the `decision_result`.

## 9. Advanced Pattern: Processing Lists in Parallel (`MapListRouterNode`)

To process each item in a list independently (and potentially in parallel), use the `MapListRouterNode`.

1.  **Configure Mapper:**
    *   Set `node_name` to `map_list_router_node`.
    *   In `node_config`:
        *   Specify the `source_path` to the list/dictionary in the input data.
        *   List the `destinations` (target `node_id`s) where *each item* should be sent.
        *   Include all destinations in the top-level `choices` list.
2.  **Define Item Transformation on Edges:**
    *   Create edges from the `MapListRouterNode` to each destination node.
    *   The `mappings` on *these specific edges* define how *each individual item* from the source list is transformed before being sent to that destination. If mappings are empty, the item is sent as-is.
3.  **Enable Parallelism with Private Modes:**
    *   **Problem:** If multiple instances of a destination node run in parallel and modify the shared central state, they can interfere with each other.
    *   **Solution:**
        *   Set **`private_input_mode: true`** on the **destination nodes** (the ones listed in the mapper's `destinations`). This tells them to get their input directly from the mapper's `Send` command, not the shared state.
        *   If a parallel branch continues further (NodeA -> NodeB, both running per-item), NodeA needs **`private_output_mode: true`** (to send its output directly) and NodeB needs **`private_input_mode: true`** (to receive it directly).
4.  **Convergence / Aggregation:** By default, branches running in private mode don't automatically write their final results back to the *main* shared central state when they finish (they operate in isolated sub-states). However, you *can* explicitly write data back to the central state (`"$graph_state"`) from nodes within these parallel branches. To combine results from multiple parallel runs (e.g., collecting all generated items into a single list), you **must** configure appropriate **reducers** in the `GraphSchema.metadata`. For instance, using an `append_list` reducer on a specific key in `"$graph_state"` allows each parallel branch to add its result to that list, effectively aggregating the output in the central state. Without such reducers, concurrent writes to the same key would likely overwrite each other (default `replace` behavior).

*(See the `MapListRouterNode` guide for a detailed example.)*

### 9.1. Advanced Pattern: Private Mode Passthrough Data

When using private input/output modes (typically with `MapListRouterNode` for parallel processing), you often need to pass additional context data between nodes that isn't part of the main data flow. The passthrough data system provides flexible mechanisms for this.

**Understanding the Dual Nature of `private_output_passthrough_data_to_central_state_keys`:**

This configuration serves two critical functions:
1. **Central State Preservation**: When a node completes, specified keys from its input state are preserved in the central state. This is essential for collecting metadata, IDs, or context from parallel processing branches.
2. **Passthrough Data Chain**: The same data becomes available to subsequent private input mode nodes as passthrough data, creating a data pipeline that flows alongside the main processing chain.

**Key Configurations:**

1. **`private_output_passthrough_data_to_central_state_keys`**: A list of keys from the node's **input state** (not output) that should be carried forward. When the node completes, these keys are:
   - Added to the central state (if edges to `$graph_state` exist)
   - Made available as passthrough data to downstream private input mode nodes
   
   **Critical insight**: This preserves data from the node's *input* (what it received), not its *output* (what it produced). This is perfect for preserving context like item IDs, batch metadata, or processing timestamps that need to flow through multiple processing steps.

2. **`private_output_to_central_state_node_output_key`**: The key name used for the main node output when writing to central state in cases where there's extra passthrough data (default: "output").

3. **`output_private_output_to_central_state`**: Whether to send private output to central state for debugging purposes.

4. **`read_private_input_passthrough_data_to_input_field_mappings`**: Maps passthrough data keys to input field names when `private_input_mode` is True. Supports dot notation for nested paths.

5. **`write_to_private_output_passthrough_data_from_output_mappings`**: Maps output field names to passthrough data keys when `private_output_mode` is True. Supports dot notation for nested paths.

**Dot Notation Support:**

Both read and write mappings support dot notation for accessing nested data:

```json
{
  "read_private_input_passthrough_data_to_input_field_mappings": {
    "user.profile.name": "display_name",           // Read user.profile.name → input.display_name
    "metadata.request_id": "tracking.info.id"     // Read metadata.request_id → input.tracking.info.id
  },
  "write_to_private_output_passthrough_data_from_output_mappings": {
    "result.user_id": "context.user.id",          // Write output.result.user_id → passthrough.context.user.id
    "processed_data.count": "stats.total"         // Write output.processed_data.count → passthrough.stats.total
  }
}
```

**Example Use Case: Processing Item List with ID/Metadata Preservation (Based on Real Workflow)**

This example demonstrates the most common usage pattern from actual workflows - preserving item IDs and metadata through parallel processing:

```json
{
  "nodes": {
    "input_node": {
      "node_id": "input_node",
      "node_name": "input_node",
      "node_config": {},
      "dynamic_output_schema": {
        "fields": {
          "items_to_process": {
            "type": "list",
            "default": [
              { "id": "item_1", "name": "Python Data Science", "user_prompt": "What are Python's advantages for data science?" },
              { "id": "item_2", "name": "Machine Learning Basics", "user_prompt": "Explain machine learning concepts." }
            ]
          }
        }
      }
    },
    "route_items": {
      "node_id": "route_items",
      "node_name": "map_list_router_node",
      "node_config": {
        "choices": ["process_individual_item"],
        "map_targets": [{
          "source_path": "items_to_process",
          "destinations": ["process_individual_item"],
          "batch_size": 1
        }]
      }
    },
    "process_individual_item": {
      "node_id": "process_individual_item",
      "node_name": "llm",
      "private_input_mode": true,  // Receive data directly from router
      "output_private_output_to_central_state": true,  // Send results to central state
      // CRITICAL: These keys from INPUT are preserved in central state
      "private_output_passthrough_data_to_central_state_keys": ["id", "name"],
      "private_output_to_central_state_node_output_key": "output",  // LLM result goes under "output" key
      "node_config": {
        "llm_config": {
          "model_spec": {"provider": "openai", "model": "gpt-4o-mini"},
          "temperature": 0.7,
          "max_tokens": 1000
        },
        "default_system_prompt": "You are a helpful AI assistant..."
      }
    }
  },
  "edges": [
    // Input to router
    { "src_node_id": "input_node", "dst_node_id": "route_items", "mappings": [
      { "src_field": "items_to_process", "dst_field": "items_to_process" }
    ]},
    // Router to LLM (private mode - no explicit mappings needed)
    { "src_node_id": "route_items", "dst_node_id": "process_individual_item", "mappings": [] },
    // LLM to central state (collect results with preserved metadata)
    { "src_node_id": "process_individual_item", "dst_node_id": "$graph_state", "mappings": [
      { "src_field": "text_content", "dst_field": "all_processed_items" }
    ]}
  ],
  "metadata": {
    "$graph_state": {
      "reducer": {
        "all_processed_items": "collect_values"  // Aggregates: [{output: "LLM response", id: "item_1", name: "Python Data Science"}, ...]
      }
    }
  }
}
```

**Data Flow Explanation:**

1. **Input Setup**: Input node provides list of items, each with `id`, `name`, and `user_prompt` fields.

2. **Parallel Distribution**: `route_items` (`map_list_router_node`) distributes individual items to the LLM processing node. Each item becomes a separate parallel execution branch.

3. **Individual Processing**: `process_individual_item` node:
   - **Receives**: Individual item data (id, name, user_prompt) directly from router via private input mode
   - **Processes**: LLM generates response to the user_prompt
   - **Preserves via passthrough**: `id` and `name` fields from its INPUT state using `private_output_passthrough_data_to_central_state_keys`
   - **Outputs to Central State**: LLM response under "output" key + preserved metadata

4. **Result Aggregation**: Central state collects all results using `collect_values` reducer, producing:
   ```json
   [
     { "output": "LLM response to item 1", "id": "item_1", "name": "Python Data Science" },
     { "output": "LLM response to item 2", "id": "item_2", "name": "Machine Learning Basics" }
   ]
   ```

**Key Benefits from Real Workflow Patterns:**
- **Simple ID Preservation**: Most common use case - preserve item IDs for result tracking
- **Metadata Continuity**: Keep descriptive names/titles through processing pipeline  
- **Clean Aggregation**: Central state receives both processing results and original context
- **Validation Support**: Easy to verify all items were processed by checking IDs

**Advanced Pattern: Multi-Stage Pipeline with Progressive Context (Based on Lead Scoring Workflow)**

For complex workflows requiring multiple sequential processing steps, each stage can preserve previous context AND add new results:

```json
{
  "nodes": {
    "step1_qualification": {
      "node_id": "step1_qualification",
      "node_name": "llm",
      "private_input_mode": true,
      "output_private_output_to_central_state": true,
      // Preserve original lead data through the pipeline
      "private_output_passthrough_data_to_central_state_keys": ["linkedinUrl", "Company", "firstName", "lastName", "emailId", "jobTitle"],
      "write_to_private_output_passthrough_data_from_output_mappings": {
        "structured_output": "qualification_result",  // Add qualification results to passthrough
        "web_search_result": "qualification_citations"
      }
    },
    "step2_content_scoring": {
      "node_id": "step2_content_scoring", 
      "node_name": "llm",
      "private_input_mode": true,
      "private_output_mode": true,
      // Preserve original data + Step 1 results
      "private_output_passthrough_data_to_central_state_keys": [
        "linkedinUrl", "Company", "firstName", "lastName", "emailId", "jobTitle",
        "qualification_result", "qualification_citations"
      ],
      "write_to_private_output_passthrough_data_from_output_mappings": {
        "text_content": "contentq_analysis",  // Add content analysis to passthrough
        "web_search_result": "contentq_citations"
      }
    },
    "step3_talking_points": {
      "node_id": "step3_talking_points",
      "node_name": "llm", 
      "private_input_mode": true,
      "output_private_output_to_central_state": true,
      // Preserve all previous context through final step
      "private_output_passthrough_data_to_central_state_keys": [
        "linkedinUrl", "Company", "firstName", "lastName", "emailId", "jobTitle",
        "qualification_result", "qualification_citations",
        "contentq_analysis", "contentq_citations"
      ],
      "private_output_to_central_state_node_output_key": "final_talking_points"
    }
  }
}
```

**Progressive Context Flow:**
- **Step 1**: Preserves original lead data, adds qualification results
- **Step 2**: Preserves lead data + qualification results, adds content analysis  
- **Step 3**: Preserves all previous context, produces final output with complete history

**Final Result Structure:**
```json
{
  "final_talking_points": "Generated talking points...",
  "linkedinUrl": "https://linkedin.com/in/...",
  "Company": "Example Corp",
  "firstName": "John",
  "qualification_result": {...},
  "contentq_analysis": "...",
  // All context preserved through entire pipeline
}
```

## 10. Example Workflow: Lead Processing with Nested Data

**Goal:** Process lead data with complex nested structures, extract relevant information using dot notation, and create structured output for downstream systems.

```json
{
  "runtime_config": {
    "db_concurrent_pool_tier": "medium"
  },
  "nodes": {
    "input_node": {
      "node_id": "input_node", 
      "node_name": "input_node", 
      "node_config": {},
      "dynamic_output_schema": {
        "fields": {
          "lead_data": {
            "type": "object",
            "required": true,
            "default": {
              "contact_info": {
                "personal": { "first_name": "John", "last_name": "Smith", "email": "john@techcorp.com" },
                "professional": { "company": "TechCorp", "title": "Senior Engineer", "department": "Engineering" }
              },
              "social_media": {
                "linkedin": {
                  "profile_url": "https://linkedin.com/in/johnsmith",
                  "experience": [
                    {
                      "company": { "name": "TechCorp", "industry": "Software" },
                      "position": { "title": "Senior Engineer", "start_date": "2021-01" },
                      "achievements": ["Led team of 5", "Increased efficiency by 40%"]
                    }
                  ],
                  "skills": ["Python", "Machine Learning", "Leadership"]
                }
              },
              "research_data": {
                "company_info": {
                  "recent_news": [
                    { "headline": "TechCorp Raises $50M Series B", "sentiment": "positive", "date": "2024-01-15" }
                  ],
                  "financial_health": { "score": 85, "trend": "growing" }
                }
              }
            }
          }
        }
      },
      "edges": [
        {
          "dst_node_id": "structure_for_analysis",
          "mappings": [
            // Extract personal information using dot notation
            { "src_field": "lead_data.contact_info.personal.first_name", "dst_field": "analysis_input.lead.first_name" },
            { "src_field": "lead_data.contact_info.personal.last_name", "dst_field": "analysis_input.lead.last_name" },
            { "src_field": "lead_data.contact_info.personal.email", "dst_field": "analysis_input.lead.email" },
            
            // Extract professional information
            { "src_field": "lead_data.contact_info.professional.company", "dst_field": "analysis_input.lead.current_company" },
            { "src_field": "lead_data.contact_info.professional.title", "dst_field": "analysis_input.lead.job_title" },
            
            // Extract LinkedIn data with array access
            { "src_field": "lead_data.social_media.linkedin.experience.0.company.name", "dst_field": "analysis_input.lead.employer_details.name" },
            { "src_field": "lead_data.social_media.linkedin.experience.0.company.industry", "dst_field": "analysis_input.lead.employer_details.industry" },
            { "src_field": "lead_data.social_media.linkedin.experience.0.achievements.0", "dst_field": "analysis_input.lead.top_achievement" },
            { "src_field": "lead_data.social_media.linkedin.skills", "dst_field": "analysis_input.lead.technical_skills" },
            
            // Extract company research with nested access
            { "src_field": "lead_data.research_data.company_info.recent_news.0.headline", "dst_field": "analysis_input.context.latest_news" },
            { "src_field": "lead_data.research_data.company_info.recent_news.0.sentiment", "dst_field": "analysis_input.context.news_sentiment" },
            { "src_field": "lead_data.research_data.company_info.financial_health.score", "dst_field": "analysis_input.context.company_health_score" }
          ]
        }
      ]
    },
    "structure_for_analysis": {
      "node_id": "structure_for_analysis",
      "node_name": "transform_data",
      "node_config": {
        "mappings": [
          {
            "source_path": "analysis_input",
            "destination_path": "structured_lead_profile",
            "action": "restructure"
          }
        ]
      },
      "edges": [
        {
          "dst_node_id": "generate_talking_points",
          "mappings": [
            { "src_field": "structured_lead_profile", "dst_field": "lead_profile" }
          ]
        },
        {
          "dst_node_id": "$graph_state",
          "mappings": [
            // Store structured data in central state using nested paths
            { "src_field": "analysis_input.lead.first_name", "dst_field": "lead_summary.contact.first_name" },
            { "src_field": "analysis_input.lead.last_name", "dst_field": "lead_summary.contact.last_name" },
            { "src_field": "analysis_input.lead.current_company", "dst_field": "lead_summary.employment.company" },
            { "src_field": "analysis_input.context.company_health_score", "dst_field": "lead_summary.insights.company_score" }
          ]
        }
      ]
    },
    "generate_talking_points": {
      "node_id": "generate_talking_points",
      "node_name": "llm",
      "node_config": {
        "llm_config": {
          "model_spec": { "provider": "openai", "model": "gpt-4o" },
          "temperature": 0.7
        },
        "default_system_prompt": "Generate personalized talking points for sales outreach based on the lead profile provided."
      },
      "edges": [
        {
          "dst_node_id": "output_node",
          "mappings": [
            // Map LLM output with existing central state data
            { "src_field": "content", "dst_field": "final_output.talking_points" }
          ]
        }
      ]
    },
    "output_node": {
      "node_id": "output_node",
      "node_name": "output_node",
      "node_config": {}
    }
  },
  "edges": [
    // Additional edge from central state to output node
    {
      "src_node_id": "$graph_state",
      "dst_node_id": "output_node", 
      "mappings": [
        { "src_field": "lead_summary.contact", "dst_field": "final_output.lead_contact" },
        { "src_field": "lead_summary.employment", "dst_field": "final_output.lead_employment" },
        { "src_field": "lead_summary.insights", "dst_field": "final_output.lead_insights" }
      ]
    }
  ],
  "input_node_id": "input_node",
  "output_node_id": "output_node"
}
```

**Key Features Demonstrated:**

1. **Node-Level Edge Declaration**: The `input_node` and other nodes declare their outgoing edges directly in their configuration
2. **Complex Nested Data Access**: Using dot notation to extract deeply nested values like `lead_data.social_media.linkedin.experience.0.achievements.0`
3. **Array Element Access**: Accessing specific array elements with numeric indices
4. **Structured Data Creation**: Creating organized nested structures in destination fields
5. **Central State Integration**: Combining node outputs with central state data for final output

**Data Flow Summary:**
- Input provides complex nested lead data
- First transformation extracts and restructures data using dot notation
- Data flows through LLM processing while maintaining structure in central state  
- Final output combines processed content with preserved lead metadata

## 11. Example Workflow: Customer Support Ticket Routing

**Goal:** Receive a support ticket, determine its topic using an LLM, and route it to the correct department, storing the ticket data using runtime context.

```json
{
  "runtime_config": {
    "db_concurrent_pool_tier": "medium" // Use medium tier for moderate database operations
  },
  "nodes": {
    "input_node": { // Receives: { "ticket_id": "...", "ticket_body": "..." }
      "node_id": "input_node", "node_name": "input_node", "node_config": {}
    },
    "build_prompt": { // Uses PromptConstructor for loading AND construction
      "node_id": "build_prompt",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
           "classifier_task": { // Key for organization
             "id": "llm_user_prompt", // Output field name
             "template_load_config": { // Load the template from DB
               "path_config": {
                 "static_name": "support_topic_classifier",
                 "static_version": "1.0"
               }
             },
             "variables": { "body": null } // Mark 'body' as required input
           }
         }
      },
      // Explicit schemas recommended
      "dynamic_input_schema": { "fields": { "body": { "type": "str", "required": true } } },
      "dynamic_output_schema": { "fields": { "llm_user_prompt": { "type": "str", "required": true }, "prompt_template_errors": { "type": "list", "required": false } } }
    },
    "determine_topic_llm": {
      "node_id": "determine_topic_llm", "node_name": "llm",
      "node_config": {
        "llm_config": { "model_spec": { "provider": "openai", "model": "gpt-3.5-turbo" }, "temperature": 0.1 },
        "output_schema": { // Expect structured output matching this spec
          "dynamic_schema_spec": {
            "schema_name": "TopicResult",
            "fields": { "topic": { "type": "enum", "enum_values": ["Billing", "Technical", "Account", "General Inquiry"], "required": true } }
          }
        }
      }
    },
    "routing_decision": {
      "node_id": "routing_decision", "node_name": "router_node",
      "node_config": {
        "choices": ["billing_queue", "tech_queue", "account_queue", "general_queue"],
        "allow_multiple": false,
        "choices_with_conditions": [
          // NOTE: Using structured_output.topic notation requires adapter/node support
          { "choice_id": "billing_queue", "input_path": "topic_from_llm.topic", "target_value": "Billing" },
          { "choice_id": "tech_queue", "input_path": "topic_from_llm.topic", "target_value": "Technical" },
          { "choice_id": "account_queue", "input_path": "topic_from_llm.topic", "target_value": "Account" },
          { "choice_id": "general_queue", "input_path": "topic_from_llm.topic", "target_value": "General Inquiry" }
        ]
      }
    },
    // Store nodes configuration - these use runtime context for org/user and service access
    "billing_queue": {
      "node_id": "billing_queue", "node_name": "store_customer_data",
      "node_config": {
        "store_configs": [{
          "input_field_path": "original_ticket", // Get data from central state
          "target_path": { "filename_config": { "static_namespace": "tickets_billing", "input_docname_field": "original_ticket.id" } }
          // versioning/schema defaults are likely sufficient (upsert unversioned)
        }]
      }
    },
    "tech_queue": {
      "node_id": "tech_queue", "node_name": "store_customer_data",
      "node_config": {
        "store_configs": [{
          "input_field_path": "original_ticket",
          "target_path": { "filename_config": { "static_namespace": "tickets_tech", "input_docname_field": "original_ticket.id" } }
        }]
      }
    },
    "account_queue": {
      "node_id": "account_queue", "node_name": "store_customer_data",
      "node_config": {
        "store_configs": [{
          "input_field_path": "original_ticket",
          "target_path": { "filename_config": { "static_namespace": "tickets_account", "input_docname_field": "original_ticket.id" } }
        }]
      }
    },
    "general_queue": {
      "node_id": "general_queue", "node_name": "store_customer_data",
      "node_config": {
        "store_configs": [{
          "input_field_path": "original_ticket",
          "target_path": { "filename_config": { "static_namespace": "tickets_general", "input_docname_field": "original_ticket.id" } }
        }]
      }
    }
  },
  "edges": [
    // Input -> Build Prompt (Provide the required 'body' variable)
    { "src_node_id": "input_node", "dst_node_id": "build_prompt", "mappings": [ { "src_field": "ticket_body", "dst_field": "body" } ] },
    // Build Prompt -> LLM (Use the 'id' from the config as src_field)
    { "src_node_id": "build_prompt", "dst_node_id": "determine_topic_llm", "mappings": [ { "src_field": "llm_user_prompt", "dst_field": "user_prompt" } ] },
    // LLM -> Router (Map the structured output to a field the router expects)
    { "src_node_id": "determine_topic_llm", "dst_node_id": "routing_decision", "mappings": [ { "src_field": "structured_output", "dst_field": "topic_from_llm" } ] },

    // State management: Store original ticket data in central state for later retrieval by store nodes
    { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "ticket_id", "dst_field": "original_ticket.id" },
        { "src_field": "ticket_body", "dst_field": "original_ticket.body" }
        // Add other relevant ticket fields if needed by store nodes
      ]
    },
    // State management: Read original ticket data from central state for store nodes
    // Note: These edges ONLY provide data, they DON'T trigger the store nodes. The router does.
    { "src_node_id": "$graph_state", "dst_node_id": "billing_queue", "mappings": [ { "src_field": "original_ticket", "dst_field": "original_ticket" } ] },
    { "src_node_id": "$graph_state", "dst_node_id": "tech_queue", "mappings": [ { "src_field": "original_ticket", "dst_field": "original_ticket" } ] },
    { "src_node_id": "$graph_state", "dst_node_id": "account_queue", "mappings": [ { "src_field": "original_ticket", "dst_field": "original_ticket" } ] },
    { "src_node_id": "$graph_state", "dst_node_id": "general_queue", "mappings": [ { "src_field": "original_ticket", "dst_field": "original_ticket" } ] },

    // Router -> Queue Nodes (Control flow only, data comes from $graph_state edges above)
    { "src_node_id": "routing_decision", "dst_node_id": "billing_queue" },
    { "src_node_id": "routing_decision", "dst_node_id": "tech_queue" },
    { "src_node_id": "routing_decision", "dst_node_id": "account_queue" },
    { "src_node_id": "routing_decision", "dst_node_id": "general_queue" }
  ],
  "input_node_id": "input_node",
  "output_node_id": "general_queue" // Example end point - could also be a dedicated output node collecting results
}
```

## 11. Example Workflow: Data Enrichment and Summarization

**Goal:** Load user data based on IDs from input, load related company data, join them, filter out inactive users, and generate a summary using an LLM. Runtime context is used by `load_customer_data`.

```json
{
  "runtime_config": {
    "db_concurrent_pool_tier": "large" // Use large tier for heavy data operations and joins
  },
  "nodes": {
    "input_node": { // Receives: { "user_ids": ["u1", "u2", ...], "filter_status": "active" }
      "node_id": "input_node", "node_name": "input_node", "node_config": {}
    },
    "load_users": { // Load user data for each ID (requires MapListRouter or custom logic)
      "node_id": "load_users", "node_name": "load_customer_data",
      "node_config": {
        "load_paths": [
          {
            // Assumes input is {"user_id": "uX"} for each item after mapping/routing
            "filename_config": { "static_namespace": "users", "input_docname_field": "user_id" },
            "output_field_name": "user_profile"
          }
        ]
      },
      // NOTE: This example simplifies list processing. A MapListRouter node would typically precede
      // this node to iterate over 'user_ids' from the input_node, mapping each ID to the
      // 'user_id' field expected by filename_config. This node would then run once per user ID.
      // Output shown below assumes aggregation after parallel runs.
      // Assumed aggregated output: { "user_profiles": [ { "id": "u1", ... }, ... ] }
    },
    "load_companies": { // Load company data (uses runtime context)
      "node_id": "load_companies", "node_name": "load_customer_data",
      "node_config": {
        "load_paths": [ { "filename_config": { "static_namespace": "companies", "static_docname": "all_company_data" }, "output_field_name": "company_list" } ]
      }
    },
    "join_data": {
      "node_id": "join_data", "node_name": "data_join_data",
      "node_config": {
        "joins": [
          {
            "primary_list_path": "user_profiles", // List from load_users output
            "secondary_list_path": "company_list", // List from load_companies output
            "primary_join_key": "company_id", // Field in user profile
            "secondary_join_key": "id", // Field in company data
            "output_nesting_field": "company_info", // Add company data here
            "join_type": "one_to_one" // Or appropriate type
          }
        ],
        "output_field_name": "joined_user_list" // Name of the output list field
      }
    },
    "filter_by_status": { // Filter using status provided in initial workflow input
      "node_id": "filter_by_status", "node_name": "filter_data",
      "node_config": {
        "targets": [
          {
            "filter_target": "joined_user_list", // Input list field name (after mapping)
            "filter_mode": "allow", // Keep matching items
            "condition_groups": [ { "conditions": [ { "field": "status", "operator": "equals", "input_value_path": "status_to_filter" } ] } ] // Compare user status to input value
          }
        ],
         "output_field_name": "filtered_users" // Name of the output field containing the filtered list
      }
    },
    "transform_to_json": { // Node to convert filtered list to JSON string for LLM
      "node_id": "transform_to_json", "node_name": "transform_data", // Assuming a node that can stringify
      "node_config": {
        "mappings": [
          { "source_path": "filtered_users", "destination_path": "user_data_json", "action": "stringify" }
         ]
      }
    },
    "build_summary_prompt": {
      "node_id": "build_summary_prompt",
      "node_name": "prompt_constructor",
      "node_config": {
         "prompt_templates": {
           "summary_task": {
             "id": "summary_prompt", // Output field name
             "template_load_config": { /* ... Config to load template from DB ... */ },
             "variables": { "user_data_json": null } // Mark as required input
           }
         }
      },
      "dynamic_input_schema": { "fields": { "user_data_json": { "type": "str", "required": true } } },
      "dynamic_output_schema": { "fields": { "summary_prompt": { "type": "str", "required": true }, "prompt_template_errors": { "type": "list", "required": false } } }
    },
    "generate_summary": {
      "node_id": "generate_summary", "node_name": "llm",
      "node_config": { "llm_config": { "model_spec": { "provider": "openai", "model": "gpt-4-turbo" } } }
    },
    "output_node": {
      "node_id": "output_node", "node_name": "output_node", "node_config": {}
    }
  },
  "edges": [
    // Input to Load/Filter nodes
    // Note: For list processing, 'input_node' -> MapListRouter -> 'load_users' would be needed.
    // Edges below assume 'load_users' magically handles the list or aggregation occurs.
    { "src_node_id": "input_node", "dst_node_id": "load_users", "mappings": [ { "src_field": "user_ids", "dst_field": "user_ids_list" } ] }, // Simplified
    { "src_node_id": "input_node", "dst_node_id": "filter_by_status", "mappings": [ { "src_field": "filter_status", "dst_field": "status_to_filter" } ] },

    // Data loading and joining
    { "src_node_id": "load_users", "dst_node_id": "join_data", "mappings": [ { "src_field": "user_profiles", "dst_field": "user_profiles" } ] }, // List of loaded profiles
    { "src_node_id": "load_companies", "dst_node_id": "join_data", "mappings": [ { "src_field": "company_list", "dst_field": "company_list" } ] },

    // Joiner -> Filter (Pass the joined list)
    { "src_node_id": "join_data", "dst_node_id": "filter_by_status", "mappings": [ { "src_field": "joined_user_list", "dst_field": "joined_user_list" } ] },

    // Filter -> Transform (Pass the filtered list)
    { "src_node_id": "filter_by_status", "dst_node_id": "transform_to_json", "mappings": [ { "src_field": "filtered_users", "dst_field": "filtered_users" } ] },

    // Transform -> Build Prompt (Provide JSON string)
    { "src_node_id": "transform_to_json", "dst_node_id": "build_summary_prompt", "mappings": [ { "src_field": "user_data_json", "dst_field": "user_data_json" } ] },

    // Prompt Builder -> LLM
    { "src_node_id": "build_summary_prompt", "dst_node_id": "generate_summary", "mappings": [ { "src_field": "summary_prompt", "dst_field": "user_prompt" } ] },

    // LLM -> Output
    { "src_node_id": "generate_summary", "dst_node_id": "output_node", "mappings": [ { "src_field": "content", "dst_field": "final_summary" } ] }
  ],
  "input_node_id": "input_node",
  "output_node_id": "output_node"
}
```
*(Note: Example 2 still simplifies list processing. A `MapListRouterNode` would typically be used before `load_users` to handle the list of `user_ids`.)*

## 12. Tips and Best Practices

### General Workflow Design
-   **Plan First:** Sketch your workflow logic before writing the JSON.
-   **Use Meaningful IDs:** Choose descriptive `node_id`s.
-   **Start Simple:** Build and test core paths first.
-   **Handle Errors:** Consider error paths and logging.
-   **Test Thoroughly:** Use various inputs and edge cases.
-   **Keep it Readable:** Use comments or separate documentation.

### Data Mapping and Dot Notation (NEW)
-   **Leverage Dot Notation:** Use dot notation extensively to avoid unnecessary data transformation nodes. Instead of creating intermediate nodes just to restructure data, use nested field mappings directly in edges.
-   **Validate Nested Paths:** Ensure `src_field` paths exist in source data and `dst_field` paths create the desired structure. The system automatically creates nested structures, but verify your path syntax.
-   **Array Access Patterns:** When accessing array elements, consider bounds checking. Use `items.0.field` for the first element, but ensure your data has at least one item.
-   **Complex Extraction Examples:** For API responses, use patterns like `api_response.data.results.0.metadata.score` to extract deeply nested values directly without preprocessing.
-   **Structured Output Creation:** Use dot notation in `dst_field` to create organized input structures for downstream nodes (e.g., `analysis_input.candidate.profile.name`).

### Edge Declaration Options (NEW)
-   **Choose Edge Declaration Style:** Use node-level edge declaration (`edges` field in node config) for better organization when a node has many outgoing edges. Use global `edges` list for complex multi-node interactions.
-   **Consistency:** Don't mix edge declaration styles for the same node - choose either node-level or global, not both.

### Node Configuration
-   **Consult Node Guides:** Each node has unique `node_config` requirements.
-   **Validate Mappings:** For nodes using path lookups (like `construct_options`), ensure the *container object* holding the start of the path is mapped correctly.
-   **Explicit Schemas:** Define `dynamic_input_schema` and `dynamic_output_schema` for nodes like `PromptConstructorNode`, `InputNode`, `OutputNode`, `HITLNode` for better validation and clarity.

### Resource Management
-   **Leverage Runtime Context:** Avoid passing user/org IDs via mappings; rely on the runtime context (Section 6) for nodes that need it (e.g., `load/store/load_multiple_customer_data`).
-   **Choose Appropriate Database Pool Tier:** Consider your workflow's database usage intensity when setting `db_concurrent_pool_tier` in `runtime_config` (Section 2.1). Use "small" for simple workflows, "medium" for moderate database operations, and "large" for data-intensive workflows with heavy parallel processing.
-   **Check External Service Costs:** Be mindful of nodes like `LinkedInScrapingNode` that consume external resources (like API credits) based on configuration and usage. Use `test_mode` where available for validation without incurring costs.

### Data Flow Strategy
-   **Choose Optimal Data Flow Method:** 
    - **Data-Only Edges**: For large datasets to specific downstream nodes (memory efficient)
    - **Central State**: For shared/persistent data accessed by multiple nodes
    - **Direct Mappings**: For sequential node-to-node flow
-   **Memory Optimization:** Use data-only edges to avoid storing large datasets in central state, reducing RAM usage and storage requirements
-   **Selective Data Distribution:** Use data-only edges when multiple downstream nodes need different subsets of data from the same source
-   **Nested Central State:** Organize central state data using nested structures (e.g., `lead_analysis.quality.score`) for better data organization and easier access
-   **Use `MergeAggregateNode` for Consolidation:** When needing to combine data from multiple potentially overlapping sources into a single structure with specific rules for conflict resolution (beyond simple joins), use the `MergeAggregateNode`

### Model and Service Integration  
-   **Check Model Capabilities:** Verify LLM features before configuring them.
-   **Structured Output Mapping:** When using LLM structured output, use dot notation to access specific fields (e.g., `structured_output.analysis.confidence_score`) rather than passing entire objects.

### Advanced Patterns
-   **Error Handling:** The dot notation system provides automatic error handling for missing paths, but design your workflow to handle cases where expected nested data might not exist.
-   **Performance Considerations:** Dot notation parsing is efficient, but extremely deep nesting (10+ levels) may impact performance. Consider restructuring very complex nested paths.

## 13. Conclusion

Building workflows involves defining nodes (tasks) and edges (connections/data flow) within a `GraphSchema`. By understanding node configurations (especially the versatile `PromptConstructorNode`), mastering edge mappings, leveraging the runtime context for implicit information like user/org context and service access, and utilizing patterns for logic and data handling, you can create sophisticated automations. Always refer to the specific node documentation and start with simpler flows.

