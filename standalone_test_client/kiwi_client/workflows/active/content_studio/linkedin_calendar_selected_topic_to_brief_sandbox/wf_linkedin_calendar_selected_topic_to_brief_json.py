"""
Selected Topic to Brief Generation Workflow for LinkedIn

This workflow takes a pre-selected topic from ContentTopicsOutput and:
- Loads executive profile and content strategy
- Generates a comprehensive LinkedIn content brief based on the selected topic
- Provides HITL editing and approval with iteration limits
- Saves the approved brief

Key Features:
- Starts with a pre-selected topic (no topic selection phase)
- Comprehensive brief generation with strategic alignment for LinkedIn
- HITL approval flow with manual editing support
- Iteration limits to prevent infinite loops
- Document storage for approved briefs
"""

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

# Import document model constants for LinkedIn
from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
    LINKEDIN_BRIEF_DOCNAME,
    LINKEDIN_BRIEF_NAMESPACE_TEMPLATE,
    LINKEDIN_BRIEF_IS_VERSIONED
)

# Import LLM inputs for LinkedIn
# Import LLM configurations from local wf_llm_inputs
from kiwi_client.workflows.active.content_studio.linkedin_calendar_selected_topic_to_brief_sandbox.wf_llm_inputs import (
    # LLM Model Configuration
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,

    # System prompts
    BRIEF_GENERATION_SYSTEM_PROMPT,
    BRIEF_FEEDBACK_SYSTEM_PROMPT,

    # User prompt templates
    BRIEF_GENERATION_USER_PROMPT_TEMPLATE,
    BRIEF_FEEDBACK_INITIAL_USER_PROMPT,
    BRIEF_FEEDBACK_ADDITIONAL_USER_PROMPT,

    # Output schemas
    BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA,
    BRIEF_GENERATION_OUTPUT_SCHEMA,
)
# Workflow Limits
MAX_ITERATIONS = 10  # Maximum iterations for HITL feedback loops

# Workflow JSON structure
workflow_graph_schema = {
    "nodes": {
        # 1. Input Node - Receives selected topic
        "input_node": {
            "node_id": "input_node",
            "node_category": "system",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "entity_username": {
                        "type": "str",
                        "required": True,
                        "description": "Name of the executive for document operations"
                    },
                    "selected_topic": {
                        "type": "dict",
                        "required": True,
                        "description": "The selected topic from ContentTopicsOutput containing title, description, theme, objective, etc."
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
            "node_category": "system",
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
            "node_category": "system",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },

        # 4. Load Executive Profile and Content Playbook Documents
        "load_executive_and_playbook": {
            "node_id": "load_executive_and_playbook",
            "node_category": "system",
            "node_name": "load_customer_data",
            "node_config": {
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_USER_PROFILE_DOCNAME,
                        },
                        "output_field_name": "executive_profile_doc"
                    },
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
                        },
                        "output_field_name": "playbook_doc"
                    }
                ]
            }
        },
        
        # 3. Brief Generation - Prompt Constructor
        "construct_brief_generation_prompt": {
            "node_id": "construct_brief_generation_prompt",
            "node_category": "brief_generation",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "brief_generation_user_prompt": {
                        "id": "brief_generation_user_prompt",
                        "template": BRIEF_GENERATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "selected_topic": None,
                            "executive_profile": None,
                            "playbook_doc": None
                        },
                        "construct_options": {
                            "selected_topic": "selected_topic",
                            "executive_profile": "executive_profile_doc",
                            "playbook_doc": "playbook_doc"
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
            "node_category": "brief_generation",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": DEFAULT_LLM_PROVIDER,
                        "model": DEFAULT_LLM_MODEL
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
            "node_category": "system",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": LINKEDIN_BRIEF_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "current_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": LINKEDIN_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "input_docname_field_pattern": LINKEDIN_BRIEF_DOCNAME,
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
                            "is_versioned": LINKEDIN_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        }
                    }
                ],
            }
        },
        
        # 6. Transform Brief HITL Additional Files Format
        "transform_brief_hitl_additional_files_config": {
            "node_id": "transform_brief_hitl_additional_files_config",
            "node_category": "brief_generation",
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

        # 7. Load Brief HITL Additional User Files
        "load_brief_hitl_additional_user_files_node": {
            "node_id": "load_brief_hitl_additional_user_files_node",
            "node_category": "brief_generation",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },

        # 8. Brief Approval - HITL Node
        "brief_approval_hitl": {
            "node_id": "brief_approval_hitl",
            "node_category": "brief_generation",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_brief_action": {
                        "type": "enum",
                        "enum_values": ["complete", "provide_feedback", "cancel_workflow", "draft"],
                        "required": True,
                        "description": "User's decision on brief approval"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for brief revision (required if provide_feedback)"
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
                        "description": "Optional list of additional user files to load for brief feedback."
                    }
                }
            }
        },
        
        # 7. Route Brief Approval
        "route_brief_approval": {
            "node_id": "route_brief_approval",
            "node_category": "brief_generation",
            "node_name": "router_node",
            "node_config": {
                "choices": ["save_brief", "check_iteration_limit", "delete_brief_on_cancel", "save_as_draft"],
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
                        "target_value": "provide_feedback"
                    },
                    {
                        "choice_id": "delete_brief_on_cancel",
                        "input_path": "user_brief_action",
                        "target_value": "cancel_workflow"
                    },
                    {
                        "choice_id": "save_as_draft",
                        "input_path": "user_brief_action",
                        "target_value": "draft"
                    }
                ],
                "default_choice": "delete_brief_on_cancel"
            }
        },
        
        # 8. Save Brief as Draft
        "save_as_draft": {
            "node_id": "save_as_draft",
            "node_category": "system",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": LINKEDIN_BRIEF_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "current_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": LINKEDIN_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "input_docname_field_pattern": LINKEDIN_BRIEF_DOCNAME,
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
                            "is_versioned": LINKEDIN_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                    }
                ],
            }
        },
        
        # 8a. Delete Brief on Cancel - Delete Customer Data Node
        "delete_brief_on_cancel": {
            "node_id": "delete_brief_on_cancel",
            "node_category": "system",
            "node_name": "delete_customer_data",
            "node_config": {
                "search_params": {
                    "input_namespace_field": "entity_username",
                    "input_namespace_field_pattern": LINKEDIN_BRIEF_NAMESPACE_TEMPLATE,
                    "input_docname_field": "brief_uuid",
                    "input_docname_field_pattern": LINKEDIN_BRIEF_DOCNAME
                }
            }
        },
        
        # 9. Check Iteration Limit
        "check_iteration_limit": {
            "node_id": "check_iteration_limit",
            "node_category": "brief_generation",
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
        
        # 10. Route Based on Iteration Limit Check
        "route_on_limit_check": {
            "node_id": "route_on_limit_check",
            "node_category": "brief_generation",
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
        
        # 11. Brief Feedback Prompt Constructor
        "construct_brief_feedback_prompt": {
            "node_id": "construct_brief_feedback_prompt",
            "node_category": "brief_generation",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "brief_feedback_user_prompt": {
                        "id": "brief_feedback_user_prompt",
                        "template": BRIEF_FEEDBACK_INITIAL_USER_PROMPT,
                        "variables": {
                            "content_brief": None,
                            "revision_feedback": None,
                            "selected_topic": None,
                            "executive_profile": None,
                            "playbook_doc": None
                        },
                        "construct_options": {
                            "content_brief": "current_content_brief",
                            "revision_feedback": "current_revision_feedback",
                            "selected_topic": "selected_topic",
                            "executive_profile": "executive_profile_doc",
                            "playbook_doc": "playbook_doc"
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
        
        # 12. Brief Feedback Analysis
        "analyze_brief_feedback": {
            "node_id": "analyze_brief_feedback",
            "node_category": "brief_generation",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": DEFAULT_LLM_PROVIDER,
                        "model": DEFAULT_LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": BRIEF_FEEDBACK_ANALYSIS_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 13. Brief Revision - Enhanced Prompt Constructor
        "construct_brief_revision_prompt": {
            "node_id": "construct_brief_revision_prompt",
            "node_category": "brief_generation",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "brief_revision_user_prompt": {
                        "id": "brief_revision_user_prompt",
                        "template": BRIEF_GENERATION_USER_PROMPT_TEMPLATE + "\n\n**Revision Instructions:**\n{revision_instructions}",
                        "variables": {
                            "selected_topic": None,
                            "executive_profile": None,
                            "playbook_doc": None,
                            "revision_instructions": None
                        },
                        "construct_options": {
                            "selected_topic": "selected_topic",
                            "executive_profile": "executive_profile_doc",
                            "playbook_doc": "playbook_doc",
                            "revision_instructions": "brief_feedback_analysis.revision_instructions"
                        }
                    },
                    "brief_revision_system_prompt": {
                        "id": "brief_revision_system_prompt",
                        "template": BRIEF_GENERATION_SYSTEM_PROMPT,
                        "variables": {},
                    }
                }
            }
        },
        
        # 14. Brief Revision - LLM Node
        "brief_revision_llm": {
            "node_id": "brief_revision_llm",
            "node_category": "brief_generation",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": DEFAULT_LLM_PROVIDER,
                        "model": DEFAULT_LLM_MODEL
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
        
        # 15. Save Brief - Store Customer Data
        "save_brief": {
            "node_id": "save_brief",
            "node_category": "system",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": LINKEDIN_BRIEF_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "final_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": LINKEDIN_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "input_docname_field_pattern": LINKEDIN_BRIEF_DOCNAME,
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
                            "is_versioned": LINKEDIN_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                    }
                ],
            }
        },
        
        # 16. Output Node
        "output_node": {
            "node_id": "output_node",
            "node_category": "system",
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
                {"src_field": "entity_username", "dst_field": "entity_username"},
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "initial_status", "dst_field": "initial_status"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"},
                {"src_field": "load_additional_user_files", "dst_field": "load_additional_user_files"}
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

        # Transform Additional Files -> Load Additional Files
        {
            "src_node_id": "transform_additional_files_config",
            "dst_node_id": "load_additional_user_files_node",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },

        # Load Additional Files -> State
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },
        
        # Input -> Load Executive and Playbook
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_executive_and_playbook",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },
        
        # Executive and Playbook -> State
        {
            "src_node_id": "load_executive_and_playbook",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "executive_profile_doc", "dst_field": "executive_profile_doc"},
                {"src_field": "playbook_doc", "dst_field": "playbook_doc"}
            ]
        },
        
        # Load Executive and Playbook -> Brief Generation Prompt (trigger)
        {
            "src_node_id": "load_executive_and_playbook",
            "dst_node_id": "construct_brief_generation_prompt",
            "mappings": []
        },
        
        # State -> Brief Generation Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_brief_generation_prompt",
            "mappings": [
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "executive_profile_doc", "dst_field": "executive_profile_doc"},
                {"src_field": "playbook_doc", "dst_field": "playbook_doc"}
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
                {"src_field": "entity_username", "dst_field": "entity_username"},
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

        # Transform Brief HITL -> Load Brief HITL Additional Files
        {
            "src_node_id": "transform_brief_hitl_additional_files_config",
            "dst_node_id": "load_brief_hitl_additional_user_files_node",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },

        # Load Brief HITL Additional Files -> State
        {
            "src_node_id": "load_brief_hitl_additional_user_files_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "brief_hitl_additional_user_files", "dst_field": "brief_hitl_additional_user_files"}
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
            "dst_node_id": "delete_brief_on_cancel",
            "description": "Route to delete brief if workflow cancelled"
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
                {"src_field": "entity_username", "dst_field": "entity_username"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}
            ]
        },
        
        # Save as Draft -> brief approval hitl
        {"src_node_id": "save_as_draft", "dst_node_id": "brief_approval_hitl"},
        
        # Delete Brief on Cancel edges
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "delete_brief_on_cancel",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}
            ]
        },
        {
            "src_node_id": "delete_brief_on_cancel",
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
                {"src_field": "executive_profile_doc", "dst_field": "executive_profile_doc"},
                {"src_field": "playbook_doc", "dst_field": "playbook_doc"}
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
        
        # State -> Brief Revision Prompt Constructor
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_brief_revision_prompt",
            "mappings": [
                {"src_field": "selected_topic", "dst_field": "selected_topic"},
                {"src_field": "executive_profile_doc", "dst_field": "executive_profile_doc"},
                {"src_field": "playbook_doc", "dst_field": "playbook_doc"}
            ]
        },

        # Load Brief HITL Additional Files -> Brief Revision Prompt (data-only edge)
        {
            "src_node_id": "load_brief_hitl_additional_user_files_node",
            "dst_node_id": "construct_brief_revision_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "brief_hitl_additional_user_files", "dst_field": "brief_hitl_additional_user_files"}
            ]
        },
        
        # Brief Revision Prompt -> LLM
        {
            "src_node_id": "construct_brief_revision_prompt",
            "dst_node_id": "brief_revision_llm",
            "mappings": [
                {"src_field": "brief_revision_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "brief_revision_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # State -> Brief Revision LLM (message history)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "brief_revision_llm",
            "mappings": [
                {"src_field": "brief_generation_messages_history", "dst_field": "messages_history"}
            ]
        },
        
        # Brief Revision LLM -> HITL (loop back)
        {
            "src_node_id": "brief_revision_llm",
            "dst_node_id": "brief_approval_hitl",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "content_brief"}
            ]
        },
        
        # Brief Revision LLM -> State
        {
            "src_node_id": "brief_revision_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "current_content_brief"},
                {"src_field": "current_messages", "dst_field": "brief_generation_messages_history"},
                {"src_field": "metadata", "dst_field": "generation_metadata"}
            ]
        },
        
        # State -> Save Brief
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_brief",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"},
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
                "brief_generation_messages_history": "add_messages",
                "brief_feedback_analysis_messages_history": "add_messages",
                "user_brief_action": "replace",
                "selected_topic": "replace",
                "executive_profile_doc": "replace",
                "playbook_doc": "replace",
                "initial_status": "replace",
                "brief_uuid": "replace",
                "additional_user_files": "collect_values",
                "brief_hitl_additional_user_files": "collect_values"
            }
        }
    }
}