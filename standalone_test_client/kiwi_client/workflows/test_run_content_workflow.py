user_dna_namespace = "user_profiles"
user_dna_docname = "user_dna_doc" # Define docname constant
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
              "initial_content_brief": { "type": "str", "required": True, "description": "Content brief for the post being generated." },
              "linkedin_username": { "type": "str", "required": True, "description": "LinkedIn username for profile scraping." },
          }
        }
    },
    # Defines workflow start inputs: post_draft_name, initial_content_brief, linkedin_username
    # outgoing edges:
    #  - Sends edge to scrape_linkedin_profile with linkedin_username
    #  - stores post_draft_name to $graph_state
    #  - stores initial_content_brief to $graph_state

    # --- 1b. Scrape LinkedIn Profile ---
    "scrape_linkedin_profile": {
      "node_id": "scrape_linkedin_profile",
      "node_name": "linkedin_scraping",
      "node_config": {
        "test_mode": False, # Set to True for testing without API calls/credits
        "jobs": [
          {
            "output_field_name": "scraped_profile", # Key for results in node output
            "job_type": { "static_value": "profile_info" },
            "type": { "static_value": "person" },
            "username": { "input_field_path": "linkedin_username" }, # Get username from node input
            "profile_info": { "static_value": "yes" } # Required flag alignment
            # Limits will use system defaults
          }
        ]
      }
      # Reads: linkedin_username from input_node
      # Writes: execution_summary, scraping_results (containing 'scraped_profile')
      # Outgoing edges:
      #  - Sends scraping_results.scraped_profile -> scraped_profile_data to construct_initial_prompt
      #  - Sends scraping_results.scraped_profile -> scraped_linkedin_profile to $graph_state
      #  - Triggers load_user_dna
    },

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
              "static_docname": f"{user_dna_docname}" # Get user ID from workflow input
              # "input_docname_field": "user_id" # Use user_id from input_node for docname
            },
            "output_field_name": f"{user_dna_docname}" # Output field containing user data (e.g., {"style_preference": "professional"})
          }
        ]
      },
      "dynamic_output_schema": {  # NOTE: this is demonstration of fields to / from dynamic schemas; they need to be defined atleast somewhere explicitly!
        "fields": {
            f"{user_dna_docname}": { "type": "dict", "required": True, "description": "User DNA document containing user preferences." },
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
      "enable_node_fan_in": True, # Wait for all inputs before running
      "node_config": {
        "prompt_templates": {
          "initial_generation_prompt": {
            "id": "initial_generation_prompt",
            "template": "Create a LinkedIn post based on the following:\nBrief: {brief}\nUser Style: {user_style}\nUser LinkedIn Profile Info (Use this to personalize the post): {linkedin_profile}\n\n",
            # "Generate the post now as JSON matching the schema: {schema_definition}",
            "variables": {
              "brief": None, # Required from input_node via edge mapping
              "user_style": "default", # Default if not found via construct_options
              # "schema_definition": f"{LinkedInPostSchemaDefinition}", # Required (placeholder for actual schema JSON string or loaded 
              # "schema_definition": None # Required via construct_options
              "linkedin_profile": None # Required from scraping node via edge mapping
            },
            "construct_options": { # P1 Sourcing: Map variables to paths within node's input fields
               "user_style": "user_dna_doc.style_preference", # Look inside the mapped 'user_dna_doc' input field
               "brief": "initial_content_brief", # Look inside the mapped 'initial_content_brief' input field
            #    "schema_definition": "schema_def_string" # Look inside the mapped 'schema_def_string' input field
               "linkedin_profile": "scraped_profile_data.scraped_profile" # Look inside the mapped 'scraped_profile_data' input field
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
      # Reads: initial_content_brief (from $graph_state), user_dna_doc (from `load_user_dna`), scraped_profile_data (from `scrape_linkedin_profile`)
      # Waits for all inputs due to enable_node_fan_in=True
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
                    "input_path": "if_else_condition_tag_results::iteration_limit_check", # Path WITHIN the node's input data
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
          "operation": "upsert_versioned", # Update existing document with new version
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
        { "src_field": "initial_content_brief", "dst_field": "initial_content_brief", "description": "Store the initial brief globally."},
        { "src_field": "linkedin_username", "dst_field": "linkedin_username", "description": "Pass the LinkedIn username for scraping."}
      ]
    },
    # Input -> Load User DNA: Control flow trigger
    { "src_node_id": "input_node", "dst_node_id": "load_user_dna", "description": "Trigger loading user data after input." },

    # Load User DNA -> State: Store loaded user data
    { "src_node_id": "load_user_dna", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": f"{user_dna_docname}", "dst_field": f"{user_dna_docname}", "description": "Store the loaded user DNA document globally."}
      ]
    },
    # Load User DNA -> Construct Initial Prompt: Provide user data for prompt construction
    { "src_node_id": "load_user_dna", "dst_node_id": "construct_initial_prompt", "mappings": [
        { "src_field": f"{user_dna_docname}", "dst_field": f"{user_dna_docname}", "description": "Pass user DNA for extracting style preference."}
      ]
    },
    # State -> Construct Initial Prompt: Provide initial brief for prompt construction
    { "src_node_id": "$graph_state", "dst_node_id": "construct_initial_prompt", "mappings": [
        { "src_field": "initial_content_brief", "dst_field": "initial_content_brief", "description": "Pass the initial brief for the prompt."}
      ]
    },

    # Input -> Scrape LinkedIn Profile: Provide username
    { "src_node_id": "input_node", "dst_node_id": "scrape_linkedin_profile", "mappings": [
        { "src_field": "linkedin_username", "dst_field": "linkedin_username", "description": "Pass the LinkedIn username for scraping."}
      ]
    },
    # Scrape LinkedIn Profile -> State: Store scraped profile globally
    { "src_node_id": "scrape_linkedin_profile", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "scraping_results", "dst_field": "scraped_linkedin_profile_results", "description": "Store the fetched LinkedIn profile data globally."}
      ]
    },
    # Scrape LinkedIn Profile -> Construct Initial Prompt: Provide scraped profile data
    { "src_node_id": "scrape_linkedin_profile", "dst_node_id": "construct_initial_prompt", "mappings": [
        { "src_field": "scraping_results", "dst_field": "scraped_profile_data", "description": "Pass scraped profile data for prompt construction."}
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


# --- Test Execution Logic ---

import asyncio
import json
import httpx
import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Union

# Import necessary components from the existing test client structure
from kiwi_client.auth_client import AuthenticatedClient, AuthenticationError
from kiwi_client.test_config import (
    CLIENT_LOG_LEVEL,
)
from kiwi_client.workflow_client import WorkflowTestClient
from kiwi_client.run_client import WorkflowRunTestClient
from kiwi_client.customer_data_client import CustomerDataTestClient
# Import HITL client
from kiwi_client.notification_hitl_client import HITLTestClient

# Import schemas used in the main function
from kiwi_client.schemas import workflow_api_schemas as wf_schemas
from kiwi_client.schemas import events_schema as event_schemas
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus, HITLJobStatus

# Setup logger (could also configure externally)
logger = logging.getLogger(__name__)
logging.basicConfig(level=CLIENT_LOG_LEVEL)

# --- Workflow Schema (Already defined in the file) ---
# workflow_graph_schema = { ... } # Assumed to be defined above this code

# --- Inputs for the Post Creation Workflow ---
# These inputs match the 'input_node' dynamic_output_schema
POST_CREATION_WORKFLOW_INPUTS = {
    "post_draft_name": "Test Post via Client v2", # Updated name slightly
    "initial_content_brief": "Create a concise LinkedIn post announcing a new feature: AI-powered comment generation. Mention the benefits for busy professionals.",
    "linkedin_username": "example-user"
}


async def main_test_post_creation():
    """
    Tests creating, running, and deleting the Post Creation Workflow.
    Handles the WAITING_HITL state, simulates feedback, and resumes the run.
    Ensures the required user_dna_doc exists before running.
    """
    print("--- Starting Post Creation Workflow API Test (with HITL Handling) --- ")
    workflow_id_to_run: Optional[uuid.UUID] = None
    created_run_id: Optional[uuid.UUID] = None
    user_dna_created_for_cleanup = False

    # Need an authenticated client first
    try:
        async with AuthenticatedClient() as auth_client:
            print("Authenticated.")
            # Initialize test clients
            workflow_tester = WorkflowTestClient(auth_client)
            run_tester = WorkflowRunTestClient(auth_client)
            data_tester = CustomerDataTestClient(auth_client) # Initialize customer data client
            hitl_tester = HITLTestClient(auth_client) # Initialize HITL client

            # --- Setup: Ensure user_dna_doc exists ---
            print(f"\n--- Setup: Ensuring '{user_dna_namespace}/{user_dna_docname}' exists ---")
            user_dna_data = {
                "style_preference": "professional", # Field referenced in 'construct_initial_prompt'
                "tone": "informative",
                "preferred_hashtags": ["#AI", "#LinkedIn", "#ContentMarketing"]
                # Add any other fields potentially useful for the user DNA
            }
            init_payload = wf_schemas.CustomerDataVersionedInitialize(
                is_shared=False, # User specific
                initial_data=user_dna_data,
                initial_version="default", # Use 'default' as the initial version
                is_system_entity=False
            )
            # Attempt to initialize - this will fail if it already exists, which is acceptable
            # We primarily want to ensure it's there for the workflow run.
            print(f"   Attempting to initialize '{user_dna_namespace}/{user_dna_docname}'...")
            init_result = await data_tester.initialize_versioned_document(user_dna_namespace, user_dna_docname, init_payload)
            if init_result:
                print(f"   ✓ Document initialized successfully.")
                user_dna_created_for_cleanup = True # Mark for cleanup only if we created it
            else:
                # If initialization failed, check if it already exists
                print(f"   Initialization failed (likely already exists). Checking metadata...")
                metadata = await data_tester.get_document_metadata(
                    namespace=user_dna_namespace,
                    docname=user_dna_docname,
                    is_shared=False,
                    is_system_entity=False
                )
                if metadata:
                    print(f"   ✓ Document already exists (Versioned: {metadata.is_versioned}). Proceeding.")
                    # Optionally, update the existing document if needed, e.g., using UPSERT_VERSIONED or UPDATE
                    # For now, just confirming existence is enough.
                else:
                    print(f"   ✗ Critical Setup Error: Document '{user_dna_namespace}/{user_dna_docname}' does not exist and could not be initialized.")
                    return # Stop the test if the prerequisite document is missing


            # --- Setup: Create the Post Creation workflow ---
            print("\n--- Setup: Creating the Post Creation workflow --- ")

            # Optional: Validate the specific workflow_graph_schema via API
            print("\n1. Validating post creation workflow schema using API...")
            validation_result = await workflow_tester.validate_graph_api(workflow_graph_schema)
            if validation_result:
                if validation_result.is_valid:
                    print("   ✓ Workflow validation completed successfully!")
                else:
                    print("   ✗ Workflow validation failed:")
                    if validation_result.errors:
                        for category, errors in validation_result.errors.items():
                            print(f"     {category}:")
                            for error in errors:
                                print(f"       - {error}")
                    # Optionally stop if validation fails critically
                    # return
            else:
                print("   ✗ Failed to perform API-based validation.")
                # Depending on severity, you might stop here
                # return


            print("\n2. Creating the workflow...")
            created_workflow = await workflow_tester.create_workflow(
                name="Post Creation Workflow Test Run",
                graph_config=workflow_graph_schema # Use the schema from this file
            )
            if created_workflow:
                workflow_id_to_run = created_workflow.id # Access UUID directly from schema
                print(f"   Setup complete: Created workflow ID: {workflow_id_to_run}")
                print(f"   Workflow name: {created_workflow.name}")
            else:
                print("   Setup failed: Could not create workflow.")
                # Need to cleanup user_dna if we created it
                if user_dna_created_for_cleanup:
                     await data_tester.delete_versioned_document(user_dna_namespace, user_dna_docname, is_shared=False)
                return
            # --- ----------------------------------------- ---

            # 3. Submit Run using the created Workflow ID
            print(f"\n3. Submitting run for workflow ID: {workflow_id_to_run}...")
            submitted_run: Optional[wf_schemas.WorkflowRunRead] = await run_tester.submit_run(
                workflow_id=workflow_id_to_run,
                inputs=POST_CREATION_WORKFLOW_INPUTS # Use the specific inputs
            )
            if submitted_run:
                created_run_id = submitted_run.id
                print(f"   Run submitted successfully: ID = {created_run_id} (Status: {submitted_run.status})")
            else:
                print("   Run submission failed.")
                # Fall through to finally block for cleanup

            # --- Wait for the run to complete or pause ---
            current_run_status_obj: Optional[wf_schemas.WorkflowRunRead] = None
            if created_run_id:
                print(f"\n--- Waiting for run {created_run_id} to finish or pause (Round 1) ---")
                current_run_status_obj = await run_tester.wait_for_run_completion(created_run_id, timeout_sec=180)

                # --- Handle First WAITING_HITL State (Reject) ---
                if current_run_status_obj and current_run_status_obj.status == WorkflowRunStatus.WAITING_HITL:
                    print(f"   Run {created_run_id} paused for HITL (Round 1).")

                    print("\n4. Fetching pending HITL job details (Round 1)...")
                    pending_job_round1 = await hitl_tester.get_latest_pending_hitl_job(run_id=created_run_id)

                    if pending_job_round1:
                        print(f"   ✓ Found pending HITL job: {pending_job_round1.id}")
                        print(f"     Request Details: {json.dumps(pending_job_round1.request_details, indent=2)}")
                        print(f"     Response Schema: {json.dumps(pending_job_round1.response_schema, indent=2)}")

                        print("\n5. Submitting HITL response (Reject - Round 1)...")
                        # Define the rejection response based on the 'capture_approval' node's dynamic_output_schema
                        hitl_response_inputs_reject = {
                            "approval_status": "needs_work",
                            "feedback_text": "The tone is a bit too generic. Make it more engaging and add a specific call to action."
                        }
                        print(f"   Submitting response: {json.dumps(hitl_response_inputs_reject, indent=2)}")

                        # Resume the run with the rejection feedback
                        resumed_run_status_round1 = await run_tester.submit_run(
                            resume_run_id=created_run_id,
                            inputs=hitl_response_inputs_reject
                        )

                        if resumed_run_status_round1:
                            print(f"   ✓ Resume request submitted (Round 1). Run status: {resumed_run_status_round1.status}")

                            # --- Wait for Run to Pause Again (Round 2) ---
                            print(f"\n--- Waiting for run {created_run_id} to finish or pause (Round 2) ---")
                            current_run_status_obj = await run_tester.wait_for_run_completion(created_run_id, timeout_sec=180) # Wait again

                            # --- Handle Second WAITING_HITL State (Approve) ---
                            if current_run_status_obj and current_run_status_obj.status == WorkflowRunStatus.WAITING_HITL:
                                print(f"   Run {created_run_id} paused for HITL (Round 2).")

                                print("\n6. Fetching pending HITL job details (Round 2)...")
                                pending_job_round2 = await hitl_tester.get_latest_pending_hitl_job(run_id=created_run_id)

                                if pending_job_round2:
                                    print(f"   ✓ Found pending HITL job: {pending_job_round2.id}")
                                    print(f"     Request Details: {json.dumps(pending_job_round2.request_details, indent=2)}")
                                    print(f"     Response Schema: {json.dumps(pending_job_round2.response_schema, indent=2)}") # Schema should be the same

                                    print("\n7. Submitting HITL response (Approve - Round 2)...")
                                    # Define the approval response
                                    hitl_response_inputs_approve = {
                                        "approval_status": "approved",
                                        "feedback_text": "" # No further feedback
                                    }
                                    print(f"   Submitting response: {json.dumps(hitl_response_inputs_approve, indent=2)}")

                                    # Resume the run with approval
                                    resumed_run_status_round2 = await run_tester.submit_run(
                                        resume_run_id=created_run_id,
                                        inputs=hitl_response_inputs_approve
                                    )

                                    if resumed_run_status_round2:
                                        print(f"   ✓ Resume request submitted (Round 2). Run status: {resumed_run_status_round2.status}")

                                        # --- Wait for Final Completion ---
                                        print(f"\n--- Waiting for run {created_run_id} to reach *final* completion ---")
                                        current_run_status_obj = await run_tester.wait_for_run_completion(created_run_id, timeout_sec=180) # Final wait

                                    else:
                                        print(f"   ✗ Failed to submit resume request (Round 2).")
                                else:
                                     print(f"   ✗ Could not find pending HITL job (Round 2). Cannot resume.")

                            # --- Handle potential immediate completion/failure after Round 1 feedback ---
                            elif current_run_status_obj and current_run_status_obj.status == WorkflowRunStatus.COMPLETED:
                                print(f"   Run {created_run_id} completed unexpectedly after Round 1 feedback.")
                            elif current_run_status_obj:
                                print(f"   Run {created_run_id} failed after Round 1 feedback. Status: {current_run_status_obj.status}")

                        else:
                            print(f"   ✗ Failed to submit resume request (Round 1).")
                    else:
                        print(f"   ✗ Could not find pending HITL job (Round 1). Cannot proceed with feedback loop.")


            # --- Final Status Check & Details ---
            if current_run_status_obj and current_run_status_obj.status == WorkflowRunStatus.COMPLETED:
                print(f"\n--- Run {created_run_id} Completed Successfully ---")
                # Fetch and display final details
                print(f"\n8. Getting final details for completed run {created_run_id}...")
                details_obj: Optional[wf_schemas.WorkflowRunDetailRead] = await run_tester.get_run_details(created_run_id)
                if details_obj:
                    output_sample = json.dumps(details_obj.outputs, indent=2) # Show full output if possible
                    event_count = len(details_obj.detailed_results) if details_obj.detailed_results else 0
                    print(f"   ✓ Successfully fetched details (Status: {details_obj.status}, Events: {event_count})")
                    print(f"   Final Output:\n{output_sample}")
                    # Add assertions based on expected output structure if needed
                    assert details_obj.id == created_run_id
                    assert details_obj.outputs is not None
                    assert details_obj.detailed_results is not None
                    # Check if the final output node fields are present
                    assert 'final_post_paths' in details_obj.outputs
                    assert 'final_post_content' in details_obj.outputs
                else:
                    print("   ✗ Failed to get final run details.")

            elif current_run_status_obj:
                print(f"\n--- Run {created_run_id} Finished with Status: {current_run_status_obj.status} ---")
                if current_run_status_obj.error_message:
                    print(f"   Error message: {current_run_status_obj.error_message}")
                # Optionally fetch details even for failed runs
                details_obj = await run_tester.get_run_details(created_run_id)
                if details_obj and details_obj.error_message:
                     print(f"   Detailed Error from Run Details: {details_obj.error_message}")

            elif created_run_id:
                print(f"\n--- Run {created_run_id} timed out or final status could not be retrieved ---")
            # --- ---------------------------------- ---

    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
    except ImportError as e:
         print(f"Import Error: {e}. Check PYTHONPATH and schema/client locations.")
    except Exception as e:
        print(f"An unexpected error occurred in the main test execution: {e}")
        logger.exception("Main test execution error:")
    finally:
        # --- Cleanup ---
        print(f"\n--- Cleanup --- ")

        # Cleanup workflow first
        if workflow_id_to_run:
            print(f"   Deleting workflow {workflow_id_to_run}...")
            try:
                async with AuthenticatedClient() as cleanup_auth_client:
                    cleanup_workflow_tester = WorkflowTestClient(cleanup_auth_client)
                    deleted = await cleanup_workflow_tester.delete_workflow(workflow_id_to_run)
                    print(f"     {'✓' if deleted else '✗'} Deleted workflow.")
            except Exception as cleanup_e:
                print(f"     ✗ Workflow cleanup failed: {cleanup_e}")
                logger.exception("Workflow cleanup error:")

        # Cleanup user_dna_doc IF we created it in this run
        if user_dna_created_for_cleanup:
            print(f"   Deleting user DNA document '{user_dna_namespace}/{user_dna_docname}'...")
            try:
                 async with AuthenticatedClient() as cleanup_auth_client:
                    cleanup_data_tester = CustomerDataTestClient(cleanup_auth_client)
                    deleted_dna = await cleanup_data_tester.delete_versioned_document(
                        namespace=user_dna_namespace,
                        docname=user_dna_docname,
                        is_shared=False # It was user-specific
                    )
                    print(f"     {'✓' if deleted_dna else '✗'} Deleted user DNA document.")
            except Exception as dna_cleanup_e:
                print(f"     ✗ User DNA document cleanup failed: {dna_cleanup_e}")
                logger.exception("User DNA document cleanup error:")
        else:
            print(f"   Skipping user DNA document cleanup (was not created in this run).")

        # TODO: Add cleanup for the created draft document in 'draft_storage_namespace'
        print(f"   NOTE: Draft document '{draft_storage_namespace}/{POST_CREATION_WORKFLOW_INPUTS['post_draft_name']}' may need manual cleanup.")


        print("\n--- Post Creation Workflow API Test Finished --- ")

if __name__ == "__main__":
    # Ensure API server is running and config (.env) is correct
    # Run with: PYTHONPATH=. python standalone_test_client/kiwi_client/_test_content_workflow.py
    print("Attempting to run Post Creation Workflow test client...")
    # Make sure the event loop is managed correctly
    # asyncio.run(main_test_post_creation()) # Use asyncio.run for top-level execution

    # Fix for potential nested loop issues if run from certain environments:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError: # \'RuntimeError: Cannot run the event loop while another loop is running\'
        loop = None

    if loop and loop.is_running():
        print("   Async event loop already running. Adding task...")
        # Schedule the task in the existing loop
        # Note: This might not wait for completion unless awaited elsewhere
        tsk = loop.create_task(main_test_post_creation())
        # If you need to wait here in a sync context, it\'s complex.
        # Better to ensure this script is run in a context where asyncio.run works.
    else:
        print("   Starting new async event loop...")
        asyncio.run(main_test_post_creation())


    print("\nRun this script from the project root directory using:")
    print("PYTHONPATH=. python standalone_test_client/kiwi_client/_test_content_workflow.py")

