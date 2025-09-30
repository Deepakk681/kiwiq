"""
Content Optimization Workflow

This workflow enables comprehensive blog content optimization with:
- Multi-faceted content analysis (structure, SEO, readability, content gaps)
- Parallel analysis execution using dynamic router
- Human-in-the-loop approval for analysis results and final content
- Sequential improvement application (content gaps → SEO → structure/readability)
- Feedback analysis and revision loops
- Company context integration throughout the process

Key Features:
- Parallel execution of content analysis steps
- Web search capabilities for competitive content gap analysis
- Structured output schemas for each analysis phase
- HITL approval flows for analysis review and final approval
- Sequential improvement processing with message history management
- Feedback-driven revision cycles
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

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_VERSIONED,
    # Blog Post constants for saving
    BLOG_POST_DOCNAME,
    BLOG_POST_NAMESPACE_TEMPLATE,
    BLOG_POST_IS_VERSIONED,
    BLOG_POST_IS_SHARED,
    BLOG_POST_IS_SYSTEM_ENTITY,
)

# Import LLM configurations from local wf_llm_inputs
from kiwi_client.workflows.active.content_studio.blog_content_optimization_sandbox.wf_llm_inputs import (
    # LLM Model Configuration
    TEMPERATURE,
    MAX_TOKENS,
    MAX_LLM_ITERATIONS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,

    # System prompts
    CONTENT_ANALYZER_SYSTEM_PROMPT,
    SEO_INTENT_ANALYZER_SYSTEM_PROMPT,
    CONTENT_GAP_FINDER_SYSTEM_PROMPT,
    CONTENT_GAP_IMPROVEMENT_SYSTEM_PROMPT,
    SEO_INTENT_IMPROVEMENT_SYSTEM_PROMPT,
    STRUCTURE_READABILITY_IMPROVEMENT_SYSTEM_PROMPT,
    FEEDBACK_ANALYSIS_SYSTEM_PROMPT,

    # User prompt templates
    CONTENT_ANALYZER_USER_PROMPT_TEMPLATE,
    SEO_INTENT_ANALYZER_USER_PROMPT_TEMPLATE,
    CONTENT_GAP_FINDER_USER_PROMPT_TEMPLATE,
    CONTENT_GAP_IMPROVEMENT_USER_PROMPT_TEMPLATE,
    SEO_INTENT_IMPROVEMENT_USER_PROMPT_TEMPLATE,
    STRUCTURE_READABILITY_IMPROVEMENT_USER_PROMPT_TEMPLATE,
    FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE,

    # Output schemas
    CONTENT_ANALYZER_OUTPUT_SCHEMA,
    SEO_INTENT_ANALYZER_OUTPUT_SCHEMA,
    CONTENT_GAP_FINDER_OUTPUT_SCHEMA,
    FINAL_OUTPUT_SCHEMA,
)

# Use imported constants
LLM_PROVIDER = DEFAULT_LLM_PROVIDER
LLM_MODEL = DEFAULT_LLM_MODEL

# Perplexity Configuration for Content Gap Research (keep as is)
PERPLEXITY_PROVIDER = "perplexity"
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_TEMPERATURE = 0.3
PERPLEXITY_MAX_TOKENS = 3000

# Workflow Limits
MAX_REVISION_ATTEMPTS = 3
MAX_ITERATIONS = 10  # Maximum iterations for HITL feedback loops

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
                        "description": "Name of the company for document operations"
                    },
                    "original_blog": {
                        "type": "str",
                        "required": True,
                        "description": "Original blog content to be optimized"
                    },
                    "route_all_choices": {
                        "type": "bool",
                        "required": False,
                        "default": True,
                        "description": "Whether to route all choices to all nodes"
                    },
                    "initial_status": {
                        "type": "str",
                        "required": False,
                        "default": "draft",
                        "description": "Initial status used when saving drafts"
                    },
                    "post_uuid": {
                        "type": "str",
                        "required": True,
                        "description": "UUID of the post being generated"
                    }
                }
            }
        },
        
        # 2. Load Company Document
        "load_company_doc": {
            "node_id": "load_company_doc",
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
                    }
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False}
            }
        },
        
        # 3. Analysis Trigger Router
        "analysis_trigger_router": {
            "node_id": "analysis_trigger_router",
            "node_name": "router_node",
            "node_config": {
                "choices": [
                    "construct_content_analyzer_prompt",
                    "construct_seo_intent_analyzer_prompt", 
                    "construct_content_gap_finder_prompt"
                ],
                "allow_multiple": True,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_content_analyzer_prompt",
                        "input_path": "route_all_choices",
                        "target_value": True
                    },
                    {
                        "choice_id": "construct_seo_intent_analyzer_prompt",
                        "input_path": "route_all_choices",
                        "target_value": True
                    },
                    {
                        "choice_id": "construct_content_gap_finder_prompt",
                        "input_path": "route_all_choices",
                        "target_value": True
                    }
                ]
            }
        },
        
        # 4a. Content Analyzer - Prompt Constructor
        "construct_content_analyzer_prompt": {
            "node_id": "construct_content_analyzer_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "content_analyzer_user_prompt": {
                        "id": "content_analyzer_user_prompt",
                        "template": CONTENT_ANALYZER_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "target_audience": None,
                            "content_goals": None,
                            "original_blog": None
                        },
                        "construct_options": {
                            "target_audience": "company_doc.icps",
                            "content_goals": "company_doc.goals",
                            "original_blog": "original_blog"
                        }
                    },
                    "content_analyzer_system_prompt": {
                        "id": "content_analyzer_system_prompt",
                        "template": CONTENT_ANALYZER_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 4b. Content Analyzer - LLM Node
        "content_analyzer_llm": {
            "node_id": "content_analyzer_llm",
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
                    "schema_definition": CONTENT_ANALYZER_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 5a. SEO Intent Analyzer - Prompt Constructor
        "construct_seo_intent_analyzer_prompt": {
            "node_id": "construct_seo_intent_analyzer_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "seo_intent_analyzer_user_prompt": {
                        "id": "seo_intent_analyzer_user_prompt",
                        "template": SEO_INTENT_ANALYZER_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "target_audience": None,
                            "content_goals": None,
                            "competitors": None,
                            "original_blog": None
                        },
                        "construct_options": {
                            "target_audience": "company_doc.icps",
                            "content_goals": "company_doc.goals",
                            "competitors": "company_doc.competitors",
                            "original_blog": "original_blog"
                        }
                    },
                    "seo_intent_analyzer_system_prompt": {
                        "id": "seo_intent_analyzer_system_prompt",
                        "template": SEO_INTENT_ANALYZER_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 5b. SEO Intent Analyzer - LLM Node
        "seo_intent_analyzer_llm": {
            "node_id": "seo_intent_analyzer_llm",
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
                    "schema_definition": SEO_INTENT_ANALYZER_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 6a. Content Gap Finder - Prompt Constructor
        "construct_content_gap_finder_prompt": {
            "node_id": "construct_content_gap_finder_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "content_gap_finder_user_prompt": {
                        "id": "content_gap_finder_user_prompt",
                        "template": CONTENT_GAP_FINDER_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "original_blog": None
                        },
                        "construct_options": {
                            "original_blog": "original_blog"
                        }
                    },
                    "content_gap_finder_system_prompt": {
                        "id": "content_gap_finder_system_prompt",
                        "template": CONTENT_GAP_FINDER_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 6b. Content Gap Finder - LLM Node (with web search)
        "content_gap_finder_llm": {
            "node_id": "content_gap_finder_llm",
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
                    "schema_definition": CONTENT_GAP_FINDER_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 7. Analysis Review - HITL Node (receives all three analysis results directly)
        "analysis_review_hitl": {
            "node_id": "analysis_review_hitl",
            "node_name": "hitl_node__default",
            "enable_node_fan_in": True,
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "final_gap_improvement": {
                        "type": "str",
                        "required": False,
                        "description": "Final user-reviewed suggestions for content gap improvements"
                    },
                    "final_seo_improvement": {
                        "type": "str",
                        "required": False,
                        "description": "Final user-reviewed suggestions for SEO improvements"
                    },
                    "final_structure_improvement": {
                        "type": "str",
                        "required": False,
                        "description": "Final user-reviewed suggestions for structure and readability improvements"
                    },
                    "gap_improvement_instructions": {
                        "type": "str",
                        "required": False,
                        "description": "Instructions for content gap improvements"
                    },
                    "seo_improvement_instructions": {
                        "type": "str",
                        "required": False,
                        "description": "Instructions for SEO improvements"
                    },
                    "structure_improvement_instructions": {
                        "type": "str",
                        "required": False,
                        "description": "Instructions for structure and readability improvements"
                    }
                }
            }
        },
        
        # 8a. Content Gap Improvement - Prompt Constructor
        "construct_content_gap_improvement_prompt": {
            "node_id": "construct_content_gap_improvement_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "content_gap_improvement_user_prompt": {
                        "id": "content_gap_improvement_user_prompt",
                        "template": CONTENT_GAP_IMPROVEMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "original_blog": None,
                            "content_gap_analysis": None,
                            "gap_improvement_instructions": None
                        },
                        "construct_options": {
                            "original_blog": "original_blog",
                            "content_gap_analysis": "final_gap_improvement",
                            "gap_improvement_instructions": "gap_improvement_instructions"
                        }
                    },
                    "content_gap_improvement_system_prompt": {
                        "id": "content_gap_improvement_system_prompt",
                        "template": CONTENT_GAP_IMPROVEMENT_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 8b. Content Gap Improvement - LLM Node
        "content_gap_improvement_llm": {
            "node_id": "content_gap_improvement_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": LLM_PROVIDER,
                        "model": LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                }
            }
        },
        
        # 9a. SEO Intent Improvement - Prompt Constructor
        "construct_seo_intent_improvement_prompt": {
            "node_id": "construct_seo_intent_improvement_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "seo_intent_improvement_user_prompt": {
                        "id": "seo_intent_improvement_user_prompt",
                        "template": SEO_INTENT_IMPROVEMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "current_blog_content": None,
                            "seo_analysis": None,
                            "seo_improvement_instructions": None
                        },
                        "construct_options": {
                            "current_blog_content": "text_content",
                            "seo_analysis": "final_seo_improvement",
                            "seo_improvement_instructions": "seo_improvement_instructions"
                        }
                    },
                    "seo_intent_improvement_system_prompt": {
                        "id": "seo_intent_improvement_system_prompt",
                        "template": SEO_INTENT_IMPROVEMENT_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 9b. SEO Intent Improvement - LLM Node
        "seo_intent_improvement_llm": {
            "node_id": "seo_intent_improvement_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": LLM_PROVIDER,
                        "model": LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS
                }
            }
        },
        
        # 10a. Structure Readability Improvement - Prompt Constructor
        "construct_structure_readability_improvement_prompt": {
            "node_id": "construct_structure_readability_improvement_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "structure_readability_improvement_user_prompt": {
                        "id": "structure_readability_improvement_user_prompt",
                        "template": STRUCTURE_READABILITY_IMPROVEMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "current_blog_content": None,
                            "structure_analysis": None,
                            "structure_improvement_instructions": None
                        },
                        "construct_options": {
                            "current_blog_content": "text_content",
                            "structure_analysis": "final_structure_improvement",
                            "structure_improvement_instructions": "structure_improvement_instructions"
                        }
                    },
                    "structure_readability_improvement_system_prompt": {
                        "id": "structure_readability_improvement_system_prompt",
                        "template": STRUCTURE_READABILITY_IMPROVEMENT_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 10b. Structure Readability Improvement - LLM Node
        "structure_readability_improvement_llm": {
            "node_id": "structure_readability_improvement_llm",
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
                    "schema_definition": FINAL_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 11. Final Approval - HITL Node
        "final_approval_hitl": {
            "node_id": "final_approval_hitl",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_action": {
                        "type": "enum",
                        "enum_values": ["complete", "provide_feedback", "cancel_workflow", "draft"],
                        "required": True,
                        "description": "User's approval decision"
                    },
                    "updated_content_draft": {
                        "type": "dict",
                        "required": True,
                        "description": "The optimized content to review and approve"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for revision (required if reject)"
                    }
                }
            }
        },
        
        # 12. Route Final Approval
        "route_final_approval": {
            "node_id": "route_final_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["save_blog_post", "check_iteration_limit", "delete_blog_post", "save_draft"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "save_blog_post",
                        "input_path": "user_action",
                        "target_value": "complete"
                    },
                    {
                        "choice_id": "check_iteration_limit",
                        "input_path": "user_action",
                        "target_value": "provide_feedback"
                    },
                    {
                        "choice_id": "delete_blog_post",
                        "input_path": "user_action",
                        "target_value": "cancel_workflow"
                    },
                    {
                        "choice_id": "save_draft",
                        "input_path": "user_action",
                        "target_value": "draft"
                    }
                ],
                "default_choice": "delete_blog_post"
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
                        "condition_groups": [ {
                            "logical_operator": "and",
                            "conditions": [ {
                                "field": "generation_metadata.iteration_count",
                                "operator": "less_than",
                                "value": MAX_ITERATIONS
                            } ]
                        } ],
                        "group_logical_operator": "and"
                    }
                ],
                "branch_logic_operator": "and"
            }
        },
        
        # 14. Route Based on Iteration Limit Check
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
        
        # 15. Feedback Analysis - Prompt Constructor
        "construct_feedback_analysis_prompt": {
            "node_id": "construct_feedback_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "feedback_analysis_user_prompt": {
                        "id": "feedback_analysis_user_prompt",
                        "template": FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "current_blog_content": None,
                            "user_feedback": None
                        },
                        "construct_options": {
                            "current_blog_content": "final_optimized_content",
                            "user_feedback": "user_feedback"
                        }
                    },
                    "feedback_analysis_system_prompt": {
                        "id": "feedback_analysis_system_prompt",
                        "template": FEEDBACK_ANALYSIS_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 13b. Feedback Analysis - LLM Node
        "feedback_analysis_llm": {
            "node_id": "feedback_analysis_llm",
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
                    "schema_definition": FINAL_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 14. Save Blog Post
        "save_blog_post": {
            "node_id": "save_blog_post",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": True,
                    "operation": "initialize",
                    "version": "optimized_v1"
                },
                "store_configs": [
                    {
                        "input_field_path": "final_optimized_content",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_POST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_POST_DOCNAME,
                                "input_docname_field": "post_uuid"
                            }
                        },
                        "generate_uuid": True,
                        "versioning": {
                            "is_versioned": BLOG_POST_IS_VERSIONED,
                            "operation": "upsert_versioned",
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
        
        # 14a. Save as Draft (Store Customer Data)
        "save_draft": {
            "node_id": "save_draft",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": True,
                    "operation": "upsert_versioned"
                },
                "store_configs": [
                    {
                        "input_field_path": "final_optimized_content",
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
        
        # 14b. Delete Blog Post on Cancel
        "delete_blog_post": {
            "node_id": "delete_blog_post",
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
        
        # 15. Output Node
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
                {"src_field": "original_blog", "dst_field": "original_blog"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "route_all_choices", "dst_field": "route_all_choices"},
                {"src_field": "initial_status", "dst_field": "initial_status"}
            ]
        },
        
        # Input -> Load Company Doc
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_company_doc",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"}
            ]
        },
        
        # Company Doc -> State: Store company context
        {
            "src_node_id": "load_company_doc",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"}
            ]
        },
        
        # Company Doc -> Analysis Router (trigger with company context loaded)
        {
            "src_node_id": "load_company_doc",
            "dst_node_id": "analysis_trigger_router"
        },

        # Analysis Router -> State: Store route_all_choices
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "analysis_trigger_router",
            "mappings": [
                {"src_field": "route_all_choices", "dst_field": "route_all_choices"}
            ]
        },
        # --- Analysis Router to Prompt Constructors ---
        {
            "src_node_id": "analysis_trigger_router",
            "dst_node_id": "construct_content_analyzer_prompt"
        },
        {
            "src_node_id": "analysis_trigger_router",
            "dst_node_id": "construct_seo_intent_analyzer_prompt"
        },
        {
            "src_node_id": "analysis_trigger_router",
            "dst_node_id": "construct_content_gap_finder_prompt"
        },
        
        # State -> All Prompt Constructors (provide context)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_analyzer_prompt",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"},
                {"src_field": "original_blog", "dst_field": "original_blog"}
            ]
        },
        {
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_seo_intent_analyzer_prompt",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"},
                {"src_field": "original_blog", "dst_field": "original_blog"}
            ]
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_gap_finder_prompt",
            "mappings": [
                {"src_field": "original_blog", "dst_field": "original_blog"}
            ]
        },
        
        # Prompt Constructors -> LLM Nodes
        {
            "src_node_id": "construct_content_analyzer_prompt",
            "dst_node_id": "content_analyzer_llm",
            "mappings": [
                {"src_field": "content_analyzer_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "content_analyzer_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        {
            "src_node_id": "construct_seo_intent_analyzer_prompt",
            "dst_node_id": "seo_intent_analyzer_llm",
            "mappings": [
                {"src_field": "seo_intent_analyzer_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "seo_intent_analyzer_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        {
            "src_node_id": "construct_content_gap_finder_prompt",
            "dst_node_id": "content_gap_finder_llm",
            "mappings": [
                {"src_field": "content_gap_finder_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "content_gap_finder_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # LLM Nodes -> HITL Review (direct connection, no merge)
        {
            "src_node_id": "content_analyzer_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "content_analysis"}
            ]
        },
        {
            "src_node_id": "seo_intent_analyzer_llm",
            "dst_node_id": "$graph_state", 
            "mappings": [
                {"src_field": "structured_output", "dst_field": "seo_analysis"}
            ]
        },
        # {
        #     "src_node_id": "content_gap_finder_llm",
        #     "dst_node_id": "$graph_state",
        #     "mappings": [
        #                         {"src_field": "structured_output", "dst_field": "content_gap_analysis"}
        #     ]
        # },
        
        {
            "src_node_id": "content_gap_finder_llm",
            "dst_node_id": "analysis_review_hitl",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "content_gap_analysis"}
            ]
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "analysis_review_hitl",
            "mappings": [
                {"src_field": "content_analysis", "dst_field": "content_analysis"},
                {"src_field": "seo_analysis", "dst_field": "seo_analysis"},
            ]
        },
        
        # HITL Review -> State: Store user-reviewed suggestions
        {
            "src_node_id": "analysis_review_hitl",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "final_gap_improvement", "dst_field": "final_gap_improvement"},
                {"src_field": "final_seo_improvement", "dst_field": "final_seo_improvement"},
                {"src_field": "final_structure_improvement", "dst_field": "final_structure_improvement"},
                {"src_field": "gap_improvement_instructions", "dst_field": "gap_improvement_instructions"},
                {"src_field": "seo_improvement_instructions", "dst_field": "seo_improvement_instructions"},
                {"src_field": "structure_improvement_instructions", "dst_field": "structure_improvement_instructions"}
            ]
        },
        
        # HITL Review -> Content Gap Improvement (start sequential chain)
        {
            "src_node_id": "analysis_review_hitl",
            "dst_node_id": "construct_content_gap_improvement_prompt"
        },
        
        # --- Sequential Improvement Chain ---
        
        # State -> Content Gap Improvement Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_gap_improvement_prompt",
            "mappings": [
                {"src_field": "original_blog", "dst_field": "original_blog"},
                {"src_field": "final_gap_improvement", "dst_field": "final_gap_improvement"},
                {"src_field": "gap_improvement_instructions", "dst_field": "gap_improvement_instructions"}
            ]
        },
        
        # Content Gap Improvement Prompt -> LLM
        {
            "src_node_id": "construct_content_gap_improvement_prompt",
            "dst_node_id": "content_gap_improvement_llm",
            "mappings": [
                {"src_field": "content_gap_improvement_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "content_gap_improvement_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Content Gap Improvement LLM -> SEO Improvement Prompt
        {
            "src_node_id": "content_gap_improvement_llm",
            "dst_node_id": "construct_seo_intent_improvement_prompt",
            "mappings": [
                {"src_field": "text_content", "dst_field": "text_content"}
            ]
        },
        
        # State -> SEO Improvement Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_seo_intent_improvement_prompt",
            "mappings": [
                {"src_field": "final_seo_improvement", "dst_field": "final_seo_improvement"},
                {"src_field": "seo_improvement_instructions", "dst_field": "seo_improvement_instructions"}
            ]
        },
        
        # SEO Improvement Prompt -> LLM
        {
            "src_node_id": "construct_seo_intent_improvement_prompt",
            "dst_node_id": "seo_intent_improvement_llm",
            "mappings": [
                {"src_field": "seo_intent_improvement_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "seo_intent_improvement_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # SEO Improvement LLM -> Structure Improvement Prompt
        {
            "src_node_id": "seo_intent_improvement_llm",
            "dst_node_id": "construct_structure_readability_improvement_prompt",
            "mappings": [
                {"src_field": "text_content", "dst_field": "text_content"}
            ]
        },
        
        # State -> Structure Improvement Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_structure_readability_improvement_prompt",
            "mappings": [
                {"src_field": "final_structure_improvement", "dst_field": "final_structure_improvement"},
                {"src_field": "structure_improvement_instructions", "dst_field": "structure_improvement_instructions"}
            ]
        },
        
        # Structure Improvement Prompt -> LLM
        {
            "src_node_id": "construct_structure_readability_improvement_prompt",
            "dst_node_id": "structure_readability_improvement_llm",
            "mappings": [
                {"src_field": "structure_readability_improvement_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "structure_readability_improvement_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Structure Improvement LLM -> State
        {
            "src_node_id": "structure_readability_improvement_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "final_optimized_content"},
                {"src_field": "metadata", "dst_field": "generation_metadata", "description": "Store LLM metadata (e.g., token usage, iteration count)."}
            ]
        },
        
        # Structure Improvement LLM -> Final Approval HITL
        {
            "src_node_id": "structure_readability_improvement_llm",
            "dst_node_id": "final_approval_hitl"
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "final_approval_hitl",
            "mappings": [
                {"src_field": "final_optimized_content", "dst_field": "final_optimized_content"}
            ]
        },
        
        # Final Approval HITL -> Route
        {
            "src_node_id": "final_approval_hitl",
            "dst_node_id": "route_final_approval",
            "mappings": [
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # Final Approval HITL -> State
        {
            "src_node_id": "final_approval_hitl",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "updated_content_draft", "dst_field": "final_optimized_content"},
                {"src_field": "revision_feedback", "dst_field": "user_feedback"},
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # --- Final Approval Router Paths ---
        {
            "src_node_id": "route_final_approval",
            "dst_node_id": "save_blog_post"
        },
        {
            "src_node_id": "route_final_approval",
            "dst_node_id": "check_iteration_limit"
        },
        {
            "src_node_id": "route_final_approval",
            "dst_node_id": "save_draft"
        },
        {
            "src_node_id": "route_final_approval",
            "dst_node_id": "delete_blog_post"
        },
        
        # Check Iteration Limit edges
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "check_iteration_limit",
            "mappings": [
                {"src_field": "generation_metadata", "dst_field": "generation_metadata", "description": "Pass LLM metadata containing iteration count."}
            ]
        },
        {
            "src_node_id": "check_iteration_limit",
            "dst_node_id": "route_on_limit_check",
            "mappings": [
                {"src_field": "branch", "dst_field": "iteration_branch_result", "description": "Pass the branch taken ('true_branch' if limit not reached, 'false_branch' if reached)."},
                {"src_field": "tag_results", "dst_field": "if_else_condition_tag_results", "description": "Pass detailed results per condition tag."},
                {"src_field": "condition_result", "dst_field": "if_else_overall_condition_result", "description": "Pass the overall boolean result of the check."}
            ]
        },
        {
            "src_node_id": "route_on_limit_check",
            "dst_node_id": "construct_feedback_analysis_prompt",
            "description": "Trigger feedback interpretation if iterations remain"
        },
        {
            "src_node_id": "route_on_limit_check",
            "dst_node_id": "output_node",
            "description": "Trigger finalization if iteration limit reached"
        },
        
        # State -> Save Blog Post
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_blog_post",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "final_optimized_content", "dst_field": "final_optimized_content"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # State -> Save as Draft
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_draft",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "final_optimized_content", "dst_field": "final_optimized_content"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"},
                {"src_field": "initial_status", "dst_field": "initial_status"}
            ]
        },
        
        # Save Draft -> HITL (loop back)
        {
            "src_node_id": "save_draft",
            "dst_node_id": "final_approval_hitl"
        },
        
        # State -> Delete Blog Post (for cancel workflow)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "delete_blog_post",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "post_uuid", "dst_field": "post_uuid"}
            ]
        },
        
        # Delete Blog Post -> Output (after deletion)
        {
            "src_node_id": "delete_blog_post",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "deleted_count", "dst_field": "deleted_count"},
                {"src_field": "deleted_documents", "dst_field": "deleted_documents"}
            ]
        },
        
        # Save Blog Post -> Output
        {
            "src_node_id": "save_blog_post",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "final_blog_post_paths"}
            ]
        },
        
        # --- Feedback Loop ---
        
        # State -> Feedback Analysis Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_feedback_analysis_prompt",
            "mappings": [
                {"src_field": "final_optimized_content", "dst_field": "final_optimized_content"},
                {"src_field": "user_feedback", "dst_field": "user_feedback"}
            ]
        },
        
        # Feedback Analysis Prompt -> LLM
        {
            "src_node_id": "construct_feedback_analysis_prompt",
            "dst_node_id": "feedback_analysis_llm",
            "mappings": [
                {"src_field": "feedback_analysis_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "feedback_analysis_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "feedback_analysis_llm",
            "mappings": [
                {"src_field": "feedback_analysis_message_history", "dst_field": "messages_history"}
            ]
        },
        
        # Feedback Analysis LLM -> Final Approval HITL (loop back)
        {
            "src_node_id": "feedback_analysis_llm",
            "dst_node_id": "final_approval_hitl",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "optimized_content"}
            ]
        },
        
        # Feedback Analysis LLM -> State
        {
            "src_node_id": "feedback_analysis_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "final_optimized_content"},
                {"src_field": "current_messages", "dst_field": "feedback_analysis_message_history"}
            ]
        },
        
        # State -> Output
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "final_optimized_content": "replace",
                "final_gap_improvement": "replace",
                "final_seo_improvement": "replace", 
                "final_structure_improvement": "replace",
                "user_feedback": "replace",
                "generation_metadata": "replace",
                "feedback_analysis_message_history": "add_messages",
                "user_action": "replace"
            }
        }
    }
}