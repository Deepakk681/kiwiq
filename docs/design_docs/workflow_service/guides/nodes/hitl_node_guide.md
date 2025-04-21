# Usage Guide: HITLNode (Human-in-the-Loop)

This guide explains the `HITLNode`, which allows you to introduce points in your workflow where a human needs to review data, provide input, or make a decision.

## Purpose

The `HITLNode` (Human-in-the-Loop) pauses the workflow execution and waits for input from a designated human user. It's essential for tasks requiring human judgment, approval, correction, or additional information that the automated parts of the workflow cannot provide.

Common use cases:
-   Content review and approval (e.g., reviewing AI-generated text before publishing).
-   Data validation or correction.
-   Decision making based on complex or ambiguous information.
-   Gathering additional context or details from a user.

## Configuration (`NodeConfig`)

The `HITLNode` typically doesn't require specific configuration within its `node_config` field. Its behavior, including the data presented to the user and the data expected back, is defined by its connections (edges) and potentially by the frontend application interacting with the workflow system.

```json
{
  "nodes": {
    "human_review_step": {
      "node_id": "human_review_step", // Choose a descriptive ID
      "node_name": "hitl_node__default", // Or a more specific registered HITL node name if available
      "node_config": {},
      // Input/Output schemas often determined by edges
      "dynamic_input_schema": null,
      "dynamic_output_schema": null
    }
    // ... other nodes
  }
  // ... other graph properties
}
```

-   `node_id`: A unique identifier for this specific HITL step in your workflow.
-   `node_name`: Must start with `hitl_` (e.g., `hitl_node__default`, `hitl_content_review`). The suffix might correspond to a specific UI or task type defined elsewhere.
-   `node_config`: Usually empty `{}`. Specific HITL implementations might define configuration options here, but the base `HITLNode` does not.
-   `dynamic_input_schema` / `dynamic_output_schema`: Like `InputNode` and `OutputNode`, the exact data fields are typically determined by the incoming and outgoing edges. Incoming edges define what data is *presented* to the human, and outgoing edges define what data the human is expected to *provide*.

## Input & Output

-   **Input:** Receives data from upstream nodes via incoming `EdgeSchema` mappings. This data is typically packaged and presented to the human reviewer through a user interface.
-   **Output:** Produces data based on the human's input. The structure of this output data is defined by the outgoing `EdgeSchema` mappings. The workflow remains paused until the human submits their input, which then becomes the output of this node.

## Example (`GraphSchema`)

Imagine a workflow where an AI generates text, and then a human reviews and approves/rejects it, optionally adding comments.

```json
{
  "nodes": {
    "ai_generator": {
      "node_id": "ai_generator",
      "node_name": "llm", // Assuming an LLM node generates content
      "node_config": { /* ... LLM config ... */ }
    },
    "human_review": {
      "node_id": "human_review",
      "node_name": "hitl_review", // Specific HITL task type
      "node_config": {},
      // Explicitly defining the output schema for clarity (optional)
      "dynamic_output_schema": {
        "fields": {
          "approved": { "type": "enum", "enum_values": ["yes", "no"], "required": true },
          "review_comments": { "type": "str", "required": false }
        }
      }
    },
    "approval_router": { // Node to route based on human input
      "node_id": "approval_router",
      "node_name": "approval_router",
      "node_config": { /* ... Router config ... */ }
    }
    // ... other nodes
  },
  "edges": [
    // AI Generator output to HITL input
    {
      "src_node_id": "ai_generator",
      "dst_node_id": "human_review",
      "mappings": [
        // Data to show the reviewer
        { "src_field": "generated_text", "dst_field": "text_to_review" },
        { "src_field": "source_prompt", "dst_field": "original_prompt" }
      ]
    },
    // HITL output to Router input
    {
      "src_node_id": "human_review",
      "dst_node_id": "approval_router",
      "mappings": [
        // Data provided by the reviewer
        { "src_field": "approved", "dst_field": "approved" }, // Pass the approval status
        { "src_field": "review_comments", "dst_field": "comments" }
      ]
    }
    // ... other edges
  ],
  "input_node_id": "__INPUT__",
  "output_node_id": "__OUTPUT__"
}
```

In this example:
1.  The `ai_generator` sends `generated_text` and `source_prompt` to the `human_review` node.
2.  The UI associated with `hitl_review` would display this information.
3.  The user interface would expect the human to provide values for `approved` (either "yes" or "no") and optionally `review_comments`.
4.  This data (`approved`, `review_comments`) becomes the output of the `human_review` node.
5.  The `approval_router` receives this data to decide the next step.

*(See `test_AI_loop.py` for a runnable example of an AI-Human feedback loop using HITL).* 

### Notes for Non-Coders

-   Use the `HITLNode` whenever you need a human to look at something or provide information before the workflow continues.
-   Think about:
    -   *What information does the human need to see?* (Define this with incoming edges/mappings).
    -   *What information does the human need to provide?* (Define this with outgoing edges/mappings or `dynamic_output_schema`).
-   The `node_name` (like `hitl_review`) might correspond to a specific screen or task setup in the application used to manage workflows.
-   You typically don't need to put anything in the `node_config` for a standard HITL node. 