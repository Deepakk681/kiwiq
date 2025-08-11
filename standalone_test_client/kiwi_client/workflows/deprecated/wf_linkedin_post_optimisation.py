"""
LinkedIn Post Optimization Workflow

This workflow enables comprehensive LinkedIn post optimization with:
- Knowledge gap analysis (insight depth and professional value)
- Content strategy alignment analysis 
- Human-in-the-loop approval for analysis results and final content
- Sequential improvement application (knowledge gaps → content strategy)
- Feedback analysis and revision loops
- Company context integration throughout the process

Key Features:
- Parallel execution of LinkedIn-specific analysis steps
- Structured output schemas for each analysis phase
- HITL approval flows for analysis review and final approval
- Sequential improvement processing with message history management
- Feedback-driven revision cycles
- LinkedIn best practices and character limit considerations
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

# Import document model constants - using LinkedIn-specific executive docs
from kiwi_client.active.document_models.customer_docs import (
    LINKEDIN_EXECUTIVE_DOCNAME,
    LINKEDIN_EXECUTIVE_NAMESPACE_TEMPLATE,
    LINKEDIN_EXECUTIVE_IS_VERSIONED,
)

# Import LinkedIn-specific LLM inputs
from kiwi_client.active.content_studio.llm_inputs.linkedin_post_optimization import (
    # System prompts
    KNOWLEDGE_GAP_ANALYZER_SYSTEM_PROMPT,
    CONTENT_STRATEGY_ANALYZER_SYSTEM_PROMPT,
    KNOWLEDGE_GAP_IMPROVEMENT_SYSTEM_PROMPT,
    CONTENT_STRATEGY_IMPROVEMENT_SYSTEM_PROMPT,
    FEEDBACK_ANALYSIS_SYSTEM_PROMPT,
    
    # User prompt templates
    KNOWLEDGE_GAP_ANALYZER_USER_PROMPT_TEMPLATE,
    CONTENT_STRATEGY_ANALYZER_USER_PROMPT_TEMPLATE,
    KNOWLEDGE_GAP_IMPROVEMENT_USER_PROMPT_TEMPLATE,
    CONTENT_STRATEGY_IMPROVEMENT_USER_PROMPT_TEMPLATE,
    FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE,
    
    # Output schemas
    KNOWLEDGE_GAP_ANALYZER_OUTPUT_SCHEMA,
    CONTENT_STRATEGY_ANALYZER_OUTPUT_SCHEMA,
    LINKEDIN_FINAL_OUTPUT_SCHEMA,
)

# LLM Configuration
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-3-7-sonnet-20250219"
TEMPERATURE = 0.7
MAX_TOKENS = 4000

# Workflow Limits
MAX_REVISION_ATTEMPTS = 3

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
                    "entity_username": {
                        "type": "str",
                        "required": True,
                        "description": "Username of the entity for document operations"
                    },
                    "original_post": {
                        "type": "str",
                        "required": True,
                        "description": "Original LinkedIn post content to be optimized"
                    },
                    "route_all_choices": {
                        "type": "bool",
                        "required": False,
                        "default": True,
                        "description": "Whether to route all choices to all nodes"
                    }
                }
            }
        },
        
        # 2. Load Company Document
        "load_executive_profile_doc": {
            "node_id": "load_executive_profile_doc",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_EXECUTIVE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_EXECUTIVE_DOCNAME,
                        },
                        "output_field_name": "executive_profile"
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
                    "construct_knowledge_gap_analyzer_prompt",
                    "construct_content_strategy_analyzer_prompt"
                ],
                "allow_multiple": True,
                "choices_with_conditions": [
                    {
                        "choice_id": "construct_knowledge_gap_analyzer_prompt",
                        "input_path": "route_all_choices",
                        "target_value": True
                    },
                    {
                        "choice_id": "construct_content_strategy_analyzer_prompt",
                        "input_path": "route_all_choices",
                        "target_value": True
                    }
                ]
            }
        },
        
        # 4a. Knowledge Gap Analyzer - Prompt Constructor
        "construct_knowledge_gap_analyzer_prompt": {
            "node_id": "construct_knowledge_gap_analyzer_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "knowledge_gap_analyzer_user_prompt": {
                        "id": "knowledge_gap_analyzer_user_prompt",
                        "template": KNOWLEDGE_GAP_ANALYZER_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "executive_profile": None,
                            "original_post": None
                        },
                        "construct_options": {
                            "executive_profile": "executive_profile",
                            "original_post": "original_post"
                        }
                    },
                    "knowledge_gap_analyzer_system_prompt": {
                        "id": "knowledge_gap_analyzer_system_prompt",
                        "template": KNOWLEDGE_GAP_ANALYZER_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 4b. Knowledge Gap Analyzer - LLM Node
        "knowledge_gap_analyzer_llm": {
            "node_id": "knowledge_gap_analyzer_llm",
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
                    "schema_definition": KNOWLEDGE_GAP_ANALYZER_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 5a. Content Strategy Analyzer - Prompt Constructor
        "construct_content_strategy_analyzer_prompt": {
            "node_id": "construct_content_strategy_analyzer_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "content_strategy_analyzer_user_prompt": {
                        "id": "content_strategy_analyzer_user_prompt",
                        "template": CONTENT_STRATEGY_ANALYZER_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "executive_profile": None,
                            "original_post": None
                        },
                        "construct_options": {
                            "executive_profile": "executive_profile",
                            "original_post": "original_post"
                        }
                    },
                    "content_strategy_analyzer_system_prompt": {
                        "id": "content_strategy_analyzer_system_prompt",
                        "template": CONTENT_STRATEGY_ANALYZER_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 5b. Content Strategy Analyzer - LLM Node
        "content_strategy_analyzer_llm": {
            "node_id": "content_strategy_analyzer_llm",
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
                    "schema_definition": CONTENT_STRATEGY_ANALYZER_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 6. Analysis Review - HITL Node (receives both analysis results)
        "analysis_review_hitl": {
            "node_id": "analysis_review_hitl",
            "node_name": "hitl_node__default",
            "enable_node_fan_in": True,
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "final_knowledge_improvement": {
                        "type": "str",
                        "required": False,
                        "description": "Final user-reviewed suggestions for knowledge gap improvements"
                    },
                    "final_strategy_improvement": {
                        "type": "str",
                        "required": False,
                        "description": "Final user-reviewed suggestions for content strategy improvements"
                    },
                    "knowledge_improvement_instructions": {
                        "type": "str",
                        "required": False,
                        "description": "Instructions for knowledge gap improvements"
                    },
                    "strategy_improvement_instructions": {
                        "type": "str",
                        "required": False,
                        "description": "Instructions for content strategy improvements"
                    }
                }
            }
        },
        
        # 7a. Knowledge Gap Improvement - Prompt Constructor
        "construct_knowledge_gap_improvement_prompt": {
            "node_id": "construct_knowledge_gap_improvement_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "knowledge_gap_improvement_user_prompt": {
                        "id": "knowledge_gap_improvement_user_prompt",
                        "template": KNOWLEDGE_GAP_IMPROVEMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "original_post": None,
                            "knowledge_gap_analysis": None,
                            "gap_improvement_instructions": None
                        },
                        "construct_options": {
                            "original_post": "original_post",
                            "knowledge_gap_analysis": "final_knowledge_improvement",
                            "gap_improvement_instructions": "knowledge_improvement_instructions"
                        }
                    },
                    "knowledge_gap_improvement_system_prompt": {
                        "id": "knowledge_gap_improvement_system_prompt",
                        "template": KNOWLEDGE_GAP_IMPROVEMENT_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 7b. Knowledge Gap Improvement - LLM Node
        "knowledge_gap_improvement_llm": {
            "node_id": "knowledge_gap_improvement_llm",
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
        
        # 8a. Content Strategy Improvement - Prompt Constructor
        "construct_content_strategy_improvement_prompt": {
            "node_id": "construct_content_strategy_improvement_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "content_strategy_improvement_user_prompt": {
                        "id": "content_strategy_improvement_user_prompt",
                        "template": CONTENT_STRATEGY_IMPROVEMENT_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "current_post_content": None,
                            "strategy_analysis": None,
                            "strategy_improvement_instructions": None
                        },
                        "construct_options": {
                            "current_post_content": "text_content",
                            "strategy_analysis": "final_strategy_improvement",
                            "strategy_improvement_instructions": "strategy_improvement_instructions"
                        }
                    },
                    "content_strategy_improvement_system_prompt": {
                        "id": "content_strategy_improvement_system_prompt",
                        "template": CONTENT_STRATEGY_IMPROVEMENT_SYSTEM_PROMPT,
                        "variables": {}
                    }
                }
            }
        },
        
        # 8b. Content Strategy Improvement - LLM Node
        "content_strategy_improvement_llm": {
            "node_id": "content_strategy_improvement_llm",
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
                    "schema_definition": LINKEDIN_FINAL_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 9. Final Approval - HITL Node
        "final_approval_hitl": {
            "node_id": "final_approval_hitl",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "approval_status": {
                        "type": "enum",
                        "enum_values": ["approve", "reject"],
                        "required": True,
                        "description": "User's approval decision"
                    },
                    "user_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for revision (required if reject)"
                    }
                }
            }
        },
        
        # 10. Route Final Approval
        "route_final_approval": {
            "node_id": "route_final_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["output_node", "construct_feedback_analysis_prompt"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "output_node",
                        "input_path": "approval_status",
                        "target_value": "approve"
                    },
                    {
                        "choice_id": "construct_feedback_analysis_prompt",
                        "input_path": "approval_status",
                        "target_value": "reject"
                    }
                ],
                "default_choice": "output_node"
            }
        },
        
        # 11a. Feedback Analysis - Prompt Constructor
        "construct_feedback_analysis_prompt": {
            "node_id": "construct_feedback_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "feedback_analysis_user_prompt": {
                        "id": "feedback_analysis_user_prompt",
                        "template": FEEDBACK_ANALYSIS_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "current_post_content": None,
                            "user_feedback": None
                        },
                        "construct_options": {
                            "current_post_content": "current_post_content",
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
        
        # 11b. Feedback Analysis - LLM Node
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
                    "schema_definition": LINKEDIN_FINAL_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },
        
        # 12. Output Node
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
                {"src_field": "entity_username", "dst_field": "entity_username"},
                {"src_field": "original_post", "dst_field": "original_post"},
                {"src_field": "route_all_choices", "dst_field": "route_all_choices"}
            ]
        },
        
        # Input -> Load Company Doc
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_executive_profile_doc",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },
        
        # Company Doc -> State: Store company context
        {
            "src_node_id": "load_executive_profile_doc",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "executive_profile", "dst_field": "executive_profile"}
            ]
        },
        
        # Company Doc -> Analysis Router (trigger with company context loaded)
        {
            "src_node_id": "load_executive_profile_doc",
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
            "dst_node_id": "construct_knowledge_gap_analyzer_prompt"
        },
        {
            "src_node_id": "analysis_trigger_router",
            "dst_node_id": "construct_content_strategy_analyzer_prompt"
        },
        
        # State -> All Prompt Constructors (provide context)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_knowledge_gap_analyzer_prompt",
            "mappings": [
                {"src_field": "executive_profile", "dst_field": "executive_profile"},
                {"src_field": "original_post", "dst_field": "original_post"}
            ]
        },
        {
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_content_strategy_analyzer_prompt",
            "mappings": [
                {"src_field": "executive_profile", "dst_field": "executive_profile"},
                {"src_field": "original_post", "dst_field": "original_post"}
            ]
        },
        
        # Prompt Constructors -> LLM Nodes
        {
            "src_node_id": "construct_knowledge_gap_analyzer_prompt",
            "dst_node_id": "knowledge_gap_analyzer_llm",
            "mappings": [
                {"src_field": "knowledge_gap_analyzer_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "knowledge_gap_analyzer_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        {
            "src_node_id": "construct_content_strategy_analyzer_prompt",
            "dst_node_id": "content_strategy_analyzer_llm",
            "mappings": [
                {"src_field": "content_strategy_analyzer_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "content_strategy_analyzer_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # LLM Nodes -> HITL Review (direct connection, no merge)
        {
            "src_node_id": "knowledge_gap_analyzer_llm",
            "dst_node_id": "analysis_review_hitl",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "knowledge_analysis"}
            ]
        },
        {
            "src_node_id": "content_strategy_analyzer_llm",
            "dst_node_id": "analysis_review_hitl", 
            "mappings": [
                {"src_field": "structured_output", "dst_field": "strategy_analysis"}
            ]
        },
        
        # HITL Review -> State: Store user-reviewed suggestions
        {
            "src_node_id": "analysis_review_hitl",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "final_knowledge_improvement", "dst_field": "final_knowledge_improvement"},
                {"src_field": "final_strategy_improvement", "dst_field": "final_strategy_improvement"},
                {"src_field": "knowledge_improvement_instructions", "dst_field": "knowledge_improvement_instructions"},
                {"src_field": "strategy_improvement_instructions", "dst_field": "strategy_improvement_instructions"}
            ]
        },
        
        # HITL Review -> Knowledge Gap Improvement (start sequential chain)
        {
            "src_node_id": "analysis_review_hitl",
            "dst_node_id": "construct_knowledge_gap_improvement_prompt"
        },
        
        # --- Sequential Improvement Chain ---
        
        # State -> Knowledge Gap Improvement Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_knowledge_gap_improvement_prompt",
            "mappings": [
                {"src_field": "original_post", "dst_field": "original_post"},
                {"src_field": "final_knowledge_improvement", "dst_field": "final_knowledge_improvement"},
                {"src_field": "knowledge_improvement_instructions", "dst_field": "knowledge_improvement_instructions"}
            ]
        },
        
        # Knowledge Gap Improvement Prompt -> LLM
        {
            "src_node_id": "construct_knowledge_gap_improvement_prompt",
            "dst_node_id": "knowledge_gap_improvement_llm",
            "mappings": [
                {"src_field": "knowledge_gap_improvement_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "knowledge_gap_improvement_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Knowledge Gap Improvement LLM -> Content Strategy Improvement Prompt
        {
            "src_node_id": "knowledge_gap_improvement_llm",
            "dst_node_id": "construct_content_strategy_improvement_prompt",
            "mappings": [
                {"src_field": "text_content", "dst_field": "text_content"}
            ]
        },
        
        # State -> Content Strategy Improvement Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_strategy_improvement_prompt",
            "mappings": [
                {"src_field": "final_strategy_improvement", "dst_field": "final_strategy_improvement"},
                {"src_field": "strategy_improvement_instructions", "dst_field": "strategy_improvement_instructions"}
            ]
        },
        
        # Content Strategy Improvement Prompt -> LLM
        {
            "src_node_id": "construct_content_strategy_improvement_prompt",
            "dst_node_id": "content_strategy_improvement_llm",
            "mappings": [
                {"src_field": "content_strategy_improvement_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "content_strategy_improvement_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        
        # Content Strategy Improvement LLM -> State
        {
            "src_node_id": "content_strategy_improvement_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "final_optimized_post"}
            ]
        },
        
        # Content Strategy Improvement LLM -> Final Approval HITL
        {
            "src_node_id": "content_strategy_improvement_llm",
            "dst_node_id": "final_approval_hitl",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "optimized_post"}
            ]
        },
        
        # Final Approval HITL -> Route
        {
            "src_node_id": "final_approval_hitl",
            "dst_node_id": "route_final_approval",
            "mappings": [
                {"src_field": "approval_status", "dst_field": "approval_status"}
            ]
        },
        
        # Final Approval HITL -> State
        {
            "src_node_id": "final_approval_hitl",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "user_feedback", "dst_field": "user_feedback"}
            ]
        },
        
        # --- Final Approval Router Paths ---
        {
            "src_node_id": "route_final_approval",
            "dst_node_id": "output_node"
        },
        {
            "src_node_id": "route_final_approval",
            "dst_node_id": "construct_feedback_analysis_prompt"
        },
        
        # --- Feedback Loop ---
        
        # State -> Feedback Analysis Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_feedback_analysis_prompt",
            "mappings": [
                {"src_field": "final_optimized_post", "dst_field": "current_post_content"},
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
        
        # Feedback Analysis LLM -> Final Approval HITL (loop back)
        {
            "src_node_id": "feedback_analysis_llm",
            "dst_node_id": "final_approval_hitl",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "optimized_post"}
            ]
        },
        
        # Feedback Analysis LLM -> State
        {
            "src_node_id": "feedback_analysis_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "final_optimized_post"}
            ]
        },
        
        # State -> Output
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "final_optimized_post", "dst_field": "final_optimized_post"}
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "final_optimized_post": "replace",
                "final_knowledge_improvement": "replace",
                "final_strategy_improvement": "replace"
            }
        }
    }
}


# --- Testing Code ---

async def validate_linkedin_post_optimization_workflow_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the LinkedIn post optimization workflow outputs.
    
    Args:
        outputs: The dictionary of final outputs from the workflow run.
        
    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating LinkedIn post optimization workflow outputs...")
    
    # Check for expected keys
    expected_keys = [
        'knowledge_analysis_results',
        'strategy_analysis_results', 
        'final_optimized_post'
    ]
    
    for key in expected_keys:
        if key in outputs:
            logger.info(f"✓ Found expected key: {key}")
        else:
            logger.warning(f"⚠ Missing optional key: {key}")
    
    # Validate knowledge analysis results if present
    if 'knowledge_analysis_results' in outputs:
        knowledge_analysis = outputs['knowledge_analysis_results']
        assert isinstance(knowledge_analysis, dict), "Knowledge analysis results should be a dict"
        assert 'knowledge_analysis' in knowledge_analysis, "Knowledge analysis missing knowledge_analysis"
        assert 'improvement_recommendations' in knowledge_analysis, "Knowledge analysis missing improvement_recommendations"
        logger.info("✓ Knowledge analysis results validated")
    
    # Validate strategy analysis results if present
    if 'strategy_analysis_results' in outputs:
        strategy_analysis = outputs['strategy_analysis_results']
        assert isinstance(strategy_analysis, dict), "Strategy analysis results should be a dict"
        assert 'strategy_analysis' in strategy_analysis, "Strategy analysis missing strategy_analysis"
        assert 'strategic_recommendations' in strategy_analysis, "Strategy analysis missing strategic_recommendations"
        logger.info("✓ Strategy analysis results validated")
    
    # Validate final optimized post if present
    if 'final_optimized_post' in outputs:
        final_post = outputs['final_optimized_post']
        assert isinstance(final_post, dict), "Final optimized post should be a dict"
        assert 'optimized_post_content' in final_post, "Final post missing optimized_post_content"
        assert 'optimization_summary' in final_post, "Final post missing optimization_summary"
        assert 'key_improvements' in final_post, "Final post missing key_improvements"
        
        # Check that optimized content is not empty
        optimized_text = final_post['optimized_post_content']
        assert isinstance(optimized_text, str), "Optimized post content should be a string"
        assert len(optimized_text.strip()) > 0, "Optimized post content should not be empty"
        
        # Check optimization summary
        optimization_summary = final_post['optimization_summary']
        assert isinstance(optimization_summary, str), "Optimization summary should be a string"
        
        # Check key improvements
        key_improvements = final_post['key_improvements']
        assert isinstance(key_improvements, list), "Key improvements should be a list"
        
        logger.info("✓ Final optimized post validated")
        logger.info(f"✓ Optimized post length: {len(optimized_text)} characters")
    
    logger.info("✓ LinkedIn post optimization workflow output validation passed.")
    return True


async def main_test_linkedin_post_optimization_workflow():
    """
    Test for LinkedIn Post Optimization Workflow.
    
    This function sets up test data, executes the workflow, and validates the output.
    The workflow analyzes LinkedIn posts for knowledge gaps and content strategy alignment,
    provides HITL approval, applies sequential improvements, and produces optimized content.
    """
    test_name = "LinkedIn Post Optimization Workflow Test"
    print(f"--- Starting {test_name} ---")
    
    # Test parameters
    test_entity_username = "TechSolutions"
    
    # Create test executive profile document data
    executive_data = {
        "executive_profile": {
            "name": "Alex Johnson",
            "title": "CEO & Founder",
            "company": "TechSolutions Pro",
            "industry_experience": "15 years in project management and SaaS",
            "expertise_areas": [
                "AI-powered project management",
                "Team productivity optimization",
                "Remote work culture",
                "SaaS product development"
            ],
            "thought_leadership_focus": [
                "The future of work and AI integration",
                "Building efficient remote teams",
                "Project management best practices",
                "Technology adoption in growing companies"
            ],
            "writing_style": {
                "tone": "Conversational yet authoritative",
                "approach": "Story-driven with actionable insights",
                "perspective": "Practical experience-based advice"
            },
            "personal_interests": [
                "Technology innovation",
                "Team building",
                "Work-life balance",
                "Continuous learning"
            ],
            "linkedin_goals": [
                "Build thought leadership in project management space",
                "Share insights on AI adoption",
                "Connect with other industry leaders",
                "Promote TechSolutions Pro's vision"
            ]
        }
    }
    
    # Sample LinkedIn post content to optimize
    original_linkedin_post = """🚀 AI is changing project management!

Just saw some interesting developments in the AI space for project management. Teams are starting to use AI tools to help with their projects.

Some benefits:
• Better planning
• Faster execution  
• Cost savings

What do you think about AI in project management? Have you tried any AI tools for your projects?

#ProjectManagement #AI #Productivity"""
    
    # Test inputs
    test_inputs = {
        "entity_username": test_entity_username,
        "original_post": original_linkedin_post
    }
    
    # Setup test documents
    setup_docs: List[SetupDocInfo] = [
        {
            'namespace': f"linkedin_executive_profile_namespace_{test_entity_username}",
            'docname': LINKEDIN_EXECUTIVE_DOCNAME,
            'initial_data': executive_data,
            'is_shared': False,
            'is_versioned': LINKEDIN_EXECUTIVE_IS_VERSIONED,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]
    
    # Cleanup configuration - force recreation of document
    cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': f"linkedin_executive_profile_namespace_{test_entity_username}",
            'docname': LINKEDIN_EXECUTIVE_DOCNAME,
            'is_shared': False,
            'is_versioned': LINKEDIN_EXECUTIVE_IS_VERSIONED,
            'is_system_entity': False
        }
    ]
    
    # Predefined HITL inputs - leaving empty to allow for interactive testing
    predefined_hitl_inputs = []
    
    # VALID HUMAN INPUTS FOR MANUAL TESTING:
    
    # For analysis review HITL:
    # {"user_action": "proceed_with_improvements", "knowledge_improvement_instructions": "Add more specific industry insights and thought leadership elements", "strategy_improvement_instructions": "Strengthen brand voice and add clear call-to-action for business development"}
    
    # For final approval HITL:
    # {"approval_status": "approve"}
    # {"approval_status": "reject", "user_feedback": "The post is too promotional, please make it more educational and value-focused"}
    
    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        hitl_inputs=predefined_hitl_inputs,
        setup_docs=setup_docs,
        cleanup_docs=cleanup_docs,
        cleanup_docs_created_by_setup=True,
        validate_output_func=validate_linkedin_post_optimization_workflow_output,
        stream_intermediate_results=True,
        poll_interval_sec=3,
        timeout_sec=1200  # 20 minutes for LinkedIn analysis and optimization
    )
    
    print(f"--- {test_name} Finished ---")
    if final_run_outputs:
        # Show analysis results
        if 'knowledge_analysis_results' in final_run_outputs:
            knowledge_analysis = final_run_outputs['knowledge_analysis_results']
            knowledge_text = knowledge_analysis.get('knowledge_analysis', 'N/A')
            recommendations_count = len(knowledge_analysis.get('improvement_recommendations', []))
            print(f"Knowledge Analysis: {recommendations_count} recommendations")
        
        if 'strategy_analysis_results' in final_run_outputs:
            strategy_analysis = final_run_outputs['strategy_analysis_results']
            strategy_text = strategy_analysis.get('strategy_analysis', 'N/A')
            strategic_recommendations_count = len(strategy_analysis.get('strategic_recommendations', []))
            print(f"Strategy Analysis: {strategic_recommendations_count} strategic recommendations")
        
        # Show final optimized post info
        if 'final_optimized_post' in final_run_outputs:
            final_post = final_run_outputs['final_optimized_post']
            optimized_text = final_post.get('optimized_post_content', '')
            optimization_summary = final_post.get('optimization_summary', '')
            key_improvements = final_post.get('key_improvements', [])
            
            print(f"Final Post: {len(optimized_text)} characters")
            print(f"Key Improvements: {len(key_improvements)}")
            print(f"Optimization Summary: {optimization_summary[:100]}..." if len(optimization_summary) > 100 else f"Optimization Summary: {optimization_summary}")


# Entry point
if __name__ == "__main__":
    print("="*80)
    print("LinkedIn Post Optimization Workflow Test")
    print("="*80)
    
    try:
        asyncio.run(main_test_linkedin_post_optimization_workflow())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=. python kiwi_client/workflows/wf_linkedin_post_optimisation.py") 