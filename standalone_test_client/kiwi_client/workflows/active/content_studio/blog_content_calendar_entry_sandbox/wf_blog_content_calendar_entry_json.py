"""
Blog Content Calendar Entry Workflow

# Workflow Overview:
1. Generate content topic suggestions for next X weeks: (X) int input optional, default 2
2. Load customer context docs such as company profile, playbook, diagnostic report
3. NO loading of previous posts - generates fresh topics based on strategy
4. Compute total topics needed based on weeks and posting frequency
5. Generate structured topic suggestions (4 topics per slot around common theme)
6. Iterate until required number of topics generated
7. Store all topic suggestions

Key differences from LinkedIn workflow:
- No loading of previous posts (drafts or scraped)
- Uses blog-specific document models
- Includes SEO optimization considerations
- Simpler context preparation without post merging
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
    # Blog Company Profile
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_VERSIONED,
    # Blog Content Strategy/Playbook
    BLOG_CONTENT_STRATEGY_DOCNAME,
    BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_STRATEGY_IS_VERSIONED,

    # Blog Topic Ideas Storage
    BLOG_TOPIC_IDEAS_CARD_DOCNAME,
    BLOG_TOPIC_IDEAS_CARD_NAMESPACE_TEMPLATE,
    BLOG_TOPIC_IDEAS_CARD_IS_VERSIONED,
    BLOG_POST_DOCNAME,
    BLOG_POST_NAMESPACE_TEMPLATE,
    BLOG_POST_IS_VERSIONED,
    BLOG_POST_IS_SHARED,
)
# Import LLM configurations from local wf_llm_inputs
from .wf_llm_inputs import (
    # LLM Model Configuration
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,

    # Perplexity Configuration
    PERPLEXITY_PROVIDER,
    PERPLEXITY_MODEL,
    PERPLEXITY_TEMPERATURE,
    PERPLEXITY_MAX_TOKENS,

    # Workflow Defaults
    DEFAULT_WEEKS_TO_GENERATE,
    DEFAULT_POSTS_PER_WEEK,

    # Prompts and schemas
    TOPIC_USER_PROMPT_TEMPLATE,
    TOPIC_SYSTEM_PROMPT_TEMPLATE,
    TOPIC_LLM_OUTPUT_SCHEMA,
    TOPIC_ADDITIONAL_USER_PROMPT_TEMPLATE,

    RESEARCH_SYSTEM_PROMPT,
    RESEARCH_USER_PROMPT_TEMPLATE,
    RESEARCH_OUTPUT_SCHEMA,
    THEME_SUGGESTION_SYSTEM_PROMPT,
    THEME_SUGGESTION_USER_PROMPT_TEMPLATE,
    THEME_SUGGESTION_OUTPUT_SCHEMA,
    THEME_ADDITIONAL_USER_PROMPT_TEMPLATE,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Workflow Configuration Constants ---

# Tool Executor Configuration
TOOL_EXECUTOR_TIMEOUT = 30.0
TOOL_EXECUTOR_MAX_CONCURRENT = 3

# Search Params Default
SEARCH_PARAMS_DEFAULT = {
                    "input_namespace_field": "company_name",
                    "input_namespace_field_pattern": BLOG_TOPIC_IDEAS_CARD_NAMESPACE_TEMPLATE,
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
              "weeks_to_generate": { 
                  "type": "int", 
                  "required": False, 
                  "default": DEFAULT_WEEKS_TO_GENERATE, 
                  "description": f"Number of weeks ahead to generate topic suggestions for (default: {DEFAULT_WEEKS_TO_GENERATE})." 
              },
              "company_name": {
                  "type": "str", 
                  "required": True,
                  "description": "Company name identifier for loading documents"
              },
              "start_date": {
                  "type": "str",
                  "required": True,
                  "description": "Start date for generating topic suggestions"
              },
              "end_date": {
                  "type": "str",
                  "required": True,
                  "description": "End date for generating topic suggestions"
              },
              "search_params": {
                  "type": "dict",
                  "required": False,
                  "default": SEARCH_PARAMS_DEFAULT,
                  "description": "Default search params object for load node",
              },
          }
        }
    },

        # --- 5. Load Customer Context Documents ---
    "load_all_context_docs": {
        "node_id": "load_all_context_docs",
        "node_category": "system",
        "node_name": "load_customer_data",
        "node_config": {
            "load_paths": [
                {
                    "filename_config": {
                        "input_namespace_field_pattern": BLOG_COMPANY_NAMESPACE_TEMPLATE, 
                        "input_namespace_field": "company_name",
                        "static_docname": BLOG_COMPANY_DOCNAME,
                    },
                    "output_field_name": "company_doc"
                },
                {
                    "filename_config": {
                        "input_namespace_field_pattern": BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE, 
                        "input_namespace_field": "company_name",
                        "static_docname": BLOG_CONTENT_STRATEGY_DOCNAME,
                    },
                    "output_field_name": "playbook"
                }
            ],
            "global_is_shared": False,
            "global_is_system_entity": False,
            "global_schema_options": {"load_schema": False}
        },
    },
 
    # --- 2. Load Previous Posts ---
    "load_previous_posts": {
        "node_id": "load_previous_posts",
        "node_category": "system",
        "node_name": "load_multiple_customer_data",
        "node_config": {
            "namespace_pattern": BLOG_POST_NAMESPACE_TEMPLATE,
            "namespace_pattern_input_path": "company_name",
            "include_shared": False,
            "include_user_specific": True,
            "include_system_entities": False,
            "limit": 10,
            "sort_by": "updated_at",
            "sort_order": "desc",
            "output_field_name": "previous_posts"
        }
    },

    # --- 3. Load Previous Topics ---
    "load_previous_topics": {
        "node_id": "load_previous_topics",
        "node_category": "system",
        "node_name": "load_multiple_customer_data",
        "node_config": {
            "namespace_pattern": BLOG_TOPIC_IDEAS_CARD_NAMESPACE_TEMPLATE,
            "namespace_pattern_input_path": "company_name", 
            "include_shared": False,
            "include_user_specific": True,
            "include_system_entities": False,
            "limit": 10,
            "sort_by": "updated_at",
            "sort_order": "desc",
            "output_field_name": "previous_topics"
        }
    },
    


    # --- 4. Prepare Generation Context (Extract posts_per_week from playbook) ---
    "prepare_generation_context": {
      "node_id": "prepare_generation_context",
      "node_category": "system",
      "node_name": "merge_aggregate",
      "enable_node_fan_in": True,
      "node_config": {
        "operations": [
          # Operation 1: Extract posts_per_week from playbook
          {
            "output_field_name": "posts_per_week",
            "select_paths": ["playbook.posts_per_week"],
            "merge_strategy": {
                "map_phase": {"unspecified_keys_strategy": "ignore"},
                "reduce_phase": {
                    "default_reducer": "replace_right",
                    "error_strategy": "skip_operation"
                }
            },
            "merge_each_object_in_selected_list": False
          },
          # Operation 2: Compute Total Topics Needed - weeks_to_generate * posts_per_week
          {
            "output_field_name": "total_topics_needed",
            "select_paths": ["playbook.posts_per_week"],
            "merge_strategy": {
                "map_phase": {"unspecified_keys_strategy": "ignore"},
                "reduce_phase": {
                    "default_reducer": "replace_right",
                    "error_strategy": "skip_operation"
                },
                "post_merge_transformations": {
                     "total_topics_needed": {
                         "operation_type": "multiply",
                         "operand_path": "weeks_to_generate"
                     }
                },
                "transformation_error_strategy": "skip_operation"
            },
            "merge_each_object_in_selected_list": False
          }
        ]
      },
    },

    # --- 5. Construct Theme Suggestion Prompt ---
    "construct_theme_prompt": {
      "node_id": "construct_theme_prompt",
      "node_category": "theme_generation",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "theme_suggestion_user_prompt": {
            "id": "theme_suggestion_user_prompt",
            "template": THEME_SUGGESTION_USER_PROMPT_TEMPLATE,
            "variables": {
              "company_doc": None,
              "playbook": None,
              "previous_topics": "",
            },
            "construct_options": {
              "company_doc": "company_doc",
              "playbook": "playbook",
              "previous_topics": "previous_topics",
            }
          },
          "theme_suggestion_system_prompt": {
            "id": "theme_suggestion_system_prompt",
            "template": THEME_SUGGESTION_SYSTEM_PROMPT,
            "variables": {}
          }
        }
      }
    },

    # --- 6. Theme Suggestion LLM ---
    "theme_suggestion_llm": {
      "node_id": "theme_suggestion_llm",
      "node_category": "theme_generation",
      "node_name": "llm",
      "node_config": {
        "llm_config": {
          "model_spec": {"provider": DEFAULT_LLM_PROVIDER, "model": DEFAULT_LLM_MODEL},
          "temperature": TEMPERATURE,
          "max_tokens": MAX_TOKENS
        },
        "output_schema": {
          "schema_definition": THEME_SUGGESTION_OUTPUT_SCHEMA,
          "convert_loaded_schema_to_pydantic": False
        }
      }
    },

    # --- 7. Construct Research Prompt ---
    "construct_research_prompt": {
      "node_id": "construct_research_prompt",
      "node_category": "theme_generation",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "research_user_prompt": {
            "id": "research_user_prompt",
            "template": RESEARCH_USER_PROMPT_TEMPLATE,
            "variables": {
              "company_doc": None,
              "playbook": None,
              "previous_posts": "",
              "selected_theme": None
            },
            "construct_options": {
              "company_doc": "company_doc",
              "playbook": "playbook",
              "previous_posts": "previous_posts",
              "selected_theme": "theme_suggestion"
            }
          },
          "research_system_prompt": {
            "id": "research_system_prompt",
            "template": RESEARCH_SYSTEM_PROMPT,
            "variables": {},
          }
        }
      }
    },
    
    # --- 8. Research LLM (Perplexity - Reddit only) ---
    "research_llm": {
      "node_id": "research_llm",
      "node_category": "theme_generation",
      "node_name": "llm",
      "node_config": {
          "llm_config": {
              "model_spec": {"provider": PERPLEXITY_PROVIDER, "model": PERPLEXITY_MODEL},
              "temperature": PERPLEXITY_TEMPERATURE,
              "max_tokens": PERPLEXITY_MAX_TOKENS
          },
          "web_search_options": {
              "search_domain_filter": ["reddit.com", "quora.com"]
          },
          "output_schema": {
             "schema_definition": RESEARCH_OUTPUT_SCHEMA,
             "convert_loaded_schema_to_pydantic": False
          }
      }
    },
    
    # --- 8.1 Check Theme Iteration ---
    "check_theme_iteration": {
      "node_id": "check_theme_iteration",
      "node_category": "theme_generation",
      "node_name": "if_else_condition",
      "node_config": {
        "tagged_conditions": [
          {
            "tag": "is_second_iteration",
            "condition_groups": [{
              "logical_operator": "and",
              "conditions": [{
                "field": "metadata.iteration_count",
                "operator": "greater_than",
                "value": 1
              }]
            }],
            "group_logical_operator": "and"
          }
        ],
        "branch_logic_operator": "and"
      }
    },

    # --- 8.2 Router Based on Theme Iteration ---
    "route_on_theme_iteration": {
      "node_id": "route_on_theme_iteration",
      "node_category": "theme_generation",
      "node_name": "router_node",
      "node_config": {
        "choices": ["construct_topic_prompt", "construct_additional_topic_prompt"],
        "allow_multiple": False,
        "choices_with_conditions": [
          {
            "choice_id": "construct_additional_topic_prompt",
            "input_path": "if_else_condition_tag_results.is_second_iteration",
            "target_value": True
          },
          {
            "choice_id": "construct_topic_prompt",
            "input_path": "if_else_condition_tag_results.is_second_iteration",
            "target_value": False
          }
        ]
      }
    },

    # --- 8.3 Construct Additional Topic Prompt ---
    "construct_additional_topic_prompt": {
      "node_id": "construct_additional_topic_prompt",
      "node_category": "topic_generation",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "additional_topic_user_prompt": {
            "id": "additional_topic_user_prompt",
            "template": TOPIC_ADDITIONAL_USER_PROMPT_TEMPLATE,
            "variables": {
              "posts_per_week": None,
              "current_datetime": "$current_date",
              "research_insights": None,
              "selected_theme": None
            },
            "construct_options": {
              "posts_per_week": "playbook.posts_per_week",
              "research_insights": "research_insights",
              "selected_theme": "theme_suggestion"
            }
          }
        }
      }
    },

    # --- 9. Construct Topic Prompt ---
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
              "company_doc": None,
              "playbook": None,
              "current_datetime": "$current_date",
              "previous_topics": "",
              "research_insights": None,
              "selected_theme": None
            },
            "construct_options": {
               "company_doc": "company_doc",
               "playbook": "playbook",
               "previous_topics": "previous_topics",
               "research_insights": "research_insights",
               "selected_theme": "theme_suggestion"
            }
          },
          "topic_system_prompt": {
            "id": "topic_system_prompt",
            "template": TOPIC_SYSTEM_PROMPT_TEMPLATE,
            "variables": { 
                "schema": json.dumps(TOPIC_LLM_OUTPUT_SCHEMA, indent=2), 
                "current_datetime": "$current_date" 
            },
            "construct_options": {}
          }
        }
      }
    },

    # --- 10. Generate Topics (LLM) ---
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
    },

    # --- 11. Check Topic Count ---
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
    },

    # --- 12. Router Based on Topic Count Check ---
    "route_on_topic_count": {
      "node_id": "route_on_topic_count",
      "node_category": "topic_generation",
      "node_name": "router_node",
      "node_config": {
        "choices": ["construct_additional_theme_prompt", "construct_delete_search_params"],
        "allow_multiple": False,
        "choices_with_conditions": [
          {
            "choice_id": "construct_additional_theme_prompt",
            "input_path": "if_else_condition_tag_results.topic_count_check",
            "target_value": True
          },
          {
            "choice_id": "construct_delete_search_params",
            "input_path": "if_else_condition_tag_results.topic_count_check",
            "target_value": False,
          }
        ]
      }
    },

    # --- 13. Construct Additional Theme Prompt ---
    "construct_additional_theme_prompt": {
      "node_id": "construct_additional_theme_prompt",
      "node_category": "theme_generation",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "additional_theme_user_prompt": {
            "id": "additional_theme_user_prompt",
            "template": THEME_ADDITIONAL_USER_PROMPT_TEMPLATE,
            "variables": {
              "all_generated_topics": None,
              "previous_topics": None
            },
            "construct_options": {
              "all_generated_topics": "all_generated_topics",
              "previous_topics": "previous_topics"
            }
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

    # --- 14. Store All Generated Topics ---
    "store_all_topics": {
      "node_id": "store_all_topics",
      "node_category": "system",
      "node_name": "store_customer_data",
      "node_config": {
          "global_versioning": { 
              "is_versioned": BLOG_TOPIC_IDEAS_CARD_IS_VERSIONED, 
              "operation": "upsert_versioned"
          },
          "global_is_shared": False,
          "store_configs": [
              {
                  "input_field_path": "all_generated_topics",
                  "process_list_items_separately": True,
                  "target_path": {
                      "filename_config": {
                          "input_namespace_field_pattern": BLOG_TOPIC_IDEAS_CARD_NAMESPACE_TEMPLATE, 
                          "input_namespace_field": "company_name",
                          "static_docname": BLOG_TOPIC_IDEAS_CARD_DOCNAME,
                      }
                  },
                  "generate_uuid": True,
              }
          ],
      }
    },

    # --- 15. Output Node ---
    "output_node": {
      "node_id": "output_node",
      "node_category": "system",
      "node_name": "output_node",
      "node_config": {},
    },

  },

  # --- Edges Defining Data Flow ---
  "edges": [
    # --- Input to State ---
    { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "weeks_to_generate", "dst_field": "weeks_to_generate" },
        { "src_field": "company_name", "dst_field": "company_name" },
        { "src_field": "start_date", "dst_field": "start_date" },
        { "src_field": "end_date", "dst_field": "end_date" },
        { "src_field": "search_params", "dst_field": "search_params" }
      ]
    },

    # --- Input to Load Context Documents ---
    { "src_node_id": "input_node", "dst_node_id": "load_all_context_docs", "mappings": [
        { "src_field": "company_name", "dst_field": "company_name" }
      ]
    },

    # --- State Updates from Loaders ---
    { "src_node_id": "load_all_context_docs", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "company_doc", "dst_field": "company_doc"},
        { "src_field": "playbook", "dst_field": "playbook"}
      ]
    },

    # --- Load Context Docs triggers Load Previous Posts ---
    { "src_node_id": "load_all_context_docs", "dst_node_id": "load_previous_posts" },

    # --- State to Load Previous Posts (provide company name) ---
    { "src_node_id": "$graph_state", "dst_node_id": "load_previous_posts", "mappings": [
        { "src_field": "company_name", "dst_field": "company_name" }
      ]
    },

    # --- Load Previous Posts triggers Load Previous Topics ---
    { "src_node_id": "load_previous_posts", "dst_node_id": "load_previous_topics" },

    # --- State to Load Previous Topics (provide company name) ---
    { "src_node_id": "$graph_state", "dst_node_id": "load_previous_topics", "mappings": [
        { "src_field": "company_name", "dst_field": "company_name" }
      ]
    },

    # --- Load Previous Posts to State ---
    { "src_node_id": "load_previous_posts", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "previous_posts", "dst_field": "previous_posts" }
      ]
    },

    # --- Load Previous Topics to State ---
    { "src_node_id": "load_previous_topics", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "previous_topics", "dst_field": "previous_topics" }
      ]
    },

    # --- Load Previous Topics triggers Context Preparation ---
    { "src_node_id": "load_previous_topics", "dst_node_id": "prepare_generation_context" },
    
    # --- Mapping State to Context Prep Node ---
    { "src_node_id": "$graph_state", "dst_node_id": "prepare_generation_context", "mappings": [
        { "src_field": "playbook", "dst_field": "playbook"},
        { "src_field": "weeks_to_generate", "dst_field": "weeks_to_generate" }
      ]
    },

    # --- Context Prep to State ---
    { "src_node_id": "prepare_generation_context", "dst_node_id": "$graph_state",
      "mappings": [
        { "src_field": "merged_data", "dst_field": "merged_data" }
      ]
    },

    # --- Trigger Theme Suggestion ---
    { "src_node_id": "prepare_generation_context", "dst_node_id": "construct_theme_prompt" },

    # --- State to Construct Theme Prompt ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_theme_prompt", "mappings": [
        { "src_field": "company_doc", "dst_field": "company_doc" },
        { "src_field": "playbook", "dst_field": "playbook"},
        { "src_field": "previous_topics", "dst_field": "previous_topics" },
      ]
    },

    # --- Theme Prompt to LLM ---
    { "src_node_id": "construct_theme_prompt", "dst_node_id": "theme_suggestion_llm", "mappings": [
        { "src_field": "theme_suggestion_user_prompt", "dst_field": "user_prompt" },
        { "src_field": "theme_suggestion_system_prompt", "dst_field": "system_prompt" }
      ]
    },

    { "src_node_id": "$graph_state", "dst_node_id": "theme_suggestion_llm", "mappings": [
        { "src_field": "theme_suggestion_messages_history", "dst_field": "messages_history" }
      ]
    },

    # --- Theme LLM to State ---
    { "src_node_id": "theme_suggestion_llm", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "theme_suggestion" },
        { "src_field": "metadata", "dst_field": "theme_suggestion_metadata" },
        { "src_field": "current_messages", "dst_field": "theme_suggestion_messages_history" }
      ]
    },

    # --- Trigger Research Prompt ---
    { "src_node_id": "theme_suggestion_llm", "dst_node_id": "construct_research_prompt" },

    # --- State to Construct Research Prompt ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_research_prompt", "mappings": [
        { "src_field": "company_doc", "dst_field": "company_doc" },
        { "src_field": "playbook", "dst_field": "playbook" },
        { "src_field": "previous_posts", "dst_field": "previous_posts" },
        { "src_field": "theme_suggestion", "dst_field": "theme_suggestion" }
      ]
    },

    # --- Research Prompt to LLM ---
    { "src_node_id": "construct_research_prompt", "dst_node_id": "research_llm", "mappings": [
        { "src_field": "research_user_prompt", "dst_field": "user_prompt" },
        { "src_field": "research_system_prompt", "dst_field": "system_prompt" }
      ]
    },

    # --- Research LLM to State ---
    { "src_node_id": "research_llm", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "research_insights" }
      ]
    },

    # --- Research triggers Theme Iteration Check ---
    { "src_node_id": "research_llm", "dst_node_id": "check_theme_iteration" },

    # --- State to Theme Iteration Check ---
    { "src_node_id": "$graph_state", "dst_node_id": "check_theme_iteration", "mappings": [
        { "src_field": "theme_suggestion_metadata", "dst_field": "metadata" }
      ]
    },

    # --- Theme Iteration Check to Router ---
    { "src_node_id": "check_theme_iteration", "dst_node_id": "route_on_theme_iteration", "mappings": [
        { "src_field": "tag_results", "dst_field": "if_else_condition_tag_results" },
        { "src_field": "condition_result", "dst_field": "if_else_overall_condition_result" }
      ]
    },

    # --- Router to Construct Topic Prompt ---
    { "src_node_id": "route_on_theme_iteration", "dst_node_id": "construct_topic_prompt" },

    # --- Router to Additional Topic Prompt ---
    { "src_node_id": "route_on_theme_iteration", "dst_node_id": "construct_additional_topic_prompt" },

    # --- State to Construct Additional Topic Prompt ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_additional_topic_prompt", "mappings": [
        { "src_field": "playbook", "dst_field": "playbook" },
        { "src_field": "research_insights", "dst_field": "research_insights" },
        { "src_field": "theme_suggestion", "dst_field": "selected_theme" }
      ]
    },

    # --- Additional Topic Prompt to Generate Topics ---
    { "src_node_id": "construct_additional_topic_prompt", "dst_node_id": "generate_topics", "mappings": [
        { "src_field": "additional_topic_user_prompt", "dst_field": "user_prompt"},
      ]
    },

    # --- State to Construct Topic Prompt ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_topic_prompt", "mappings": [
        { "src_field": "company_doc", "dst_field": "company_doc" },
        { "src_field": "playbook", "dst_field": "playbook"},
        { "src_field": "previous_topics", "dst_field": "previous_topics" },
        { "src_field": "research_insights", "dst_field": "research_insights" },
        { "src_field": "theme_suggestion", "dst_field": "selected_theme" }
      ]
    },

    # --- Construct Prompt to Generate Topics ---
    { "src_node_id": "construct_topic_prompt", "dst_node_id": "generate_topics", "mappings": [
        { "src_field": "topic_user_prompt", "dst_field": "user_prompt"},
        { "src_field": "topic_system_prompt", "dst_field": "system_prompt"}
      ], "description": "Private edge: Sends prompts to LLM."
    },

    # --- State to Generate Topics (for history) ---
    { "src_node_id": "$graph_state", "dst_node_id": "generate_topics", "mappings": [
        { "src_field": "generate_topics_messages_history", "dst_field": "messages_history"}
      ]
    },

    # --- Generate Topics to State ---
    { "src_node_id": "generate_topics", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "all_generated_topics"},
        { "src_field": "current_messages", "dst_field": "generate_topics_messages_history"}
      ]
    },

    # --- Generate Topics to Check Topic Count ---
    { "src_node_id": "generate_topics", "dst_node_id": "check_topic_count", "mappings": [
        { "src_field": "metadata", "dst_field": "metadata"}
      ]},

    # --- State to Check Topic Count ---
    { "src_node_id": "$graph_state", "dst_node_id": "check_topic_count", "mappings": [
        { "src_field": "merged_data", "dst_field": "merged_data" }
      ]
    },

    # --- Check Topic Count to Router ---
    { "src_node_id": "check_topic_count", "dst_node_id": "route_on_topic_count", "mappings": [
        { "src_field": "tag_results", "dst_field": "if_else_condition_tag_results" },
        { "src_field": "condition_result", "dst_field": "if_else_overall_condition_result" }
      ]
    },

    # --- Router to Additional Theme Prompt ---
    { "src_node_id": "route_on_topic_count", "dst_node_id": "construct_additional_theme_prompt" },

    # --- State to Additional Theme Prompt ---
    { "src_node_id": "$graph_state", "dst_node_id": "construct_additional_theme_prompt", "mappings": [
        { "src_field": "all_generated_topics", "dst_field": "all_generated_topics" },
        # { "src_field": "company_doc", "dst_field": "company_doc" },
        # { "src_field": "playbook", "dst_field": "playbook" },
        { "src_field": "previous_topics", "dst_field": "previous_topics" }
      ]
    },

    # --- Router to Construct Topic Feedback ---
    { "src_node_id": "construct_additional_theme_prompt", "dst_node_id": "theme_suggestion_llm",
      "mappings": [
        { "src_field": "additional_theme_user_prompt", "dst_field": "user_prompt"}      ]
    }, 

    # --- Router to Construct Delete Params ---
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
        { "src_field": "company_name", "dst_field": "company_name" }
      ]
    },

    # --- Delete then Store ---
    { "src_node_id": "delete_previous_entries", "dst_node_id": "store_all_topics" },

    # --- State to Store ---
    { "src_node_id": "$graph_state", "dst_node_id": "store_all_topics", "mappings": [
        { "src_field": "all_generated_topics", "dst_field": "all_generated_topics"},
        { "src_field": "company_name", "dst_field": "company_name" }
      ]
    },

    # --- Store to Output ---
    { "src_node_id": "store_all_topics", "dst_node_id": "output_node", "mappings": [
        { "src_field": "paths_processed", "dst_field": "final_topics_list"}
      ]
    },
  ],

  # --- Define Start and End ---
  "input_node_id": "input_node",
  "output_node_id": "output_node",

  # --- State Reducers ---
  "metadata": {
      "$graph_state": {
        "reducer": {
          "all_generated_topics": "collect_values",
          "generate_topics_messages_history": "add_messages",
          "previous_posts": "replace",
          "previous_topics": "replace",
          "research_insights": "replace",
          "content_pillars": "replace",
          "theme_suggestion": "replace",
          "theme_suggestion_metadata": "replace"
          }
      }
  }
}