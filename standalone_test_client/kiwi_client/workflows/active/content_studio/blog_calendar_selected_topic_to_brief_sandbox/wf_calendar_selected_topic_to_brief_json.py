from typing import Dict, Any, List, Optional
import asyncio
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflow testing utilities
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_VERSIONED,
    BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_BRIEF_DOCNAME,
    BLOG_CONTENT_BRIEF_IS_VERSIONED,
    BLOG_CONTENT_STRATEGY_DOCNAME,
    BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_STRATEGY_IS_VERSIONED
)

# Import LLM inputs
from kiwi_client.workflows.active.content_studio.blog_calendar_selected_topic_to_brief_sandbox.wf_llm_inputs import (
    # System prompts
    BRIEF_GENERATION_SYSTEM_PROMPT,
    BRIEF_FEEDBACK_SYSTEM_PROMPT,
    GOOGLE_RESEARCH_SYSTEM_PROMPT,
    REDDIT_RESEARCH_SYSTEM_PROMPT,
    KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT,

    # User prompt templates
    GOOGLE_RESEARCH_USER_PROMPT_TEMPLATE,
    REDDIT_RESEARCH_USER_PROMPT_TEMPLATE,
    KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE,
    BRIEF_GENERATION_USER_PROMPT_TEMPLATE,
    BRIEF_FEEDBACK_INITIAL_USER_PROMPT,
    BRIEF_REVISION_USER_PROMPT_TEMPLATE,

    # Output schemas
    BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA,
    GOOGLE_RESEARCH_OUTPUT_SCHEMA,
    REDDIT_RESEARCH_OUTPUT_SCHEMA,
    KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA,
    BRIEF_GENERATION_OUTPUT_SCHEMA,

    # LLM Configurations
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    LLM_PROVIDER,
    LLM_MODEL,

    # Knowledge Enrichment LLM Configuration
    KNOWLEDGE_ENRICHMENT_LLM_PROVIDER,
    KNOWLEDGE_ENRICHMENT_LLM_MODEL,
    KNOWLEDGE_ENRICHMENT_TEMPERATURE,
    KNOWLEDGE_ENRICHMENT_MAX_TOKENS,

    # Perplexity Configuration
    PERPLEXITY_PROVIDER,
    PERPLEXITY_MODEL,
    PERPLEXITY_TEMPERATURE,
    PERPLEXITY_MAX_TOKENS,

    # Feedback LLM Configuration
    FEEDBACK_LLM_PROVIDER,
    FEEDBACK_ANALYSIS_MODEL,
    FEEDBACK_TEMPERATURE,
    FEEDBACK_MAX_TOKENS,

    # Workflow Limits
    MAX_ITERATIONS,
    MAX_REGENERATION_ATTEMPTS,
    MAX_REVISION_ATTEMPTS
)

# Workflow JSON structure
workflow_graph_schema = {
    "nodes": {
        # 1. Input Node - Receives selected topic and user input
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "company_name": {
                        "type": "str",
                        "required": True,
                        "description": "Name of the company for document operations"
                    },
                    "selected_topic": {
                        "type": "dict",
                        "required": True,
                        "description": "The selected topic from ContentTopicsOutput containing title, description, theme, objective, etc."
                    },
                    "user_instructions": {
                        "type": "str",
                        "required": True,
                        "description": "User's content ideas, brainstorm, or transcript"
                    },
                    "initial_status": {
                        "type": "str",
                        "required": False,
                        "default": "draft",
                        "description": "Initial status of the workflow"
                    },
                    "brief_uuid": {
                        "type": "str",
                        "required": True,
                        "description": "UUID of the brief being generated"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    }
                }
            }
        },
        
        # 2. Transform Additional User Files Format (if provided)
        "transform_additional_files_config": {
            "node_id": "transform_additional_files_config",
            "node_name": "transform_data",
            "node_config": {
                "apply_transform_to_each_item_in_list_at_path": "load_additional_user_files",
                "base_object": {
                    "output_field_name": "additional_user_files"
                },
                "mappings": [
                    {"source_path": "namespace", "destination_path": "filename_config.static_namespace"},
                    {"source_path": "docname", "destination_path": "filename_config.static_docname"},
                    {"source_path": "is_shared", "destination_path": "is_shared"}
                ]
            }
        },
        
        # 3. Load Additional User Files (conditional)
        "load_additional_user_files_node": {
            "node_id": "load_additional_user_files_node", 
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },
        
        # 4. Load Company and Content Strategy Documents
        "load_company_and_playbook": {
            "node_id": "load_company_and_playbook",
            "node_name": "load_customer_data",
            "node_config": {
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
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
                        "output_field_name": "playbook_doc"
                    }
                ]
            }
        },
        
        # 2.5 Google Research - Prompt Constructor
        "construct_google_research_prompt": {
            "node_id": "construct_google_research_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "google_research_user_prompt": {
                        "id": "google_research_user_prompt",
                        "template": GOOGLE_RESEARCH_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "company_doc": None,
                            "user_input": None,
                            "additional_user_files": "",
                            "topic_hitl_additional_user_files": ""
                        },
                        "construct_options": {
                            "company_doc": "company_doc",
                            "user_input": "user_instructions",
                            "additional_user_files": "additional_user_files",
                            "topic_hitl_additional_user_files": "additional_user_files"
                        }
                    },
                    "google_research_system_prompt": {
                        "id": "google_research_system_prompt",
                        "template": GOOGLE_RESEARCH_SYSTEM_PROMPT,
                        "variables": {},
                    }
                }
            }
        },
        
        # 2.6 Google Research - LLM Node (Perplexity)
        "google_research_llm": {
            "node_id": "google_research_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": PERPLEXITY_PROVIDER,
                        "model": PERPLEXITY_MODEL
                    },
                    "temperature": PERPLEXITY_TEMPERATURE,
                    "max_tokens": PERPLEXITY_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": GOOGLE_RESEARCH_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 2.7 Reddit Research - Prompt Constructor
        "construct_reddit_research_prompt": {
            "node_id": "construct_reddit_research_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "reddit_research_user_prompt": {
                        "id": "reddit_research_user_prompt",
                        "template": REDDIT_RESEARCH_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "company_doc": None,
                            "google_research_output": None,
                            "user_input": None,
                            "additional_user_files": "",
                            "topic_hitl_additional_user_files": ""
                        },
                        "construct_options": {
                            "company_doc": "company_doc",
                            "google_research_output": "google_research_output",
                            "user_input": "user_instructions",
                            "additional_user_files": "additional_user_files",
                            "topic_hitl_additional_user_files": "additional_user_files"
                        }
                    },
                    "reddit_research_system_prompt": {
                        "id": "reddit_research_system_prompt",
                        "template": REDDIT_RESEARCH_SYSTEM_PROMPT,
                        "variables": {},
                    }
                }
            }
        },
        
        # 2.8 Reddit Research - LLM Node (Perplexity)
        "reddit_research_llm": {
            "node_id": "reddit_research_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": PERPLEXITY_PROVIDER,
                        "model": PERPLEXITY_MODEL
                    },
                    "temperature": PERPLEXITY_TEMPERATURE,
                    "max_tokens": PERPLEXITY_MAX_TOKENS
                },
                "web_search_options": {
                    "search_domain_filter": [
                        "reddit.com",
                        "quora.com"
                    ]
                },
                "output_schema": {
                    "schema_definition": REDDIT_RESEARCH_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 3. Knowledge Enrichment - Prompt Constructor
        "construct_knowledge_enrichment_prompt": {
            "node_id": "construct_knowledge_enrichment_prompt",
            "node_name": "prompt_constructor",
            "defer_node": True,  # Wait for all data loads before proceeding
            "node_config": {
                "prompt_templates": {
                    "knowledge_enrichment_user_prompt": {
                        "id": "knowledge_enrichment_user_prompt",
                        "template": KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "selected_topic": None,
                            "google_research_output": None,
                            "reddit_research_output": None,
                            "user_instructions_on_selected_topic": "",
                            "additional_user_files": "",
                            "topic_hitl_additional_user_files": "",
                            "company_name": None
                        },
                        "construct_options": {
                            "selected_topic": "selected_topic",
                            "google_research_output": "google_research_output",
                            "reddit_research_output": "reddit_research_output",
                            "user_instructions_on_selected_topic": "user_instructions",
                            "additional_user_files": "additional_user_files",
                            "topic_hitl_additional_user_files": "additional_user_files",
                            "company_name": "company_name"
                        }
                    },
                    "knowledge_enrichment_system_prompt": {
                        "id": "knowledge_enrichment_system_prompt",
                        "template": KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },

        # 3.1 Knowledge Enrichment - LLM Node with Document Tools
        "knowledge_enrichment_llm": {
            "node_id": "knowledge_enrichment_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": KNOWLEDGE_ENRICHMENT_LLM_PROVIDER,
                        "model": KNOWLEDGE_ENRICHMENT_LLM_MODEL
                    },
                    "temperature": KNOWLEDGE_ENRICHMENT_TEMPERATURE,
                    "max_tokens": KNOWLEDGE_ENRICHMENT_MAX_TOKENS,
                    "reasoning_effort_class": "medium",
                },
                "tool_calling_config": {
                    "enable_tool_calling": True,
                    "parallel_tool_calls": True
                },
                "tools": [
                    {
                        "tool_name": "search_documents",
                        "is_provider_inbuilt_tool": False,
                        "provider_inbuilt_user_config": {}
                    },
                    {
                        "tool_name": "view_documents",
                        "is_provider_inbuilt_tool": False,
                        "provider_inbuilt_user_config": {}
                    },
                    {
                        "tool_name": "list_documents",
                        "is_provider_inbuilt_tool": False,
                        "provider_inbuilt_user_config": {}
                    }
                ],
                "output_schema": {
                    "schema_definition": KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False,
                }
            }
        },

        # 3.2 Check Conditions for Knowledge Enrichment Tool Use
        "check_conditions": {
            "node_id": "check_conditions",
            "node_name": "if_else_condition",
            "node_config": {
                "tagged_conditions": [
                    {
                        "tag": "iteration_limit_check",
                        "condition_groups": [{
                            "conditions": [{
                                "field": "generation_metadata.iteration_count",
                                "operator": "greater_than_or_equals",
                                "value": MAX_ITERATIONS
                            }]
                        }]
                    },
                    {
                        "tag": "tool_calls_empty",
                        "condition_groups": [{
                            "conditions": [{
                                "field": "tool_calls",
                                "operator": "is_empty"
                            }]
                        }]
                    },
                    {
                        "tag": "structured_output_empty",
                        "condition_groups": [{
                            "conditions": [{
                                "field": "knowledge_context",
                                "operator": "is_empty"
                            }]
                        }]
                    }
                ],
                "branch_logic_operator": "or"
            }
        },

        # 3.3 Route Based on Conditions (no HITL)
        "route_from_conditions": {
            "node_id": "route_from_conditions",
            "node_name": "router_node",
            "node_config": {
                "choices": ["tool_executor", "construct_brief_generation_prompt"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_brief_generation_prompt",
                        "input_path": "tag_results.iteration_limit_check",
                        "target_value": True
                    },
                    {
                        "choice_id": "tool_executor",
                        "input_path": "tag_results.tool_calls_empty",
                        "target_value": False
                    },
                    {
                        "choice_id": "construct_brief_generation_prompt",
                        "input_path": "tag_results.structured_output_empty",
                        "target_value": False
                    }
                ],
                "default_choice": "construct_brief_generation_prompt"
            }
        },

        # 3.4 Tool Executor (executes document tools)
        "tool_executor": {
            "node_id": "tool_executor",
            "node_name": "tool_executor",
            "node_config": {
                "default_timeout": 30.0,
                "max_concurrent_executions": 5,
                "continue_on_error": True,
                "include_error_details": True,
                "map_executor_input_fields_to_tool_input": True,
                "tool_call_limit": 20,
                "consider_failed_calls_in_limit": True,
            }
        },

        # 4. Brief Generation - Prompt Constructor
        "construct_brief_generation_prompt": {
            "node_id": "construct_brief_generation_prompt",
            "node_name": "prompt_constructor",
            "defer_node": True,
            "node_config": {
                "prompt_templates": {
                    "brief_generation_user_prompt": {
                        "id": "brief_generation_user_prompt",
                        "template": BRIEF_GENERATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "selected_topic": None,
                            "company_doc": None,
                            "content_playbook_doc": None,
                            "google_research_output": None,
                            "reddit_research_output": None,
                            "knowledge_context": None,
                            "user_instructions_on_selected_topic": "",
                            "additional_user_files": "",
                            "topic_hitl_additional_user_files": ""
                        },
                        "construct_options": {
                            "selected_topic": "selected_topic",
                            "company_doc": "company_doc",
                            "content_playbook_doc": "content_playbook_doc",
                            "google_research_output": "google_research_output",
                            "reddit_research_output": "reddit_research_output",
                            "knowledge_context": "knowledge_context",
                            "user_instructions_on_selected_topic": "user_instructions",
                            "additional_user_files": "additional_user_files",
                            "topic_hitl_additional_user_files": "additional_user_files"
                        }
                    },
                    "brief_generation_system_prompt": {
                        "id": "brief_generation_system_prompt",
                        "template": BRIEF_GENERATION_SYSTEM_PROMPT,
                        "variables": {},
                    }
                }
            }
        },
        
        # 4. Brief Generation - LLM Node
        "brief_generation_llm": {
            "node_id": "brief_generation_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": LLM_PROVIDER,
                        "model": LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": BRIEF_GENERATION_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 5. Save as Draft After Generation
        "save_as_draft_after_generation": {
            "node_id": "save_as_draft_after_generation",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": BLOG_CONTENT_BRIEF_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "current_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_CONTENT_BRIEF_DOCNAME,
                                "input_docname_field": "brief_uuid"
                            }
                        },
                        "extra_fields": [
                            {
                                "src_path": "initial_status",
                                "dst_path": "status"
                            },
                            {
                                "src_path": "brief_uuid",
                                "dst_path": "uuid"
                            }
                        ],
                        "versioning": {
                            "is_versioned": BLOG_CONTENT_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        }
                    }
                ],
            }
        },
        
        # 6. Brief Approval - HITL Node
        "brief_approval_hitl": {
            "node_id": "brief_approval_hitl",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_brief_action": {
                        "type": "enum",
                        "enum_values": ["complete", "revise_brief", "cancel_workflow", "draft"],
                        "required": True,
                        "description": "User's decision on brief approval"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for brief revision (required if revise_brief)"
                    },
                    "updated_content_brief": {
                        "type": "dict",
                        "required": True,
                        "description": "Updated content brief (may contain user edits)"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load for brief approval. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    }
                }
            }
        },
        
        # 6.5 Transform Brief HITL Additional Files Format
        "transform_brief_hitl_additional_files_config": {
            "node_id": "transform_brief_hitl_additional_files_config",
            "node_name": "transform_data",
            "node_config": {
                "apply_transform_to_each_item_in_list_at_path": "load_additional_user_files",
                "base_object": {
                    "output_field_name": "brief_hitl_additional_user_files"
                },
                "mappings": [
                    {"source_path": "namespace", "destination_path": "filename_config.static_namespace"},
                    {"source_path": "docname", "destination_path": "filename_config.static_docname"},
                    {"source_path": "is_shared", "destination_path": "is_shared"}
                ]
            }
        },
        
        # 6.7 Load Brief HITL Additional User Files
        "load_brief_hitl_additional_user_files_node": {
            "node_id": "load_brief_hitl_additional_user_files_node",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },
        
        # 7. Route Brief Approval
        "route_brief_approval": {
            "node_id": "route_brief_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["save_brief", "check_iteration_limit", "delete_on_cancel", "save_as_draft"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "save_brief",
                        "input_path": "user_brief_action",
                        "target_value": "complete"
                    },
                    {
                        "choice_id": "check_iteration_limit",
                        "input_path": "user_brief_action",
                        "target_value": "revise_brief"
                    },
                    {
                        "choice_id": "delete_on_cancel",
                        "input_path": "user_brief_action",
                        "target_value": "cancel_workflow"
                    },
                    {
                        "choice_id": "save_as_draft",
                        "input_path": "user_brief_action",
                        "target_value": "draft"
                    }
                ],
                "default_choice": "delete_on_cancel"
            }
        },
        
        # 8. Save Brief as Draft
        "save_as_draft": {
            "node_id": "save_as_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": True,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "current_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_CONTENT_BRIEF_DOCNAME,
                                "input_docname_field": "brief_uuid"
                            }
                        },
                        "extra_fields": [
                            {
                                "src_path": "user_brief_action",
                                "dst_path": "status"
                            },
                            {
                                "src_path": "brief_uuid",
                                "dst_path": "uuid"
                            }
                        ],
                        "versioning": {
                            "is_versioned": BLOG_CONTENT_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                    }
                ],
            }
        },
        
        # 9. Delete on Cancel - Delete the saved brief document
        "delete_on_cancel": {
            "node_id": "delete_on_cancel",
            "node_name": "delete_customer_data",
            "node_config": {
                "search_params": {
                    "input_namespace_field": "company_name",
                    "input_namespace_field_pattern": BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
                    "input_docname_field": "brief_uuid",
                    "input_docname_field_pattern": BLOG_CONTENT_BRIEF_DOCNAME
                }
            }
        },
        
        # 10. Check Iteration Limit
        "check_iteration_limit": {
            "node_id": "check_iteration_limit",
            "node_name": "if_else_condition",
            "node_config": {
                "tagged_conditions": [
                    {
                        "tag": "iteration_limit_check",
                        "condition_groups": [{
                            "logical_operator": "and",
                            "conditions": [{
                                "field": "generation_metadata.iteration_count",
                                "operator": "less_than",
                                "value": MAX_ITERATIONS
                            }]
                        }],
                        "group_logical_operator": "and"
                    }
                ],
                "branch_logic_operator": "and"
            }
        },
        
        # 11. Route Based on Iteration Limit Check
        "route_on_limit_check": {
            "node_id": "route_on_limit_check",
            "node_name": "router_node",
            "node_config": {
                "choices": ["construct_brief_feedback_prompt", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_brief_feedback_prompt",
                        "input_path": "if_else_condition_tag_results.iteration_limit_check",
                        "target_value": True
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "iteration_branch_result",
                        "target_value": "false_branch"
                    },
                ]
            }
        },
        
        # 12. Brief Feedback Prompt Constructor
        "construct_brief_feedback_prompt": {
            "node_id": "construct_brief_feedback_prompt",
            "node_name": "prompt_constructor",
            "defer_node": True,  # Wait for all data loads before proceeding
            "node_config": {
                "prompt_templates": {
                    "brief_feedback_user_prompt": {
                        "id": "brief_feedback_user_prompt",
                        "template": BRIEF_FEEDBACK_INITIAL_USER_PROMPT,
                        "variables": {
                            "content_brief": None,
                            "revision_feedback": None,
                            "selected_topic": None,
                            "company_doc": None,
                            "content_playbook_doc": None,
                            "user_input": None,
                            "google_research_output": None,
                            "reddit_research_output": None,
                            "brief_hitl_additional_user_files": ""
                        },
                        "construct_options": {
                            "content_brief": "current_content_brief",
                            "revision_feedback": "current_revision_feedback",
                            "selected_topic": "selected_topic",
                            "company_doc": "company_doc",
                            "content_playbook_doc": "content_playbook_doc",
                            "user_input": "user_instructions",
                            "google_research_output": "google_research_output",
                            "reddit_research_output": "reddit_research_output",
                            "brief_hitl_additional_user_files": "brief_hitl_additional_user_files"
                        }
                    },
                    "brief_feedback_system_prompt": {
                        "id": "brief_feedback_system_prompt",
                        "template": BRIEF_FEEDBACK_SYSTEM_PROMPT,
                        "variables": {},
                    }
                }
            }
        },
        
        # 13. Brief Feedback Analysis
        "analyze_brief_feedback": {
            "node_id": "analyze_brief_feedback",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": FEEDBACK_LLM_PROVIDER,
                        "model": FEEDBACK_ANALYSIS_MODEL
                    },
                    "temperature": FEEDBACK_TEMPERATURE,
                    "max_tokens": FEEDBACK_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 14. Brief Revision - Enhanced Prompt Constructor
        "construct_brief_revision_prompt": {
            "node_id": "construct_brief_revision_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "brief_revision_user_prompt": {
                        "id": "brief_revision_user_prompt",
                        "template": BRIEF_REVISION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "revision_instructions": None,
                            "brief_hitl_additional_user_files": ""
                        },
                        "construct_options": {
                            "revision_instructions": "brief_feedback_analysis.revision_instructions",
                            "brief_hitl_additional_user_files": "brief_hitl_additional_user_files"
                        }
                    }
                }
            }
        },
        
        # 16. Save Brief - Store Customer Data
        "save_brief": {
            "node_id": "save_brief",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": BLOG_CONTENT_BRIEF_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "final_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_CONTENT_BRIEF_DOCNAME,
                                "input_docname_field": "brief_uuid"
                            }
                        },
                        "extra_fields": [
                            {
                                "src_path": "user_brief_action",
                                "dst_path": "status"
                            },
                            {
                                "src_path": "brief_uuid",
                                "dst_path": "uuid"
                            }
                        ],
                        "versioning": {
                            "is_versioned": BLOG_CONTENT_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        }
                    }
                ],
            }
        },
        
        # 18. Output Node
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {}
        }
    },
    
    "edges": [
        # Input -> State: Store initial values
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"},
                {"src_field": "initial_status", "dst_field": "initial_status"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"},
                {"src_field": "load_additional_user_files", "dst_field": "load_additional_user_files"}
            ]
        },
        
        # Input -> Load Company and Playbook
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_company_and_playbook",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"}
            ]
        },
        
        # Input -> Transform Additional Files Config
        {
            "src_node_id": "input_node",
            "dst_node_id": "transform_additional_files_config",
            "mappings": [
                {"src_field": "load_additional_user_files", "dst_field": "load_additional_user_files"}
            ]
        },
        
        # Transform -> Load Additional Files (pass transformed config)
        {
            "src_node_id": "transform_additional_files_config",
            "dst_node_id": "load_additional_user_files_node",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },
        
        # Company and Playbook -> State
        {
            "src_node_id": "load_company_and_playbook",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"},
                {"src_field": "playbook_doc", "dst_field": "content_playbook_doc"}
            ]
        },
        
        # Load Company and Playbook -> Google Research Prompt (trigger)
        {
            "src_node_id": "load_company_and_playbook",
            "dst_node_id": "construct_google_research_prompt",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"}            ]
        },
        
        # Load Additional Files -> Google Research Prompt (data-only edge)
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_google_research_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },
        
        # State -> Google Research Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_google_research_prompt",
            "mappings": [
                {"src_field": "user_instructions", "dst_field": "user_instructions"}
            ]
        },
        
        # Google Research Prompt -> LLM
        {
            "src_node_id": "construct_google_research_prompt",
            "dst_node_id": "google_research_llm",
            "mappings": [
                {"src_field": "google_research_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "google_research_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Google Research LLM -> State
        {
            "src_node_id": "google_research_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "google_research_output"}
            ]
        },
        
        # Google Research LLM -> Reddit Research Prompt (trigger)
        {
            "src_node_id": "google_research_llm",
            "dst_node_id": "construct_reddit_research_prompt",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "google_research_output"}
            ]
        },
        
        # State -> Reddit Research Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_reddit_research_prompt",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"}
            ]
        },
        
        # Load Additional Files -> Reddit Research Prompt (data-only edge)
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_reddit_research_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },
        
        # Reddit Research Prompt -> LLM
        {
            "src_node_id": "construct_reddit_research_prompt",
            "dst_node_id": "reddit_research_llm",
            "mappings": [
                {"src_field": "reddit_research_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "reddit_research_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Reddit Research LLM -> State
        {
            "src_node_id": "reddit_research_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "reddit_research_output"}
            ]
        },
        
        # Reddit Research LLM -> Knowledge Enrichment Prompt (trigger)
        {
            "src_node_id": "reddit_research_llm",
            "dst_node_id": "construct_knowledge_enrichment_prompt",
            "mappings": []
        },

        # State -> Knowledge Enrichment Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_knowledge_enrichment_prompt",
            "mappings": [
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "google_research_output", "dst_field": "google_research_output"},
                {"src_field": "reddit_research_output", "dst_field": "reddit_research_output"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"},
                {"src_field": "company_name", "dst_field": "company_name"}
            ]
        },

        # Load Additional Files -> Knowledge Enrichment Prompt (data-only edge)
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_knowledge_enrichment_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },

        # Knowledge Enrichment Prompt -> Knowledge Enrichment LLM
        {
            "src_node_id": "construct_knowledge_enrichment_prompt",
            "dst_node_id": "knowledge_enrichment_llm",
            "mappings": [
                {"src_field": "knowledge_enrichment_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "knowledge_enrichment_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        # Knowledge Enrichment LLM -> State (store results)
        {
            "src_node_id": "knowledge_enrichment_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "knowledge_context"},
                {"src_field": "current_messages", "dst_field": "messages_history"},
                {"src_field": "metadata", "dst_field": "generation_metadata"},
                {"src_field": "tool_calls", "dst_field": "latest_tool_calls"}
            ]
        },

        # Knowledge Enrichment LLM -> Check Conditions (control flow after enrichment)
        {
            "src_node_id": "knowledge_enrichment_llm",
            "dst_node_id": "check_conditions",
            "mappings": [
                {"src_field": "tool_calls", "dst_field": "tool_calls"},
                {"src_field": "structured_output", "dst_field": "knowledge_context"},
                {"src_field": "metadata", "dst_field": "generation_metadata"}
            ]
        },

        # State -> Check Conditions
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "check_conditions",
            "mappings": [
                {"src_field": "latest_tool_calls", "dst_field": "tool_calls"},
                {"src_field": "generation_metadata", "dst_field": "generation_metadata"},
                {"src_field": "knowledge_context", "dst_field": "knowledge_context"}
            ]
        },

        # Check Conditions -> Router
        {
            "src_node_id": "check_conditions",
            "dst_node_id": "route_from_conditions",
            "mappings": [
                {"src_field": "tag_results", "dst_field": "tag_results"},
                {"src_field": "condition_result", "dst_field": "condition_result"}
            ]
        },

        # Router -> Tool Executor (control flow)
        {
            "src_node_id": "route_from_conditions",
            "dst_node_id": "tool_executor"
        },

        # State -> Tool Executor (provide context)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "tool_executor",
            "mappings": [
                {"src_field": "latest_tool_calls", "dst_field": "tool_calls"},
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "view_context", "dst_field": "view_context"},
                {"src_field": "successful_tool_calls", "dst_field": "prior_successful_calls"},
                {"src_field": "failed_tool_calls", "dst_field": "prior_failed_calls"}
            ]
        },

        # Tool Executor -> State (update view context and tool outputs)
        {
            "src_node_id": "tool_executor",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "tool_outputs", "dst_field": "latest_tool_outputs"},
                {"src_field": "state_changes", "dst_field": "view_context"},
                {"src_field": "successful_calls", "dst_field": "successful_tool_calls"},
                {"src_field": "failed_calls", "dst_field": "failed_tool_calls"}
            ]
        },

        # Tool Executor -> Knowledge Enrichment LLM (continue the loop with tool outputs and messages)
        {
            "src_node_id": "tool_executor",
            "dst_node_id": "knowledge_enrichment_llm",
            "mappings": [
                {"src_field": "tool_outputs", "dst_field": "tool_outputs"}
            ]
        },

        # State -> Knowledge Enrichment LLM (messages history for next iteration)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "knowledge_enrichment_llm",
            "mappings": [
                {"src_field": "messages_history", "dst_field": "messages_history"}
            ]
        },

        # Router -> Brief Generation Prompt (control flow when no tools or limit reached)
        {
            "src_node_id": "route_from_conditions",
            "dst_node_id": "construct_brief_generation_prompt"
        },

        # State -> Brief Generation Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_brief_generation_prompt",
            "mappings": [
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "company_doc", "dst_field": "company_doc"},
                {"src_field": "content_playbook_doc", "dst_field": "content_playbook_doc"},
                {"src_field": "google_research_output", "dst_field": "google_research_output"},
                {"src_field": "reddit_research_output", "dst_field": "reddit_research_output"},
                {"src_field": "knowledge_context", "dst_field": "knowledge_context"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"}
            ]
        },
        
        # Load Additional Files -> Brief Generation Prompt (data-only edge)
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_brief_generation_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },
        
        # Brief Generation Prompt -> LLM
        {
            "src_node_id": "construct_brief_generation_prompt",
            "dst_node_id": "brief_generation_llm",
            "mappings": [
                {"src_field": "brief_generation_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "brief_generation_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # State -> Brief Generation LLM (message history)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "brief_generation_llm",
            "mappings": [
                {"src_field": "brief_generation_messages_history", "dst_field": "messages_history"}
            ]
        },
        
        # Brief Generation LLM -> State
        {
            "src_node_id": "brief_generation_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "current_content_brief"},
                {"src_field": "current_messages", "dst_field": "brief_generation_messages_history"},
                {"src_field": "metadata", "dst_field": "generation_metadata"}
            ]
        },
        
        # Brief Generation LLM -> Save as Draft After Generation
        {
            "src_node_id": "brief_generation_llm",
            "dst_node_id": "save_as_draft_after_generation",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "current_content_brief"}
            ]
        },
        
        # State -> Save as Draft After Generation
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_as_draft_after_generation",
            "mappings": [
                {"src_field": "initial_status", "dst_field": "initial_status"},
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}
            ]
        },
        
        # Save as Draft After Generation -> Brief Approval HITL
        {
            "src_node_id": "save_as_draft_after_generation",
            "dst_node_id": "brief_approval_hitl"
        },
        
        # State -> Brief Approval HITL (content brief)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "brief_approval_hitl",
            "mappings": [
                {"src_field": "current_content_brief", "dst_field": "content_brief"}
            ]
        },
        
        # Brief Approval HITL -> Route
        {
            "src_node_id": "brief_approval_hitl",
            "dst_node_id": "route_brief_approval",
            "mappings": [
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"}
            ]
        },
        
        # Brief Approval HITL -> State
        {
            "src_node_id": "brief_approval_hitl",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "revision_feedback", "dst_field": "current_revision_feedback"},
                {"src_field": "updated_content_brief", "dst_field": "current_content_brief"},
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"},
                {"src_field": "load_additional_user_files", "dst_field": "brief_hitl_load_additional_user_files"}
            ]
        },
        
        # Brief HITL -> Transform Brief HITL Additional Files Config
        {
            "src_node_id": "brief_approval_hitl",
            "dst_node_id": "transform_brief_hitl_additional_files_config",
            "mappings": [
                {"src_field": "load_additional_user_files", "dst_field": "load_additional_user_files"}
            ]
        },
        
        # Transform Brief HITL -> Load Brief HITL Additional Files (pass transformed config)
        {
            "src_node_id": "transform_brief_hitl_additional_files_config",
            "dst_node_id": "load_brief_hitl_additional_user_files_node",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },
        
        # Route Brief Approval paths
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "save_brief",
            "description": "Route to save brief if approved"
        },
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "check_iteration_limit",
            "description": "Route to check iteration limit if revision requested"
        },
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "delete_on_cancel",
            "description": "Route to delete node if workflow cancelled"
        },
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "save_as_draft",
            "description": "Route to save as draft if requested"
        },
        
        # Check Iteration Limit edges
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "check_iteration_limit",
            "mappings": [
                {"src_field": "generation_metadata", "dst_field": "generation_metadata"}
            ]
        },
        {
            "src_node_id": "check_iteration_limit",
            "dst_node_id": "route_on_limit_check",
            "mappings": [
                {"src_field": "branch", "dst_field": "iteration_branch_result"},
                {"src_field": "tag_results", "dst_field": "if_else_condition_tag_results"},
                {"src_field": "condition_result", "dst_field": "if_else_overall_condition_result"}
            ]
        },
        {
            "src_node_id": "route_on_limit_check",
            "dst_node_id": "construct_brief_feedback_prompt",
            "description": "Trigger feedback interpretation if iterations remain"
        },
        {
            "src_node_id": "route_on_limit_check",
            "dst_node_id": "output_node",
            "description": "Trigger finalization if iteration limit reached"
        },
        
        # State -> Save as Draft
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_as_draft",
            "mappings": [
                {"src_field": "current_content_brief", "dst_field": "current_content_brief"},
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"},
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}
            ]
        },
        
        # Save as Draft -> brief approval hitl
        {"src_node_id": "save_as_draft", "dst_node_id": "brief_approval_hitl"},
        
        # State -> Delete on Cancel
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "delete_on_cancel",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}
            ]
        },
        
        # Delete on Cancel -> Output
        {
            "src_node_id": "delete_on_cancel",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "deleted_count", "dst_field": "deleted_count"},
                {"src_field": "deleted_documents", "dst_field": "deleted_documents"}
            ]
        },
        
        # State -> Brief Feedback Prompt Constructor
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_brief_feedback_prompt",
            "mappings": [
                {"src_field": "current_content_brief", "dst_field": "current_content_brief"},
                {"src_field": "current_revision_feedback", "dst_field": "current_revision_feedback"},
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "company_doc", "dst_field": "company_doc"},
                {"src_field": "content_playbook_doc", "dst_field": "content_playbook_doc"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"},
                {"src_field": "google_research_output", "dst_field": "google_research_output"},
                {"src_field": "reddit_research_output", "dst_field": "reddit_research_output"}
            ]
        },
        
        # Load Brief HITL Additional Files -> State (store data)
        {
            "src_node_id": "load_brief_hitl_additional_user_files_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "brief_hitl_additional_user_files", "dst_field": "brief_hitl_additional_user_files"}
            ]
        },
        
        # Load Brief HITL Additional Files -> Brief Feedback Prompt (data-only edge)
        {
            "src_node_id": "load_brief_hitl_additional_user_files_node",
            "dst_node_id": "construct_brief_feedback_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "brief_hitl_additional_user_files", "dst_field": "brief_hitl_additional_user_files"}
            ]
        },
        
        # Brief Feedback Prompt -> LLM
        {
            "src_node_id": "construct_brief_feedback_prompt",
            "dst_node_id": "analyze_brief_feedback",
            "mappings": [
                {"src_field": "brief_feedback_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "brief_feedback_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # State -> Brief Feedback Analysis (message history)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "analyze_brief_feedback",
            "mappings": [
                {"src_field": "brief_feedback_analysis_messages_history", "dst_field": "messages_history"}
            ]
        },
        
        # Brief Feedback Analysis -> State
        {
            "src_node_id": "analyze_brief_feedback",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "brief_feedback_analysis"},
                {"src_field": "current_messages", "dst_field": "brief_feedback_analysis_messages_history"}
            ]
        },
        
        # Brief Feedback Analysis -> Brief Revision Prompt Constructor
        {
            "src_node_id": "analyze_brief_feedback",
            "dst_node_id": "construct_brief_revision_prompt",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "brief_feedback_analysis"}
            ]
        },
        
        # State -> Brief Revision Prompt Constructor (provide brief_hitl_additional_user_files)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_brief_revision_prompt",
            "mappings": [
                {"src_field": "brief_hitl_additional_user_files", "dst_field": "brief_hitl_additional_user_files"}
            ]
        },
        
        # Brief Revision Prompt -> LLM
        {
            "src_node_id": "construct_brief_revision_prompt",
            "dst_node_id": "brief_generation_llm",
            "mappings": [
                {"src_field": "brief_revision_user_prompt", "dst_field": "user_prompt"},
            ]
        },
        
        # State -> Save Brief
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_brief",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "current_content_brief", "dst_field": "final_content_brief"},
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}
            ]
        },
        
        # Save Brief -> Output
        {
            "src_node_id": "save_brief",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "final_paths_processed"}
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "current_content_brief": "replace",
                "current_revision_feedback": "replace",
                "generation_metadata": "replace",
                "knowledge_context": "replace",
                "latest_tool_calls": "replace",
                "latest_tool_outputs": "replace",
                "view_context": "merge_dicts",
                "successful_tool_calls": "replace",
                "failed_tool_calls": "replace",
                "messages_history": "add_messages",
                "brief_generation_messages_history": "add_messages",
                "brief_feedback_analysis_messages_history": "add_messages",
                "brief_feedback_analysis": "replace",
                "user_brief_action": "replace",
                "selected_topic": "replace",
                "company_doc": "replace",
                "playbook_doc": "replace",
                "content_playbook_doc": "replace",
                "google_research_output": "replace",
                "reddit_research_output": "replace",
                "user_instructions": "replace",
                "additional_user_files": "replace",
                "brief_hitl_load_additional_user_files": "replace",
                "brief_hitl_additional_user_files": "replace",
                "initial_status": "replace",
                "brief_uuid": "replace"
            }
        }
    }
}