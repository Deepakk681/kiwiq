"""
# Inputs to workflow:
1. Generate content topic suggestions for next X weeks: (X) int input optional, default 2
2. Load list of customer context docs such as strategy doc, scraped posts etc
3. Load multiple user draft posts using multiple loader node within posts namespace, load latest N posts (limit and sort by updated_at, DESC); also load user preferences from onboarding namespace, user preferences doc which has user's requested posting frequency / week
5. Merge both lists and limit the merged list limit using merge aggregate node; also in another operation: compute next X weeks (input) multiplied by user preferences post frequency / week (this is number of content topic suggestions we have to generate)
6. construct prompt for first generation (includes system prompt) with all user docs and merged list in prompt
7. Generate 1 structured output content topic suggestion (containing exactly 4 topic ideas around one common theme); it reads message history from LLM; this also has fields such as date / time of posting; it sends structured outputs to all_generated_topics with reducer collect values
8. check IF else on iteration limit, if we have generated the required number of topic suggestions
9. Router node to route to store node to store all generated topic suggestions OR to construct prompt for additional topic suggestions
10. Construct prompt for additional topic suggestions constructs user prompt which just says generate 1 more additional topic suggestion, ensure difference from previous suggestions; it sends to same above LLM node; the LLM node loads message history from central state where it can see previous suggestions and generate the next topic suggestion
10. (after iteration loop ends) store node stores topic suggestions in separate paths using filename pattern with suggestion ID
11. send all topic suggestions to output node

"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum
from datetime import date, datetime, timedelta

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# Internal dependencies (assuming similar structure to example)
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus
from kiwi_client.workflows.active.document_models.customer_docs import (

    # Content Strategy (Playbook)
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
    # LinkedIn scraping
    LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE,
    LINKEDIN_SCRAPED_POSTS_DOCNAME,
    # User Profile (contains preferences)
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,
    # Content Drafts
    LINKEDIN_DRAFT_DOCNAME,
    LINKEDIN_DRAFT_NAMESPACE_TEMPLATE,
    LINKEDIN_DRAFT_IS_VERSIONED,
    # LinkedIn Ideas (for storing topic suggestions)
    LINKEDIN_IDEA_DOCNAME,
    LINKEDIN_IDEA_NAMESPACE_TEMPLATE,
    LINKEDIN_IDEA_IS_VERSIONED,

)
# Import LLM configurations from local wf_llm_inputs
from kiwi_client.workflows.active.content_studio.linkedin_content_calendar_entry_sandbox.wf_llm_inputs import (
    # LLM Model Configuration
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    # Prompts and Schemas
    TOPIC_USER_PROMPT_TEMPLATE,
    TOPIC_SYSTEM_PROMPT_TEMPLATE,
    TOPIC_LLM_OUTPUT_SCHEMA,
    TOPIC_ADDITIONAL_USER_PROMPT_TEMPLATE,
)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Workflow Configuration Constants ---

# Workflow Defaults
DEFAULT_WEEKS_TO_GENERATE = 2
# DEFAULT_DRAFTS_LIMIT = 20 # Default number of latest drafts to load
# DEFAULT_SCRAPED_LIMIT = 20 # Default number of scraped posts to load
PAST_CONTEXT_POSTS_LIMIT = 10 # Limit the combined list of posts fed to the LLM

# Search Params Default (for delete window)
SEARCH_PARAMS_DEFAULT = {
    "input_namespace_field": "entity_username",
    "input_namespace_field_pattern": LINKEDIN_IDEA_NAMESPACE_TEMPLATE,
    "docname_pattern": "*",
    "value_filter": {
        "scheduled_date": {
            "$gt": None,
            "$lte": None,
        },
    }
}

# --- Workflow Graph Schema Definition ---

workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node ---
        "input_node": {
            "node_id": "input_node",
            "node_category": "system",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "weeks_to_generate": { "type": "int", "required": False, "default": DEFAULT_WEEKS_TO_GENERATE, "description": f"Number of weeks ahead to generate topic suggestions for (default: {DEFAULT_WEEKS_TO_GENERATE})." },
                    "past_context_posts_limit": { "type": "int", "required": False, "default": PAST_CONTEXT_POSTS_LIMIT, "description": f"Max number of combined posts (drafts + scraped) to use for context (default: {PAST_CONTEXT_POSTS_LIMIT})."},
                    "entity_username": {"type": "str", "required": True},
                    "start_date": {"type": "str", "required": True, "description": "Start date for generating topic suggestions"},
                    "end_date": {"type": "str", "required": True, "description": "End date for generating topic suggestions"},
                    "search_params": {"type": "dict", "required": False, "default": SEARCH_PARAMS_DEFAULT, "description": "Default search params object for load/delete nodes"},
                }
            }
        },
 
    # --- 2. Load Customer Context Documents and Scraped Posts (Single Node) ---
    "load_all_context_docs": {
        "node_id": "load_all_context_docs",
        "node_category": "system",
        "node_name": "load_customer_data",
        "node_config": {
            "load_paths": [
                {
                    "filename_config": {
                        "input_namespace_field_pattern": LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE, 
                        "input_namespace_field": "entity_username",
                        "static_docname": LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
                    },
                    "output_field_name": "strategy_doc"
                },
                {
                    "filename_config": {
                        "input_namespace_field_pattern": LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE, 
                        "input_namespace_field": "entity_username",
                        "static_docname": LINKEDIN_SCRAPED_POSTS_DOCNAME,
                    },
                    "output_field_name": "scraped_posts"
                },
                {
                    "filename_config": {
                        "input_namespace_field_pattern": LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE, 
                        "input_namespace_field": "entity_username",
                        "static_docname": LINKEDIN_USER_PROFILE_DOCNAME,
                    },
                    "output_field_name": "user_profile"
                },
            ],
            "global_is_shared": False,
            "global_is_system_entity": False,
            "global_schema_options": {"load_schema": False}
        }
    },

    # --- 3. Load Latest User Draft Posts ---
    "load_draft_posts": {
      "node_id": "load_draft_posts",
      "node_category": "system",
      "node_name": "load_multiple_customer_data", # Use the multi-loader node
      "node_config": {
          "namespace_pattern": LINKEDIN_DRAFT_NAMESPACE_TEMPLATE,
          "namespace_pattern_input_path": "entity_username",
          "include_shared": False,        # User-specific drafts only
          "include_user_specific": True,
          "include_system_entities": False,
          # Pagination and Sorting (Inputs mapped from state)
          "skip": 0,
          "limit": PAST_CONTEXT_POSTS_LIMIT, # Mapped from draft_posts_limit input
          "sort_by": "updated_at",
          "sort_order": "desc",

          # Loading options (default)
          "global_version_config": None, # Load active version if versioned
          "global_schema_options": {"load_schema": False},

          # Output field name
          "output_field_name": "draft_posts" # The list will be under this key
      },
    },

    # --- 4. Merge Posts, Compute Limit, Prepare Generation Context ---
    "prepare_generation_context": {
      "node_id": "prepare_generation_context",
      "node_category": "system",
      "node_name": "merge_aggregate", # Use merge_aggregate to combine multiple sources
      "enable_node_fan_in": True, # Wait for all data loads before proceeding
      "node_config": {
        "operations": [
          # Operation 1: Merge Drafts and Scraped Posts and limit the result
          {
            "output_field_name": "final_merged_posts_for_prompt",
            # Order matters for priority (draft posts first, then scraped posts)
            "select_paths": ["draft_posts", "scraped_posts"], # Inputs from state
            "merge_strategy": {
                "map_phase": {"unspecified_keys_strategy": "ignore"}, # Only care about merging lists
                "reduce_phase": {
                    "default_reducer": "extend", # Combine the two lists
                    "error_strategy": "fail_node"
                },
                # Add transformation to limit the number of posts
                "post_merge_transformations": {
                    "final_merged_posts_for_prompt": {
                        "operation_type": "limit_list", 
                        "operand_path": "past_context_posts_limit" # Get limit value from input
                    }
                },
                "transformation_error_strategy": "skip_operation"
            },
            "merge_each_object_in_selected_list": False # Treat lists as atomic values to be EXTENDed
          },
          # Operation 2: Compute Total Topics Needed - weeks_to_generate * posts_per_week
          {
            "output_field_name": "total_topics_needed",
            "select_paths": ["user_profile.posting_schedule.posts_per_week"], # Inputs from state
            "merge_strategy": {
                "map_phase": {"unspecified_keys_strategy": "ignore"}, # Only care about the selected value
                "reduce_phase": {
                    "default_reducer": "replace_right", # Take the posts_per_week value
                    "error_strategy": "fail_node"
                },
                # Use transformation to calculate product of weeks and posts_per_week from user preferences
                "post_merge_transformations": {
                     "total_topics_needed": {
                         "operation_type": "multiply",
                         "operand_path": "weeks_to_generate" # Multiply posts_per_week by weeks_to_generate
                     }
                },
                "transformation_error_strategy": "fail_node"
            },
            "merge_each_object_in_selected_list": False # Operate on values
          }
        ]
      },
    
    },

    # --- 9. Construct Topic Prompt (Inside Map Branch) ---
    "construct_topic_prompt": {
      "node_id": "construct_topic_prompt",
      "node_category": "topic_generation",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "topic_user_prompt": {
            "id": "topic_user_prompt",
            "template": TOPIC_USER_PROMPT_TEMPLATE,
            "variables": {
              "strategy_doc": None,  # Mapped from strategy_doc
              "merged_posts": None,     # Mapped from merged_posts
              "user_timezone": None, # Mapped from playbook.timezone
              "current_datetime": "$current_date",
            },
            "construct_options": {
               "user_timezone": "user_profile.timezone",
               "strategy_doc": "strategy_doc", # Map the number passed by the mapper
               "merged_posts": "merged_data.final_merged_posts_for_prompt", # Map directly from merged_posts
            }
          },
          "topic_system_prompt": {
            "id": "topic_system_prompt",
            "template": TOPIC_SYSTEM_PROMPT_TEMPLATE,
            "variables": { 
                "schema": json.dumps(TOPIC_LLM_OUTPUT_SCHEMA, indent=2), 
                "current_datetime": "$current_date" },
            "construct_options": {}
          }
        }
      }
    },

    # --- 10. Generate Topics (LLM - Inside Map Branch) ---
    "generate_topics": {
      "node_id": "generate_topics",
      "node_category": "topic_generation",
      "node_name": "llm",
      "node_config": {
          "llm_config": {
              "model_spec": {"provider": DEFAULT_LLM_PROVIDER, "model": DEFAULT_LLM_MODEL},
              "temperature": TEMPERATURE,
              "max_tokens": MAX_TOKENS
          },
          "output_schema": {
             "schema_definition": TOPIC_LLM_OUTPUT_SCHEMA,
             "convert_loaded_schema_to_pydantic": False
          },
      }
      # Reads (private): user_prompt, system_prompt
      # Writes: structured_output -> all_generated_topics (state reducer)
    },

    # --- Check Topic Count Node (after first topic generation) ---
    "check_topic_count": {
      "node_id": "check_topic_count",
      "node_category": "topic_generation",
      "node_name": "if_else_condition",
      "node_config": {
        "tagged_conditions": [
          {
            "tag": "topic_count_check", 
            "condition_groups": [{
              "logical_operator": "and",
              "conditions": [{
                "field": "metadata.iteration_count",
                "operator": "less_than",
                "value_path": "merged_data.total_topics_needed"
              }]
            }],
            "group_logical_operator": "and"
          }
        ],
        "branch_logic_operator": "and"
      }
      # Reads: topic_generation_metadata from state, total_topics_needed from state
      # Writes: branch, tag_results, condition_result
    },

    # --- Router Based on Topic Count Check ---
    "route_on_topic_count": {
      "node_id": "route_on_topic_count",
      "node_category": "topic_generation",
      "node_name": "router_node",
      "node_config": {
        "choices": ["construct_additional_topic_prompt", "construct_delete_search_params"],
        "allow_multiple": False,
        "choices_with_conditions": [
          {
            "choice_id": "construct_additional_topic_prompt", # Continue generating more topics
            "input_path": "if_else_condition_tag_results.topic_count_check",
            "target_value": True
          },
          {
            "choice_id": "construct_delete_search_params", # End loop and prepare delete
            "input_path": "if_else_condition_tag_results.topic_count_check",
            "target_value": False,
          }
        ]
      }
      # Reads: if_else_condition_tag_results, iteration_branch_result from check_topic_count
      # Routes to: construct_additional_topic_prompt OR construct_delete_search_params
    },

    # --- Construct Additional Topic Prompt ---
    "construct_additional_topic_prompt": {
      "node_id": "construct_additional_topic_prompt",
      "node_category": "topic_generation",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "additional_topic_prompt": {
            "id": "additional_topic_prompt",
            "template": TOPIC_ADDITIONAL_USER_PROMPT_TEMPLATE,

          },
        }
      }
    },

    # --- Construct Delete Search Params ---
    "construct_delete_search_params": {
      "node_id": "construct_delete_search_params",
      "node_category": "system",
      "node_name": "transform_data",
      "node_config": {
        "merge_conflicting_paths_as_list": False,
        "mappings": [
          { "source_path": "search_params.input_namespace_field", "destination_path": "input_namespace_field" },
          { "source_path": "search_params.input_namespace_field_pattern", "destination_path": "input_namespace_field_pattern" },
          { "source_path": "search_params.docname_pattern", "destination_path": "docname_pattern" },
          { "source_path": "start_date", "destination_path": "value_filter.scheduled_date.$gt" },
          { "source_path": "end_date", "destination_path": "value_filter.scheduled_date.$lte" }
        ]
      }
    },

    # --- Delete Existing Entries in Window ---
    "delete_previous_entries": {
      "node_id": "delete_previous_entries",
      "node_category": "system",
      "node_name": "delete_customer_data",
      "node_config": {
        "search_params_input_path": "search_params"
      }
    },


    # --- 11. Store All Generated Topics (After Map Completes) ---
    "store_all_topics": {
      "node_id": "store_all_topics",
      "node_category": "system",
      "node_name": "store_customer_data", # Store the final list
      "node_config": {
          "global_versioning": { "is_versioned": LINKEDIN_IDEA_IS_VERSIONED, "operation": "upsert_versioned"},
          "global_is_shared": False,
          "store_configs": [
              {
                  # Store the entire list collected in the state
                  "input_field_path": "all_generated_topics", # Mapped from state
                  "process_list_items_separately": True,
                  "target_path": {
                      "filename_config": {
                          "input_namespace_field_pattern": LINKEDIN_IDEA_NAMESPACE_TEMPLATE, 
                          "input_namespace_field": "entity_username",
                          "static_docname": LINKEDIN_IDEA_DOCNAME,
                      }
                  },
                  "generate_uuid": True,
              }
          ],
      },
      "dynamic_input_schema": { # Define expected final inputs
          "fields": {
          }
      }

    },

    # --- 12. Output Node ---
    "output_node": {
      "node_id": "output_node",
      "node_category": "system",
      "node_name": "output_node",
      "node_config": {},

        }
    },
    
    "edges": [
    # --- Input to State ---
    { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "weeks_to_generate", "dst_field": "weeks_to_generate" },
        { "src_field": "past_context_posts_limit", "dst_field": "past_context_posts_limit" },
        { "src_field": "entity_username", "dst_field": "entity_username" },
        { "src_field": "start_date", "dst_field": "start_date" },
        { "src_field": "end_date", "dst_field": "end_date" },
        { "src_field": "search_params", "dst_field": "search_params" },
      ]
    },

    { "src_node_id": "input_node", "dst_node_id": "load_all_context_docs", "mappings": [
        { "src_field": "entity_username", "dst_field": "entity_username" },
      ], "description": "Trigger context docs loading."
    },

    { "src_node_id": "input_node", "dst_node_id": "load_draft_posts",
      "mappings": [
        { "src_field": "entity_username", "dst_field": "entity_username" },
      ],
    },

    # --- State Updates from Loaders ---
    { "src_node_id": "load_all_context_docs", "dst_node_id": "$graph_state", "mappings": [
        # Store the lists under their respective keys in state
        { "src_field": "strategy_doc", "dst_field": "strategy_doc"},
        { "src_field": "scraped_posts", "dst_field": "scraped_posts"},
        { "src_field": "user_profile", "dst_field": "user_profile"}
      ]
    },
    # --- Start Draft Posts Loading ---
    

    { "src_node_id": "load_draft_posts", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "draft_posts", "dst_field": "draft_posts"}
      ]
    },

    # --- Trigger Context Preparation after Loads ---
    # Edges from all loaders feeding into prepare_generation_context (fan-in enabled)
    { "src_node_id": "load_all_context_docs", "dst_node_id": "prepare_generation_context"},
    { "src_node_id": "load_draft_posts", "dst_node_id": "prepare_generation_context"},

    # --- Mapping State to Context Prep Node ---
    { "src_node_id": "$graph_state", "dst_node_id": "prepare_generation_context", "mappings": [
        { "src_field": "draft_posts", "dst_field": "draft_posts" },
        { "src_field": "scraped_posts", "dst_field": "scraped_posts" },
        { "src_field": "past_context_posts_limit", "dst_field": "past_context_posts_limit" },
        { "src_field": "weeks_to_generate", "dst_field": "weeks_to_generate" },
        { "src_field": "user_profile", "dst_field": "user_profile" },
      ]
    },

    # --- Map Iteration -> Construct Prompt (Private Edge) ---
    { "src_node_id": "prepare_generation_context", "dst_node_id": "construct_topic_prompt",
      "mappings": [
        { "src_field": "merged_data", "dst_field": "merged_data" },
      ]
    },

    { "src_node_id": "prepare_generation_context", "dst_node_id": "$graph_state",
      "mappings": [
        { "src_field": "merged_data", "dst_field": "merged_data" },
      ]
    },

    # --- State -> Construct Prompt (Public Edges for Context) ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_topic_prompt", "mappings": [
        { "src_field": "strategy_doc", "dst_field": "strategy_doc" },
        { "src_field": "user_profile", "dst_field": "user_profile" },
        { "src_field": "merged_data", "dst_field": "merged_data" },
      ]
    },

    # --- Construct Prompt -> Generate Topics (Private Edge) ---
    { "src_node_id": "construct_topic_prompt", "dst_node_id": "generate_topics", "mappings": [
        { "src_field": "topic_user_prompt", "dst_field": "user_prompt"},
        { "src_field": "topic_system_prompt", "dst_field": "system_prompt"}
      ], "description": "Private edge: Sends prompts to LLM."
    },
    # --- State -> Generate Topics (Public Edge for History) ---
    { "src_node_id": "$graph_state", "dst_node_id": "generate_topics", "mappings": [
        { "src_field": "generate_topics_messages_history", "dst_field": "messages_history"}
      ]
    },

    # --- Generate Topics -> State (Public Edge for Collection/History Update) ---
    { "src_node_id": "generate_topics", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "all_generated_topics"}, # Collected by reducer
        { "src_field": "current_messages", "dst_field": "generate_topics_messages_history"} # Update history
      ]
    },
    

    # --- Generate Topics -> Check Topic Count
    { "src_node_id": "generate_topics", "dst_node_id": "check_topic_count", "mappings": [
        { "src_field": "metadata", "dst_field": "metadata"} # Collected by reducer
      ]},

    # --- State -> Check Topic Count (for metadata)
    { "src_node_id": "$graph_state", "dst_node_id": "check_topic_count", "mappings": [
        { "src_field": "merged_data", "dst_field": "merged_data" }
      ]
    },

    # --- Check Topic Count -> Route on Topic Count
    { "src_node_id": "check_topic_count", "dst_node_id": "route_on_topic_count", "mappings": [
        { "src_field": "tag_results", "dst_field": "if_else_condition_tag_results" },
        { "src_field": "condition_result", "dst_field": "if_else_overall_condition_result" }
      ]
    },

    # --- Route on Topic Count -> Construct Additional Topic Prompt (if more topics needed)
    { "src_node_id": "route_on_topic_count", "dst_node_id": "construct_additional_topic_prompt" },

    # --- Route on Topic Count -> Construct Delete Params (if all topics generated)
    { "src_node_id": "route_on_topic_count", "dst_node_id": "construct_delete_search_params" },

    # --- State to Construct Delete Params ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_delete_search_params", "mappings": [
        { "src_field": "search_params", "dst_field": "search_params" },
        { "src_field": "start_date", "dst_field": "start_date" },
        { "src_field": "end_date", "dst_field": "end_date" }
      ]
    },

    # --- Construct Delete Params to Delete Node ---
    { "src_node_id": "construct_delete_search_params", "dst_node_id": "delete_previous_entries", "mappings": [
        { "src_field": "transformed_data", "dst_field": "search_params" }
      ]
    },

    # --- State to Delete Node (to resolve input_namespace_field path) ---
    { "src_node_id": "$graph_state", "dst_node_id": "delete_previous_entries", "mappings": [
        { "src_field": "entity_username", "dst_field": "entity_username" }
      ]
    },

    # --- Delete then Store ---
    { "src_node_id": "delete_previous_entries", "dst_node_id": "store_all_topics" },

    # --- Trigger Storage (After Map Completes) ---
    { "src_node_id": "$graph_state", "dst_node_id": "store_all_topics", "mappings": [
        { "src_field": "all_generated_topics", "dst_field": "all_generated_topics"},
        { "src_field": "entity_username", "dst_field": "entity_username" }
      ]
    },

    # --- Construct Additional Topic Prompt -> Generate Topics (completes the loop)
    { "src_node_id": "construct_additional_topic_prompt", "dst_node_id": "generate_topics", "mappings": [
        { "src_field": "additional_topic_prompt", "dst_field": "user_prompt" },
      ]
    },

    { "src_node_id": "store_all_topics", "dst_node_id": "output_node", 
     "mappings": [
        { "src_field": "paths_processed", "dst_field": "final_post_paths"}
      ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "all_generated_topics": "collect_values",   # Collect topic objects from each generation iteration
                "generate_topics_messages_history": "add_messages" # Message history for topic generation LLM
            }
        }
    }
}