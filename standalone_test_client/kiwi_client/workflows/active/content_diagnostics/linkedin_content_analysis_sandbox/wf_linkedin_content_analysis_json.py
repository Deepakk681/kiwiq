"""
batch ID -> 10 posts
- post ID
- theme 1, confidence score, relevance score

# NOTE: don't use a filter node to filter by confidence score; instruct LLM to only assign a theme if confidence score is high


1. Inputs: entity name
2. Load posts using entity name and scraping namespace
3. Optional: Posts filtering -> only get text content
4. Extract upto 5 themes using all posts in context with LLM (you can use generated theme name to be theme ID potentially?)
5. create batches of 10 posts each
6. For each batch classify posts into the most relevant theme with LLM -> check above structure for classification
7. Map each post to the most relevant theme to create theme groups; merge all batches together
8. Analyze each theme group with LLM to create a detailed report for each group
9. combine all reports together
10. Store combined results

"""

from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_SCRAPED_POSTS_DOCNAME,
    # Namespace and docname for storing the final analysis result
    LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_ANALYSIS_DOCNAME,
    LINKEDIN_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
)

from kiwi_client.workflows.active.content_diagnostics.linkedin_content_analysis_sandbox.wf_llm_inputs import (
    # LLM Configuration
    LLM_PROVIDER,
    EXTRACTION_MODEL_FOR_CLASSIFY,
    EXTRACTION_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS_CLASSIFY,
    LLM_MAX_TOKENS_THEMES,
    LLM_MAX_TOKENS_ANALYSIS,
    EXTRACTED_THEMES_SCHEMA,
    BATCH_CLASSIFICATION_SCHEMA,
    THEME_ANALYSIS_REPORT_SCHEMA,
    THEME_EXTRACTION_USER_PROMPT_TEMPLATE,
    THEME_EXTRACTION_SYSTEM_PROMPT_TEMPLATE,
    POST_CLASSIFICATION_USER_PROMPT_TEMPLATE,
    POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE,
    THEME_ANALYSIS_USER_PROMPT_TEMPLATE,
    THEME_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
)

import json
import asyncio
from typing import List, Optional, Dict, Any, Literal


# --- Workflow Constants ---

POST_BATCH_SIZE = 10

# --- Workflow Graph Definition ---
# Based on the 10 steps provided

workflow_graph_schema = {
  "nodes": {
    # --- 1. Input Node ---
    "input_node": {
      "node_id": "input_node",
      "node_name": "input_node",
      "node_config": {},
      "dynamic_output_schema": {
          "fields": {
              "entity_username": { "type": "str", "required": True, "description": "Name of the LinkedIn entity (person or company) whose posts are to be analyzed." },
          }
        }
    },

    # --- 2. Load Posts ---
    "load_posts": {
      "node_id": "load_posts",
      "node_name": "load_customer_data",
      "node_config": {
          # Assumes posts were saved unversioned by the scraping workflow
          # NOTE: LoadCustomerDataNode typically outputs a dict like {"output_field_name": [data...]}
          # Need to adjust paths based on actual node output structure. Assuming it outputs {"raw_posts_data": [list_of_posts]}
          "load_paths": [
              {
                  "filename_config": {
                      "input_namespace_field_pattern": LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE, 
                      "input_namespace_field": "entity_username",
                      "static_docname": LINKEDIN_SCRAPED_POSTS_DOCNAME,
                  },
                  "output_field_name": "raw_posts_data" # Expect output containing LinkedIn posts
              },
              
          ]
      },
      "dynamic_output_schema": {
          "fields": {
              "raw_posts_data": { "type": "list", "required": True, "description": "List of posts from the LinkedIn entity." },
          }
        }
      # Input: entity_username
      # Output: {"raw_posts_data": [list_of_posts]}
    },

    # --- 4. Extract Themes (using LLM) ---
    "construct_theme_extraction_prompt": {
      "node_id": "construct_theme_extraction_prompt",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "theme_user_prompt": {
            "id": "theme_user_prompt",
            # Template expects a single JSON string containing the list of posts (or just texts)
            "template": THEME_EXTRACTION_USER_PROMPT_TEMPLATE,
            "variables": {
              "posts_json": None # Mapped from prepare_posts
            },
            "construct_options": {
                 # Map the list directly, prompt constructor might handle JSON conversion
                "posts_json": "prepared_posts_list" # Expect this field in input
            }
          },
          "theme_system_prompt": {
            "id": "theme_system_prompt",
            "template": THEME_EXTRACTION_SYSTEM_PROMPT_TEMPLATE,
            "variables": { "schema":  EXTRACTED_THEMES_SCHEMA}, # Pass schema as string
            "construct_options": {}
          }
        }
      }
      # Input: entity_username (from state), prepared_posts_list (from prepare_posts)
      # Output: user_prompt, system_prompt
    },
    "extract_themes": {
        "node_id": "extract_themes",
        "node_name": "llm",
        "node_config": {
            "llm_config": {
              "model_spec": {"provider": LLM_PROVIDER, "model": EXTRACTION_MODEL},
              "temperature": LLM_TEMPERATURE,
              "max_tokens": LLM_MAX_TOKENS_THEMES,
              # "reasoning_effort_class": "low"
            },
            "output_schema": {
                "schema_definition": EXTRACTED_THEMES_SCHEMA,
                "convert_loaded_schema_to_pydantic": False
            }
        }
        # Input: user_prompt, system_prompt (from construct_theme_extraction_prompt)
        # Output: structured_output (containing extracted_themes object) -> store in state
    },

    # --- 5. Batch Posts (using MapListRouterNode) ---
    "batch_and_route_posts": {
        "node_id": "batch_and_route_posts",
        "node_name": "map_list_router_node",
        "node_config": {
            "choices": ["construct_classification_prompt"], # Target node for each batch
            "map_targets": [
                {
                    # Path to the list of prepared posts within this node's input data
                    "source_path": "prepared_posts_list", # From prepare_posts output
                    "destinations": ["construct_classification_prompt"],
                    "batch_size": POST_BATCH_SIZE,
                    "batch_field_name": "post_batch" # Wraps output: {"post_batch": [post1, post2, ...]}
                }
            ]
        }
        # Input: {"prepared_posts_list": [list_of_posts]} (from prepare_posts)
        # Output: Sends {"post_batch": [...]} to construct_classification_prompt
    },

    # --- 6. Classify Posts per Batch (using LLM) ---
    "construct_classification_prompt": {
      "node_id": "construct_classification_prompt",
      "node_name": "prompt_constructor",
      "private_input_mode": True, # Receives input from batch_and_route_posts
      "output_private_output_to_central_state": True,
      "private_output_mode": True, # Sends output to classify_batch
      "node_config": {
        "prompt_templates": {
          "classify_user_prompt": {
            "id": "classify_user_prompt",
            "template": POST_CLASSIFICATION_USER_PROMPT_TEMPLATE,
            "variables": {
              "themes_json": None,      # Mapped from state (extracted_themes_list)
              "posts_batch_json": None # Mapped from input (post_batch field)
            },
            "construct_options": {
                # Input field names expected by this node
                "themes_json": "themes_data_json", # Needs JSON string representation from state
                "posts_batch_json": "post_batch" # Map the list from the batcher's output field directly
            }
          },
          "classify_system_prompt": {
            "id": "classify_system_prompt",
            "template": POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE,
            "variables": { "schema": json.dumps(BATCH_CLASSIFICATION_SCHEMA, indent=2) },
            "construct_options": {}
          }
        }
      }
      # Input (private): {"post_batch": [...]}, themes_data_json (mapped from state)
      # Output (private): user_prompt, system_prompt
    },
    "classify_batch": {
        "node_id": "classify_batch",
        "node_name": "llm",
        "private_input_mode": True, # Receives input from construct_classification_prompt
        "output_private_output_to_central_state": True,
        # Output goes to graph state for aggregation
        "node_config": {
            "llm_config": {
                "model_spec": {"provider": LLM_PROVIDER, "model": EXTRACTION_MODEL_FOR_CLASSIFY},
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS_CLASSIFY
            },
            "output_schema": {
                "schema_definition": BATCH_CLASSIFICATION_SCHEMA,
                "convert_loaded_schema_to_pydantic": False
            }
        }
        # Input (private): user_prompt, system_prompt
        # Output: structured_output (containing batch_classifications) -> sent to state: all_classifications_batches
    },

    # --- 7a. Flatten Classification Results ---
    # The reducer 'collect_values' will create a list of lists. We need a flat list for joining.
    # Using merge_aggregate node to flatten the list.
    "flatten_classifications": {
        "node_id": "flatten_classifications",
        "node_name": "merge_aggregate", # Use merge_aggregate for list operations
        "node_config": {
            "operations": [
                {
                    "output_field_name": "flat_classifications",
                    # Path to the list of lists collected in the state
                    "select_paths": ["all_classifications_batches"], # Input field name, mapped from state
                    # "merge_each_object_in_selected_list": False,
                    "merge_strategy": {
                        "reduce_phase": {
                            # Use 'append' or similar list flattening reducer
                            "default_reducer": "nested_merge_aggregate", # Assuming 'append_flatten' exists
                            "error_strategy": "fail_node",
                        },
                        # "post_merge_transformations": {
                        #     # Key doesn't matter for non-dict, config is used
                        #     "flatten_op": {
                        #         "operation_type": "recursive_flatten_list"
                        #     }
                        # },
                        
                    }
                }
            ]
        }
    },

    # --- 7b. Join Classifications to Posts ---
    "join_classifications_to_posts": {
        "node_id": "join_classifications_to_posts",
        "node_name": "data_join_data", # Use the DataJoinNode
        "node_config": {
            "joins": [
                {
                    "primary_list_path": "prepared_posts_list", # From state or prepare_posts output
                    "secondary_list_path": "merged_data.flat_classifications.classifications", # From flatten_classifications output
                    "primary_join_key": "urn", # Assuming 'urn' is the unique ID in prepared posts
                    "secondary_join_key": "post_id", # Matches 'urn' based on classification prompt
                    "output_nesting_field": "mapped_theme", # Nest classification under this key in post
                    "join_type": "one_to_one"
                }
            ]
        },
        # Input: prepared_posts_list (from state), flat_classifications (from flatten_classifications)
        # Output: {"mapped_data": {"prepared_posts_list": [post_with_theme1, post_with_theme2, ...]}}
    },

    # --- 7c. Group Posts under Themes ---
    "group_posts_under_themes": {
        "node_id": "group_posts_under_themes",
        "node_name": "data_join_data",
        "node_config": {
            "joins": [
                {
                    "primary_list_path": "extracted_themes.themes", # From state (list of ThemeSchema)
                    # Path to the modified posts list *within* the previous node's output
                    "secondary_list_path": "mapped_data.prepared_posts_list", # From join_classifications_to_posts output
                    "primary_join_key": "theme_id", # Key in ThemeSchema
                    "secondary_join_key": "mapped_theme.assigned_theme_id", # Key nested in post object
                    "output_nesting_field": "mapped_posts", # Nest list of posts under this key in theme
                    "join_type": "one_to_many"
                }
            ]
        },
        # Input: extracted_themes_list (from state), mapped_data (from join_classifications_to_posts)
        # Output: {"mapped_data": {"extracted_themes_list": [theme_with_posts1, theme_with_posts2, ...]}}
    },


    # --- 8. Analyze Each Theme Group (Map/Reduce Pattern) ---
    "route_theme_groups": {
        "node_id": "route_theme_groups",
        "node_name": "map_list_router_node",
        "node_config": {
            "choices": ["construct_analysis_prompt"], # Target for each theme group
            "map_targets": [
                {
                    # Path to the list of themes (which now contain mapped_posts)
                    # from the output of the previous join node.
                    "source_path": "mapped_data.extracted_themes.themes", # Adjust based on group_posts_under_themes output key
                    "destinations": ["construct_analysis_prompt"],
                    "batch_size": 1, # Process one theme group at a time
                    "batch_field_name": "theme_group_data" # Wraps output: {"theme_group_data": {theme_info + mapped_posts}}
                }
            ]
        }
        # Input: {"mapped_data": {"extracted_themes_list": [...]}} (from group_posts_under_themes)
        # Output: Sends {"theme_group_data": {...}} to construct_analysis_prompt
    },
    "construct_analysis_prompt": {
      "node_id": "construct_analysis_prompt",
      "node_name": "prompt_constructor",
      "private_input_mode": True,
      "output_private_output_to_central_state": True,
      "private_output_mode": True,
      "node_config": {
        "prompt_templates": {
          "analyze_user_prompt": {
            "id": "analyze_user_prompt",
            # Template expects a single theme group object (theme info + mapped_posts list)
            "template": THEME_ANALYSIS_USER_PROMPT_TEMPLATE,
            "variables": {
              "theme_id": None,    # Mapped from theme_group_data input
              "theme_name": None,  # Mapped from theme_group_data input
              "theme_description": None, # Mapped from theme_group_data input
              "theme_group_json": None # Mapped from theme_group_data input (entire object)
            },
            # Assumes input 'theme_group_data' has keys: theme_id, theme_name, theme_description, mapped_posts
            "construct_options": {
                "theme_id": "theme_group_data.theme_id",
                "theme_name": "theme_group_data.theme_name",
                "theme_description": "theme_group_data.theme_description",
                "theme_group_json": "theme_group_data" # Pass the whole theme group object as JSON
            }
          },
          "analyze_system_prompt": {
            "id": "analyze_system_prompt",
            "template": THEME_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
            "variables": {},
            "construct_options": {}
          }
        }
      }
      # Input (private): {"theme_group_data": {...}}, entity_username (from state)
      # Output (private): user_prompt, system_prompt
    },
    "analyze_theme_group": {
        "node_id": "analyze_theme_group",
        "node_name": "llm",
        "private_input_mode": True,
        "output_private_output_to_central_state": True,
        # Output goes to graph state for aggregation
        "node_config": {
            "llm_config": {
                "model_spec": {"provider": LLM_PROVIDER, "model": EXTRACTION_MODEL},
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS_ANALYSIS,
                "reasoning_effort_class": "low"
            },
            "output_schema": {
                "schema_definition": THEME_ANALYSIS_REPORT_SCHEMA,
                "convert_loaded_schema_to_pydantic": False
            }
        }
    },

    # --- 9. Combine All Reports ---
    "combine_reports": {
        "node_id": "combine_reports",
        "node_name": "transform_data", # Or a custom node
        "node_config": {
            "mappings": [
                { "source_path": "entity_username", "destination_path": "final_report_data.entity_username"},
                # Embed the collected list of report objects
                { "source_path": "all_reports_list", "destination_path": "final_report_data.theme_reports"},
            ]
        },
    },

    # --- 10. Store Combined Results ---
    "store_analysis": {
      "node_id": "store_analysis",
      "node_name": "store_customer_data",
      "node_config": {
        "global_versioning": { "is_versioned": False, "operation": "upsert" },
        "global_is_shared": False,
        "store_configs": [
          {
            "input_field_path": "transformed_data.final_report_data", # From combine_reports output
            "target_path": {
              "filename_config": {
                "input_namespace_field_pattern": LINKEDIN_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE, 
                "input_namespace_field": "entity_username",
                "static_docname": LINKEDIN_CONTENT_ANALYSIS_DOCNAME,
              }
            }
          }
        ]
      }
      # Input: final_report_data (from combine_reports), entity_username (from $graph_state)
      # Output: passthrough_data, paths_processed
    },

    # --- 11. Output Node ---
    "output_node": {
      "node_id": "output_node",
      "node_name": "output_node",
      "enable_node_fan_in": True,
      "node_config": {},
    }
  },

  # --- Edges Defining Data Flow ---
  "edges": [
    # --- Input & Setup ---
    { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "entity_username", "dst_field": "entity_username", "description": "Store entity name globally." }
      ]
    },
    { "src_node_id": "input_node", "dst_node_id": "load_posts", "mappings": [
        { "src_field": "entity_username", "dst_field": "entity_username", "description": "Pass entity name to load posts."}
      ]
    },
    # Store prepared posts list in state for later joins
    { "src_node_id": "load_posts", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "raw_posts_data", "dst_field": "prepared_posts_list", "description": "Store prepared posts list in state."}
      ]
    },

    # --- Step 4: Theme Extraction ---
    { "src_node_id": "load_posts", "dst_node_id": "construct_theme_extraction_prompt", "mappings": [
         # Pass the list needed for the prompt
         { "src_field": "raw_posts_data", "dst_field": "prepared_posts_list"}
      ]
    },
    { "src_node_id": "construct_theme_extraction_prompt", "dst_node_id": "extract_themes", "mappings": [
        { "src_field": "theme_user_prompt", "dst_field": "user_prompt"},
        { "src_field": "theme_system_prompt", "dst_field": "system_prompt"}
      ]
    },

    # --- State -> Extract Themes (Message History) ---
    { "src_node_id": "$graph_state", "dst_node_id": "extract_themes", "mappings": [
      ]
    },

    { "src_node_id": "extract_themes", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "extracted_themes", "description": "Store extracted themes structure."},
      ]
    },
    
    # --- Step 5 & 6: Batching and Classification ---
    { "src_node_id": "extract_themes", "dst_node_id": "batch_and_route_posts", "mappings": [
      ]
    },
    { "src_node_id": "$graph_state", "dst_node_id": "batch_and_route_posts", "mappings": [
        # Pass the prepared list for batching
        { "src_field": "prepared_posts_list", "dst_field": "prepared_posts_list" }
      ]
    },
    { "src_node_id": "batch_and_route_posts", "dst_node_id": "construct_classification_prompt", "mappings": [
      ]
    },

    { "src_node_id": "$graph_state", "dst_node_id": "construct_classification_prompt", "mappings": [
        # Pass themes as JSON string (assuming prompt node handles conversion)
        { "src_field": "extracted_themes", "dst_field": "themes_data_json", "description": "Pass themes list to classification prompt."}
      ]
    },
    { "src_node_id": "construct_classification_prompt", "dst_node_id": "classify_batch", "mappings": [
        { "src_field": "classify_user_prompt", "dst_field": "user_prompt"},
        { "src_field": "classify_system_prompt", "dst_field": "system_prompt"}
      ]
    },

    # --- State -> Classify Batch (Message History) ---
    { "src_node_id": "$graph_state", "dst_node_id": "classify_batch", "mappings": [
        { "src_field": "classify_batch_messages_history", "dst_field": "messages_history"}
      ]
    },

    { "src_node_id": "classify_batch", "dst_node_id": "$graph_state", "mappings": [
        # Store the list of classifications *from this batch*
        { "src_field": "structured_output", "dst_field": "all_classifications_batches", "description": "Collect classification results from each batch."},
      ]
    },

    { "src_node_id": "classify_batch", "dst_node_id": "flatten_classifications", "mappings": [
      ]
    },

    # --- Step 7a: Flatten Classifications (Runs after map completes) ---
    { "src_node_id": "$graph_state", "dst_node_id": "flatten_classifications", "mappings": [
        { "src_field": "all_classifications_batches", "dst_field": "all_classifications_batches", "description": "Pass collected batches for flattening."}
      ]
    },

    # --- Step 7b: Join Classifications to Posts ---
    { "src_node_id": "flatten_classifications", "dst_node_id": "join_classifications_to_posts", "mappings": [
        { "src_field": "merged_data", "dst_field": "merged_data", "description": "Pass flattened classifications to join node."}
      ]
    },
    { "src_node_id": "$graph_state", "dst_node_id": "join_classifications_to_posts", "mappings": [
        { "src_field": "prepared_posts_list", "dst_field": "prepared_posts_list", "description": "Pass original prepared posts for join."}
      ]
    },

    # --- Step 7c: Group Posts under Themes ---
    { "src_node_id": "join_classifications_to_posts", "dst_node_id": "group_posts_under_themes", "mappings": [
        { "src_field": "mapped_data", "dst_field": "mapped_data", "description": "Pass posts with mapped themes."}
      ]
    },
    { "src_node_id": "$graph_state", "dst_node_id": "group_posts_under_themes", "mappings": [
        { "src_field": "extracted_themes", "dst_field": "extracted_themes", "description": "Pass original themes list for grouping."}
      ]
    },

    # --- Step 8: Theme Analysis ---
    { "src_node_id": "group_posts_under_themes", "dst_node_id": "route_theme_groups", "mappings": [
        { "src_field": "mapped_data", "dst_field": "mapped_data", "description": "Pass theme groups for analysis routing."}
      ]
    },
    
    # Router edge no mapping!
    { "src_node_id": "route_theme_groups", "dst_node_id": "construct_analysis_prompt", "mappings": [
      ]
    },

    { "src_node_id": "construct_analysis_prompt", "dst_node_id": "analyze_theme_group", "mappings": [
        { "src_field": "analyze_user_prompt", "dst_field": "user_prompt"},
        { "src_field": "analyze_system_prompt", "dst_field": "system_prompt"}
      ]
    },

    { "src_node_id": "analyze_theme_group", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "all_theme_reports", "description": "Collect all theme analysis reports."}      ]
    },

    # --- Step 9: Combine Reports (Runs after map completes) ---
    { "src_node_id": "analyze_theme_group", "dst_node_id": "combine_reports", "mappings": [
      ]
    },
    { "src_node_id": "$graph_state", "dst_node_id": "combine_reports", "mappings": [
        { "src_field": "all_theme_reports", "dst_field": "all_reports_list"},
        { "src_field": "entity_username", "dst_field": "entity_username"},
      ]
    },

    # --- Step 10: Store Results ---
    { "src_node_id": "combine_reports", "dst_node_id": "store_analysis", "mappings": [
        { "src_field": "transformed_data", "dst_field": "transformed_data" }
      ]
    },
    { "src_node_id": "$graph_state", "dst_node_id": "store_analysis", "mappings": [
        { "src_field": "entity_username", "dst_field": "entity_username" }
      ]
    },

    # --- Step 11: Output ---
    { "src_node_id": "store_analysis", "dst_node_id": "output_node", "mappings": [
        { "src_field": "passthrough_data", "dst_field": "passthrough_data" }
    ]}
  ],

  # --- Define Start and End ---
  "input_node_id": "input_node",
  "output_node_id": "output_node",

  # --- State Reducers ---
  "metadata": {
      "$graph_state": {
        "reducer": {
          # Collect results from parallel branches
          "all_classifications_batches": "collect_values", # Collect lists of lists from each batch classification
          "all_theme_reports": "collect_values",   # Collect report objects from each theme analysis
          # Message histories for LLM nodes
        #   "entity_username": "replace",
        #   "prepared_posts_list": "replace", # Store the prepared posts list
        #   "extracted_themes_output": "replace",
        #   "extracted_themes_list": "replace"
        }
      }
  }
}