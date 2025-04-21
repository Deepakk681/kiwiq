# Usage Guide: IfElseConditionNode

This guide explains how to configure and use the `IfElseConditionNode` to create decision points and control the flow of your workflow based on data conditions.

## Purpose

The `IfElseConditionNode` acts like a traffic controller or a fork in the road for your workflow. It allows you to:
-   Evaluate one or more sets of conditions against the current data.
-   Determine if the overall conditions evaluate to `true` or `false`.
-   **Output which branch (`true_branch` or `false_branch`) should be taken next.**

This is essential for building workflows that adapt their behavior based on the data they are processing, such as routing leads based on qualification criteria, handling different types of user requests, or implementing approval steps.

**Important:** This node *determines* the desired branch but does *not* perform the actual routing action in the workflow execution graph. You typically need to connect its output to a **Router Node** (like `DynamicRouterNode` or a custom router) which will read the `branch` output and direct the flow accordingly.

## Configuration (`NodeConfig`)

You configure the `IfElseConditionNode` within the `node_config` field of its entry in the `GraphSchema`.

```json
{
  "nodes": {
    "check_lead_qualification": {
      "node_id": "check_lead_qualification", // Unique ID for this node instance
      "node_name": "if_else_condition", // ** Must be "if_else_condition" **
      "node_config": { // This is the IfElseConfigSchema
        "tagged_conditions": [ // A list of named condition sets to evaluate
          // --- Tag 1: Check for High Score OR Priority Flag ---
          {
            "tag": "high_value_or_priority", // Unique name for this condition set
            "condition_groups": [
              {
                "conditions": [
                  { "field": "lead.score", "operator": "greater_than_or_equals", "value": 70 }
                ],
                "logical_operator": "and"
              },
              {
                "conditions": [
                    { "field": "lead.flags", "operator": "contains", "value": "priority"}
                ],
                "logical_operator": "and"
              }
            ],
            "group_logical_operator": "or" // Pass if score >= 70 OR flags contains "priority"
          },
          // --- Tag 2: Check for Contact Info and Recent Activity ---
          {
            "tag": "contactable_and_active",
            "condition_groups": [
              {
                "conditions": [
                  { "field": "lead.email", "operator": "is_not_empty" },
                  { "field": "lead.last_activity_days_ago", "operator": "less_than", "value": 30 }
                ],
                "logical_operator": "and" // Must have email AND be active recently
              }
            ],
            "group_logical_operator": "and",
            "nested_list_logical_operator": "and"
          }
        ],
        // How to combine results of the *tags*: Both tags must pass.
        "branch_logic_operator": "and"
      }
      // dynamic_input_schema / dynamic_output_schema usually not needed
    },
    // --- Subsequent Nodes --- 
    // The actual routing is done here based on the output of 'check_lead_qualification'
    "qualification_router": { 
      "node_id": "qualification_router",
      "node_name": "approval_router", // Or another dynamic router type
      "node_config": {
        "field_name": "branch", // Check the 'branch' output from the IfElse node
        "field_value": "true_branch", // Value corresponding to the true path
        "route_if_true": "assign_to_sales", // Node ID for true branch
        "route_if_false": "send_to_nurturing", // Node ID for false branch
        "choices": ["assign_to_sales", "send_to_nurturing"], // Possible routes
        "allow_multiple": false
      }
    },
    "assign_to_sales": { "node_id": "assign_to_sales" /* ... */ },
    "send_to_nurturing": { "node_id": "send_to_nurturing" /* ... */ }
    // ... other nodes
  }
  // ... other graph properties like edges
}
```

### Key Configuration Sections:

1.  **`tagged_conditions`** (List): A list where each item defines a named set of conditions to evaluate. Each item in this list must have a unique `tag`.
2.  **Inside each `tagged_condition`**:
    *   **`tag`** (String): **Required**. A unique name or identifier for this specific condition set (e.g., `"is_urgent"`, `"needs_manager_approval"`). This helps in understanding the output.
    *   **`condition_groups`** (List): One or more groups of conditions. Works exactly like in the `FilterNode`.
    *   **`group_logical_operator`** (String: `"and"` or `"or"`): How to combine the boolean results (`true`/`false`) of the `condition_groups` *within this tag*. `and` means all groups must pass for this tag to be true; `or` means at least one group must pass.
    *   **`nested_list_logical_operator`** (String: `"and"` or `"or"`): How to combine results when evaluating conditions on nested lists. Works exactly like in the `FilterNode`.
    *   **Conditions within `condition_groups`**: Each `condition` has `field`, `operator`, and `value` (and list options like `apply_to_each_value_in_list_field`), working exactly as described in the `FilterNode` guide. Handles non-existent fields similarly (usually evaluating to `false` except for `is_empty`).
3.  **`branch_logic_operator`** (String: `"and"` or `"or"`): **Crucial**. This determines how the boolean results (`true`/`false`) of *all* the `tagged_conditions` are combined to get the final overall result (`condition_result` in the output).
    *   `"and"`: The final result is `true` **only if** *all* tagged conditions evaluate to `true`.
    *   `"or"`: The final result is `true` **if** *at least one* tagged condition evaluates to `true`.

## Input (`DynamicSchema`)

The `IfElseConditionNode` typically receives the entire data object from the previous node or the central graph state. The specific fields it expects depend entirely on the `field` paths used in your conditions across all tags.

-   Data can be passed via incoming `EdgeSchema` mappings directly to the node, or implicitly via the graph's central state.

## Output (`IfElseOutputSchema`)

The node produces data matching the `IfElseOutputSchema`:

-   **`data`** (Dict[str, Any]): A copy of the original input data that was passed into the node. This allows the data to continue flowing down the chosen branch.
-   **`tag_results`** (Dict[str, bool]): A dictionary showing the boolean result (`true` or `false`) for each `tag` defined in the configuration. Example: `{"high_value_or_priority": true, "contactable_and_active": false}`.
-   **`condition_result`** (bool): The final, overall boolean result after combining the `tag_results` using the `branch_logic_operator`.
-   **`branch`** (String: `"true_branch"` or `"false_branch"`): Indicates which path the workflow *should* take next based on the `condition_result`. **This field is typically consumed by a subsequent Router Node.**

## Connecting to a Router Node (Required for Branching)

The `IfElseConditionNode` calculates the decision, but a **Router Node** executes it.

1.  **Output Connection:** The `IfElseConditionNode`'s output needs to be connected to a router node (e.g., `DynamicRouterNode`, `approval_router`).
2.  **Mapping:** You need an edge mapping from the `IfElseConditionNode`'s output field `branch` to an input field on the router node that the router uses to make its decision (e.g., the `field_name` configured in `ApprovalRouterNode` could be set to check the incoming `branch` value).
3.  **Router Configuration:** The router node must be configured to know which downstream node corresponds to the `"true_branch"` value and which corresponds to the `"false_branch"` value.
4.  **Downstream Connections:** The router node will then have edges connecting to the actual nodes that represent the true and false paths of your workflow.

See the configuration example above for how `check_lead_qualification` (IfElse) feeds into `qualification_router`.

## Example `GraphSchema` Snippet (Focus on Edges)

```json
{
  "nodes": {
    "get_lead_data": { /* ... */ },
    "check_qualification": { /* ... IfElseConditionNode config ... */ },
    "qualification_router": { /* ... DynamicRouterNode config checking 'branch' ... */ },
    "assign_to_sales": { /* ... node for TRUE branch ... */ },
    "send_to_nurturing": { /* ... node for FALSE branch ... */ },
    "final_step": { /* ... common node after branching ... */ }
  },
  "edges": [
    // Data flows into the condition node
    {
      "src_node_id": "get_lead_data",
      "dst_node_id": "check_qualification",
      "mappings": [] // Assumes direct passthrough or central state
    },
    // --- Edge from IfElse to Router --- 
    // Pass the decision result to the router
    {
      "src_node_id": "check_qualification",
      "dst_node_id": "qualification_router",
      "mappings": [
        // Map the 'branch' output field to the field the router expects
        { "src_field": "branch", "dst_field": "branch_decision" } 
        // Router's node_config would be set to check 'branch_decision' field
        // Note: Also map original data if needed: { "src_field": "data", "dst_field": "original_lead_data" }
      ]
    },
    // --- Edges FROM the Router Node --- 
    // These edges are defined, but the router *selects* which one to follow based on its logic
    {
      "src_node_id": "qualification_router",
      "dst_node_id": "assign_to_sales" // Router routes here if branch_decision == "true_branch"
    },
    {
      "src_node_id": "qualification_router",
      "dst_node_id": "send_to_nurturing" // Router routes here if branch_decision == "false_branch"
    },
    // --- Edges converging after branch ---
    {
      "src_node_id": "assign_to_sales",
      "dst_node_id": "final_step"
    },
    {
      "src_node_id": "send_to_nurturing",
      "dst_node_id": "final_step"
    }
  ],
  "input_node_id": "...",
  "output_node_id": "..."
}
```

## Notes for Non-Coders

-   Use this node when your workflow needs to make a decision: "If X is true, go path A, otherwise go path B".
-   `tagged_conditions`: Define your checks here. Give each check a clear `tag` name (like `"is_urgent"`). Set up the conditions (`field`, `operator`, `value`) just like in the Filter node.
-   `branch_logic_operator`: Decide how the results of your tagged checks combine. `"and"` means *all* checks must pass to choose the 'true' path. `"or"` means only *one* check needs to pass.
-   **Important:** This node *only* outputs the decision (`"true_branch"` or `"false_branch"`). It *doesn't* actually send the workflow down the path.
-   **You MUST connect this node's output to a `Router` node.** The Router node reads the `branch` decision and directs the workflow to the correct next step (`assign_to_sales` or `send_to_nurturing` in the example).
-   In the workflow editor, you connect the `IfElse` node to the `Router`, and then connect the `Router` to the two different downstream nodes.
-   The original data is passed along in the `data` output field, so the nodes in the chosen branch can use it. 