import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# Internal dependencies
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

from kiwi_client.workflows.active.document_models.customer_docs import (
    # User DNA
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
)

# Import LLM configurations from local wf_llm_inputs
from kiwi_client.workflows.active.content_studio.linkedin_alternate_text_suggestion_sandbox.wf_llm_inputs import (
    # LLM Model Configuration
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    # Schemas
    GENERATION_SCHEMA,
    FEEDBACK_SCHEMA,
    # Prompts
    USER_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE,
    FEEDBACK_SYSTEM_PROMPT,
    FEEDBACK_INITIAL_USER_PROMPT,
    FEEDBACK_ADDITIONAL_USER_PROMPT,
)

# --- Workflow Configuration Constants ---
# MAX_ITERATIONS is used for the HITL loop, not LLM iterations
MAX_ITERATIONS = 5

# Use the imported schema directly
GENERATION_SCHEMA_JSON = GENERATION_SCHEMA
FEEDBACK_SCHEMA_JSON = FEEDBACK_SCHEMA

# Prompt template variables and construct options
USER_PROMPT_TEMPLATE_VARIABLES = {
    "selected_text": None,
    "content_draft": None,
    "user_dna": None,
    "feedback_section": None
}

USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {
    "selected_text": "selected_text",
    "content_draft": "complete_content_doc",
    "user_dna": "user_dna",
    "feedback_section": "user_feedback"
}

SYSTEM_PROMPT_TEMPLATE_VARIABLES = {
    "schema": GENERATION_SCHEMA_JSON
}

SYSTEM_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {}

### INPUTS ###
INPUT_FIELDS = {
    "selected_text": {
        "type": "str",
        "required": True,
        "description": "The text that was selected by the user for alternate suggestions"
    },
    "complete_content_doc": {
        "type": "str",
        "required": True,
        "description": "The complete content text (e.g., full LinkedIn post) containing the selected text"
    },
    "user_feedback": {
        "type": "str",
        "required": False,
        "description": "Optional feedback from the user about what kind of alternate text they want"
    },
    "entity_username": { 
        "type": "str", 
        "required": True, 
        "description": "Name of the entity to generate alternate text suggestions for."
    }
}

workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node ---
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": INPUT_FIELDS
            }
        },

        # --- 2. Load User DNA ---
        "load_all_context_docs": {
            "node_id": "load_all_context_docs",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE, 
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
                        },
                        "output_field_name": "user_dna"
                    }
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False}
            },
        },

        # --- 3. Construct Prompt ---
        "construct_prompt": {
            "node_id": "construct_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": USER_PROMPT_TEMPLATE,
                        "variables": USER_PROMPT_TEMPLATE_VARIABLES,
                        "construct_options": USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": SYSTEM_PROMPT_TEMPLATE,
                        "variables": SYSTEM_PROMPT_TEMPLATE_VARIABLES,
                        "construct_options": SYSTEM_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS
                    }
                }
            }
        },

        # --- 4. Generate Alternatives ---
        "generate_content": {
            "node_id": "generate_content",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": DEFAULT_LLM_PROVIDER, "model": DEFAULT_LLM_MODEL},
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": GENERATION_SCHEMA_JSON,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 5. Capture Approval ---
        "capture_approval": {
            "node_id": "capture_approval",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "approval_status": { 
                        "type": "enum", 
                        "enum_values": ["approved", "needs_work"], 
                        "required": True, 
                        "description": "User decision on the alternatives." 
                    },
                    "feedback_text": { 
                        "type": "str", 
                        "required": False, 
                        "description": "Optional feedback text from the user." 
                    }
                }
            }
        },

        # --- 6. Route Based on Approval ---
        "route_on_approval": {
            "node_id": "route_on_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["check_iteration_limit", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "check_iteration_limit",
                        "input_path": "approval_status_from_hitl",
                        "target_value": "needs_work"
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "approval_status_from_hitl",
                        "target_value": "approved"
                    }
                ]
            }
        },

        # --- 7. Check Iteration Limit ---
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

        # --- 8. Route Based on Iteration Limit ---
        "route_on_limit_check": {
            "node_id": "route_on_limit_check",
            "node_name": "router_node",
            "node_config": {
                "choices": ["route_to_initial_or_additional_prompt", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "route_to_initial_or_additional_prompt",
                        "input_path": "if_else_condition_tag_results.iteration_limit_check",
                        "target_value": True
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "iteration_branch_result",
                        "target_value": "false_branch"
                    }
                ]
            }
        },

        # --- 9. Route to Appropriate Prompt Constructor ---
        "route_to_initial_or_additional_prompt": {
            "node_id": "route_to_initial_or_additional_prompt",
            "node_name": "router_node",
            "node_config": {
                "choices": ["construct_user_feedback_initial_prompt", "construct_user_feedback_additional_prompt"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_user_feedback_initial_prompt",
                        "input_path": "generation_metadata.iteration_count",
                        "target_value": 1
                    }
                ],
                "default_choice": "construct_user_feedback_additional_prompt"
            }
        },

        # --- 10. Construct Initial Feedback Prompt ---
        "construct_user_feedback_initial_prompt": {
            "node_id": "construct_user_feedback_initial_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "interpret_feedback_prompt": {
                        "id": "interpret_feedback_prompt",
                        "template": FEEDBACK_INITIAL_USER_PROMPT,
                        "variables": {
                            "current_alternatives": None,
                            "feedback_text": None,
                            "content_draft": None,
                            "user_dna": None
                        },
                        "construct_options": {
                            "current_alternatives": "current_alternatives",
                            "feedback_text": "current_feedback_text",
                            "content_draft": "complete_content_doc",
                            "user_dna": "user_dna"
                        }
                    }
                }
            }
        },

        # --- 11. Construct Additional Feedback Prompt ---
        "construct_user_feedback_additional_prompt": {
            "node_id": "construct_user_feedback_additional_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "interpret_feedback_prompt": {
                        "id": "interpret_feedback_prompt",
                        "template": FEEDBACK_ADDITIONAL_USER_PROMPT,
                        "variables": {
                            "current_alternatives": None,
                            "feedback_text": None,
                            "content_draft": None
                        },
                        "construct_options": {
                            "current_alternatives": "current_alternatives",
                            "feedback_text": "current_feedback_text",
                            "content_draft": "complete_content_doc"
                        }
                    }
                }
            }
        },

        # --- 12. Interpret Feedback ---
        "interpret_feedback": {
            "node_id": "interpret_feedback",
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
                "default_system_prompt": FEEDBACK_SYSTEM_PROMPT,
                "output_schema": {
                    "schema_definition": FEEDBACK_SCHEMA_JSON,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 13. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {
            }
        }
    },

    "edges": [
        # Input -> State
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "selected_text", "dst_field": "selected_text" },
                { "src_field": "complete_content_doc", "dst_field": "complete_content_doc" },
                { "src_field": "user_feedback", "dst_field": "user_feedback" },
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },
        
        # Input -> Load User DNA
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_all_context_docs", 
            "mappings": [
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },
        
        # Load User DNA -> State
        { 
            "src_node_id": "load_all_context_docs", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "user_dna", "dst_field": "user_dna" }
            ]
        },

        # Load User DNA -> Construct Prompt: Direct flow to next step
        { 
            "src_node_id": "load_all_context_docs", 
            "dst_node_id": "construct_prompt", 
            "mappings": [
                { "src_field": "user_dna", "dst_field": "user_dna" }
            ]
        },

        # State -> Construct Prompt: Provide all required data
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_prompt", 
            "mappings": [
                { "src_field": "selected_text", "dst_field": "selected_text" },
                { "src_field": "complete_content_doc", "dst_field": "complete_content_doc" },
                { "src_field": "user_feedback", "dst_field": "user_feedback" }
            ]
        },
        
        # Construct Prompt -> Generate Alternatives
        { 
            "src_node_id": "construct_prompt", 
            "dst_node_id": "generate_content", 
            "mappings": [
                { "src_field": "user_prompt", "dst_field": "user_prompt" },
                { "src_field": "system_prompt", "dst_field": "system_prompt" }
            ]
        },

        # State (Messages) -> Generate Content: Provide conversation history if any
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "generate_content", 
            "mappings": [
                { "src_field": "generate_content_messages_history", "dst_field": "messages_history", "description": "Pass existing message history for context."}
            ]
        },

        # Generate Content -> State
        { 
            "src_node_id": "generate_content", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "current_messages", "dst_field": "generate_content_messages_history" },
                { "src_field": "metadata", "dst_field": "generation_metadata", "description": "Store LLM metadata (e.g., token usage, iteration count)."},
                { "src_field": "structured_output", "dst_field": "current_alternatives" }
            ]
        },

        # Generate Content -> Capture Approval
        { 
            "src_node_id": "generate_content", 
            "dst_node_id": "capture_approval", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "current_alternatives" }
            ]
        },

        # Capture Approval -> State
        { 
            "src_node_id": "capture_approval", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "approval_status", "dst_field": "approval_status_from_hitl" },
                { "src_field": "feedback_text", "dst_field": "current_feedback_text" }
            ]
        },

        # Capture Approval -> Route on Approval
        { 
            "src_node_id": "capture_approval", 
            "dst_node_id": "route_on_approval", 
            "mappings": [
                { "src_field": "approval_status", "dst_field": "approval_status_from_hitl" }
            ]
        },

        # Route on Approval -> Check Iteration Limit
        { 
            "src_node_id": "route_on_approval", 
            "dst_node_id": "check_iteration_limit", 
            "mappings": []
        },

        # Route on Approval -> Output Node (approved case)
        { 
            "src_node_id": "route_on_approval", 
            "dst_node_id": "output_node", 
            "mappings": []
        },

        # State -> Output Node (for approved case)
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "output_node", 
            "mappings": [
            ]
        },

        # State -> Check Iteration Limit
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "check_iteration_limit", 
            "mappings": [
                { "src_field": "generation_metadata", "dst_field": "generation_metadata" }
            ]
        },

        # Check Iteration Limit -> Route on Limit Check
        { 
            "src_node_id": "check_iteration_limit", 
            "dst_node_id": "route_on_limit_check", 
            "mappings": [
                { "src_field": "if_else_condition_tag_results", "dst_field": "if_else_condition_tag_results" },
                { "src_field": "iteration_branch_result", "dst_field": "iteration_branch_result" }
            ]
        },

        # Route on Limit Check -> Route to Initial or Additional Prompt
        { 
            "src_node_id": "route_on_limit_check", 
            "dst_node_id": "route_to_initial_or_additional_prompt", 
            "mappings": []
        },

        # Route on Limit Check -> Output Node (limit exceeded case)
        { 
            "src_node_id": "route_on_limit_check", 
            "dst_node_id": "output_node", 
            "mappings": []
        },

        # State -> Route to Initial or Additional Prompt
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "route_to_initial_or_additional_prompt", 
            "mappings": [
                { "src_field": "generation_metadata", "dst_field": "generation_metadata" }
            ]
        },

        # Route to Initial or Additional Prompt -> Construct User Feedback Initial Prompt
        { 
            "src_node_id": "route_to_initial_or_additional_prompt", 
            "dst_node_id": "construct_user_feedback_initial_prompt", 
            "mappings": []
        },

        # Route to Initial or Additional Prompt -> Construct User Feedback Additional Prompt
        { 
            "src_node_id": "route_to_initial_or_additional_prompt", 
            "dst_node_id": "construct_user_feedback_additional_prompt", 
            "mappings": []
        },

        # State -> Construct User Feedback Initial Prompt
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_user_feedback_initial_prompt", 
            "mappings": [
                { "src_field": "current_alternatives", "dst_field": "current_alternatives" },
                { "src_field": "current_feedback_text", "dst_field": "current_feedback_text" },
                { "src_field": "complete_content_doc", "dst_field": "complete_content_doc" },
                { "src_field": "user_dna", "dst_field": "user_dna" }
            ]
        },

        # State -> Construct User Feedback Additional Prompt
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_user_feedback_additional_prompt", 
            "mappings": [
                { "src_field": "current_alternatives", "dst_field": "current_alternatives" },
                { "src_field": "current_feedback_text", "dst_field": "current_feedback_text" },
                { "src_field": "complete_content_doc", "dst_field": "complete_content_doc" }
            ]
        },

        # Construct User Feedback Initial Prompt -> Interpret Feedback
        { 
            "src_node_id": "construct_user_feedback_initial_prompt", 
            "dst_node_id": "interpret_feedback", 
            "mappings": [
                { "src_field": "interpret_feedback_prompt", "dst_field": "user_prompt" }
            ]
        },

        # Construct User Feedback Additional Prompt -> Interpret Feedback
        { 
            "src_node_id": "construct_user_feedback_additional_prompt", 
            "dst_node_id": "interpret_feedback", 
            "mappings": [
                { "src_field": "interpret_feedback_prompt", "dst_field": "user_prompt" }
            ]
        },

        # State -> Interpret Feedback
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "interpret_feedback", 
            "mappings": [
                { "src_field": "interpret_feedback_messages_history", "dst_field": "messages_history" }
            ]
        },

        # Interpret Feedback -> State
        { 
            "src_node_id": "interpret_feedback", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "current_messages", "dst_field": "interpret_feedback_messages_history" },
                { "src_field": "structured_output", "dst_field": "interpreted_feedback" }
            ]
        },

        # Interpret Feedback -> Construct Prompt (back to generation)
        { 
            "src_node_id": "interpret_feedback", 
            "dst_node_id": "construct_prompt", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "feedback_section" }
            ]
        }
    ],

    "input_node_id": "input_node",
    "output_node_id": "output_node",

    "metadata": {
        "$graph_state": {
            "reducer": {
                "generate_content_messages_history": "add_messages",
                "interpret_feedback_messages_history": "add_messages"
            }
        }
    }
}