"""
File Summarization Workflow

This workflow enables comprehensive document summarization with:
- GPT-5 for intelligent document analysis and summarization
- Automatic summary name generation using GPT-5-mini
- UUID-based unique document naming
- Human-in-the-loop approval for summary review and feedback
- Iteration limit checking to prevent infinite loops
- Flexible save configuration for custom document storage
- Final summary report saving with proper document management

Test Configuration:
- Uses document summary types from the system configuration
- Creates realistic test data matching the summary document schemas
- Tests various scenarios including summary generation, HITL approval, and feedback processing
- Includes proper HITL approval flows and document saving with iteration limits
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

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
    DOCUMENT_SUMMARY_REPORT_NAMESPACE_TEMPLATE,
)

# Import LLM inputs
from kiwi_client.workflows.active.labs.llm_inputs.file_summarisation_workflow import (
    # System prompts
    DEFAULT_SUMMARIZATION_SYSTEM_PROMPT,
    SUMMARY_NAME_GENERATION_SYSTEM_PROMPT,
    
    # User prompt templates
    DEFAULT_SUMMARIZATION_USER_PROMPT_TEMPLATE,
    SUMMARY_NAME_GENERATION_USER_PROMPT_TEMPLATE,
    FEEDBACK_REVISION_USER_PROMPT_TEMPLATE,
    
    # Schemas
    SUMMARY_NAME_OUTPUT_SCHEMA,
    
    # Code runner configurations
    SAVE_CONFIG_GENERATION_CODE,
)

# Configuration constants
MAX_LLM_ITERATIONS = 10  # Maximum LLM loop iterations

# LLM Providers per task
GPT_5_PROVIDER = "openai"
GPT_5_MODEL = "gpt-5"
GPT_MINI_PROVIDER = "openai"
GPT_MINI_MODEL = "gpt-5-mini"

# LLM Configuration
TEMPERATURE = 0.7
MAX_TOKENS = 8000
SUMMARY_NAME_MAX_TOKENS = 500

# Workflow JSON structure
workflow_graph_schema = {
    "nodes": {
        # 1. Input Node
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "summary_context": {
                        "type": "str",
                        "required": True,
                        "description": "The context or purpose for the document summarization"
                    },
                    "asset_name": {
                        "type": "str",
                        "required": True,
                        "description": "Asset name used for namespace and docname placeholder replacement"
                    },
                    "namespace": {
                        "type": "str",
                        "required": False,
                        "default": DOCUMENT_SUMMARY_REPORT_NAMESPACE_TEMPLATE,
                        "description": "Optional namespace for saving document summary. Use {item} placeholder for asset name insertion"
                    },
                    "docname": {
                        "type": "str", 
                        "required": False,
                        "description": "Optional docname for saving document summary. Use {item} for random UUID suffix insertion"
                    },
                    "is_shared": {
                        "type": "bool",
                        "required": False,
                        "default": False,
                        "description": "Optional flag to determine if document summary should be shared. Defaults to False"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": True,
                        "description": "Optional list of additional user files to load for summarization context. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    }
                }
            }
        },
        
        # 2. Check if docname is provided
        "check_docname_provided": {
            "node_id": "check_docname_provided",
            "node_name": "if_else_condition",
            "node_config": {
                "tagged_conditions": [
                    {
                        "tag": "docname_provided",
                        "condition_groups": [{
                            "conditions": [{
                                "field": "docname",
                                "operator": "is_not_empty"
                            }]
                        }]
                    }
                ],
                "branch_logic_operator": "and"
            }
        },
        
        # 3. Route based on docname check
        "route_docname_check": {
            "node_id": "route_docname_check",
            "node_name": "router_node",
            "node_config": {
                "choices": ["generate_save_config", "construct_summary_name_prompt"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "generate_save_config",
                        "input_path": "tag_results.docname_provided",
                        "target_value": True
                    },
                    {
                        "choice_id": "construct_summary_name_prompt",
                        "input_path": "tag_results.docname_provided",
                        "target_value": False
                    }
                ],
                "default_choice": "construct_summary_name_prompt"
            }
        },
        
        # 4. Construct Summary Name Prompt
        "construct_summary_name_prompt": {
            "node_id": "construct_summary_name_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "summary_name_user_prompt": {
                        "id": "summary_name_user_prompt",
                        "template": SUMMARY_NAME_GENERATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "summary_context": None
                        },
                        "construct_options": {
                            "summary_context": "summary_context"
                        }
                    }
                }
            }
        },

        # 5. Generate Summary Name (GPT-5-mini with structured output)
        "generate_summary_name": {
            "node_id": "generate_summary_name",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": GPT_MINI_PROVIDER,
                        "model": GPT_MINI_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": SUMMARY_NAME_MAX_TOKENS,
                    "reasoning_effort_class": "low",  # low, medium, high
                },
                "default_system_prompt": SUMMARY_NAME_GENERATION_SYSTEM_PROMPT,
                "output_schema": {
                    "schema_definition": SUMMARY_NAME_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False,
                }
            }
        },
        
        # 3a. Transform Additional User Files Format (if provided)
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

        # 3b. Load Additional User Files (conditional)
        "load_additional_user_files_node": {
            "node_id": "load_additional_user_files_node", 
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },

        # 6. Generate Save Config with UUID
        "generate_save_config": {
            "node_id": "generate_save_config",
            "node_name": "code_runner",
            "node_config": {
                "timeout_seconds": 30,
                "memory_mb": 256,
                "default_code": SAVE_CONFIG_GENERATION_CODE,
                "persist_artifacts": False,
                "fail_node_on_code_error": True
            }
        },
        
        # 7. Construct Summary Prompt
        "construct_summary_prompt": {
            "node_id": "construct_summary_prompt",
            "node_name": "prompt_constructor",
            "defer_node": True,
            "node_config": {
                "prompt_templates": {
                    "summary_user_prompt": {
                        "id": "summary_user_prompt",
                        "template": DEFAULT_SUMMARIZATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "summary_context": None,
                            "additional_user_files": ""
                        },
                        "construct_options": {
                            "summary_context": "summary_context",
                            "additional_user_files": "additional_user_files"
                        }
                    }
                }
            }
        },

        # 8. Construct Feedback Prompt  
        "construct_feedback_prompt": {
            "node_id": "construct_feedback_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "revision_user_prompt": {
                        "id": "revision_user_prompt", 
                        "template": FEEDBACK_REVISION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "revision_feedback": None,
                            "hitl_additional_user_files": ""
                        },
                        "construct_options": {
                            "revision_feedback": "revision_feedback",
                            "hitl_additional_user_files": "hitl_additional_user_files"
                        }
                    }
                }
            },
        },

        # 9. Conduct Document Summarization with GPT-5
        "conduct_summarization": {
            "node_id": "conduct_summarization",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": GPT_5_PROVIDER,
                        "model": GPT_5_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                },
                "default_system_prompt": DEFAULT_SUMMARIZATION_SYSTEM_PROMPT,
            }
        },
        
        # 10. Save Summary Draft
        "save_summary_draft": {
            "node_id": "save_summary_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "store_configs_input_path": "save_config",
            }
        },
        
        # 11. HITL Summary Approval
        "summary_approval": {
            "node_id": "summary_approval",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_action": {
                        "type": "enum",
                        "enum_values": ["approve", "request_revisions", "cancel"],
                        "required": True,
                        "description": "User's decision on the document summary"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for summary improvements (required if action is request_revisions)"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load for summary feedback analysis. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    }
                }
            }
        },
        
        # 12. Route from HITL approval
        "route_summary_approval": {
            "node_id": "route_summary_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["check_iteration_limit", "output_node"],  # "save_final_research", 
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "output_node",  # output_node  save_final_research
                        "input_path": "user_action",
                        "target_value": "approve"
                    },
                    {
                        "choice_id": "check_iteration_limit",
                        "input_path": "user_action",
                        "target_value": "request_revisions"
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "user_action",
                        "target_value": "cancel"
                    }
                ],
                "default_choice": "output_node"
            }
        },
        
        # 13. Check Iteration Limit
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
                                "value": MAX_LLM_ITERATIONS
                            }]
                        }],
                        "group_logical_operator": "and"
                    }
                ],
                "branch_logic_operator": "and"
            }
        },
        
        # 14. Route based on iteration limit check
        "route_iteration_check": {
            "node_id": "route_iteration_check",
            "node_name": "router_node",
            "defer_node": True,
            "node_config": {
                "choices": ["construct_feedback_prompt", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_feedback_prompt",
                        "input_path": "tag_results.iteration_limit_check",
                        "target_value": True
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "tag_results.iteration_limit_check",
                        "target_value": False
                    }
                ],
                "default_choice": "output_node"
            }
        },
        
        
        # 15. Transform HITL Additional Files Format
        "transform_hitl_additional_files_config": {
            "node_id": "transform_hitl_additional_files_config",
            "node_name": "transform_data",
            "node_config": {
                "apply_transform_to_each_item_in_list_at_path": "load_additional_user_files",
                "base_object": {
                    "output_field_name": "hitl_additional_user_files"
                },
                "mappings": [
                    {"source_path": "namespace", "destination_path": "filename_config.static_namespace"},
                    {"source_path": "docname", "destination_path": "filename_config.static_docname"},
                    {"source_path": "is_shared", "destination_path": "is_shared"}
                ]
            }
        },

        # 16. Load HITL Additional User Files
        "load_hitl_additional_user_files_node": {
            "node_id": "load_hitl_additional_user_files_node",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },
        
        # 17. Output Node
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
                {"src_field": "summary_context", "dst_field": "summary_context"},
                {"src_field": "asset_name", "dst_field": "asset_name"},
                {"src_field": "namespace", "dst_field": "namespace"},
                {"src_field": "docname", "dst_field": "docname"},
                {"src_field": "is_shared", "dst_field": "is_shared"},
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
        
        # Transform -> Load Additional Files (pass transformed config)
        {
            "src_node_id": "transform_additional_files_config",
            "dst_node_id": "load_additional_user_files_node",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },

        # Input -> Check docname provided
        {
            "src_node_id": "input_node",
            "dst_node_id": "check_docname_provided",
            "mappings": [
                {"src_field": "docname", "dst_field": "docname"}
            ]
        },
        
        # Check docname -> Route docname check
        {
            "src_node_id": "check_docname_provided",
            "dst_node_id": "route_docname_check",
            "mappings": [
                {"src_field": "tag_results", "dst_field": "tag_results"}
            ]
        },
        
        # Route -> Construct research name prompt
        {
            "src_node_id": "route_docname_check",
            "dst_node_id": "construct_summary_name_prompt"
        },
        
        # State -> Construct research name prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_summary_name_prompt",
            "mappings": [
                {"src_field": "summary_context", "dst_field": "summary_context"}
            ]
        },

        # Construct research name prompt -> Generate research name
        {
            "src_node_id": "construct_summary_name_prompt",
            "dst_node_id": "generate_summary_name",
            "mappings": [
                {"src_field": "summary_name_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # Generate research name -> Generate save config
        {
            "src_node_id": "generate_summary_name",
            "dst_node_id": "generate_save_config",
            "mappings": [
                {"src_field": "structured_output.summary_name", "dst_field": "input_data.summary_name"}
            ]
        },
        
        # Generate save config -> State (store generated save config)
        {
            "src_node_id": "generate_save_config",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "result.save_config", "dst_field": "save_config"},
                {"src_field": "result.final_docname", "dst_field": "generated_docname"}
            ]
        },
        
        # State -> Generate save config (provide input fields)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "generate_save_config",
            "mappings": [
                {"src_field": "asset_name", "dst_field": "input_data.asset_name"},
                {"src_field": "namespace", "dst_field": "input_data.namespace"},
                {"src_field": "docname", "dst_field": "input_data.docname"},
                {"src_field": "is_shared", "dst_field": "input_data.is_shared"}
            ]
        },
        
        # Generate save config -> Construct summary prompt
        {
            "src_node_id": "generate_save_config",
            "dst_node_id": "construct_summary_prompt"
        },
        
        # Route -> Generate save config (when docname is provided)
        {
            "src_node_id": "route_docname_check",
            "dst_node_id": "generate_save_config"
        },
        
        # Load additional files -> Construct summary prompt (pass additional files data)
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_summary_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },
        
        # State -> Construct summary prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_summary_prompt",
            "mappings": [
                {"src_field": "summary_context", "dst_field": "summary_context"},
                {"src_field": "revision_feedback", "dst_field": "revision_feedback"}
            ]
        },
        
        # Construct summary prompt -> Conduct summarization
        {
            "src_node_id": "construct_summary_prompt",
            "dst_node_id": "conduct_summarization",
            "mappings": [
                {"src_field": "summary_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # State -> Conduct summarization
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "conduct_summarization",
            "mappings": [
                {"src_field": "messages_history", "dst_field": "messages_history"}
            ]
        },
        
        # Conduct summarization -> State (store summary results and metadata)
        {
            "src_node_id": "conduct_summarization",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "text_content", "dst_field": "summary_content.report"},
                {"src_field": "current_messages", "dst_field": "messages_history"},
                {"src_field": "metadata", "dst_field": "generation_metadata"}
            ]
        },
        
        # Conduct summarization -> Save summary draft
        {
            "src_node_id": "conduct_summarization",
            "dst_node_id": "save_summary_draft"
        },
        
        # State -> Save summary draft (provide save config and summary content)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_summary_draft",
            "mappings": [
                {"src_field": "save_config", "dst_field": "save_config"},
                {"src_field": "summary_content", "dst_field": "summary_content"}
            ]
        },
        
        # Save summary draft -> HITL approval
        {
            "src_node_id": "save_summary_draft",
            "dst_node_id": "summary_approval"
        },
        
        # State -> HITL approval
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "summary_approval",
            "mappings": [
                {"src_field": "summary_content", "dst_field": "summary_content"}
            ]
        },
        
        # HITL approval -> State (store user feedback)
        {
            "src_node_id": "summary_approval",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "revision_feedback", "dst_field": "revision_feedback"},
                {"src_field": "user_action", "dst_field": "user_action"},
                {"src_field": "load_additional_user_files", "dst_field": "hitl_load_additional_user_files"}
            ]
        },
        
        # HITL approval -> Transform HITL Additional Files Config
        {
            "src_node_id": "summary_approval",
            "dst_node_id": "transform_hitl_additional_files_config",
            "mappings": [
                {"src_field": "load_additional_user_files", "dst_field": "load_additional_user_files"}
            ]
        },
        
        # Transform HITL -> Load HITL Additional Files (pass transformed config)
        {
            "src_node_id": "transform_hitl_additional_files_config",
            "dst_node_id": "load_hitl_additional_user_files_node",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },
        
        # HITL approval -> Route summary approval
        {
            "src_node_id": "summary_approval",
            "dst_node_id": "route_summary_approval",
            "mappings": [
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # Route -> Check iteration limit
        {
            "src_node_id": "route_summary_approval",
            "dst_node_id": "check_iteration_limit"
        },
        
        # State -> Check iteration limit
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "check_iteration_limit",
            "mappings": [
                {"src_field": "generation_metadata", "dst_field": "generation_metadata"}
            ]
        },
        
        # Check iteration limit -> Route iteration check
        {
            "src_node_id": "check_iteration_limit",
            "dst_node_id": "route_iteration_check",
            "mappings": [
                {"src_field": "tag_results", "dst_field": "tag_results"}
            ]
        },
        
        # Load HITL additional files -> Route iteration check (sync point)
        {
            "src_node_id": "load_hitl_additional_user_files_node",
            "dst_node_id": "route_iteration_check"
        },
        
        # Route iteration -> Construct feedback prompt (loop back for revisions)
        {
            "src_node_id": "route_iteration_check",
            "dst_node_id": "construct_feedback_prompt"
        },

        # Load HITL additional files -> Construct feedback prompt (pass additional files data)
        {
            "src_node_id": "load_hitl_additional_user_files_node",
            "dst_node_id": "construct_feedback_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "hitl_additional_user_files", "dst_field": "hitl_additional_user_files"}
            ]
        },

        # State -> Construct feedback prompt (provide revision inputs)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_feedback_prompt",
            "mappings": [
                {"src_field": "revision_feedback", "dst_field": "revision_feedback"}
            ]
        },

        # Construct feedback prompt -> Conduct summarization (revision loop)
        {
            "src_node_id": "construct_feedback_prompt",
            "dst_node_id": "conduct_summarization",
            "mappings": [
                {"src_field": "revision_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # Route -> Output node (multiple paths)
        {
            "src_node_id": "route_summary_approval",
            "dst_node_id": "output_node"
        },
        
        {
            "src_node_id": "route_iteration_check",
            "dst_node_id": "output_node"
        },
        
        # Save final summary -> Output node
        {
            "src_node_id": "save_summary_draft",
            "dst_node_id": "output_node",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "final_summary_paths"}
            ]
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "summary_content", "dst_field": "summary_content"}
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "messages_history": "add_messages",
                "hitl_load_additional_user_files": "replace"
            }
        }
    }
}

# Helper function to prepare store configs
def prepare_store_configs(save_config: Dict[str, Any], generated_docname: Optional[str] = None, summary_content: str = "") -> List[Dict[str, Any]]:
    """
    Prepare store configurations for saving research data.
    
    Args:
        save_config: User provided save configuration
        generated_docname: Generated docname if not provided in save_config
        summary_content: The research content to save
        
    Returns:
        List of store config dictionaries
    """
    # Use provided values or defaults
    namespace = save_config.get("namespace") or DOCUMENT_SUMMARY_REPORT_NAMESPACE_TEMPLATE.replace("{item}", "default")
    docname = save_config.get("docname") or generated_docname or "document_summary"
    is_shared = save_config.get("is_shared", False)
    
    store_config = {
        "input_field_path": "summary_content",
        "target_path": {
            "filename_config": {
                "static_namespace": namespace,
                "static_docname": docname
            }
        },
        "versioning": {
            "is_versioned": True,
            "operation": "upsert_versioned",
            "version": "latest_draft"
        },
        "is_shared": is_shared
    }
    
    return [store_config]

# Validation function for research workflow output
async def validate_file_summarization_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the file summarization workflow outputs.
    
    Args:
        outputs: The dictionary of final outputs from the workflow run.
        
    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating file summarization workflow outputs...")
    
    # Check if summary was completed and saved
    final_summary_paths = outputs.get('final_summary_paths')
    if final_summary_paths:
        logger.info("✓ Summary was successfully completed and saved")
        assert isinstance(final_summary_paths, list), "Validation Failed: final_summary_paths should be a list."
        logger.info(f"   Summary saved to: {final_summary_paths}")
    
    # Check for summary content in outputs
    summary_content = outputs.get('summary_content')
    if summary_content:
        logger.info(f"✓ Summary content available: {len(summary_content)} characters")
    
    logger.info("✓ File summarization workflow validation passed.")
    
    return True

# Test function
async def main_test_file_summarization():
    """
    Test the File Summarization Workflow.
    """
    test_name = "File Summarization Workflow Test"
    print(f"\n--- Starting {test_name} ---")
    
    # Test scenarios
    test_scenario = {
        "name": "AI Impact on Healthcare Document Summary",
        "initial_inputs": {
            "summary_context": "Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.",
            "asset_name": "healthcare_ai_2024",
            "namespace": "document_summary_reports_healthcare_{item}",  # Will replace {item} with asset_name
            # "docname": "ai_healthcare_impact_2024_research",  # Commented out to test auto-generation
            "is_shared": False,
            # Example of optional additional user files to load during research
            "load_additional_user_files": [
                {
                    "namespace": "summary_context_files_healthcare",
                    "docname": "ai_diagnostic_trends_2024",
                    "is_shared": False
                }
            ]
        }
    }
    
    # Predefined HITL inputs for comprehensive testing
    predefined_hitl_inputs = [
        # 1) Research approval: request revisions first
        {
            "user_action": "request_revisions",
            "revision_feedback": "Great start! Please expand the section on regulatory challenges and add more specific examples of AI diagnostic tools currently in use. Also, include more recent data from 2024 if available.",
            # Example of optional additional user files to load for feedback analysis
            "load_additional_user_files": [
                {
                    "namespace": "summary_context_files_healthcare", 
                    "docname": "fda_ai_medical_devices_2024",
                    "is_shared": False
                }
            ]
        },
        
        # 2) Research approval: approve final version
        {
            "user_action": "approve",
            "revision_feedback": None,
        }
    ]
    
    # Setup test documents including additional context files
    setup_docs: List[SetupDocInfo] = [
        # Initial additional context file
        {
            'namespace': "summary_context_files_healthcare",
            'docname': "ai_diagnostic_trends_2024",
            'initial_data': {
                "title": "AI Diagnostic Trends 2024",
                "content": "Recent advances in AI diagnostic tools have shown significant promise. Key developments include FDA approval of new AI-powered imaging systems, integration with electronic health records, and improved accuracy in early disease detection.",
                "key_statistics": [
                    "73% increase in AI diagnostic tool approvals in 2024",
                    "Medical imaging AI accuracy rates now exceed 95%",
                    "40% reduction in diagnostic errors with AI assistance"
                ],
                "regulatory_updates": [
                    "FDA released new guidelines for AI medical devices",
                    "European Union updated medical device regulations for AI",
                    "Increased focus on algorithm transparency and bias detection"
                ]
            },
            'is_shared': False,
            'is_versioned': False,
            'initial_version': "None",
            'is_system_entity': False
        },
        # HITL feedback additional context file
        {
            'namespace': "summary_context_files_healthcare",
            'docname': "fda_ai_medical_devices_2024",
            'initial_data': {
                "title": "FDA AI Medical Device Regulations 2024",
                "content": "The FDA has implemented new regulatory frameworks for AI-powered medical devices, focusing on post-market monitoring and algorithm transparency.",
                "approved_devices": [
                    "AI-powered retinal screening systems",
                    "Machine learning ECG analysis tools",
                    "Computer-aided pathology diagnosis platforms"
                ],
                "regulatory_challenges": [
                    "Algorithm drift monitoring requirements",
                    "Clinical validation standards for AI",
                    "Data quality and bias mitigation protocols"
                ],
                "compliance_requirements": [
                    "Software lifecycle processes",
                    "Real-world performance monitoring", 
                    "Risk management for AI algorithms"
                ]
            },
            'is_shared': False,
            'is_versioned': False,
            'initial_version': "None",
            'is_system_entity': False
        }
    ]
    cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': "summary_context_files_healthcare",
            'docname': "ai_diagnostic_trends_2024",
            'is_shared': False,
            'is_versioned': False,
            'is_system_entity': False
        },
        {
            'namespace': "summary_context_files_healthcare",
            'docname': "fda_ai_medical_devices_2024",
            'is_shared': False,
            'is_versioned': False,
            'is_system_entity': False
        }
    ]
    
    print(f"\n--- Running Scenario: {test_scenario['name']} ---")
    
    try:
        final_status, final_outputs = await run_workflow_test(
            test_name=f"{test_name} - {test_scenario['name']}",
            workflow_graph_schema=workflow_graph_schema,
            initial_inputs=test_scenario['initial_inputs'],
            expected_final_status=WorkflowRunStatus.COMPLETED,
            hitl_inputs=predefined_hitl_inputs,
            setup_docs=setup_docs,
            cleanup_docs=cleanup_docs,
            cleanup_docs_created_by_setup=False,
            validate_output_func=validate_file_summarization_output,
            stream_intermediate_results=True,
            poll_interval_sec=3,
            timeout_sec=1800  # 30 minutes for comprehensive summarization
        )
        
        # Display results
        if final_outputs:
            print(f"\nTest Results:")
            summary_content = final_outputs.get('summary_content', '')
            print(f"Summary Content Length: {len(summary_content)} characters")
            
            if final_outputs.get('final_summary_paths'):
                print("✓ Summary report was successfully saved")
                print(f"Saved to: {final_outputs.get('final_summary_paths')}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    
    print(f"\n--- {test_name} Completed Successfully ---")


# Entry point
if __name__ == "__main__":
    print("="*60)
    print("File Summarization Workflow Test")
    print("="*60)
    
    try:
        asyncio.run(main_test_file_summarization())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=$(pwd):$(pwd)/services poetry run python standalone_test_client/kiwi_client/workflows/active/labs/wf_on_demand_external_research.py")
