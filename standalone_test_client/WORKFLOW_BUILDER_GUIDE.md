# Workflow Builder Guide for Claude

This guide provides a comprehensive reference for building KiwiQ workflows. It consolidates core concepts, patterns, and best practices to help efficiently create and debug workflows.

---

## 📋 Table of Contents

1. [Quick Start Overview](#quick-start-overview)
2. [Core Concepts](#core-concepts)
3. [GraphSchema Structure](#graphschema-structure)
4. [Available Node Types](#available-node-types)
5. [Edge Mapping Patterns](#edge-mapping-patterns)
6. [Data Flow Strategies](#data-flow-strategies)
7. [Common Workflow Patterns](#common-workflow-patterns)
8. [Runtime Configuration](#runtime-configuration)
9. [Advanced Features](#advanced-features)
10. [Best Practices & Gotchas](#best-practices--gotchas)
11. [Debugging Tips](#debugging-tips)

---

## Quick Start Overview

### What is a Workflow?

A workflow is an automated sequence of tasks (nodes) connected by edges that define execution flow and data transfer. The entire workflow is configured declaratively using a `GraphSchema` JSON object.

```
┌────────┐    ┌───────────┐    ┌───────────┐    ┌─────────┐
│  Input │───►│  Process  │───►│   HITL    │───►│  Output │
└────────┘    └───────────┘    └───────────┘    └─────────┘
```

### Key Components

- **Nodes**: Processing units that perform specific tasks (LLM calls, data transformations, routing, etc.)
- **Edges**: Connections that define execution order and data flow between nodes
- **Central State**: Shared memory accessible by all nodes for data persistence
- **GraphSchema**: JSON configuration defining the entire workflow structure

---

## Core Concepts

### 1. Nodes: The Building Blocks

Each node has three key aspects:

1. **Input Schema**: Defines expected input data structure
2. **Process Logic**: The actual computation/action performed
3. **Output Schema**: Defines produced output data structure

**Node Configuration Structure:**

```json
{
  "node_id": "unique_instance_id",
  "node_name": "registered_node_type",
  "node_config": {
    // Node-specific configuration
  },
  // Advanced options
  "private_input_mode": false,
  "private_output_mode": false,
  "dynamic_input_schema": null,
  "dynamic_output_schema": null
}
```

### 2. Schemas: Static vs Dynamic

**Static Schemas**: Fixed, predefined structure (e.g., `llm` node always expects `user_prompt`, `messages_history`)

**Dynamic Schemas**: Adapt based on connections/configuration
- `InputNode`: Output schema defined by outgoing edge mappings
- `OutputNode`: Input schema defined by incoming edge mappings
- `HITLNode`: Often uses dynamic schemas for flexible review workflows
- `PromptConstructorNode`: Dynamic based on templates and variables

**Best Practice**: Always define `dynamic_input_schema` and `dynamic_output_schema` explicitly for clarity and validation.

### 3. Edges: Connecting the Flow

Edges serve two purposes:
1. **Execution Control**: Define which node runs after which
2. **Data Transfer**: Map output fields from source to input fields in destination

**Edge Definition Locations:**
- **Global `edges` list**: Traditional approach, good for complex multi-source patterns
- **Node-level `edges` field**: NEW - Better organization for nodes with many outputs

```json
// Global edge definition
{
  "edges": [
    {
      "src_node_id": "source_node",
      "dst_node_id": "target_node",
      "mappings": [
        {"src_field": "output_name", "dst_field": "input_name"}
      ]
    }
  ]
}

// Node-level edge definition (NEW)
{
  "nodes": {
    "source_node": {
      "node_id": "source_node",
      "edges": [
        {
          "dst_node_id": "target_node",
          "mappings": [
            {"src_field": "output_name", "dst_field": "input_name"}
          ]
        }
      ]
    }
  }
}
```

**Important**: Don't mix edge declaration styles for the same node.

### 4. Central State (`$graph_state`)

The central state is a shared data repository accessible by all nodes throughout workflow execution.

**When to Use Central State:**
- Data persistence across loop iterations (e.g., conversation history)
- Sharing data between non-adjacent nodes
- Tracking global workflow state (e.g., iteration counts, approval status)

**Reducers**: Control how data is combined when multiple nodes write to the same state key
- `replace` (default): Overwrites previous value
- `add_messages`: For message history (appends correctly)
- `append_list`: Adds to existing lists
- `merge_dicts`: Combines dictionaries

```json
{
  "metadata": {
    "$graph_state": {
      "reducers": {
        "messages_history": "add_messages",
        "approved": "replace",
        "iteration_count": "replace"
      }
    }
  }
}
```

---

## GraphSchema Structure

The complete workflow blueprint:

```json
{
  "nodes": {
    "node_id_1": {
      "node_id": "node_id_1",
      "node_name": "node_type",
      "node_config": {}
    }
  },
  "edges": [
    {
      "src_node_id": "node_id_1",
      "dst_node_id": "node_id_2",
      "mappings": []
    }
  ],
  "input_node_id": "input_node",
  "output_node_id": "output_node",
  "runtime_config": {
    "db_concurrent_pool_tier": "medium"
  },
  "metadata": {
    "$graph_state": {
      "reducers": {}
    }
  }
}
```

### Required Fields
- `nodes`: Dictionary of all node instances
- `edges`: List of connections (or use node-level `edges`)
- `input_node_id`: Workflow entry point
- `output_node_id`: Workflow exit point

### Optional Fields
- `runtime_config`: Performance settings (see [Runtime Configuration](#runtime-configuration))
- `metadata`: Advanced settings like reducers

---

## Available Node Types

For detailed configuration of each node, refer to the linked guide in `/workflow_service_docs/workflow_builder_guides/nodes/`.

### Core & Flow Control

| Node Type | Purpose | Guide Link |
|-----------|---------|------------|
| `input_node` | Workflow entry point | [core_dynamic_nodes_guide.md](workflow_service_docs/workflow_builder_guides/nodes/core_dynamic_nodes_guide.md) |
| `output_node` | Workflow exit point | [core_dynamic_nodes_guide.md](workflow_service_docs/workflow_builder_guides/nodes/core_dynamic_nodes_guide.md) |
| `hitl_node__default` | Human-in-the-loop review | [core_dynamic_nodes_guide.md](workflow_service_docs/workflow_builder_guides/nodes/core_dynamic_nodes_guide.md) |

### Routing & Conditionals

| Node Type | Purpose | Guide Link |
|-----------|---------|------------|
| `if_else_condition` | Evaluates conditions | [if_else_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/if_else_node_guide.md) |
| `router_node` | Routes based on data values | [dynamic_router_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/dynamic_router_node_guide.md) |
| `map_list_router_node` | Parallel list processing | [map_list_router_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/map_list_router_node_guide.md) |

### Data Operations

| Node Type | Purpose | Guide Link |
|-----------|---------|------------|
| `filter_data` | Filter data by conditions | [filter_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/filter_node_guide.md) |
| `transform_data` | Restructure/rename fields | [transform_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/transform_node_guide.md) |
| `data_join_data` | Join datasets by keys | [data_join_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/data_join_node_guide.md) |
| `merge_aggregate` | Merge with conflict resolution | [merge_aggregate_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/merge_aggregate_node_guide.md) |

### Data Storage

| Node Type | Purpose | Guide Link |
|-----------|---------|------------|
| `load_customer_data` | Fetch stored documents | [load_customer_data_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/load_customer_data_node_guide.md) |
| `store_customer_data` | Save documents to storage | [store_customer_data_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/store_customer_data_node_guide.md) |
| `load_multiple_customer_data` | Batch load documents | [load_multiple_customer_data_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/load_multiple_customer_data_node_guide.md) |
| `delete_customer_data` | Remove stored documents | [delete_customer_data_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/delete_customer_data_node_guide.md) |

### LLM & Prompts

| Node Type | Purpose | Guide Link |
|-----------|---------|------------|
| `llm` | AI model interactions | [llm_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/llm_node_guide.md) |
| `prompt_constructor` | Build prompts from templates | [prompt_constructor_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/prompt_constructor_node_guide.md) |
| `prompt_loader` | (Deprecated - use constructor) | [prompt_loader_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/prompt_loader_node_guide.md) |

### External Services

| Node Type | Purpose | Guide Link |
|-----------|---------|------------|
| `linkedin_scraping` | LinkedIn data extraction | [linkedin_scraping_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/linkedin_scraping_node_guide.md) |
| `crawler_scraper` | Web crawling/scraping | [crawler_scraper_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/crawler_scraper_node_guide.md) |
| `workflow_runner` | Execute child workflows | [workflow_runner_node_guide.md](workflow_service_docs/workflow_builder_guides/nodes/workflow_runner_node_guide.md) |

---

## Edge Mapping Patterns

### 1. Dot Notation Support (NEW FEATURE)

**Full dot notation** is now supported in edge mappings for accessing nested data:

```json
{
  "mappings": [
    // Object property access
    {"src_field": "user.profile.email", "dst_field": "contact.email"},

    // Array element access
    {"src_field": "results.0.title", "dst_field": "top_result"},

    // Deep nesting
    {"src_field": "api_data.items.0.metadata.score", "dst_field": "quality_score"},

    // Creating nested structures
    {"src_field": "simple_value", "dst_field": "nested.output.value"}
  ]
}
```

**Benefits:**
- Eliminate many `transform_data` nodes
- Direct API response processing
- Cleaner, more maintainable workflows

### 2. Data-Only Edges (NEW FEATURE)

Pass large datasets efficiently without affecting execution flow:

```json
{
  "src_node_id": "load_large_data",
  "dst_node_id": "analysis_node",
  "data_only_edge": true,  // KEY: Data only, no execution trigger
  "mappings": [
    {"src_field": "large_dataset", "dst_field": "analysis_data"}
  ]
}
```

**When to Use:**
- Large datasets (>10MB)
- Data needed by non-consecutive nodes
- Avoiding central state storage overhead

**Key Points:**
- Does NOT trigger destination node execution
- Data available when node executes via regular edges
- Reduces memory and storage requirements

### 3. Central State Patterns

**Writing to Central State:**
```json
{
  "src_node_id": "processor",
  "dst_node_id": "$graph_state",
  "mappings": [
    {"src_field": "results.score", "dst_field": "analysis.quality.score"},
    {"src_field": "metadata.time", "dst_field": "metrics.timing.duration"}
  ]
}
```

**Reading from Central State:**
```json
{
  "src_node_id": "$graph_state",
  "dst_node_id": "consumer",
  "mappings": [
    {"src_field": "analysis.quality.score", "dst_field": "input_score"}
  ]
}
```

---

## Data Flow Strategies

### Choose the Right Approach

| Strategy | Use Case | Memory Impact | Complexity |
|----------|----------|---------------|------------|
| **Direct Edge Mapping** | Sequential node-to-node flow | Low | Simple |
| **Central State** | Shared/persistent data, loops | Medium | Simple |
| **Data-Only Edges** | Large data, specific targets | Very Low | Medium |

### Example: Optimized Large Data Flow

```json
{
  "nodes": {
    "load_data": {"node_id": "load_data", "node_name": "load_customer_data"},
    "validate": {"node_id": "validate", "node_name": "filter_data"},
    "analyze": {"node_id": "analyze", "node_name": "llm"}
  },
  "edges": [
    // Regular flow: load -> validate -> analyze
    {"src_node_id": "load_data", "dst_node_id": "validate", "mappings": [
      {"src_field": "summary", "dst_field": "data_summary"}
    ]},
    {"src_node_id": "validate", "dst_node_id": "analyze", "mappings": [
      {"src_field": "status", "dst_field": "validation_status"}
    ]},

    // Data-only: Pass full dataset directly to analysis (skip central state)
    {
      "src_node_id": "load_data",
      "dst_node_id": "analyze",
      "data_only_edge": true,
      "mappings": [{"src_field": "full_dataset", "dst_field": "data_to_analyze"}]
    }
  ]
}
```

---

## Common Workflow Patterns

### 1. AI-Human Feedback Loop

```
Input -> LLM -> HITL -> Router -> [Approved: Output | Rejected: back to LLM]
```

**Key Elements:**
- Use central state for `messages_history` with `add_messages` reducer
- Router checks HITL approval status
- Loop back to LLM with `review_comments` from central state

### 2. Conditional Branching

```
Input -> IfElseCondition -> Router -> [Branch A | Branch B] -> Output
```

**Key Elements:**
- `IfElseConditionNode` outputs `branch` field ("true_branch" or "false_branch")
- Router routes based on `branch` value
- Define edges to both branches

### 3. Parallel List Processing

```
Load List -> MapListRouter -> [Process Item (parallel)] -> Aggregate
```

**Key Elements:**
- `MapListRouterNode` distributes items
- Destination nodes use `private_input_mode: true`
- Use passthrough data to preserve item IDs/metadata
- Configure reducers for aggregation (e.g., `append_list`, `collect_values`)

**Most Common Pattern (from real workflows):**

```json
{
  "process_item": {
    "node_name": "llm",
    "private_input_mode": true,
    "output_private_output_to_central_state": true,
    // Preserve ID and metadata from INPUT state
    "private_output_passthrough_data_to_central_state_keys": ["id", "name"],
    "private_output_to_central_state_node_output_key": "output"
  }
}
```

Result aggregation: `[{output: "result1", id: "item_1", name: "Title"}, ...]`

### 4. Multi-Stage Processing Pipeline

```
Input -> Stage1 (Qualification) -> Stage2 (Analysis) -> Stage3 (Output)
```

**Progressive Context Pattern:**
```json
{
  "stage1": {
    "private_output_passthrough_data_to_central_state_keys": ["id", "company"],
    "write_to_private_output_passthrough_data_from_output_mappings": {
      "structured_output": "stage1_results"
    }
  },
  "stage2": {
    "private_output_passthrough_data_to_central_state_keys": [
      "id", "company", "stage1_results"  // Preserve previous context
    ],
    "write_to_private_output_passthrough_data_from_output_mappings": {
      "text_content": "stage2_results"  // Add new results
    }
  }
}
```

### 5. Data Enrichment & Joining

```
Input -> LoadUser -> LoadCompany -> DataJoin -> Filter -> Output
```

**Key Elements:**
- Multiple `load_customer_data` nodes fetch different datasets
- `data_join_data` combines based on join keys
- `filter_data` applies business logic
- Use runtime context for org/user permissions

---

## Runtime Configuration

### Database Pool Tiers

Configure database connection pooling based on workflow intensity:

```json
{
  "runtime_config": {
    "db_concurrent_pool_tier": "medium"  // "small" | "medium" | "large"
  }
}
```

| Tier | Max Connections | Use Case |
|------|----------------|----------|
| `small` | Default pool | Simple workflows, development, minimal DB usage |
| `medium` | 25 connections | 10-25 concurrent DB operations, moderate processing |
| `large` | 50 connections | 25+ concurrent operations, data-intensive workflows |

**Guidelines:**
- Default to `small` for simple workflows
- Use `medium` for production workflows with parallel operations
- Use `large` only for heavy data processing with high concurrency
- Monitor database connection usage to optimize tier selection

### Runtime Context

Nodes automatically receive runtime context with:
- **Application Context**: Current user, org ID, workflow run details
- **External Context Manager**: Database connections, service clients, registries

**Benefits:**
- No need to pass `user_id`/`org_id` through edges
- Automatic permission enforcement
- Centralized service access

**Nodes Using Runtime Context:**
- `load_customer_data`
- `store_customer_data`
- `load_multiple_customer_data`
- `delete_customer_data`

---

## Advanced Features

### 1. Private Mode & Passthrough Data

**Purpose**: Preserve context data through parallel processing branches

**Key Configuration:**

```json
{
  "private_input_mode": true,  // Receive data directly from router
  "output_private_output_to_central_state": true,  // Send results to central state

  // Keys from INPUT state to preserve and pass forward
  "private_output_passthrough_data_to_central_state_keys": ["id", "name"],

  // Key for node output in central state
  "private_output_to_central_state_node_output_key": "output",

  // Map passthrough data to input fields (supports dot notation)
  "read_private_input_passthrough_data_to_input_field_mappings": {
    "user.profile.name": "display_name"
  },

  // Map output fields to passthrough data (supports dot notation)
  "write_to_private_output_passthrough_data_from_output_mappings": {
    "result.user_id": "context.user.id"
  }
}
```

**Critical Insight**: `private_output_passthrough_data_to_central_state_keys` preserves data from node's **INPUT** state, not output.

### 2. Iteration Limiting Pattern

Prevent infinite HITL loops:

```python
MAX_ITERATIONS = 10

# Add check_iteration_limit node
"check_iteration_limit": {
    "node_name": "if_else_condition",
    "node_config": {
        "tagged_conditions": [{
            "tag": "iteration_limit_check",
            "condition_groups": [{
                "logical_operator": "and",
                "conditions": [{
                    "field": "generation_metadata.iteration_count",  # Dot notation
                    "operator": "less_than",
                    "value": MAX_ITERATIONS
                }]
            }]
        }]
    }
}
```

### 3. Structured LLM Output

Configure LLM to produce structured JSON:

```json
{
  "llm_node": {
    "node_config": {
      "output_schema": {
        "dynamic_schema_spec": {
          "schema_name": "AnalysisResult",
          "fields": {
            "quality_score": {"type": "int", "required": true},
            "confidence": {"type": "float", "required": true},
            "recommendations": {"type": "list", "items_type": "str"}
          }
        }
      }
    }
  }
}
```

Access fields: `structured_output.quality_score`, `structured_output.recommendations.0`

### 4. System Variables in Prompt Constructor

**Purpose**: System-provided variables that are automatically populated by the workflow runtime

**Available System Variables:**

System variables are prefixed with `$` and include:

| Variable | Description | Common Use Cases |
|----------|-------------|------------------|
| `$current_date` | Current date in ISO format | Timestamps, date-aware content generation |
| `$current_datetime` | Current date and time | Detailed timestamps, scheduling |
| `$graph_state` | Reference to central state | Advanced state operations |

**Critical Configuration Rules:**

```json
{
  "prompt_constructor_node": {
    "node_config": {
      "prompt_templates": {
        "my_prompt": {
          "template": "Today is {current_datetime}. Generate content for {topic}.",
          "variables": {
            "current_datetime": "$current_date",  // System variable - note the $ prefix
            "topic": None                          // Regular variable
          },
          "construct_options": {
            // System variables ($) do NOT need construct_options mapping
            "topic": "topic"  // Only regular variables need mapping
          }
        }
      }
    }
  }
}
```

**Key Points:**

1. **System Variables Do NOT Need:**
   - `construct_options` mappings
   - Incoming edges providing data
   - Entries in central state

2. **System Variables Are:**
   - Automatically populated by the runtime
   - Always prefixed with `$` in the variables dict
   - Available throughout workflow execution

3. **Common Mistake to Avoid:**
   ```json
   // ❌ WRONG - Don't add system variables to construct_options
   "construct_options": {
     "current_datetime": "$current_date"  // This is unnecessary and incorrect
   }

   // ✅ CORRECT - System variables only in variables dict
   "variables": {
     "current_datetime": "$current_date"  // System handles this automatically
   }
   ```

**Example Usage:**

```json
{
  "construct_content_prompt": {
    "node_id": "construct_content_prompt",
    "node_name": "prompt_constructor",
    "node_config": {
      "prompt_templates": {
        "content_prompt": {
          "id": "content_prompt",
          "template": "Create content for {topic} as of {current_date}. Use company info: {company_doc}",
          "variables": {
            "current_date": "$current_date",    // System variable
            "topic": None,                       // Regular variable
            "company_doc": None                  // Regular variable
          },
          "construct_options": {
            // Only map regular variables, NOT system variables
            "topic": "selected_topic",
            "company_doc": "company_context"
          }
        }
      }
    }
  }
}
```

**Validation Note**: When validating workflows, system variables should be excluded from:
- Edge mapping validation
- construct_options completeness checks
- Data source availability checks

This prevents false positive errors when analyzing workflow configurations.

---

## Best Practices & Gotchas

### ✅ Do's

1. **Leverage Dot Notation**: Use extensively for nested data access instead of transform nodes
2. **Explicit Dynamic Schemas**: Always define `dynamic_input_schema` and `dynamic_output_schema` for dynamic nodes
3. **Choose Right Pool Tier**: Match database tier to workflow intensity
4. **Use Data-Only Edges**: For large datasets to avoid memory overhead
5. **Organize Central State**: Use nested keys (e.g., `analysis.quality.score`) for clarity
6. **Test with Various Inputs**: Verify workflows handle edge cases
7. **Consult Node Guides**: Always check specific node documentation for configuration details

### ❌ Don'ts

1. **Don't Mix Edge Declaration Styles**: Use either node-level OR global edges for a node, not both
2. **Don't Overuse Central State**: Direct edge mappings are clearer for sequential flow
3. **Don't Forget Reducers**: Using default `replace` on lists will lose data - use `add_messages` or `append_list`
4. **Don't Ignore Array Bounds**: When using `results.0.field`, ensure data has at least one item
5. **Don't Over-Provision DB Pools**: Start with `small` tier and scale up only if needed
6. **Don't Skip Validation**: Missing edge mappings cause runtime errors

### Common Pitfalls

**1. Dot Notation Path Errors**
- **Problem**: Accessing `results.0.title` when results is empty
- **Solution**: System handles gracefully with warnings, but validate data structure

**2. Edge Declaration Mixing**
- **Problem**: Using both node-level and global edges for same node
- **Solution**: Choose one style consistently

**3. Private Mode Passthrough Misunderstanding**
- **Problem**: Expecting passthrough from OUTPUT instead of INPUT
- **Solution**: Remember it preserves from INPUT state

**4. Database Pool Mismatching**
- **Problem**: Using wrong tier causing performance issues
- **Solution**: Monitor DB usage and adjust tier appropriately

**5. Reducer Issues**
- **Problem**: Message history getting overwritten in loops
- **Solution**: Use `add_messages` reducer, not default `replace`

**6. System Variable Validation False Positives**
- **Problem**: Validation tools reporting "missing construct_options" for variables like `$current_date`
- **Solution**: System variables (prefixed with `$`) don't need construct_options or incoming edges - they're auto-populated
- **How to identify**: Check if variable name starts with `$` in the variables dict
- **Examples**: `$current_date`, `$current_datetime`, `$graph_state`

---

## Debugging Tips

### 1. Validation

Workflows validate schema before execution:
- Check node registration
- Verify edge mappings
- Validate required fields

### 2. Monitoring

Track workflow execution:
- Review event streams
- Check HITL job IDs
- Examine state dumps from failed runs

### 3. Testing

Best practices for testing:
- Use predefined HITL inputs when possible
- Test with various input data types
- Monitor logs for iteration counting
- Verify dot notation paths with sample data

### 4. Common Issues

**Workflow hangs waiting for HITL:**
- Add `predefined_hitl_inputs` in test function

**409/500 errors on document init:**
- Check if document exists first

**Long execution times:**
- Be patient with multiple LLM calls
- Use background execution
- Set appropriate timeouts

**Data not flowing correctly:**
- Verify `src_field` and `dst_field` match actual schema fields
- Check dot notation path syntax
- Ensure required edges exist

---

## Quick Reference: Node Selection Guide

### Need to...

**Process LLM interactions?**
→ Use `llm` node ([guide](workflow_service_docs/workflow_builder_guides/nodes/llm_node_guide.md))

**Build prompts from templates?**
→ Use `prompt_constructor` node ([guide](workflow_service_docs/workflow_builder_guides/nodes/prompt_constructor_node_guide.md))

**Get human feedback?**
→ Use `hitl_node__default` ([guide](workflow_service_docs/workflow_builder_guides/nodes/core_dynamic_nodes_guide.md))

**Make decisions/route flow?**
→ Use `if_else_condition` + `router_node` ([if_else guide](workflow_service_docs/workflow_builder_guides/nodes/if_else_node_guide.md), [router guide](workflow_service_docs/workflow_builder_guides/nodes/dynamic_router_node_guide.md))

**Process list items in parallel?**
→ Use `map_list_router_node` ([guide](workflow_service_docs/workflow_builder_guides/nodes/map_list_router_node_guide.md))

**Filter/transform data?**
→ Use `filter_data` or `transform_data` ([filter guide](workflow_service_docs/workflow_builder_guides/nodes/filter_node_guide.md), [transform guide](workflow_service_docs/workflow_builder_guides/nodes/transform_node_guide.md))

**Join datasets?**
→ Use `data_join_data` ([guide](workflow_service_docs/workflow_builder_guides/nodes/data_join_node_guide.md))

**Merge with conflict resolution?**
→ Use `merge_aggregate` ([guide](workflow_service_docs/workflow_builder_guides/nodes/merge_aggregate_node_guide.md))

**Load/store customer data?**
→ Use `load_customer_data` / `store_customer_data` ([load guide](workflow_service_docs/workflow_builder_guides/nodes/load_customer_data_node_guide.md), [store guide](workflow_service_docs/workflow_builder_guides/nodes/store_customer_data_node_guide.md))

**Scrape LinkedIn?**
→ Use `linkedin_scraping` ([guide](workflow_service_docs/workflow_builder_guides/nodes/linkedin_scraping_node_guide.md))

---

## Additional Resources

### Documentation Structure

- **Core Concepts**: `/workflow_service_docs/workflow_concepts/`
  - Workflows Guide & Concepts
  - Anatomy of Node and Workflows
  - Workflow Example Template

- **Builder Guides**: `/workflow_service_docs/workflow_builder_guides/`
  - Workflow Building Guide
  - Nodes Interplay Guide
  - Individual Node Guides (in `/nodes/` subdirectory)

- **Integration Guides**: `/workflow_service_docs/integration_guides/`
  - Frontend Integration
  - Customer Data Integration
  - User Resume Metadata Integration

### Key Files to Reference

- **Node Registration**: `services/workflow_service/services/db_node_register.py`
- **Graph Schema**: `services/workflow_service/graph/graph.py`
- **Base Node**: `services/workflow_service/registry/nodes/core/base.py`
- **Reducers**: `services/workflow_service/graph/reducers.py`

---

## Recent Updates & Evolution

### Major Features Added (2025-09-15)

1. **Full Dot Notation Support**: Access nested data directly in edge mappings
2. **Data-Only Edges**: Memory-efficient data passing without execution flow impact
3. **Node-Level Edge Declaration**: Better organization with `edges` in node config
4. **Database Pool Tiers**: Optimize performance with runtime config
5. **Enhanced Private Mode**: Advanced passthrough data with dot notation support

### Documentation Updates (2025-10-01)

**System Variables in Prompt Constructor** - Comprehensive documentation added for system-provided variables:
- Documented `$current_date`, `$current_datetime`, and `$graph_state` system variables
- Clarified that system variables (prefixed with `$`) do NOT require:
  - `construct_options` mappings
  - Incoming edges providing data
  - Entries in central state
- Added validation guidance to prevent false positive errors
- Included common pitfall: mistakenly adding system variables to construct_options
- Based on analysis of all 11 content_studio workflows confirming correct usage patterns

### Deprecations

- `load_prompt_templates` node → Use `prompt_constructor` with `template_load_config`

---

*Last Updated: 2025-10-01*
*Remember: Always consult specific node guides for detailed configuration options!*
