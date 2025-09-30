"""
On-Demand External Research Workflow

This workflow enables comprehensive external research with:
- Perplexity deep research models for comprehensive web research
- Automatic research name generation using GPT-5-mini
- UUID-based unique document naming
- Human-in-the-loop approval for research review and feedback
- Iteration limit checking to prevent infinite loops
- Flexible save configuration for custom document storage
- Final research report saving with proper document management

Test Configuration:
- Uses external research document types from the system configuration
- Creates realistic test data matching the research document schemas
- Tests various scenarios including research generation, HITL approval, and feedback processing
- Includes proper HITL approval flows and document saving with iteration limits
"""


# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    EXTERNAL_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
)

# Import LLM inputs
from kiwi_client.workflows.active.labs.on_demand_external_research.wf_llm_inputs import (
    # System prompts
    DEFAULT_RESEARCH_SYSTEM_PROMPT,
    RESEARCH_NAME_GENERATION_SYSTEM_PROMPT,
    
    # User prompt templates
    DEFAULT_RESEARCH_USER_PROMPT_TEMPLATE,
    RESEARCH_NAME_GENERATION_USER_PROMPT_TEMPLATE,
    FEEDBACK_REVISION_USER_PROMPT_TEMPLATE,
    
    # Schemas
    RESEARCH_NAME_OUTPUT_SCHEMA,
    
    # Code runner configurations
    SAVE_CONFIG_GENERATION_CODE,
    
    # LLM configuration
    MAX_LLM_ITERATIONS,
    PERPLEXITY_LLM_PROVIDER,
    PERPLEXITY_LLM_MODEL,
    GPT_MINI_PROVIDER,
    GPT_MINI_MODEL,
    TEMPERATURE,
    MAX_TOKENS,
    RESEARCH_NAME_MAX_TOKENS,
)

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
                    "research_context": {
                        "type": "str",
                        "required": True,
                        "description": "The research topic or context to investigate"
                    },
                    "asset_name": {
                        "type": "str",
                        "required": True,
                        "description": "Asset name used for namespace and docname placeholder replacement"
                    },
                    "namespace": {
                        "type": "str",
                        "required": False,
                        "default": EXTERNAL_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
                        "description": "Optional namespace for saving research report. Use {item} placeholder for asset name insertion"
                    },
                    "docname": {
                        "type": "str", 
                        "required": False,
                        "description": "Optional docname for saving research report. Use {item} for random UUID suffix insertion"
                    },
                    "is_shared": {
                        "type": "bool",
                        "required": False,
                        "default": False,
                        "description": "Optional flag to determine if research report should be shared. Defaults to False"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load for research context. Each item should have 'namespace', 'docname', and 'is_shared' fields."
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
                "choices": ["generate_save_config", "construct_research_name_prompt"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "generate_save_config",
                        "input_path": "tag_results.docname_provided",
                        "target_value": True
                    },
                    {
                        "choice_id": "construct_research_name_prompt",
                        "input_path": "tag_results.docname_provided",
                        "target_value": False
                    }
                ],
                "default_choice": "construct_research_name_prompt"
            }
        },
        
        # 4. Construct Research Name Prompt
        "construct_research_name_prompt": {
            "node_id": "construct_research_name_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "research_name_user_prompt": {
                        "id": "research_name_user_prompt",
                        "template": RESEARCH_NAME_GENERATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "research_context": None
                        },
                        "construct_options": {
                            "research_context": "research_context"
                        }
                    }
                }
            }
        },

        # 5. Generate Research Name (GPT-5-mini with structured output)
        "generate_research_name": {
            "node_id": "generate_research_name",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": GPT_MINI_PROVIDER,
                        "model": GPT_MINI_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": RESEARCH_NAME_MAX_TOKENS,
                    "reasoning_effort_class": "low",  # low, medium, high
                },
                "default_system_prompt": RESEARCH_NAME_GENERATION_SYSTEM_PROMPT,
                "output_schema": {
                    "schema_definition": RESEARCH_NAME_OUTPUT_SCHEMA,
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
        
        # 7. Construct Research Prompt
        "construct_research_prompt": {
            "node_id": "construct_research_prompt",
            "node_name": "prompt_constructor",
            "defer_node": True,
            "node_config": {
                "prompt_templates": {
                    "research_user_prompt": {
                        "id": "research_user_prompt",
                        "template": DEFAULT_RESEARCH_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "research_context": None,
                            "additional_user_files": ""
                        },
                        "construct_options": {
                            "research_context": "research_context",
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

        # 9. Conduct Deep Research with Perplexity
        "conduct_research": {
            "node_id": "conduct_research",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": PERPLEXITY_LLM_PROVIDER,
                        "model": PERPLEXITY_LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                },
                "default_system_prompt": DEFAULT_RESEARCH_SYSTEM_PROMPT,
            }
        },
        
        # 10. Save Research Draft
        "save_research_draft": {
            "node_id": "save_research_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "store_configs_input_path": "save_config",
            }
        },
        
        # 11. HITL Research Approval
        "research_approval": {
            "node_id": "research_approval",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_action": {
                        "type": "enum",
                        "enum_values": ["approve", "request_revisions", "cancel"],
                        "required": True,
                        "description": "User's decision on the research report"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for research improvements (required if action is request_revisions)"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load for research feedback analysis. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    }
                }
            }
        },
        
        # 12. Route from HITL approval
        "route_research_approval": {
            "node_id": "route_research_approval",
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
            # "defer_node": True,
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
        
        # # 15. Save Final Research
        # "save_final_research": {
        #     "node_id": "save_final_research",
        #     "node_name": "store_customer_data",
        #     "node_config": {
        #         "store_configs_input_path": "save_config",
        #     }
        # },
        
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
                {"src_field": "research_context", "dst_field": "research_context"},
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
            "dst_node_id": "construct_research_name_prompt"
        },
        
        # State -> Construct research name prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_research_name_prompt",
            "mappings": [
                {"src_field": "research_context", "dst_field": "research_context"}
            ]
        },

        # Construct research name prompt -> Generate research name
        {
            "src_node_id": "construct_research_name_prompt",
            "dst_node_id": "generate_research_name",
            "mappings": [
                {"src_field": "research_name_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # Generate research name -> Generate save config
        {
            "src_node_id": "generate_research_name",
            "dst_node_id": "generate_save_config",
            "mappings": [
                {"src_field": "structured_output.research_name", "dst_field": "input_data.research_name"}
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
        
        # Generate save config -> Construct research prompt
        {
            "src_node_id": "generate_save_config",
            "dst_node_id": "construct_research_prompt"
        },
        
        # Route -> Generate save config (when docname is provided)
        {
            "src_node_id": "route_docname_check",
            "dst_node_id": "generate_save_config"
        },
        
        # Load additional files -> Construct research prompt (pass additional files data)
        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_research_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },
        
        # State -> Construct research prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_research_prompt",
            "mappings": [
                {"src_field": "research_context", "dst_field": "research_context"},
                {"src_field": "revision_feedback", "dst_field": "revision_feedback"}
            ]
        },
        
        # Construct research prompt -> Conduct research
        {
            "src_node_id": "construct_research_prompt",
            "dst_node_id": "conduct_research",
            "mappings": [
                {"src_field": "research_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # State -> Conduct research
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "conduct_research",
            "mappings": [
                {"src_field": "messages_history", "dst_field": "messages_history"}
            ]
        },
        
        # Conduct research -> State (store research results and metadata)
        {
            "src_node_id": "conduct_research",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "text_content", "dst_field": "research_content.report"},
                {"src_field": "current_messages", "dst_field": "messages_history"},
                {"src_field": "metadata", "dst_field": "generation_metadata"},
                {"src_field": "web_search_result", "dst_field": "research_content.citations"}
            ]
        },
        
        # Conduct research -> Save research draft
        {
            "src_node_id": "conduct_research",
            "dst_node_id": "save_research_draft"
        },
        
        # State -> Save research draft (provide save config and research content)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_research_draft",
            "mappings": [
                {"src_field": "save_config", "dst_field": "save_config"},
                {"src_field": "research_content", "dst_field": "research_content"}
            ]
        },
        
        # Save research draft -> HITL approval
        {
            "src_node_id": "save_research_draft",
            "dst_node_id": "research_approval"
        },
        
        # State -> HITL approval
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "research_approval",
            "mappings": [
                {"src_field": "research_content", "dst_field": "research_content"}
            ]
        },
        
        # HITL approval -> State (store user feedback)
        {
            "src_node_id": "research_approval",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "revision_feedback", "dst_field": "revision_feedback"},
                {"src_field": "user_action", "dst_field": "user_action"},
                {"src_field": "load_additional_user_files", "dst_field": "hitl_load_additional_user_files"}
            ]
        },
        
        # HITL approval -> Transform HITL Additional Files Config
        {
            "src_node_id": "research_approval",
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
        
        # HITL approval -> Route research approval
        {
            "src_node_id": "load_hitl_additional_user_files_node",
            "dst_node_id": "route_research_approval"
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "route_research_approval",
            "mappings": [
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # # Route -> Save final research
        # {
        #     "src_node_id": "route_research_approval",
        #     "dst_node_id": "save_final_research"
        # },
        
        # # State -> Save final research (provide save config and research content)
        # {
        #     "src_node_id": "$graph_state",
        #     "dst_node_id": "save_final_research",
        #     "mappings": [
        #         {"src_field": "save_config", "dst_field": "save_config"},
        #         {"src_field": "research_content", "dst_field": "research_content"}
        #     ]
        # },
        
        # Route -> Check iteration limit
        {
            "src_node_id": "route_research_approval",
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
        # {
        #     "src_node_id": "load_hitl_additional_user_files_node",
        #     "dst_node_id": "route_iteration_check"
        # },
        
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

        # Construct feedback prompt -> Conduct research (revision loop)
        {
            "src_node_id": "construct_feedback_prompt",
            "dst_node_id": "conduct_research",
            "mappings": [
                {"src_field": "revision_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # Route -> Output node (multiple paths)
        {
            "src_node_id": "route_research_approval",
            "dst_node_id": "output_node"
        },
        
        {
            "src_node_id": "route_iteration_check",
            "dst_node_id": "output_node"
        },
        
        # Save final research -> Output node
        {
            "src_node_id": "save_research_draft",
            "dst_node_id": "output_node",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "final_research_paths"}
            ]
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "research_content", "dst_field": "research_content"}
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
