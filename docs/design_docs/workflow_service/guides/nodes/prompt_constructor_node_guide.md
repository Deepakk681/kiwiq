# Usage Guide: PromptConstructorNode

This guide explains how to use the `PromptConstructorNode` to dynamically build text prompts for other nodes (like the `LLMNode`) using templates and variables.

## Purpose

The `PromptConstructorNode` takes predefined text templates containing placeholders (like `{variable_name}`) and fills those placeholders with actual values provided as input data. This allows you to create complex and context-specific prompts without hardcoding them directly into your workflow graph.

Think of it as a mail merge tool for your workflow prompts.

Common use cases:
-   Creating personalized prompts using user data.
-   Building complex instructions for LLMs by combining static text with dynamic information.
-   Generating system prompts based on workflow state.
-   Standardizing prompt structures across different parts of a workflow.

## Configuration (`NodeConfig`)

The main configuration happens within the `node_config` field, specifically using the `PromptTemplateConfig` schema.

```json
{
  "nodes": {
    "build_my_prompt": {
      "node_id": "build_my_prompt",
      "node_name": "prompt_constructor", // ** Must be "prompt_constructor" **
      "node_config": {
        "prompt_templates": {
          // --- Define one or more templates --- 
          "user_query_tpl": { // Key used internally for organization
            "id": "final_user_prompt", // ** This becomes the output field name **
            "name": "User Query Enhancer", // Optional descriptive name
            "template": "User Query: {user_input}\nContext: {context_summary}\nFormat: {output_format}",
            "variables": {
              // List all variables expected by this template
              "user_input": null, // null: MUST be provided by input edge
              "context_summary": null,
              "output_format": "Provide a concise answer." // Default value
            }
          },
          "system_message_tpl": {
            "id": "system_prompt_for_llm", // ** Another output field name **
            "template": "You are an expert in {domain}. Respond in a {tone} tone. Context: {context_summary}", // Reuses context_summary
            "variables": {
              "domain": "General Knowledge", // Default value
              "tone": "helpful", // Default value
              "context_summary": null // Also needs context_summary
            }
          }
          // ... more templates
        }
      },
      // Input/Output schemas are DYNAMIC. They are not typically defined here
      // but are inferred from the `variables` in `node_config` and edge mappings.
      "dynamic_input_schema": null,
      "dynamic_output_schema": null
    }
    // ... other nodes
  }
  // ... other graph properties
}
```

### `node_config.prompt_templates` Details:

-   This is a dictionary where you define each prompt template.
-   The *key* of each entry (e.g., `"user_query_tpl"`) is just for organization within the config.
-   Inside each template definition:
    *   **`id`** (str, required): **Very important!** This ID determines the name of the output field where the constructed prompt string will be placed. Choose a meaningful ID (e.g., `final_user_prompt`, `summary_request_prompt`).
    *   `name` (str, optional): A human-readable name for the template.
    *   `template` (str, required): The template string itself. Use curly braces `{}` to denote placeholders for variables (e.g., `{user_name}`, `{document_text}`).
    *   `variables` (Dict[str, Optional[str]], required): A dictionary listing *all* the variable names used as placeholders in the `template` string.
        *   The *key* is the variable name (e.g., `"user_input"`).
        *   The *value* is either:
            *   `null`: This variable **must** be provided as input to the node via an edge mapping (either globally or template-specific). Execution will fail if it's not provided.
            *   A string/number/boolean: This is the **default value** to use if the variable is *not* provided as input. Default values should be primitive types.

## Input (Dynamic Schema)

The `PromptConstructorNode` has a dynamic input schema determined by the `variables` defined across all configured `prompt_templates`.

Input data is provided via incoming `EdgeSchema` mappings. The node resolves the value for each placeholder (`{variable}`) in each template according to this priority:

1.  **Template-Specific Input Mapping (Highest Priority):**
    *   If an incoming edge has a `dst_field` matching the pattern `TEMPLATE_ID::VARIABLE_NAME` (e.g., `final_user_prompt::output_format`), the value from that edge's `src_field` is used *only* for the `{output_format}` variable within the template whose `id` is `final_user_prompt`.
    *   This uses the `OBJECT_PATH_REFERENCE_DELIMITER` (`::`).

2.  **Global Input Mapping:**
    *   If an incoming edge has a `dst_field` that exactly matches a variable name (e.g., `context_summary`), the value from that edge's `src_field` is used for the `{context_summary}` variable in *all* templates that contain it, *unless* it was already set by a template-specific mapping (priority 1).

3.  **Default Value:**
    *   If a variable is not provided by either a template-specific or global input mapping, the node checks the template's `variables` definition in the `node_config`.
    *   If a default value (a string, number, or boolean) is defined there, that value is used.

4.  **Required Input (Error):**
    *   If a variable has `null` defined as its value in the template's `variables` section, and it was *not* provided by either a template-specific or global input mapping, the workflow execution will fail because a required input is missing.

## Output (Dynamic Schema)

The `PromptConstructorNode` produces a dynamic output schema.

-   For each prompt template defined in the `node_config`, an output field is created.
-   The **name** of the output field is taken directly from the **`id`** specified for that template in the configuration (e.g., `final_user_prompt`, `system_prompt_for_llm`).
-   The **value** of the output field is the fully constructed prompt string after all placeholders within that template have been filled according to the input priority rules.

## Example (`GraphSchema`)

Let's connect the `PromptConstructorNode` defined above, providing inputs from different sources.

```json
{
  "nodes": {
    "gather_data": { /* ... node that outputs user_query, context_doc ... */ },
    "build_my_prompt": {
      "node_id": "build_my_prompt",
      "node_name": "prompt_constructor",
      "node_config": { /* ... From config example above ... */ }
    },
    "call_llm": {
      "node_id": "call_llm",
      "node_name": "llm",
      "node_config": { /* ... LLM config ... */ }
    }
  },
  "edges": [
    // --- Edges providing variables TO the PromptConstructorNode ---
    {
      "src_node_id": "gather_data",
      "dst_node_id": "build_my_prompt",
      "mappings": [
        // Global mapping: sets {user_input} in template "final_user_prompt"
        { "src_field": "user_query", "dst_field": "user_input" }, 
        // Global mapping: sets {context_summary} in BOTH templates
        { "src_field": "context_doc", "dst_field": "context_summary" } 
      ]
    },
    // Edge providing a template-specific override for "system_prompt_for_llm"
    {
      "src_node_id": "__INPUT__", // Example: getting tone from workflow start
      "dst_node_id": "build_my_prompt",
      "mappings": [
         // Specifically set {tone} only for the system prompt template
        { "src_field": "desired_tone", "dst_field": "system_prompt_for_llm::tone" }
      ]
    },
    // --- Edges using the constructed prompts FROM the PromptConstructorNode ---
    {
      "src_node_id": "build_my_prompt",
      "dst_node_id": "call_llm",
      "mappings": [
        // Use the output named after the template ID
        { "src_field": "final_user_prompt", "dst_field": "user_prompt" }, 
        { "src_field": "system_prompt_for_llm", "dst_field": "system_prompt" }
      ]
    }
  ],
  "input_node_id": "__INPUT__",
  "output_node_id": "__OUTPUT__"
}
```

**How variables are filled in this example:**

-   `final_user_prompt` template:
    *   `{user_input}`: Gets value from `gather_data` node's `user_query` field (Global Mapping).
    *   `{context_summary}`: Gets value from `gather_data` node's `context_doc` field (Global Mapping).
    *   `{output_format}`: Gets value `"Provide a concise answer."` (Default Value).
-   `system_prompt_for_llm` template:
    *   `{domain}`: Gets value `"General Knowledge"` (Default Value).
    *   `{tone}`: Gets value from `__INPUT__` node's `desired_tone` field (Template-Specific Mapping - overrides default).
    *   `{context_summary}`: Gets value from `gather_data` node's `context_doc` field (Global Mapping).

## Notes for Non-Coders

-   Use `PromptConstructorNode` to create reusable prompt text by filling in blanks.
-   **Define Templates:** In `node_config.prompt_templates`, write your base text (`template`) with placeholders like `{variable}`.
-   **List Variables & Defaults:** For each template, list all `{variable}` names in `variables`. Give a default value if it's often the same, or use `null` if the value *must* come from another node.
-   **Name Your Outputs:** The `id` you give each template (e.g., `final_user_prompt`) becomes the name of the output field containing the finished prompt string.
-   **Connect Inputs:** Feed data using edges.
    *   To set a variable in *all* templates that use it, map to the variable name directly (e.g., `dst_field: "context_summary"`).
    *   To set a variable *only* for a specific template, map to `TEMPLATE_ID::VARIABLE_NAME` (e.g., `dst_field: "system_prompt_for_llm::tone"`).
    *   Template-specific inputs override global inputs, which override defaults.
-   **Connect Outputs:** Use edges to take the finished prompts (using the template `id` as the `src_field`) and send them to the next node (like an `LLMNode`). 