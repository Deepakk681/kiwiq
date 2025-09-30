"""
Brief to Blog Generation Workflow

This workflow enables blog content generation from a brief with:
- Loading blog brief, SEO best practices, and company documentation
- Domain knowledge enrichment from knowledge base using document tools
- Comprehensive content generation with SEO optimization
- Human-in-the-loop approval for content review and feedback
- Feedback processing and content iteration
- Final blog post saving with proper document management

Test Configuration:
- Uses blog document types from the system configuration (blog_content_brief, blog_company_doc, etc.)
- Creates realistic test data matching the blog document schemas
- Tests various scenarios including knowledge enrichment, content generation, and feedback processing
- Includes proper HITL approval flows and document saving
"""

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    # Blog Content Brief
    BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
    # Blog Company Doc
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    # Blog Post
    BLOG_POST_DOCNAME,
    BLOG_POST_NAMESPACE_TEMPLATE,
    BLOG_POST_IS_VERSIONED,

    # Blog SEO Best Practices
    BLOG_SEO_BEST_PRACTICES_DOCNAME,
    BLOG_SEO_BEST_PRACTICES_NAMESPACE_TEMPLATE,
    BLOG_SEO_BEST_PRACTICES_IS_SHARED,
    BLOG_SEO_BEST_PRACTICES_IS_SYSTEM_ENTITY,
)

from kiwi_client.workflows.active.content_studio.blog_brief_to_blog_sandbox.wf_llm_inputs import (
    KNOWLEDGE_ENRICHMENT_SYSTEM_PROMPT,
    KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE,
    CONTENT_GENERATION_SYSTEM_PROMPT,
    CONTENT_GENERATION_USER_PROMPT_TEMPLATE,
    FEEDBACK_ANALYSIS_SYSTEM_PROMPT,
    FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE,
    CONTENT_UPDATE_USER_PROMPT_TEMPLATE,
    KNOWLEDGE_ENRICHMENT_OUTPUT_SCHEMA,
    CONTENT_GENERATION_OUTPUT_SCHEMA,
    FEEDBACK_ANALYSIS_OUTPUT_SCHEMA,
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    MAX_TOOL_CALLS,
    CONSIDER_FAILED_CALLS_IN_LIMIT,
    TOOLCALL_LLM_PROVIDER,
    TOOLCALL_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
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
                    "company_name": {
                        "type": "str",
                        "required": True,
                        "description": "Name of the company to analyze"
                    },
                    "brief_docname": { "type": "str", "required": True, "description": "Docname of the brief being used for drafting." },
                    "post_uuid": { "type": "str", "required": True, "description": "UUID of the post being generated." },
                    "initial_status": { "type": "str", "required": False, "default": "draft", "description": "Initial status used when saving drafts." },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    },
                    "user_instructions": {
                        "type": "str",
                        "required": False,
                        "description": "User instructions for the blog post."
                    }
                }
            }
        },
        
        # 2. Load All Context Documents  
        "load_all_context_docs": {
            "node_id": "load_all_context_docs",
            "node_name": "load_customer_data",
            "node_config": {
                # Global defaults
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
                
                # Configure to load multiple documents
                "load_paths": [
                    # Blog Content Brief
                    {
                        "filename_config": {
                            "input_namespace_field": "company_name",
                            "input_namespace_field_pattern": BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
                            "input_docname_field": "brief_docname",
                        },
                        "output_field_name": "blog_brief",
                    },
                    # Company Guidelines
                    {
                        "filename_config": {
                            "input_namespace_field": "company_name",
                            "input_namespace_field_pattern": BLOG_COMPANY_NAMESPACE_TEMPLATE,
                            "static_docname": BLOG_COMPANY_DOCNAME,
                        },
                        "output_field_name": "company_guidelines",
                    },
                    # SEO Best Practices (System Document)
                    {
                        "filename_config": {
                            "static_namespace": BLOG_SEO_BEST_PRACTICES_NAMESPACE_TEMPLATE,
                            "static_docname": BLOG_SEO_BEST_PRACTICES_DOCNAME,
                        },
                        "output_field_name": "seo_best_practices",
                        "is_shared": BLOG_SEO_BEST_PRACTICES_IS_SHARED,
                        "is_system_entity": BLOG_SEO_BEST_PRACTICES_IS_SYSTEM_ENTITY
                    }
                ],
            },
        },
        
        # 3. Transform Additional User Files Format (if provided)
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
        
        # 5. Load Additional User Files (conditional)
        "load_additional_user_files_node": {
            "node_id": "load_additional_user_files_node", 
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },
        
        # 6. Construct Knowledge Enrichment Prompt
        "construct_knowledge_enrichment_prompt": {
            "node_id": "construct_knowledge_enrichment_prompt",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,  # Wait for all data loads before proceeding
            "node_config": {
                "prompt_templates": {
                    "knowledge_enrichment_user_prompt": {
                        "id": "knowledge_enrichment_prompt",
                        "template": KNOWLEDGE_ENRICHMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "blog_brief": None,
                            "company_name": None
                        },
                        "construct_options": {
                            "blog_brief": "blog_brief",
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
        
        # 4. Knowledge Enrichment LLM with Document Tools
        "knowledge_enrichment_llm": {
            "node_id": "knowledge_enrichment_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": TOOLCALL_LLM_PROVIDER,
                        "model": TOOLCALL_LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS,
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
        
        # 5a. Check Conditions for Knowledge Enrichment Tool Use
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
                                "value": MAX_LLM_ITERATIONS
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
        
        # 5b. Route Based on Conditions (no HITL)
        "route_from_conditions": {
            "node_id": "route_from_conditions",
            "node_name": "router_node",
            "node_config": {
                "choices": ["tool_executor", "construct_content_generation_prompt"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_content_generation_prompt",
                        "input_path": "tag_results.iteration_limit_check",
                        "target_value": True
                    },
                    {
                        "choice_id": "tool_executor",
                        "input_path": "tag_results.tool_calls_empty",
                        "target_value": False
                    },
                    {
                        "choice_id": "construct_content_generation_prompt",
                        "input_path": "tag_results.structured_output_empty",
                        "target_value": False
                    }
                ],
                "default_choice": "construct_content_generation_prompt"
            }
        },
        
        # 5c. Tool Executor (executes document tools)
        "tool_executor": {
            "node_id": "tool_executor",
            "node_name": "tool_executor",
            "node_config": {
                "default_timeout": 30.0,
                "max_concurrent_executions": 5,
                "continue_on_error": True,
                "include_error_details": True,
                "map_executor_input_fields_to_tool_input": True,
                "tool_call_limit": MAX_TOOL_CALLS,
                "consider_failed_calls_in_limit": CONSIDER_FAILED_CALLS_IN_LIMIT,
            }
        },

        # 7. Construct Content Generation Prompt
        "construct_content_generation_prompt": {
            "node_id": "construct_content_generation_prompt",
            "node_name": "prompt_constructor",
            "defer_node": True,
            "node_config": {
                "prompt_templates": {
                    "content_generation_user_prompt": {
                        "id": "content_generation_user_prompt",
                        "template": CONTENT_GENERATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "blog_brief": None,
                            "knowledge_context": None,
                            "additional_user_files": "",
                            "user_instructions": None,
                        },
                        "construct_options": {
                            "blog_brief": "blog_brief",
                            "knowledge_context": "knowledge_context",
                            "additional_user_files": "additional_user_files",
                            "user_instructions": "user_instructions"
                        }
                    },
                    "content_generation_system_prompt": {
                        "id": "content_generation_system_prompt",
                        "template": CONTENT_GENERATION_SYSTEM_PROMPT,
                        "variables": {
                            "seo_best_practices": None,
                        },
                        "construct_options": {
                            "seo_best_practices": "seo_best_practices",
                        }
                    }
                }
            }
        },
        
        # 7. Content Generation LLM
        "content_generation_llm": {
            "node_id": "content_generation_llm",
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
                    "schema_definition": CONTENT_GENERATION_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False,
                }
            }
        },
        
        # 7b. Store Initial Draft
        "store_draft": {
            "node_id": "store_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": True,
                    "operation": "initialize",
                    "version": "draft_v1"
                },
                "store_configs": [
                    {
                        "input_field_path": "blog_content",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_POST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_POST_DOCNAME,
                                "input_docname_field": "post_uuid"
                            }
                        },
                        "versioning": {
                            "is_versioned": BLOG_POST_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                        "extra_fields": [
                            {
                                "src_path": "initial_status",     
                                "dst_path": "status"
                            },
                            {
                                "src_path": "post_uuid",
                                "dst_path": "uuid"
                            }
                        ]
                    }
                ]
            }
        },
        
        # 7c. Save Draft (manual upsert)
        "save_draft": {
            "node_id": "save_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": BLOG_POST_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "store_configs": [
                    {
                        "input_field_path": "blog_content",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_POST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_POST_DOCNAME,
                                "input_docname_field": "post_uuid"
                            }
                        },
                        "versioning": {
                            "is_versioned": BLOG_POST_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                        "extra_fields": [
                            {
                                "src_path": "initial_status",
                                "dst_path": "status"
                            },
                            {
                                "src_path": "post_uuid",
                                "dst_path": "uuid"
                            }
                        ]
                    }
                ]
            }
        },
        
        # 7d. Save Final Draft
        "save_final_draft": {
            "node_id": "save_final_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": BLOG_POST_IS_VERSIONED,
                    "operation": "upsert_versioned"
                },
                "store_configs": [
                    {
                        "input_field_path": "blog_content",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_POST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_POST_DOCNAME,
                                "input_docname_field": "post_uuid"
                            }
                        },
                        "versioning": {
                            "is_versioned": BLOG_POST_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                        "extra_fields": [
                            {
                                "src_path": "user_action",
                                "dst_path": "status"
                            },
                            {
                                "src_path": "post_uuid",
                                "dst_path": "uuid"
                            }
                        ]
                    }
                ]
            }
        },
        
        # 8. HITL Approval Node
        "content_approval": {
            "node_id": "content_approval",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_action": {
                        "type": "enum",
                        "enum_values": ["complete", "provide_feedback", "cancel_workflow", "draft"],
                        "required": True,
                        "description": "User's decision on the generated content"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for content improvement (required if action is revise_content)"
                    },
                    "updated_content_draft": {
                        "type": "dict",
                        "required": True,
                        "description": "Updated blog content"
                    },
                    "load_additional_user_files": {
                        "type": "list",
                        "required": False,
                        "default": [],
                        "description": "Optional list of additional user files to load for feedback analysis. Each item should have 'namespace', 'docname', and 'is_shared' fields."
                    }
                }
            }
        },
        
        # 8b. Delete Draft on Cancel
        "delete_draft_on_cancel": {
            "node_id": "delete_draft_on_cancel",
            "node_name": "delete_customer_data",
            "node_config": {
                "search_params": {
                    "input_namespace_field": "company_name",
                    "input_namespace_field_pattern": BLOG_POST_NAMESPACE_TEMPLATE,
                    "input_docname_field": "post_uuid",
                    "input_docname_field_pattern": BLOG_POST_DOCNAME
                }
            }
        },
        
        # 9. Route from HITL (content approval)
        "route_content_approval": {
            "node_id": "route_content_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["save_final_draft", "check_iteration_limit", "delete_draft_on_cancel", "save_draft"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "save_final_draft",
                        "input_path": "user_action",
                        "target_value": "complete"
                    },
                    {
                        "choice_id": "check_iteration_limit",
                        "input_path": "user_action",
                        "target_value": "provide_feedback"
                    },
                    {
                        "choice_id": "delete_draft_on_cancel",
                        "input_path": "user_action",
                        "target_value": "cancel_workflow"
                    },
                    {
                        "choice_id": "save_draft",
                        "input_path": "user_action",
                        "target_value": "draft"
                    }
                ],
                "default_choice": "delete_draft_on_cancel"
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
                        "condition_groups": [ {
                            "logical_operator": "and",
                            "conditions": [ {
                                "field": "generation_metadata.iteration_count",
                                "operator": "less_than",
                                "value": MAX_LLM_ITERATIONS
                            } ]
                        } ],
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
                "choices": ["construct_feedback_analysis_prompt", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_feedback_analysis_prompt",
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
        
        # 12. Transform HITL Additional Files Format
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
        
        # 13. Load HITL Additional User Files
        "load_hitl_additional_user_files_node": {
            "node_id": "load_hitl_additional_user_files_node",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },
        
        # 14. Construct Feedback Analysis Prompt
        "construct_feedback_analysis_prompt": {
            "node_id": "construct_feedback_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "feedback_analysis_prompt": {
                        "id": "feedback_analysis_prompt",
                        "template": FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "blog_content": None,
                            "user_feedback": None,
                            "hitl_additional_user_files": "",
                        },
                        "construct_options": {
                            "blog_content": "blog_content",
                            "user_feedback": "user_feedback",
                            "hitl_additional_user_files": "hitl_additional_user_files",
                        }
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": FEEDBACK_ANALYSIS_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 13. Feedback Analysis LLM with Tools
        "feedback_analysis_llm": {
            "node_id": "feedback_analysis_llm",
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
                    "schema_definition": FEEDBACK_ANALYSIS_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False,
                }
            }
        },
        
        # 14. Construct Feedback-based Content Update Prompt
        "construct_content_update_prompt": {
            "node_id": "construct_content_update_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "content_update_prompt": {
                        "id": "content_update_prompt",
                        "template": CONTENT_UPDATE_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "original_content": None,
                            "update_instructions": None,
                            "hitl_additional_user_files": "",
                        },
                        "construct_options": {
                            "original_content": "original_content",
                            "update_instructions": "update_instructions",
                            "hitl_additional_user_files": "hitl_additional_user_files",
                        }
                    }
                }
            }
        },
        
        # 16. Output Node
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
                {"src_field": "brief_docname", "dst_field": "brief_docname"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "initial_status", "dst_field": "initial_status"},
                {"src_field": "load_additional_user_files", "dst_field": "load_additional_user_files"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"}
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
        
        # # Load Additional Files -> State (store loaded files)
        # {
        #     "src_node_id": "load_additional_user_files_node",
        #     "dst_node_id": "$graph_state",
        #     "mappings": [
        #         {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
        #     ]
        # },
        
        # Input -> Load All Context Documents
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_all_context_docs",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "brief_docname", "dst_field": "brief_docname"}
            ]
        },
        
        # Store loaded docs in state
        {
            "src_node_id": "load_all_context_docs",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "blog_brief", "dst_field": "blog_brief"},
                {"src_field": "company_guidelines", "dst_field": "company_guidelines"},
                {"src_field": "seo_best_practices", "dst_field": "seo_best_practices"}
            ]
        },
        
        # Loaded Context Docs -> Knowledge Enrichment Prompt
        {
            "src_node_id": "load_all_context_docs",
            "dst_node_id": "construct_knowledge_enrichment_prompt"
        },
        
        # State -> Knowledge Enrichment Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_knowledge_enrichment_prompt",
            "mappings": [
                {"src_field": "blog_brief", "dst_field": "blog_brief"},
                {"src_field": "company_name", "dst_field": "company_name"}
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

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "check_conditions",
            "mappings": [
                {"src_field": "latest_tool_calls", "dst_field": "tool_calls"},
                {"src_field": "generation_metadata", "dst_field": "generation_metadata"},
                {"src_field": "knowledge_context", "dst_field": "knowledge_context"}
            ]
        },
        
        # State -> Content Generation Prompt
        
        
        # State -> Check Conditions (pass latest tool calls and metadata)
        
        
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
                {"src_field": "failed_tool_calls", "dst_field": "prior_failed_calls"},
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
                {"src_field": "failed_calls", "dst_field": "failed_tool_calls"},
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
        
        # Router -> Construct Content Generation Prompt (control flow when no tools or limit reached)
        {
            "src_node_id": "route_from_conditions",
            "dst_node_id": "construct_content_generation_prompt"
        },

        {
            "src_node_id": "load_additional_user_files_node",
            "dst_node_id": "construct_content_generation_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "additional_user_files", "dst_field": "additional_user_files"}
            ]
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_generation_prompt",
            "mappings": [
                {"src_field": "blog_brief", "dst_field": "blog_brief"},
                {"src_field": "company_guidelines", "dst_field": "company_guidelines"},
                {"src_field": "knowledge_context", "dst_field": "knowledge_context"},
                {"src_field": "seo_best_practices", "dst_field": "seo_best_practices"},
                # {"src_field": "additional_user_files", "dst_field": "additional_user_files"},
                {"src_field": "user_instructions", "dst_field": "user_instructions"}
            ]
        },
        
        # Content Generation Prompt -> Content Generation LLM
        {
            "src_node_id": "construct_content_generation_prompt",
            "dst_node_id": "content_generation_llm",
            "mappings": [
                {"src_field": "content_generation_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "content_generation_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Content Generation LLM -> State (store generated content)
        {
            "src_node_id": "content_generation_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "blog_content"},
                {"src_field": "current_messages", "dst_field": "content_generation_messages"},
                {"src_field": "metadata", "dst_field": "generation_metadata", "description": "Store LLM metadata (e.g., token usage, iteration count)."}
            ]
        },
        
        # Content Generation LLM -> HITL
        {
            "src_node_id": "content_generation_llm",
            "dst_node_id": "content_approval",
            "mappings": []
        },
        
        # Content Generation LLM -> Store Initial Draft
        {
            "src_node_id": "content_generation_llm",
            "dst_node_id": "store_draft",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "blog_content"}
            ]
        },
        
        # State -> Store Initial Draft
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "store_draft",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "initial_status", "dst_field": "initial_status"}
            ]
        },
        
        # Store Initial Draft -> State (save paths)
        {
            "src_node_id": "store_draft",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "draft_storage_paths"}
            ]
        },
        
        
        
        # HITL -> State (store user edits and action)
        {
            "src_node_id": "content_approval",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "revision_feedback", "dst_field": "current_revision_feedback"},
                {"src_field": "updated_content_draft", "dst_field": "blog_content"},
                {"src_field": "user_action", "dst_field": "user_action"},
                {"src_field": "load_additional_user_files", "dst_field": "hitl_load_additional_user_files"}
            ]
        },
        
        # HITL -> Transform HITL Additional Files Config
        {
            "src_node_id": "content_approval",
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

        # HITL -> Router (content approval)
        {
            "src_node_id": "load_hitl_additional_user_files_node",
            "dst_node_id": "route_content_approval",
            "mappings": [
            ]
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "route_content_approval",
            "mappings": [
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # Router -> Save Blog Post (control flow)
        {
            "src_node_id": "route_content_approval",
            "dst_node_id": "save_final_draft"
        },
        
        # State -> Save Blog Post
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_final_draft",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "blog_content", "dst_field": "blog_content"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "brief_docname", "dst_field": "brief_docname"},
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # Router -> Check Iteration Limit (control flow)
        {
            "src_node_id": "route_content_approval",
            "dst_node_id": "check_iteration_limit"
        },
        
        # State -> Check Iteration Limit (provide generation metadata)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "check_iteration_limit",
            "mappings": [
                {"src_field": "generation_metadata", "dst_field": "generation_metadata"}
            ]
        },
        
        # Check Iteration Limit -> Route on Limit Check (pass results for routing)
        {
            "src_node_id": "check_iteration_limit",
            "dst_node_id": "route_on_limit_check",
            "mappings": [
                {"src_field": "branch", "dst_field": "iteration_branch_result"},
                {"src_field": "tag_results", "dst_field": "if_else_condition_tag_results"},
                {"src_field": "condition_result", "dst_field": "if_else_overall_condition_result"}
            ]
        },
        
        # Route on Limit Check -> Construct Feedback Analysis Prompt (control flow)
        {
            "src_node_id": "route_on_limit_check",
            "dst_node_id": "construct_feedback_analysis_prompt"
        },
        
        {
            "src_node_id": "load_hitl_additional_user_files_node",
            "dst_node_id": "construct_feedback_analysis_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "hitl_additional_user_files", "dst_field": "hitl_additional_user_files"}
            ]
        },

        {
            "src_node_id": "load_hitl_additional_user_files_node",
            "dst_node_id": "construct_content_update_prompt",
            "data_only_edge": True,
            "mappings": [
                {"src_field": "hitl_additional_user_files", "dst_field": "hitl_additional_user_files"}
            ]
        },
        
        # Route on Limit Check -> Output Node (control flow)
        {
            "src_node_id": "route_on_limit_check",
            "dst_node_id": "output_node"
        },
        
        # Router -> Save as Draft (control flow)
        {
            "src_node_id": "route_content_approval",
            "dst_node_id": "save_draft"
        },
        
        # Router -> Delete Draft on Cancel (control flow)
        {
            "src_node_id": "route_content_approval",
            "dst_node_id": "delete_draft_on_cancel"
        },
        
        # State -> Delete Draft on Cancel (provide company_name and post_uuid)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "delete_draft_on_cancel",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"}
            ]
        },
        
        # Delete Draft on Cancel -> Output Node
        {
            "src_node_id": "delete_draft_on_cancel",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "deleted_count", "dst_field": "cancelled_drafts_deleted"},
                {"src_field": "deleted_documents", "dst_field": "cancelled_draft_details"}
            ]
        },
        
        # State -> Save as Draft
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_draft",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "blog_content", "dst_field": "blog_content"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "brief_docname", "dst_field": "brief_docname"},
                {"src_field": "initial_status", "dst_field": "initial_status"}
            ]
        },
        
        # Save Draft -> HITL (loop back)
        {
            "src_node_id": "save_draft",
            "dst_node_id": "content_approval"
        },
        
        # State -> HITL (provide current blog content back to HITL)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "content_approval",
            "mappings": [
                {"src_field": "blog_content", "dst_field": "blog_content"}
            ]
        },
        
        # State -> Feedback Analysis Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_feedback_analysis_prompt",
            "mappings": [
                {"src_field": "blog_content", "dst_field": "blog_content"},
                {"src_field": "current_revision_feedback", "dst_field": "user_feedback"}
            ]
        },
        
        # Feedback Analysis Prompt -> Feedback Analysis LLM
        {
            "src_node_id": "construct_feedback_analysis_prompt",
            "dst_node_id": "feedback_analysis_llm",
            "mappings": [
                {"src_field": "feedback_analysis_prompt", "dst_field": "user_prompt"},
                {"src_field": "system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Feedback Analysis LLM -> Content Update Prompt
        {
            "src_node_id": "feedback_analysis_llm",
            "dst_node_id": "construct_content_update_prompt",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "update_instructions"}
            ]
        },
        
        # State -> Content Update Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_update_prompt",
            "mappings": [
                {"src_field": "blog_content", "dst_field": "original_content"}
            ]
        },
        
        # Content Update Prompt -> Content Generation LLM (for iteration)
        {
            "src_node_id": "construct_content_update_prompt",
            "dst_node_id": "content_generation_llm",
            "mappings": [
                {"src_field": "content_update_prompt", "dst_field": "user_prompt"}            ]
        },
        
        # State -> Content Generation LLM (provide message history for iteration)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "content_generation_llm",
            "mappings": [
                {"src_field": "content_generation_messages", "dst_field": "messages_history"}
            ]
        },
        
        # Save Blog Post -> Output
        {
            "src_node_id": "save_final_draft",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "final_blog_post_paths"}
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "messages_history": "add_messages",
                "content_generation_messages": "add_messages",
                "generation_metadata": "replace",
                "latest_tool_calls": "replace",
                "latest_tool_outputs": "replace",
                "view_context": "merge_dicts",
                "user_action": "replace",
                "hitl_load_additional_user_files": "replace"
            }
        }
    }
}
