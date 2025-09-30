import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_SCRAPED_PROFILE_DOCNAME,
    LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_AI_VISIBILITY_TEST_DOCNAME,
    LINKEDIN_USER_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_AI_VISIBILITY_RAW_DATA_DOCNAME,
    LINKEDIN_UPLOADED_FILES_NAMESPACE_TEMPLATE,
)

from kiwi_client.workflows.active.content_diagnostics.executive_ai_visibility_sandbox.wf_llm_inputs import (
    # LLM Configuration
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,

    EXEC_VISIBILITY_SYSTEM_PROMPT,
    EXEC_VISIBILITY_USER_PROMPT_TEMPLATE,
    EXEC_VISIBILITY_QUERIES_SCHEMA,
    EXEC_VISIBILITY_REPORT_SYSTEM_PROMPT,
    EXEC_VISIBILITY_REPORT_USER_PROMPT_TEMPLATE,
    EXEC_VISIBILITY_REPORT_SCHEMA,
)

workflow_graph_schema = {
    "nodes": {
        # 1) Input
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "entity_username": {"type": "str", "required": True},
                    "enable_cache": {"type": "bool", "required": False},
                    "cache_lookback_days": {"type": "int", "required": False},
                }
            },
        },

        # 2) Load required context docs
        "load_context_docs": {
            "node_id": "load_context_docs",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_USER_PROFILE_DOCNAME,
                        },
                        "output_field_name": "linkedin_user_profile_doc",
                    },
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_SCRAPED_PROFILE_DOCNAME,
                        },
                        "output_field_name": "linkedin_scraped_profile_doc",
                    },
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 4.3 Executive Query Generation ---
        "construct_exec_queries_prompt": {
            "node_id": "construct_exec_queries_prompt",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,
            "node_config": {
                "prompt_templates": {
                    "system_prompt": {"id": "system_prompt", "template": EXEC_VISIBILITY_SYSTEM_PROMPT, "variables": {}},
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": EXEC_VISIBILITY_USER_PROMPT_TEMPLATE,
                        "variables": {"linkedin_user_profile": None, 
                                      "linkedin_scraped_profile": None,
                                      "current_date": "$current_date"
                                      },
                        "construct_options": {
                            "linkedin_user_profile": "linkedin_user_profile_doc",
                            "linkedin_scraped_profile": "linkedin_scraped_profile_doc"
                        },
                    },
                }
            },
        },
        "generate_exec_queries": {
            "node_id": "generate_exec_queries",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": LLM_MODEL},
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
                "output_schema": {"schema_definition": EXEC_VISIBILITY_QUERIES_SCHEMA, "convert_loaded_schema_to_pydantic": False},
            },
        },

        "exec_ai_query": {
            "node_id": "exec_ai_query",
            "node_name": "ai_answer_engine_scraper",
            "node_config": {
                "return_nested_entity_results": True,
                "entity_name_path": "entity_name"
            }
        },

        # Store raw scraper results to uploaded_files namespace
        "store_exec_raw_scraper_results": {
            "node_id": "store_exec_raw_scraper_results",
            "node_name": "store_customer_data",
            "node_config": {
                "store_configs": [
                    {
                        "input_field_path": "query_results",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": LINKEDIN_UPLOADED_FILES_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": LINKEDIN_USER_AI_VISIBILITY_RAW_DATA_DOCNAME
                            }
                        },
                        "generate_uuid": True
                    }
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_versioning": {"is_versioned": False, "operation": "upsert"}
            }
        },

        # 6.3 Executive Visibility Report
        "construct_exec_report_prompt": {
            "node_id": "construct_exec_report_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "system_prompt": {"id": "system_prompt", "template": EXEC_VISIBILITY_REPORT_SYSTEM_PROMPT, "variables": {}},
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": EXEC_VISIBILITY_REPORT_USER_PROMPT_TEMPLATE,
                        "variables": {"loaded_query_results": None},
                        "construct_options": {"loaded_query_results": "loaded_query_results"},
                    },
                }
            },
        },
        "generate_exec_report": {
            "node_id": "generate_exec_report",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": LLM_MODEL},
                    "temperature": 0.4,
                    "max_tokens": 3500,
                },
                "output_schema": {"schema_definition": EXEC_VISIBILITY_REPORT_SCHEMA, "convert_loaded_schema_to_pydantic": False},
            },
        },
        "store_exec_report": {
            "node_id": "store_exec_report",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": True, "operation": "upsert_versioned"},
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": LINKEDIN_USER_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": LINKEDIN_USER_AI_VISIBILITY_TEST_DOCNAME,
                            }
                        },
                    }
                ],
            },
        },

        # Final output
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {},
            "enable_node_fan_in": True,
        },
    },
    "edges": [
        # --- Initial Setup: Store inputs to graph state ---
        {"src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "entity_username", "dst_field": "entity_username"},
            {"src_field": "enable_cache", "dst_field": "enable_cache"},
            {"src_field": "cache_lookback_days", "dst_field": "cache_lookback_days"},
        ]},

        # Input -> Load context
        {"src_node_id": "input_node", "dst_node_id": "load_context_docs", "mappings": [
            {"src_field": "entity_username", "dst_field": "entity_username"},
        ]},

        # Load context -> State
        {"src_node_id": "load_context_docs", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "linkedin_user_profile_doc", "dst_field": "linkedin_user_profile_doc"},
            {"src_field": "linkedin_scraped_profile_doc", "dst_field": "linkedin_scraped_profile_doc"},
        ]},

        # Exec path: State -> exec queries prompt
        {"src_node_id": "load_context_docs", "dst_node_id": "construct_exec_queries_prompt", "mappings": [
            {"src_field": "linkedin_user_profile_doc", "dst_field": "linkedin_user_profile_doc"},
            {"src_field": "linkedin_scraped_profile_doc", "dst_field": "linkedin_scraped_profile_doc"},
        ]},
        {"src_node_id": "construct_exec_queries_prompt", "dst_node_id": "generate_exec_queries", "mappings": [
            {"src_field": "user_prompt", "dst_field": "user_prompt"},
            {"src_field": "system_prompt", "dst_field": "system_prompt"},
        ]},

       
        {"src_node_id": "generate_exec_queries", "dst_node_id": "exec_ai_query", "mappings": [
            {"src_field": "structured_output", "dst_field": "query_templates"},
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "exec_ai_query", "mappings": [
            {"src_field": "enable_cache", "dst_field": "enable_mongodb_cache"},
            {"src_field": "cache_lookback_days", "dst_field": "cache_lookback_days"},
            {"src_field": "entity_username", "dst_field": "entity_name"}
        ]},

        # Store raw scraper results to uploaded_files namespace
        {"src_node_id": "exec_ai_query", "dst_node_id": "store_exec_raw_scraper_results", "mappings": [
            {"src_field": "query_results", "dst_field": "query_results"}
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "store_exec_raw_scraper_results", "mappings": [
            {"src_field": "entity_username", "dst_field": "entity_username"}
        ]},

        # Construct report prompts
        {"src_node_id": "exec_ai_query", "dst_node_id": "construct_exec_report_prompt", "mappings": [
            {"src_field": "query_results", "dst_field": "loaded_query_results"}
        ]},

        {"src_node_id": "construct_exec_report_prompt", "dst_node_id": "generate_exec_report", "mappings": [
            {"src_field": "user_prompt", "dst_field": "user_prompt"},
            {"src_field": "system_prompt", "dst_field": "system_prompt"},
        ]},

        # Store generated reports in state
        {"src_node_id": "generate_exec_report", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "exec_report"},
        ]},

        # Store reports
        {"src_node_id": "generate_exec_report", "dst_node_id": "store_exec_report", "mappings": [
            {"src_field": "structured_output", "dst_field": "structured_output"},
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "store_exec_report", "mappings": [
            {"src_field": "entity_username", "dst_field": "entity_username"},
        ]},

        # Store paths in state
        {"src_node_id": "store_exec_report", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "paths_processed", "dst_field": "stored_exec_report_paths"},
        ]},

        # Direct output connections from storage nodes
        {"src_node_id": "store_exec_report", "dst_node_id": "output_node", "mappings": [
            {"src_field": "passthrough_data", "dst_field": "passthrough_data"}
        ]},
    ],
    # --- Define Start and End ---
    "input_node_id": "input_node",
    "output_node_id": "output_node",

    # --- State Reducers ---
    "metadata": {
        "$graph_state": {
            "reducer": {
                # Define how to merge values for specific fields
                "exec_queries": "replace",
                "exec_query_results": "replace",
                "exec_loaded_query_results": "replace",
                "exec_report": "replace",
                "stored_exec_report_paths": "replace",
            }
        }
    }
}