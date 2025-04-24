import json
import asyncio


user_dna_namespace = "user_profiles"
draft_storage_namespace = "drafts"
llm_provider = "openai"
generation_model_name = "gpt-4.1"
temperature = 0.5
max_tokens = 1000
max_iterations = 3
feedback_analysis_model = "gpt-4.1"


# Full GraphSchema Structure
workflow_graph_schema = {
  "nodes": {
    # --- 1. Input Node ---
    "input_node": {
      "node_id": "input_node",
      "node_name": "input_node",
      "node_config": {
      },
      "dynamic_output_schema": {
          "fields": {
              "post_draft_name": { "type": "str", "required": True, "description": "Name of the post being drafted for saving." },
              "initial_content_brief": { "type": "str", "required": True, "description": "Content brief for the post being generated." }
          }
        }
    },
    # Defines workflow start inputs: post_draft_name, initial_content_brief
    # outgoing edges:
    #  - Sends edge to load_user_dna without mapping
    #  - stores post_draft_name to $graph_state
    #  - stores initial_content_brief to $graph_state

    # --- 2. Load User Data ---
    "load_user_dna": {
      "node_id": "load_user_dna",
      "node_name": "load_customer_data",
      "node_config": {
        "load_paths": [
          {
            # Configuration to load user preferences/DNA document
            "filename_config": {
              "static_namespace": f"{user_dna_namespace}", # Placeholder e.g., "user_profiles"
              "static_docname": "user_dna_doc" # Get user ID from workflow input
              # "input_docname_field": "user_id" # Use user_id from input_node for docname
            },
            "output_field_name": "user_dna_doc" # Output field containing user data (e.g., {"style_preference": "professional"})
          }
        ]
      },
      "dynamic_output_schema": {  # NOTE: this is demonstration of fields to / from dynamic schemas; they need to be defined atleast somewhere explicitly!
        "fields": {
            "user_dna_doc": { "type": "dict", "required": True, "description": "User DNA document containing user preferences." },
        }
      }
      # Loads user_dna_doc of current user -> its a versioned document!
      # outgoing edges:
      #   - Stores user_dna_doc to $graph_state
      #   - sends user_dna_doc to `construct_initial_prompt`
    },

    # --- 3. Construct Initial Prompt ---
    "construct_initial_prompt": {
      "node_id": "construct_initial_prompt",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "initial_generation_prompt": {
            "id": "initial_generation_prompt",
            "template": "Create a LinkedIn post based on the following:\nBrief: {brief}\nUser Style: {user_style}\n\n",  #  + 
                # "Generate the post now as JSON matching the schema: {schema_definition}",
            "variables": {
              "brief": None, # Required from input_node via edge mapping
              "user_style": "default", # Default if not found via construct_options
              # "schema_definition": f"{LinkedInPostSchemaDefinition}", # Required (placeholder for actual schema JSON string or loaded 
              # "schema_definition": None # Required via construct_options
            },
            "construct_options": { # P1 Sourcing: Map variables to paths within node's input fields
               "user_style": "user_dna_doc.style_preference", # Look inside the mapped 'user_dna_doc' input field
               "brief": "initial_content_brief", # Look inside the mapped 'initial_content_brief' input field
            #    "schema_definition": "schema_def_string" # Look inside the mapped 'schema_def_string' input field
            }
          },
          "system_prompt": {  # NOTE: this can directly be set in the LLM node too! But putting it here for using template variables!
            "id": "system_prompt",
            "template": "You are a LinkedIn post generator. You are given a brief and a user style. You need to generate a LinkedIn post based on the brief and user style guidelines. If you are given feedback, you should rewrite it based on the user's feedback.",
            "variables": {
            #   "original_post": None, # Required from $graph_state
            }
          }
        }
      }
      # Reads: initial_content_brief (from $graph_state), user_dna_doc from `load_user_dna` edge
      # Outgoing edges
      #   - Sends: initial_generation_prompt -> to user_prompt ; system_prompt -> system_prompt in LLM Node
    },

    # --- 4. Generate Content (Structured) ---
    "generate_content": {
      "node_id": "generate_content",
      "node_name": "llm",
      "node_config": {
        "llm_config": {
          "model_spec": {
            "provider": f"{llm_provider}", # e.g., "openai"
            "model": f"{generation_model_name}" # e.g., "gpt-4-turbo"
          },
          "temperature": temperature, # Low temperature for deterministic interpretation
          "max_tokens": max_tokens,
        },
        # Define the structured output for the post
        "output_schema": {
          "dynamic_schema_spec": {
            "schema_name": "LinkedInPost",
            "fields": {
              # NOTE: Ensure these match the schema provided in linked_in_schema_string and used in prompts
              "post_text": { "type": "str", "required": True, "description": "The main body of the LinkedIn post." },
              "hashtags": { "type": "list", "items_type": "str", "required": True, "description": "Suggested hashtags." }
            }
          }
        }
        # Input prompt field name will be 'user_prompt' , 'system_prompt'
        # Also expects 'messages_history' as input if available from $graph_state
      }
      # Reads: user_prompt, system_prompt (from construct_initial_prompt OR construct_rewrite_prompt), 
      # Reads: messages_history (from $graph_state)
      # Writes: structured_output (the post), content, metadata, current_messages
      # Outgoing edges
      #   - Sends: structured_output to store_draft
      #   - Sends: structured_output -> draft_for_review to capture_approval
      #   - Sends: messages_history -> to $graph_state
      #   - Sends: structured_output -> `current_post_draft` to $graph_state
      #   - Sends: metadata -> `generation_metadata` to $graph_state
    },

    # --- 5. Store Draft ---
    # TODO: CHECK if post is correctly saved given interrupt in parallel branch!
    "store_draft": {  # NOTE: this is demonstrating node parallism / branching for now and under what conditions it should be used! Store Branch post LLM generation
      "node_id": "store_draft",
      "node_name": "store_customer_data",
      "node_config": {
        "global_versioning": {
          "is_versioned": True,
          "operation": "initialize", # Must not exist yet
          "version": "draft_v1" # Name the initial version
        },
        "store_configs": [
          {
            "input_field_path": "structured_output", # Field name in node input containing the value to save
            "target_path": {
              "filename_config": {
                "static_namespace": f"{draft_storage_namespace}",
                "input_docname_field": "post_draft_name",
                # "static_docname": "latest_draft_for_post" # Simpler alternative placeholder
                # "static_docname": "latest_draft_${user_id}" # Simpler alternative placeholder
              }
            }
          }
        ]
      }
      # Reads: `post_draft_name` from central State
      # Reads: structured_output (mapped from generate_content.structured_output)
    },

    # --- 6. Human Review ---
    "capture_approval": {  # NOTE: this is demonstrating node parallism / branching for now and under what conditions it should be used! HITL Branch post LLM generation
      "node_id": "capture_approval",
      "node_name": "hitl_node__default",
      "node_config": {}, # Config removed as base HITLNode ignores it
      "dynamic_output_schema": {
          "fields": {
              "approval_status": { "type": "enum", "enum_values": ["approved", "needs_work"], "required": True, "description": "User decision on the draft." },
              "feedback_text": { "type": "str", "required": False, "description": "Optional feedback text from the user." }
          }
      },
      # Reads: draft_for_review (mapped from generate_content.structured_output)
      # Writes: approval_status, feedback_text
      # Outgoing edges
      #   - Sends: approval_status -> approval_status_from_hitl to route_on_approval
      #   - Sends: feedback_text -> current_feedback_text to $graph_state
    },

    # --- 7. Route Based on Approval ---
    "route_on_approval": {
      "node_id": "route_on_approval",
      "node_name": "router_node",
      "node_config": {
        "choices": ["check_iteration_limit", "finalize_post"], # Node IDs to route to
        "allow_multiple": False,
        "choices_with_conditions": [
          {
            "choice_id": "check_iteration_limit", # Route to feedback loop (needs iteration check first)
            "input_path": "approval_status_from_hitl", # Path WITHIN the node's input data
            "target_value": "needs_work"
          },
          {
            "choice_id": "finalize_post", # Route to final storage
            "input_path": "approval_status_from_hitl", # Path WITHIN the node's input data
            "target_value": "approved"
          }
        ]
        # Removed default_choice (NOT SUPPORTED AS OF NOW!) - relies on the conditions covering expected values
      }
      # Reads: approval_status_from_hitl (mapped from capture_approval.approval_status)
      # Routes execution, passes state implicitly.
      # Outgoing edges (Routes execution)
      #   - Send: check_iteration_limit (no mapping)
      #   - Send: finalize_post (no mapping)
    },

    # --- 8. Check Iteration Limit ---
    "check_iteration_limit": {
        "node_id": "check_iteration_limit",
        "node_name": "if_else_condition",
        "node_config": {
            "tagged_conditions": [
                {
                    "tag": "iteration_limit_check", # Identifier for the condition group
                    "condition_groups": [ {
                        "logical_operator": "and", # Operator within the group
                        "conditions": [ {
                            "field": "generation_metadata.iteration_count", # Field name expected in the node's input data
                            "operator": "less_than",
                            "value": max_iterations
                        } ]
                    } ],
                    "group_logical_operator": "and" # Operator between groups (only one group here)
                }
            ],
            "branch_logic_operator": "and"
        }
        # Reads: generation_metadata from $graph_state
        # Writes: branch ('true_branch' or 'false_branch') in `branch`; tag_results ; condition_result
        # Outgoing edges
        #   - route_on_limit_check:
        #     - Send: tag_results -> if_else_condition_tag_results to `route_on_limit_check`
        #     - Send: condition_result -> if_else_overall_condition_result to `route_on_limit_check`
        #     - Send: branch -> iteration_branch_result (no mapping) to `route_on_limit_check`
    },

    # --- 8b. Route Based on Iteration Limit Check ---
    "route_on_limit_check": {  # NOTE: this demonstrates 3 diff ways of checking IFElse outputs to perform routing -> check tag or check overall result (via condition or branch name) across all tags!
        "node_id": "route_on_limit_check",
        "node_name": "router_node",
        "node_config": {
            "choices": ["interpret_feedback", "finalize_post"], # Node IDs to route to
            "allow_multiple": False,
            "choices_with_conditions": [
                {
                    "choice_id": "interpret_feedback", # Continue loop
                    "input_path": "if_else_condition_tag_results.iteration_limit_check", # Path WITHIN the node's input data
                    "target_value": True # Value output by check_iteration_limit
                },
                {
                    "choice_id": "finalize_post", # Limit reached, finalize
                    "input_path": "iteration_branch_result", # Path WITHIN the node's input data
                    "target_value": "false_branch" # Value output by check_iteration_limit
                },
                # NOTE: this is the alternative way to check the overall condition result across all tags!
                # {
                #     "choice_id": "finalize_post", # Limit reached, finalize
                #     "input_path": "if_else_overall_condition_result", # Path WITHIN the node's input data
                #     "target_value": "False" # Value output by check_iteration_limit
                # }
            ]
        }
        # Reads: if_else_condition_tag_results, `route_on_limit_check`, iteration_branch_result from `check_iteration_limit`
        # Outgoing edges
        #   - Routes execution (no mapping in outgoing edges) to ["interpret_feedback", "finalize_post"].
    },

    # --- 9. Interpret Feedback (Structured) ---
    "interpret_feedback": {
        "node_id": "interpret_feedback",
        "node_name": "llm",
        "node_config": {
            "llm_config": {
              "model_spec": {
                "provider": f"{llm_provider}", # e.g., "openai"
                "model": f"{feedback_analysis_model}" # e.g., "gpt-3.5-turbo"
              },
              "temperature": temperature, # Low temperature for deterministic interpretation
              "max_tokens": max_tokens,
            },
            "default_system_prompt": "You're an expert LinkedIn Marketing Analyst. \nInterpret the user's feedback and provide specific instructions for rewriting the LinkedIn post.", # Optional default if no system message in input
            "output_schema": { # Define the structured output for feedback directives
                "dynamic_schema_spec": {
                    "schema_name": "FeedbackDirectives",
                    "fields": {
                        "feedback_type": { "type": "enum", "enum_values": ["rewrite_request", "unclear"], "required": True, "description": "Classification of the feedback intent." },
                        "summary": { "type": "str", "required": False, "description": "A concise summary of the feedback." },
                        "rewrite_instructions": { "type": "str", "required": False, "description": "Specific instructions extracted for the rewrite." }
                    }
                }
            }
            # Input prompt field name will be 'prompt_for_feedback_analysis'
            # Also expects 'messages_history' as input if available from $graph_state
        }
        # Reads: current_feedback_text, messages_history (from $graph_state)
        # Writes: structured_output (directives)
        # Outgoing edges
        #   - Sends: structured_output -> rewrite_interpretation to `construct_rewrite_prompt`
    },

    # --- 10. Construct Rewrite Prompt ---
    "construct_rewrite_prompt": {  # NOTE: we don't need a system prompt since LLM will have access to message history with preexisting system prompt!
      "node_id": "construct_rewrite_prompt",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "rewrite_prompt": {
            "id": "rewrite_prompt",
            "template": "Rewrite the LinkedIn post based on the following feedback.Feedback Summary: {feedback_summary}\nRewrite Instructions: {rewrite_instructions}\n\n",
            "variables": {
                # Available from previous `message_history`!
                # "original_post": None, # Required from $graph_state.original_draft_content
                "feedback_summary": None, # Required from transform_feedback_output
                "rewrite_instructions": None, # Required from transform_feedback_output
                # "user_style": "default", # Default if not found via construct_options
                # "schema_definition": None # Required via construct_options
                # "schema_definition": f"{LinkedInPostSchemaDefinition}" # Required (placeholder for actual schema JSON string or loaded value)
            },
            "construct_options": { # P1 Sourcing: Map variables to paths within node's input fields
                "feedback_summary": "rewrite_interpretation.summary", # Look inside the mapped 'feedback_directives' input field
                "rewrite_instructions": "rewrite_interpretation.rewrite_instructions", # Look inside the mapped 'feedback_directives' input field
                # NOTE: user_style, brief not required here probably since they wil be available from previous `message_history`!
                # "user_style": "user_dna_doc.style_preference", # Look inside the mapped 'user_dna_doc' input field
                # "brief": "initial_content_brief", # Look inside the mapped 'initial_content_brief' input field
            }
          }
        }
      }
      # Reads: rewrite_interpretation (mapped from `interpret_feedback`)
      # Writes: rewrite_prompt
      # Outgoing edges
      #   - Sends: rewrite_prompt -> to user_prompt in LLM Node
    },

    # --- 11. Store Final Post ---
    "finalize_post": {  # Store the finalized version of the post after feedback and revisions
      "node_id": "finalize_post",
      "node_name": "store_customer_data",
      "node_config": {
        "global_versioning": {
          "is_versioned": True,
          "operation": "upsert", # Update existing document with new version
          "version": "finalized_v1" # Name the finalized version
        },
        "store_configs": [
          {
            "input_field_path": "current_post_draft", # Field name in node input containing the value to save
            "target_path": {
              "filename_config": {
                "static_namespace": f"{draft_storage_namespace}",
                "input_docname_field": "post_draft_name",
                # "static_docname": "latest_draft_for_post" # Simpler alternative placeholder
                # "static_docname": "latest_draft_${user_id}" # Simpler alternative placeholder
              }
            }
          }
        ]
      }
      # Reads: `post_draft_name`, `current_post_draft`  from central State
      # Outgoing edges
      #   - Sends: `paths_processed` to output node (# List of docs and paths saved)
    },

    # --- 12. Output Node ---
    "output_node": {
      "node_id": "output_node",
      "node_name": "output_node",
      "node_config": {}
    }
    # Reads: `paths_processed` from store_draft
    # Reads: `current_post_draft` from central State
  },

  # --- Edges Defining Data Flow ---
  "edges": [
    # --- Initial Setup ---
    # Input -> State: Store initial inputs globally
    { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "post_draft_name", "dst_field": "post_draft_name", "description": "Store the draft name for later use (e.g., saving)."},
        { "src_field": "initial_content_brief", "dst_field": "initial_content_brief", "description": "Store the initial brief globally."}
      ]
    },
    # Input -> Load User DNA: Control flow trigger
    { "src_node_id": "input_node", "dst_node_id": "load_user_dna", "description": "Trigger loading user data after input." },

    # Load User DNA -> State: Store loaded user data
    { "src_node_id": "load_user_dna", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "user_dna_doc", "dst_field": "user_dna_doc", "description": "Store the loaded user DNA document globally."}
      ]
    },
    # Load User DNA -> Construct Initial Prompt: Provide user data for prompt construction
    { "src_node_id": "load_user_dna", "dst_node_id": "construct_initial_prompt", "mappings": [
        { "src_field": "user_dna_doc", "dst_field": "user_dna_doc", "description": "Pass user DNA for extracting style preference."}
      ]
    },
    # State -> Construct Initial Prompt: Provide initial brief for prompt construction
    { "src_node_id": "$graph_state", "dst_node_id": "construct_initial_prompt", "mappings": [
        { "src_field": "initial_content_brief", "dst_field": "initial_content_brief", "description": "Pass the initial brief for the prompt."}
      ]
    },

    # --- First Generation Path ---
    # Construct Initial Prompt -> Generate Content: Provide the user and system prompts
    { "src_node_id": "construct_initial_prompt", "dst_node_id": "generate_content", "mappings": [
        { "src_field": "initial_generation_prompt", "dst_field": "user_prompt", "description": "Pass the main generation prompt to the LLM."},
        { "src_field": "system_prompt", "dst_field": "system_prompt", "description": "Pass the system prompt/instructions to the LLM."}
      ]
    },
    # State (Messages) -> Generate Content: Provide conversation history if any (unlikely on first run)
    { "src_node_id": "$graph_state", "dst_node_id": "generate_content", "mappings": [
        { "src_field": "messages_history", "dst_field": "messages_history", "description": "Pass existing message history for context."}
      ]
    },

    # --- Parallel Branches Post-Generation ---
    # Generate Content -> Store Draft: Send generated content for initial draft storage
    { "src_node_id": "generate_content", "dst_node_id": "store_draft", "mappings": [
        { "src_field": "structured_output", "dst_field": "structured_output", "description": "Pass the generated post content for saving as a draft. (Parallel Branch 1)"}
      ]
    },
    # State -> Store Draft: Provide draft name for saving
    { "src_node_id": "$graph_state", "dst_node_id": "store_draft", "mappings": [
        { "src_field": "post_draft_name", "dst_field": "post_draft_name", "description": "Pass the draft name needed by the node's target_path config."}
      ]
    },
    # Generate Content -> Capture Approval: Send generated content for human review
    { "src_node_id": "generate_content", "dst_node_id": "capture_approval", "mappings": [
        { "src_field": "structured_output", "dst_field": "draft_for_review", "description": "Pass the generated post content for HITL review. (Parallel Branch 2)"}
      ]
    },

    # --- Update State Post-Generation ---
    # Generate Content -> State: Update global state with results and context
    { "src_node_id": "generate_content", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "current_messages", "dst_field": "messages_history", "description": "Update message history with the latest interaction."},
        { "src_field": "metadata", "dst_field": "generation_metadata", "description": "Store LLM metadata (e.g., token usage, iteration count)."},
        { "src_field": "structured_output", "dst_field": "current_post_draft", "description": "Store the latest generated post draft globally."}
      ]
    },

    # --- Approval and Routing ---
    # Capture Approval -> Route on Approval: Send approval status for routing decision
    { "src_node_id": "capture_approval", "dst_node_id": "route_on_approval", "mappings": [
        { "src_field": "approval_status", "dst_field": "approval_status_from_hitl", "description": "Pass the user's decision ('approved' or 'needs_work')."}
      ]
    },
    # Capture Approval -> State: Store user feedback
    { "src_node_id": "capture_approval", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "feedback_text", "dst_field": "current_feedback_text", "description": "Store the user's feedback text globally."}
      ]
    },
    # Route on Approval -> Check Iteration Limit: Control flow if 'needs_work'
    { "src_node_id": "route_on_approval", "dst_node_id": "check_iteration_limit", "description": "Trigger iteration check if feedback provided (Control Flow: 'needs_work')." },
    # Route on Approval -> Finalize Post: Control flow if 'approved'
    { "src_node_id": "route_on_approval", "dst_node_id": "finalize_post", "description": "Trigger finalization if post approved (Control Flow: 'approved')." },

    # --- Feedback Loop ---
    # State -> Check Iteration Limit: Provide metadata needed for the check
    { "src_node_id": "$graph_state", "dst_node_id": "check_iteration_limit", "mappings": [
        { "src_field": "generation_metadata", "dst_field": "generation_metadata", "description": "Pass LLM metadata containing iteration count."}
      ]
    },
    # Check Iteration Limit -> Route on Limit Check: Send check results for routing
    { "src_node_id": "check_iteration_limit", "dst_node_id": "route_on_limit_check", "mappings": [
        { "src_field": "branch", "dst_field": "iteration_branch_result", "description": "Pass the branch taken ('true_branch' if limit not reached, 'false_branch' if reached)."},
        { "src_field": "tag_results", "dst_field": "if_else_condition_tag_results", "description": "Pass detailed results per condition tag."},
        { "src_field": "condition_result", "dst_field": "if_else_overall_condition_result", "description": "Pass the overall boolean result of the check."}
      ]
    },
    # Route on Limit Check -> Interpret Feedback: Control flow if iteration limit NOT reached
    { "src_node_id": "route_on_limit_check", "dst_node_id": "interpret_feedback", "description": "Trigger feedback interpretation if iterations remain (Control Flow: 'true_branch')." },
    # Route on Limit Check -> Finalize Post: Control flow if iteration limit REACHED
    { "src_node_id": "route_on_limit_check", "dst_node_id": "finalize_post", "description": "Trigger finalization if iteration limit reached (Control Flow: 'false_branch')." },

    # State -> Interpret Feedback: Provide necessary context for feedback analysis
    { "src_node_id": "$graph_state", "dst_node_id": "interpret_feedback", "mappings": [
        { "src_field": "feedback_messages_history", "dst_field": "messages_history", "description": "Pass message history for LLM context."},
        { "src_field": "current_feedback_text", "dst_field": "user_prompt", "description": "Pass the user's feedback as the main input user_prompt for analysis."} # Assuming the LLM node expects 'prompt_for_feedback_analysis' based on its config comments
      ]
    },
    # Interpret Feedback -> Construct Rewrite Prompt: Send structured feedback interpretation
    { "src_node_id": "interpret_feedback", "dst_node_id": "construct_rewrite_prompt", "mappings": [
        { "src_field": "structured_output", "dst_field": "rewrite_interpretation", "description": "Pass the structured analysis (summary, instructions) for constructing the rewrite prompt."}
      ]
    },
    # Interpret Feedback -> State: Update message history and metadata after analysis LLM call
    { "src_node_id": "interpret_feedback", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "current_messages", "dst_field": "feedback_messages_history", "description": "Update message history with the feedback analysis interaction."},
        # { "src_field": "metadata", "dst_field": "feedback_generation_metadata", "description": "Update LLM metadata (overwrites previous if reducer is 'replace')."}
      ]
    },
    # Construct Rewrite Prompt -> Generate Content: Send the new prompt for regeneration
    { "src_node_id": "construct_rewrite_prompt", "dst_node_id": "generate_content", "mappings": [
        { "src_field": "rewrite_prompt", "dst_field": "user_prompt", "description": "Pass the rewrite prompt back to the main LLM node to generate a revised post."}
      ]
    }, # This completes the feedback loop, flowing back to Generate Content

    # --- Finalization Path ---
    # State -> Finalize Post: Provide the final draft content and name for saving
    { "src_node_id": "$graph_state", "dst_node_id": "finalize_post", "mappings": [
        { "src_field": "current_post_draft", "dst_field": "current_post_draft", "description": "Pass the final approved post content for saving."},
        { "src_field": "post_draft_name", "dst_field": "post_draft_name", "description": "Pass the draft name for the final save operation."}
      ]
    },
    # Finalize Post -> Output Node: Send confirmation/ID of the saved final post
    { "src_node_id": "finalize_post", "dst_node_id": "output_node", "mappings": [
        { "src_field": "paths_processed", "dst_field": "final_post_paths", "description": "Pass the path(s) or ID(s) of the finalized stored document(s)."} # Assuming Store node outputs 'paths_processed'
      ]
    },
    # State -> Output Node: Provide the final content for the graph output
    { "src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
        { "src_field": "current_post_draft", "dst_field": "final_post_content", "description": "Pass the final post content itself to the output."}
      ]
    }
  ],

  # --- Define Start and End ---
  "input_node_id": "input_node",
  "output_node_id": "output_node",

#   # --- Optional Metadata ---
#   "metadata": {
#     # State reducers define how to merge data written to the same key in $graph_state.
#      "state_reducers": {
#        "messages_history": { "reducer_type": "add_messages", "description": "Append new messages to maintain conversation history."},
#        "generation_metadata": { "reducer_type": "replace", "description": "Replace with the latest LLM metadata (e.g., iteration count)."},
#        "current_post_draft": { "reducer_type": "replace", "description": "Replace with the latest generated/approved draft."},
#        "current_feedback_text": { "reducer_type": "replace", "description": "Replace with the latest feedback received."},
#        # Other state keys like post_draft_name, initial_content_brief, user_dna_doc are typically written once, so default 'replace' is fine.
#      }
#   }
}




# --- Mock Final State and Output ---

# Example of what the $graph_state might contain after a successful run (e.g., one round of feedback)
mock_final_graph_state = {
    "post_draft_name": "Q3 Campaign Launch Post",
    "initial_content_brief": "Announce the launch of our new Q3 campaign focused on AI-driven efficiency.",
    "user_dna_doc": {
        "style_preference": "professional and slightly informal",
        "tone": "enthusiastic",
        "target_audience": "Marketing Managers",
        "preferred_hashtags": ["#AI", "#MarketingAutomation", "#Efficiency"],
        # ... other user DNA fields
    },
    "messages_history": [
        # Initial generation messages
        {"role": "system", "content": "You are a LinkedIn post generator..."},
        {"role": "user", "content": "Create a LinkedIn post based on the following:\nBrief: Announce the launch of our new Q3 campaign focused on AI-driven efficiency.\nUser Style: professional and slightly informal\n\n"},
        {"role": "assistant", "content": '{"post_text": "Excited to launch our Q3 campaign! Discover how AI can boost your team\'s efficiency. #AI #Marketing", "hashtags": ["#AI", "#Marketing"]}'},
        # Feedback messages
        {"role": "user", "content": "Feedback: Needs to be more enthusiastic and mention Marketing Managers specifically."}, # This corresponds to 'current_feedback_text' before analysis
        {"role": "system", "content": "You're an expert LinkedIn Marketing Analyst..."}, # Feedback analysis system prompt
        {"role": "user", "content": "Needs to be more enthusiastic and mention Marketing Managers specifically."}, # Feedback analysis user prompt (same as feedback text)
        {"role": "assistant", "content": '{"feedback_type": "rewrite_request", "summary": "Increase enthusiasm, target Marketing Managers.", "rewrite_instructions": "Rewrite the post with a more enthusiastic tone and explicitly mention Marketing Managers as the audience."}'},
        # Rewrite generation messages
        {"role": "system", "content": "You are a LinkedIn post generator..."}, # Same system prompt persists
        {"role": "user", "content": "Rewrite the LinkedIn post based on the following feedback.Feedback Summary: Increase enthusiasm, target Marketing Managers.\nRewrite Instructions: Rewrite the post with a more enthusiastic tone and explicitly mention Marketing Managers as the audience.\n\n"},
        {"role": "assistant", "content": '{"post_text": "🚀 Big news for Marketing Managers! Our Q3 campaign is LIVE, showcasing amazing AI-driven efficiency gains. Ready to supercharge your strategy? #AI #MarketingAutomation #Efficiency", "hashtags": ["#AI", "#MarketingAutomation", "#Efficiency"]}'}
    ],
    "generation_metadata": {
        # Metadata from the *last* LLM call (either feedback analysis or rewrite generation)
        "model_used": "gpt-4-turbo",
        "prompt_tokens": 150,
        "completion_tokens": 80,
        "total_tokens": 230,
        "iteration_count": 2, # Incremented after the first generation
        # ... other metadata fields like latency, finish reason, etc.
    },
    "current_post_draft": {
        "post_text": "🚀 Big news for Marketing Managers! Our Q3 campaign is LIVE, showcasing amazing AI-driven efficiency gains. Ready to supercharge your strategy? #AI #MarketingAutomation #Efficiency",
        "hashtags": ["#AI", "#MarketingAutomation", "#Efficiency"]
    },
    "current_feedback_text": "Needs to be more enthusiastic and mention Marketing Managers specifically.", # Stores the last feedback provided
}

# Example of what the final output_node might produce
mock_final_graph_output = {
    # Data explicitly mapped from finalize_post node
    "final_post_paths": [
        {
            "namespace": "user_drafts", # Example value
            "docname": "q3_campaign_launch_post", # Example value based on post_draft_name
            "version": "finalized_v1",
            "full_path": "user_drafts/q3_campaign_launch_post/finalized_v1" # Example generated path
        }
    ],
    # Data explicitly mapped from $graph_state
    "final_post_content": {
        "post_text": "🚀 Big news for Marketing Managers! Our Q3 campaign is LIVE, showcasing amazing AI-driven efficiency gains. Ready to supercharge your strategy? #AI #MarketingAutomation #Efficiency",
        "hashtags": ["#AI", "#MarketingAutomation", "#Efficiency"]
    }
    # Potentially other fields could be mapped here if needed
}


async def get_db_registry():
    external_context_manager = await get_external_context_manager_with_clients()
    db_registry = external_context_manager.db_registry
    return db_registry

if __name__ == "__main__":
    print(json.dumps(workflow_graph_schema, indent=2))
    from workflow_service.graph.graph import GraphSchema
    from workflow_service.graph.builder import GraphBuilder
    from workflow_service.services.external_context_manager import get_external_context_manager_with_clients
    
    # Run the async function in an event loop to get the db_registry
    db_registry = asyncio.run(get_db_registry())
    graph_schema = GraphSchema(**workflow_graph_schema)
    graph_builder = GraphBuilder(db_registry)
    graph_entities = graph_builder.build_graph_entities(graph_schema)
    print(graph_entities)
