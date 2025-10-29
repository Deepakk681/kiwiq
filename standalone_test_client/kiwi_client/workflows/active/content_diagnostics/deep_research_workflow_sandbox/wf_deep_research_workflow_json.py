import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field


from kiwi_client.workflows.active.document_models.customer_docs import (
    # Deep Research Report
    BLOG_DEEP_RESEARCH_REPORT_DOCNAME,
    BLOG_DEEP_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
    BLOG_DEEP_RESEARCH_REPORT_IS_VERSIONED,
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_DEEP_RESEARCH_REPORT_DOCNAME,
    BLOG_DEEP_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
    BLOG_DEEP_RESEARCH_REPORT_IS_VERSIONED,
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_DEEP_RESEARCH_REPORT_DOCNAME,
    BLOG_DEEP_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
    BLOG_DEEP_RESEARCH_REPORT_IS_VERSIONED,
)

from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_SCRAPED_PROFILE_DOCNAME,
    LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_DEEP_RESEARCH_REPORT_DOCNAME,
    LINKEDIN_DEEP_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
    LINKEDIN_DEEP_RESEARCH_REPORT_IS_VERSIONED,
)

from kiwi_client.workflows.active.content_diagnostics.deep_research_workflow_sandbox.wf_llm_inputs import (
    # LLM Configuration
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    MAX_TOOL_CALLS_LINKEDIN,
    MAX_TOOL_CALLS_BLOG,
    STRUCTURED_OUTPUT_PROVIDER,
    STRUCTURED_OUTPUT_MODEL,
    STRUCTURED_OUTPUT_MAX_TOKENS,
    # Content Strategy only schemas and prompts
    GENERATION_SCHEMA_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY,
    SYSTEM_PROMPT_TEMPLATE_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY,
    USER_PROMPT_TEMPLATE_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY,
    # LinkedIn Research only schemas and prompts
    SCHEMA_TEMPLATE_FOR_LINKEDIN_RESEARCH,
    SYSTEM_PROMPT_TEMPLATE_FOR_LINKEDIN_RESEARCH,
    USER_PROMPT_TEMPLATE_FOR_LINKEDIN_RESEARCH,
)

workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node with routing options ---
        "input_node": {
            "node_id": "input_node",
            "node_category": "system",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "company_name": { "type": "str", "required": False, "description": "Name of the company to analyze" },
                    "entity_username": { "type": "str", "required": False, "description": "LinkedIn username for executive research" },
                    "run_blog_analysis": { "type": "bool", "required": True, "description": "Whether to run content strategy research" },
                    "run_linkedin_exec": { "type": "bool", "required": True, "description": "Whether to run LinkedIn research" }
                }
            }
        },

        "document_router": {
            "node_id": "document_router",
            "node_category": "system",
            "node_name": "router_node",
            "node_config": {
                "choices": [
                    "load_company_data",
                    "load_linkedin_data"
                ],
                "allow_multiple": True,
                "default_choice": None,
                "choices_with_conditions": [
                    {"choice_id": "load_company_data", "input_path": "run_blog_analysis", "target_value": True},
                    {"choice_id": "load_linkedin_data", "input_path": "run_linkedin_exec", "target_value": True}
                ]
            }
        },
        
        # --- 2. Load Company Data ---
        "load_company_data": {
            "node_id": "load_company_data",
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
                        "output_field_name": "company_data"
                    },
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False}
            },
        },
        
        # --- 3. Load LinkedIn Data (conditional) ---
        "load_linkedin_data": {
            "node_id": "load_linkedin_data",
            "node_category": "system",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_USER_PROFILE_DOCNAME,
                        },
                        "output_field_name": "linkedin_user_profile"
                    },
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_SCRAPED_PROFILE_DOCNAME,
                        },
                        "output_field_name": "linkedin_scraped_profile"
                    },
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False}
            },
        },
        
        # --- 5. Prompt Constructors for Different Research Types ---
        "construct_content_strategy_prompt": {
            "node_id": "construct_content_strategy_prompt",
            "node_category": "research",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": USER_PROMPT_TEMPLATE_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY,
                        "variables": {
                            "company_info": None,
                        },
                        "construct_options": {
                            "company_info": "company_data"
                        }
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": SYSTEM_PROMPT_TEMPLATE_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY,
                        "variables": {
                            "schema": json.dumps(GENERATION_SCHEMA_FOR_DEEP_RESEARCH_BLOG_CONTENT_STRATEGY, indent=2)
                        },
                        "construct_options": {}
                    }
                }
            }
        },
        
        "construct_linkedin_prompt": {
            "node_id": "construct_linkedin_prompt",
            "node_category": "research",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": USER_PROMPT_TEMPLATE_FOR_LINKEDIN_RESEARCH,
                        "variables": {
                            "linkedin_user_profile": None,
                            "linkedin_scraped_profile": None
                        },
                        "construct_options": {
                            "linkedin_user_profile": "linkedin_user_profile",
                            "linkedin_scraped_profile": "linkedin_scraped_profile"
                        }
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": SYSTEM_PROMPT_TEMPLATE_FOR_LINKEDIN_RESEARCH,
                        "variables": {
                            "schema": json.dumps(SCHEMA_TEMPLATE_FOR_LINKEDIN_RESEARCH, indent=2)
                        },
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 7. Deep Research LLM Nodes for different research types ---
        "deep_researcher_content_strategy": {
            "node_id": "deep_researcher_content_strategy",
            "node_category": "research",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": LLM_PROVIDER, 
                        "model": LLM_MODEL
                    },
                    "temperature": LLM_TEMPERATURE,
                    "max_tool_calls": MAX_TOOL_CALLS_BLOG,
                    "max_tokens": LLM_MAX_TOKENS,
                },
                "output_schema": {
                },
                "tool_calling_config": {
                    "enable_tool_calling": True,
                    "parallel_tool_calls": True
                },
                "tools": [
                    {
                        "tool_name": "web_search",
                        "is_provider_inbuilt_tool": True,
                    }
                ]
            }
        },
        
        "deep_researcher_linkedin": {
            "node_id": "deep_researcher_linkedin",
            "node_category": "research",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": LLM_PROVIDER, 
                        "model": LLM_MODEL
                    },
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS,
                    "max_tool_calls": MAX_TOOL_CALLS_LINKEDIN,
                },
                "output_schema": {
                },
                "tool_calling_config": {
                    "enable_tool_calling": True,
                    "parallel_tool_calls": True
                },
                "tools": [
                    {
                        "tool_name": "web_search",
                        "is_provider_inbuilt_tool": True,
                    }
                ]
            }
        },
        
        # --- 9. Store Research Results - Separate nodes for each report type ---
        "store_blog_research": {
            "node_id": "store_blog_research",
            "node_category": "system",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": BLOG_DEEP_RESEARCH_REPORT_IS_VERSIONED, "operation": "upsert"},
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "content_strategy_report",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_DEEP_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "static_docname": BLOG_DEEP_RESEARCH_REPORT_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },
        
        "store_linkedin_research": {
            "node_id": "store_linkedin_research",
            "node_category": "system",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": LINKEDIN_DEEP_RESEARCH_REPORT_IS_VERSIONED, "operation": "upsert"},
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "linkedin_report",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": LINKEDIN_DEEP_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": LINKEDIN_DEEP_RESEARCH_REPORT_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },

        # --- 10. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_category": "system",
            "node_name": "output_node",
            "defer_node": True,
            "node_config": {}
        },
    },

    "edges": [
        # --- Initial Setup: Store inputs to graph state ---
        {"src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"},
            {"src_field": "entity_username", "dst_field": "entity_username"},
            {"src_field": "run_blog_analysis", "dst_field": "run_blog_analysis"},
            {"src_field": "run_linkedin_exec", "dst_field": "run_linkedin_exec"},
        ]},

        {"src_node_id": "input_node", "dst_node_id": "document_router", "mappings": [
            {"src_field": "run_blog_analysis", "dst_field": "run_blog_analysis"},
            {"src_field": "run_linkedin_exec", "dst_field": "run_linkedin_exec"}
        ]},

        {"src_node_id": "document_router", "dst_node_id": "load_company_data", "mappings": []}, 
        {"src_node_id": "document_router", "dst_node_id": "load_linkedin_data", "mappings": []},
        
        # Route Data Loading -> Load Company Data (if run_blog_analysis is true)
        {"src_node_id": "$graph_state", "dst_node_id": "load_company_data", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"}
        ]},

        {"src_node_id": "$graph_state", "dst_node_id": "load_linkedin_data", "mappings": [
            {"src_field": "entity_username", "dst_field": "entity_username"}
        ]},
        
        {"src_node_id": "load_company_data", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "company_data", "dst_field": "company_data"}
        ]},

        {"src_node_id": "load_linkedin_data", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "linkedin_user_profile", "dst_field": "linkedin_user_profile"},
            {"src_field": "linkedin_scraped_profile", "dst_field": "linkedin_scraped_profile"}
        ]},
        
        # --- Content Strategy Path ---
        {"src_node_id": "load_company_data", "dst_node_id": "construct_content_strategy_prompt", "mappings": [
            {"src_field": "company_data", "dst_field": "company_data"}
        ]},
        {"src_node_id": "construct_content_strategy_prompt", "dst_node_id": "deep_researcher_content_strategy", "mappings": [
            {"src_field": "user_prompt", "dst_field": "user_prompt"},
            {"src_field": "system_prompt", "dst_field": "system_prompt"}
        ]},
        {"src_node_id": "deep_researcher_content_strategy", "dst_node_id": "store_blog_research", "mappings": [
            {"src_field": "text_content", "dst_field": "content_strategy_report"}
        ]},
        
        # --- LinkedIn Path ---
        {"src_node_id": "load_linkedin_data", "dst_node_id": "construct_linkedin_prompt", "mappings": [
            {"src_field": "linkedin_user_profile", "dst_field": "linkedin_user_profile"},
            {"src_field": "linkedin_scraped_profile", "dst_field": "linkedin_scraped_profile"}
        ]},
        {"src_node_id": "construct_linkedin_prompt", "dst_node_id": "deep_researcher_linkedin", "mappings": [
            {"src_field": "user_prompt", "dst_field": "user_prompt"},
            {"src_field": "system_prompt", "dst_field": "system_prompt"}
        ]},
        {"src_node_id": "deep_researcher_linkedin", "dst_node_id": "store_linkedin_research", "mappings": [
            {"src_field": "text_content", "dst_field": "linkedin_report"}
        ]},
        
        # State -> Store nodes (for namespace fields)
        {"src_node_id": "$graph_state", "dst_node_id": "store_blog_research", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"}
        ]},

        {"src_node_id": "$graph_state", "dst_node_id": "store_linkedin_research", "mappings": [
            {"src_field": "entity_username", "dst_field": "entity_username"}
        ]},

        # Store -> Output
        {"src_node_id": "store_blog_research", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "paths_processed", "dst_field": "blog_storage_paths"}
        ]},
        {"src_node_id": "store_linkedin_research", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "paths_processed", "dst_field": "linkedin_storage_paths"}
        ]},

        {"src_node_id": "store_blog_research", "dst_node_id": "output_node", "mappings": [
        ]},
        {"src_node_id": "store_linkedin_research", "dst_node_id": "output_node", "mappings": [
        ]},

        {"src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
            {"src_field": "blog_storage_paths", "dst_field": "blog_storage_paths"},
            {"src_field": "linkedin_storage_paths", "dst_field": "linkedin_storage_paths"}
        ]},

    ],

    # --- Define Start and End ---
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    # --- State Reducers ---
    "metadata": {
        "$graph_state": {
            "reducer": {
                "company_name": "replace",
                "entity_username": "replace",
                "run_blog_analysis": "replace",
                "run_linkedin_exec": "replace",
                "company_data": "replace",
                "linkedin_user_profile": "replace",
                "linkedin_scraped_profile": "replace",
                "linkedin_exec_context": "replace",
                "combined_output": "replace",
                "research_type": "replace",
            }
        }
    }
}