# Usage Guide: MapListRouterNode (map_list_router_node)

This guide explains how to configure and use the `MapListRouterNode` to iterate over collections (lists or dictionaries) and dispatch individual items to other nodes for processing, potentially in parallel.

## Purpose

The `MapListRouterNode` acts as a distributor or dispatcher in your workflow. It allows you to:

-   Take a list of items (e.g., a list of products, tasks, or documents) or the values from a dictionary found at a specific `source_path` in the input data.
-   For *each individual item* in that collection:
    -   Send it to one or more specified `destination` nodes.
    -   Optionally transform the item's structure *before* sending it, based on mappings defined on the *outgoing edges*.
-   Enable parallel processing of items by leveraging LangGraph's `Send` mechanism, allowing multiple downstream nodes to potentially run concurrently for different items.

This is fundamental for patterns like:
-   **Map-Reduce:** Processing each item in a list independently (map) before potentially aggregating results later (reduce).
-   **Batch Processing:** Applying the same operation (like an LLM call or data validation) to multiple data points.
-   **Dynamic Fan-Out:** Distributing tasks based on the content of a list generated earlier in the workflow.

**Key Concept:** Unlike nodes that process data as a whole, this node breaks down a collection and initiates separate processing paths for its constituent items via `Send` commands.

## Configuration (`NodeConfig`)

You configure the `MapListRouterNode` within the `node_config` field of its entry in the `GraphSchema`.

```json
{
  "nodes": {
    "distribute_tasks": {
      "node_id": "distribute_tasks", // Unique ID for this node instance
      "node_name": "map_list_router_node", // ** Must be "map_list_router_node" **
      "node_config": { // This is the MapperConfigSchema
        // --- Base Router Settings ---
        "choices": ["process_item_node", "log_item_node", "error_handler_node"], // List ALL possible destination node IDs
        // "allow_multiple": false, // Not directly used by mapper logic

        // --- Specific Distribution Rules ---
        "map_targets": [
          {
            // Rule 1: Send items from 'pending_tasks' list to 'process_item_node' and 'log_item_node'
            "source_path": "tasks.pending", // Dot-notation path to the list in the input data
            "destinations": ["process_item_node", "log_item_node"] // Node IDs to send each item to
          },
          {
            // Rule 2: Send items from 'failed_tasks' list to 'error_handler_node'
            "source_path": "tasks.failed",
            "destinations": ["error_handler_node"]
          }
          // Add more map_target objects if you need to distribute items from other lists/dicts
        ]
      },
      // Input/Output schemas are dynamic for this node
      "dynamic_input_schema": null,
      "dynamic_output_schema": null
    },
    // --- Destination Nodes (Must be defined) ---
    "process_item_node": {
      "node_id": "process_item_node",
      /* ... other config ... */
      // CRITICAL for parallel processing:
      "private_input_mode": true
    },
    "log_item_node": {
      "node_id": "log_item_node",
      /* ... other config ... */
      "private_input_mode": true
    },
    "error_handler_node": {
      "node_id": "error_handler_node",
      /* ... other config ... */
      "private_input_mode": true
    },
    "next_node_after_processing": {
        "node_id": "next_node_after_processing",
        // IMPORTANT: If this node receives input from a node with private_output_mode=true,
        // it must also have private_input_mode=true to receive the direct Send.
        "private_input_mode": true 
        /* ... other config ... */
    },
    "final_aggregator": { /* ... Node to potentially collect results ... */ }
    // ... other nodes
  }
  // ... other graph properties (Edges are crucial - see example below)
}
```

### `node_config` Details (`MapperConfigSchema`):

-   **`choices`** (List[str], required): Inherited from the base router schema. This list **must** include the `node_id` of *every* possible destination node that any `map_target` might send items to. It's used for graph validation and visualization.
-   **`allow_multiple`** (bool, default: `false`): Inherited, but not directly used by the mapper's distribution logic (which inherently sends to all specified destinations for an item).
-   **`map_targets`** (List[`MapTargetConfig`], required): **Core configuration**. A list where each item defines a rule for distributing items from a specific source collection.
    -   **Inside each `MapTargetConfig`**:
        *   **`source_path`** (str, required): Dot-notation path to the collection (list or dictionary) in the node's input data whose items you want to distribute (e.g., `customer_orders`, `results.analysis_items`). If it's a dictionary, the node iterates over its *values*.
        *   **`destinations`** (List[str], required): A list of `node_id`s. For *every item* found at the `source_path`, a `Send` command will be generated targeting each `node_id` in this list. These IDs must be present in the top-level `choices`.

### Data Transformation Happens on Edges!

**Crucially**, unlike the `TransformerNode` or `DataJoinNode`, the `MapListRouterNode` **does not** define how individual items are transformed within its *own* configuration. Instead:

-   **Transformations are defined via `mappings` on the outgoing `EdgeSchema`** connecting the `MapListRouterNode` to each destination node.
-   If an edge has mappings, the item will be transformed into a new dictionary according to those mappings before being sent.
-   If an edge has *no* mappings (`mappings: []` or omitted), the item is sent "as-is" (copied).
-   You can send the *same* item to different destinations with *different structures* by defining different mappings on the respective edges.

## Input (`DynamicSchema`)

-   The node expects input data containing the collections (lists or dictionaries) specified in the `source_path` of its `map_targets`.
-   It uses a `DynamicSchema` and adapts based on the `source_path` fields configured.

## Output (`Command`)

-   The `MapListRouterNode` does **not** produce a standard data output field like `transformed_data`.
-   Its primary output is a LangGraph `Command` object. This command contains:
    -   A list of `Send` actions, one for each item and each destination it needs to be sent to. Each `Send` action encapsulates the (potentially transformed) item data and the target `node_id`.
    -   A state update dictionary, primarily containing the execution order tracker (`__central_state__::node_execution_order`).

## Parallel Processing & Private Modes

The `MapListRouterNode` enables parallel execution using LangGraph's `Send` mechanism. Here's how it works and why `private_input_mode` / `private_output_mode` are essential:

1.  **Dispatch via `Send`:** For each item in the source list and each destination node specified, the mapper generates a `Send(node_id=destination, data=item_data)` action within a `Command`.
2.  **Independent Execution:** LangGraph interprets this `Command`. Each `Send` action effectively triggers an independent execution instance of the `destination` node with the provided `item_data`. If you send 5 items to 2 destinations each, you could potentially trigger 10 parallel node runs (subject to runtime execution limits).
3.  **The State Conflict Problem:** If these parallel destination nodes read from and write to the *shared central graph state*, they can interfere with each other, leading to race conditions and incorrect results. Imagine multiple parallel runs trying to update the same `summary` field in the central state – the final result would be unpredictable.
4.  **Solution: `private_input_mode`:** To enable safe parallel processing, the **destination nodes** (e.g., `process_item_node`, `log_item_node` in the example) **must** be configured with `private_input_mode: true`.
    -   This tells the node: "Expect your input data *directly* from the `Send` command that triggered you, not by reading from the shared central graph state."
    -   It effectively gives each parallel run its own isolated input data.
5.  **Solution: `private_output_mode`:** If a node *downstream* from a private-input node also needs to operate in this isolated, per-item context, it must *also* have `private_input_mode: true`. Furthermore, the node *immediately preceding it* (the one that received the private input) must be configured with `private_output_mode: true`.
    -   This tells the node: "Instead of writing my output to the central state, package it and `Send` it directly to my downstream nodes (which must be expecting private input)."
    -   This continues the isolated processing chain for that specific item branch.
6.  **Convergence:** Branches running in private mode do not automatically merge back into the main graph state. You typically need a dedicated aggregator/reducer node later in the workflow that collects results (often via the central state using specific reducers configured in the `GraphSchema` metadata, though this node doesn't implement reduction itself).

**In short: To run branches in parallel after this mapper, set `private_input_mode: true` on the immediate destination nodes. If the parallel branches continue further, subsequent nodes also need `private_input_mode: true`, and the nodes feeding them need `private_output_mode: true`.**

## Example `GraphSchema` Snippet (Focus on Edges & Parallelism)

```json
{
  "nodes": {
    "get_data": { /* ... outputs { "items_to_process": [ { "id": 1, "value": "A" }, { "id": 2, "value": "B" } ] } ... */ },
    "distribute_items": {
      "node_id": "distribute_items",
      "node_name": "map_list_router_node",
      "node_config": {
        "choices": ["analyze_item", "archive_item_id"],
        "map_targets": [
          {
            "source_path": "items_to_process", // Iterate over this list
            "destinations": ["analyze_item", "archive_item_id"] // Send each item to both nodes
          }
        ]
      }
    },
    "analyze_item": {
      "node_id": "analyze_item",
      "node_name": "some_analyzer_node", // Replace with actual node name
      "private_input_mode": true, // Expect direct input via Send
      "private_output_mode": true, // Send output directly to the next node in this branch
      "node_config": { /* ... */ }
    },
    "archive_item_id": {
      "node_id": "archive_item_id",
      "node_name": "some_archiver_node", // Replace with actual node name
      "private_input_mode": true, // Expect direct input via Send
      // No private_output_mode needed if this is the end of this branch
      "node_config": { /* ... */ }
    },
    "process_analysis_result": {
        "node_id": "process_analysis_result",
        "node_name": "some_result_processor",
        "private_input_mode": true, // Must be true to receive from analyze_item's private output
        "node_config": { /* ... */ }
    },
    "collect_results": { /* ... Node to gather results, likely reads from central state ... */ }
  },
  "edges": [
    // Data into the mapper
    { "src_node_id": "get_data", "dst_node_id": "distribute_items", "mappings": [{ "src_field": "items_to_process", "dst_field": "items_to_process" }] },

    // --- Edges FROM the Mapper (Define transformations here!) ---
    {
      "src_node_id": "distribute_items",
      "dst_node_id": "analyze_item",
      "mappings": [ // Transform item for analyzer
        { "src_field": "id", "dst_field": "analysis_subject_id" },
        { "src_field": "value", "dst_field": "data_payload" }
      ]
    },
    {
      "src_node_id": "distribute_items",
      "dst_node_id": "archive_item_id",
      "mappings": [ // Transform item differently for archiver
        { "src_field": "id", "dst_field": "record_id_to_archive" }
        // Note: 'value' field is not mapped, so it won't be sent to archive_item_id
      ]
    },
    // --- Edge continuing a parallel branch ---
    {
        "src_node_id": "analyze_item", // From a node in private output mode
        "dst_node_id": "process_analysis_result", // To a node in private input mode
        "mappings": [ /* ... map analysis output to processor input ... */]
    }
    // --- Edges converging later (Example - not handled by mapper) ---
    // Edges from parallel branches might eventually feed into a central state collector/reducer node.
    // { "src_node_id": "process_analysis_result", "dst_node_id": "collect_results", /* ... */ },
    // { "src_node_id": "archive_item_id", "dst_node_id": "collect_results", /* ... */ }
  ],
  "input_node_id": "...",
  "output_node_id": "..."
}
```

## Notes for Non-Coders

-   Use this node (`map_list_router_node`) when you have a list of things and want to do something **for each thing separately**, maybe even at the same time (in parallel).
-   Think of it like taking a stack of papers (your list) and handing each paper out to different people (the destination nodes) for processing.
-   **`map_targets`**: Define your distribution rules.
    -   `source_path`: Where is the list of items located in the input data? (e.g., `products_to_update`).
    -   `destinations`: Which node(s) should receive *each* item from that list? (e.g., `["update_inventory_node", "log_update_node"]`).
-   **Data Shape Changes on Edges:** If you need to rename fields or select only parts of the item before sending it, you configure that on the **connecting line (edge)** going from *this* node to the destination node, *not* in this node's settings.
-   **Parallel Work Setup:**
    -   To make the destination nodes work in parallel without messing each other up, you **must** go into the settings of those **destination nodes** and check the box/set the flag for `private_input_mode: true`.
    -   If the parallel work continues for more steps, the nodes in those steps also need `private_input_mode: true`, and the node right before them needs `private_output_mode: true`.
-   Connect the input data containing the list to this node.
-   Connect this node with **edges** to all the destination nodes listed in `choices`. Define any necessary data transformations in the `mappings` section *of those edges*. 