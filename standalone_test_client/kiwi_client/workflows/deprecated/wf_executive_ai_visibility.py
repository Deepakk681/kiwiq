"""
Executive AI Visibility Testing Workflow

This workflow enables comprehensive testing of executive thought leadership visibility across AI platforms with:
- Executive context loading from executive profiles
- AI test prompt generation with expert system guidance based on executive positioning and expertise
- Parallel testing across multiple AI platforms (Perplexity and ChatGPT)
- Real-time web search capabilities for current data
- Platform-specific result analysis with clear source attribution
- Comprehensive visibility analysis and gap identification
- Citation opportunity detection for executive content optimization
- Structured output generation following ExecutiveAiVisibilityTestSchema
- Document storage for test results and tracking

Key Features:
- Dual AI platform testing (Perplexity sonar-pro and ChatGPT)
- Real web search integration for current visibility data
- Separate platform result handling for precise analysis
- Clear source attribution in analysis prompts
- Expert system guidance for AI test prompt generation
- Platform-specific visibility gap analysis and citation opportunities
- Comprehensive test result storage and retrieval

Workflow Architecture:
1. Load executive context from executive profiles
2. Generate AI test prompts using expert system guidance
3. Execute parallel testing on Perplexity and ChatGPT platforms
4. Construct analysis prompts with clearly attributed platform results
5. Analyze responses with platform-specific insights
6. Store comprehensive test results and recommendations

LLM Configuration:
- Analysis LLM: Claude-3-7-sonnet-20250219 (Anthropic)
- Perplexity Testing: sonar-pro model with web search
- ChatGPT Testing: gpt-4o-mini model with web search
- Temperature settings optimized for different task types
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# Internal dependencies
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

from kiwi_client.workflows.document_models.customer_docs import (
    # Blog Executive Profile
    EXECUTIVE_DOCNAME,
    EXECUTIVE_NAMESPACE_TEMPLATE,
    EXECUTIVE_IS_VERSIONED,
    EXECUTIVE_IS_SHARED,
    EXECUTIVE_IS_SYSTEM_ENTITY,
    
    # Blog Executive AI Visibility Test
    EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
    EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED,
    EXECUTIVE_AI_VISIBILITY_TEST_IS_SHARED,
    EXECUTIVE_AI_VISIBILITY_TEST_IS_SYSTEM_ENTITY
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.executive_ai_visibility_test import (
    GENERATION_SCHEMA,
    WEB_SEARCH_GENERATION_SCHEMA,
    AI_VISIBILITY_TEST_PROMPT,
    AI_TEST_PROMPT_GENERATION_SYSTEM,
    SYSTEM_PROMPT_TEMPLATE,
    USER_PROMPT_TEMPLATE,
    CHATGPT_QUERY_GENERATION_USER_PROMPT_TEMPLATE,
    GENERATED_QUERIES_LIST_SCHEMA,
    CHATGPT_QUERY_GENERATION_SYSTEM_PROMPT_TEMPLATE,
    CHATGPT_SINGLE_QUERY_USER_PROMPT_TEMPLATE,
    CHATGPT_SINGLE_QUERY_SYSTEM_PROMPT_TEMPLATE
)

# --- Workflow Configuration Constants ---

# LLM Configuration - Updated to match user_input_to_brief.py patterns
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4.1"
LLM_TEMPERATURE = 0.8
LLM_MAX_TOKENS = 4000

# Perplexity Configuration for web search
PERPLEXITY_PROVIDER = "perplexity"
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_TEMPERATURE = 0.3
PERPLEXITY_MAX_TOKENS = 3000

# OpenAI Configuration for ChatGPT testing
OPENAI_PROVIDER = "openai"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.2
OPENAI_MAX_TOKENS = 4000


workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node ---
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                        "entity_username": {
                            "type": "str",
                            "required": True,
                            "description": "Name of the executive to test AI visibility for"
                        }
                    }
            }
        },

        # --- 2. Load Executive Context ---
        "load_executive_context": {
            "node_id": "load_executive_context",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": EXECUTIVE_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": EXECUTIVE_DOCNAME,
                        },
                        "output_field_name": "blog_executive_doc"
                    }
                ],
                "global_is_shared": EXECUTIVE_IS_SHARED,
                "global_is_system_entity": EXECUTIVE_IS_SYSTEM_ENTITY,
                "global_schema_options": {"load_schema": False}
            },
        },

        # --- 3. Build AI Test Prompts ---
        "build_ai_test_prompts": {
            "node_id": "build_ai_test_prompts",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "ai_test_user_prompt": {
                        "id": "ai_test_user_prompt",
                        "template": AI_VISIBILITY_TEST_PROMPT,
                        "variables": {
                            "full_name": None,
                            "profile_url": None,
                            "persona_tags": None,
                            "primary_goal": None,
                            "secondary_goal": None,
                        },
                        "construct_options": {
                            "full_name": "blog_executive_doc.username",
                            "profile_url": "blog_executive_doc.profile_url",
                            "persona_tags": "blog_executive_doc.persona_tags",
                            "primary_goal": "blog_executive_doc.content_goals.primary_goal",
                            "secondary_goal": "blog_executive_doc.content_goals.secondary_goal",
                        },
                    },
                    "ai_test_system_prompt": {
                        "id": "ai_test_system_prompt",
                        "template": AI_TEST_PROMPT_GENERATION_SYSTEM,
                        "variables": { "schema": json.dumps(WEB_SEARCH_GENERATION_SCHEMA, indent=2) },
                    }
                }
            },
        },



        # --- 4. Execute Perplexity AI Tests ---
        "execute_perplexity_tests": {
            "node_id": "execute_perplexity_tests",
            "node_name": "llm",
            "enable_node_fan_in": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": PERPLEXITY_PROVIDER, "model": PERPLEXITY_MODEL},
                    "temperature": PERPLEXITY_TEMPERATURE,
                    "max_tokens": PERPLEXITY_MAX_TOKENS,
                },
                "output_schema": {
                    "schema_definition": WEB_SEARCH_GENERATION_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            },
        },

        # --- 5.1. Construct Query Generation Prompt ---
        "construct_query_generation_prompt": {
            "node_id": "construct_query_generation_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "generate_queries_user_prompt": {
                        "id": "generate_queries_user_prompt",
                        "template": CHATGPT_QUERY_GENERATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "executive_context": None
                        },
                        "construct_options": {
                            "executive_context": "blog_executive_doc"
                        }
                    },
                    "generate_queries_system_prompt": {
                        "id": "generate_queries_system_prompt",
                        "template": CHATGPT_QUERY_GENERATION_SYSTEM_PROMPT_TEMPLATE,
                        "variables": {},
                        "construct_options": {}
                    }
                }
            },
        },

        # --- 5.2. LLM Node to Generate Queries ---
        "generate_chatgpt_queries": {
            "node_id": "generate_chatgpt_queries",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": OPENAI_PROVIDER, "model": OPENAI_MODEL},
                    "temperature": OPENAI_TEMPERATURE,
                    "max_tokens": OPENAI_MAX_TOKENS,
                },
                "output_schema": {
                    "schema_definition": GENERATED_QUERIES_LIST_SCHEMA,  # Use the schema for the list of queries
                    "convert_loaded_schema_to_pydantic": False
                },
            },
        },

        # --- 5.3. Route Each Query for Parallel Execution ---
        "route_chatgpt_queries": {
            "node_id": "route_chatgpt_queries",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["construct_single_query_prompt"],
                "map_targets": [
                    {
                        "source_path": "structured_output.queries",  # This should match the output field from generate_chatgpt_queries
                        "destinations": ["construct_single_query_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "single_query"
                    }
                ]
            }
        },

        # --- 5.4. Prompt Constructor for Each Query ---
        "construct_single_query_prompt": {
            "node_id": "construct_single_query_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "node_config": {
                "prompt_templates": {
                    "single_query_user_prompt": {
                        "id": "single_query_user_prompt",
                        "template": CHATGPT_SINGLE_QUERY_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "single_query": None
                        },
                        "construct_options": {
                            "single_query": "single_query.query_text"
                        }
                    },
                    "single_query_system_prompt": {
                        "id": "single_query_system_prompt",
                        "template": CHATGPT_SINGLE_QUERY_SYSTEM_PROMPT_TEMPLATE,
                        "variables": {},
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 5.5. LLM Node for Each Query ---
        "execute_single_chatgpt_query": {
            "node_id": "execute_single_chatgpt_query",
            "node_name": "llm",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": OPENAI_PROVIDER, "model": OPENAI_MODEL},
                    "temperature": OPENAI_TEMPERATURE,
                    "max_tokens": OPENAI_MAX_TOKENS,
                },
                "tool_calling_config": {
                    "enable_tool_calling": True,
                    "parallel_tool_calls": True
                },
                "tools": [
                    {
                        "tool_name": "web_search_preview",
                        "is_provider_inbuilt_tool": True
                    }
                ],
                "output_schema": {
                    "schema_definition": WEB_SEARCH_GENERATION_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            },
        },

        # --- 5.6. Aggregate All Query Results ---
        "combine_chatgpt_results": {
            "node_id": "combine_chatgpt_results",
            "node_name": "merge_aggregate",
            "private_input_mode": True,
            "node_config": {
                "operations": [
                    {
                        "output_field_name": "all_chatgpt_results",
                        "select_paths": ["all_single_chatgpt_query_results"],
                        "merge_each_object_in_selected_list": False,
                        "merge_strategy": {
                            "reduce_phase": {
                                "default_reducer": "combine_in_list",
                                "error_strategy": "fail_node"
                            }
                        }
                    }
                ]
            }
        },

        # --- 6. Construct Analysis Prompt ---
        "construct_analysis_prompt": {
            "node_id": "construct_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "analysis_user_prompt": {
                        "id": "analysis_user_prompt",
                        "template": USER_PROMPT_TEMPLATE,
                        "variables": {
                            "company_context": None,
                            "perplexity_results": None,
                            "chatgpt_results": None,
                        },
                        "construct_options": {
                            "company_context": "company_context",
                            "perplexity_results": "perplexity_results",
                            "chatgpt_results": "merged_data.all_chatgpt_results",
                        },
                    },
                    "analysis_system_prompt": {
                        "id": "analysis_system_prompt",
                        "template": SYSTEM_PROMPT_TEMPLATE,
                        "variables": { "schema": json.dumps(GENERATION_SCHEMA, indent=2) },
                        "construct_options": {},
                    }
                }
            },
        },

        # --- 7. Analyze AI Responses & Generate Visibility Report ---
        "analyze_responses": {
            "node_id": "analyze_responses",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": LLM_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": GENERATION_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            },
        },

        # --- 8. Store Test Results ---
        "store_test_results": {
            "node_id": "store_test_results",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED,
                    "operation": "upsert",
                },
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
                            }
                        },
                    }
                ],
            },
        },

        # --- 9. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {
                "output_schema": {
                    "fields": {
                        "visibility_report": {
                            "type": "object",
                            "description": "Complete AI visibility test results following BlogAiVisibilityTestSchema"
                        }
                    }
                }
            },
        },
    },

    "edges": [
        # Input -> Load Executive Context
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_executive_context",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"},
            ],
        },
        # Input -> State
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"},
            ],
        },
        # Load Executive Context -> State
        {
            "src_node_id": "load_executive_context",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "blog_executive_doc", "dst_field": "blog_executive_doc"},
            ],
        },
        # Load Executive Context -> Build AI Test Prompts
        {
            "src_node_id": "load_executive_context",
            "dst_node_id": "build_ai_test_prompts",
            "mappings": [
                {"src_field": "blog_executive_doc", "dst_field": "blog_executive_doc"},
            ],
        },
        # Build AI Test Prompts -> Execute Perplexity Tests
        {
            "src_node_id": "build_ai_test_prompts",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "ai_test_user_prompt", "dst_field": "ai_test_user_prompt"},
                {"src_field": "ai_test_system_prompt", "dst_field": "ai_test_system_prompt"},
            ],
        },
                {
            "src_node_id": "build_ai_test_prompts",
            "dst_node_id": "execute_perplexity_tests",
            "mappings": [],
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "execute_perplexity_tests",
            "mappings": [
                {"src_field": "ai_test_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "ai_test_system_prompt", "dst_field": "system_prompt"},
            ],
        },
        {
            "src_node_id": "execute_perplexity_tests",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "perplexity_results"},
            ],
        },
        # Build AI Test Prompts -> Construct Query Generation Prompt
        {
            "src_node_id": "execute_perplexity_tests",
            "dst_node_id": "construct_query_generation_prompt",
            "mappings": []
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_query_generation_prompt",
            "mappings": [
                {"src_field": "blog_executive_doc", "dst_field": "blog_executive_doc"}
            ]
        },
        {
            "src_node_id": "construct_query_generation_prompt",
            "dst_node_id": "generate_chatgpt_queries",
            "mappings": [
                {"src_field": "generate_queries_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "generate_queries_system_prompt", "dst_field": "system_prompt"}
            ]
        },
        {
            "src_node_id": "generate_chatgpt_queries",
            "dst_node_id": "route_chatgpt_queries",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "structured_output"}
            ]
        },
        {
            "src_node_id": "route_chatgpt_queries",
            "dst_node_id": "construct_single_query_prompt",
            "mappings": []
        },
        {
            "src_node_id": "route_chatgpt_queries",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "single_query", "dst_field": "single_query"}
            ]
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_single_query_prompt",
            "mappings": [
                {"src_field": "single_query", "dst_field": "single_query"}
            ]
        },
        {
            "src_node_id": "construct_single_query_prompt",
            "dst_node_id": "execute_single_chatgpt_query",
            "mappings": [
                {"src_field": "single_query_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "single_query_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        {
            "src_node_id": "execute_single_chatgpt_query",
            "dst_node_id": "$graph_state",
            "mappings": [{"src_field": "structured_output", "dst_field": "all_single_chatgpt_query_results"}]
        },

        {
            "src_node_id": "execute_single_chatgpt_query",
            "dst_node_id": "combine_chatgpt_results",
            "mappings": []
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "combine_chatgpt_results",
            "mappings": [{"src_field": "all_single_chatgpt_query_results", "dst_field": "all_single_chatgpt_query_results"}]
        },   

        {
            "src_node_id": "combine_chatgpt_results",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "merged_data", "dst_field": "merged_data"}
            ]
        },
        # Execute Perplexity Tests -> Construct Analysis Prompt
        {
            "src_node_id": "combine_chatgpt_results",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": [],
        },
        # Execute ChatGPT Tests -> Construct Analysis Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": [
                {"src_field": "merged_data", "dst_field": "merged_data"},
                {"src_field": "perplexity_results", "dst_field": "perplexity_results"},
                {"src_field": "blog_executive_doc", "dst_field": "company_context"}
            ]
        },
        # Construct Analysis Prompt -> Analyze Responses
        {
            "src_node_id": "construct_analysis_prompt",
            "dst_node_id": "analyze_responses",
            "mappings": [
                {"src_field": "analysis_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "analysis_system_prompt", "dst_field": "system_prompt"},
            ],
        },
        # Analyze Responses -> Store Test Results
        {
            "src_node_id": "analyze_responses",
            "dst_node_id": "store_test_results",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "structured_output"},
            ],
        },
        {
            "src_node_id": "analyze_responses",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "analysis_structured_output"},
            ],
        },
        # State -> Store Test Results
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "store_test_results",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"},
            ],
        },
        # Analyze Responses -> Output Node
        {
            "src_node_id": "store_test_results",
            "dst_node_id": "output_node",
            "mappings": [],
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "analysis_structured_output", "dst_field": "visibility_report"},
            ],
        },
    ],
    
    # --- Define Start and End ---
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    # --- Metadata for state management ---
    "metadata": {
        "$graph_state": {
            "reducer": {
                "blog_executive_doc": "replace",
                "perplexity_results": "replace",
                "all_single_chatgpt_query_results": "collect_values",
                "chatgpt_results": "replace",
                "visibility_report": "replace"
            }
        }
    }
}

# Test functions
async def main_test_executive_ai_visibility_workflow():
    """Main test function for the executive AI visibility workflow"""
    test_name = "Executive AI Visibility Workflow Test"
    print(f"--- Starting {test_name} ---")
    
    test_executive_name = "john_doe"
    
    test_input = {
        "entity_username": test_executive_name,
    }
    
    # Setup test documents with comprehensive executive data
    setup_docs = [
        # Blog Executive Profile Document
        {
            'namespace': f"executive_presence_{test_executive_name}",
            'docname': EXECUTIVE_DOCNAME,
            'initial_data': {
                "profile_url": "https://www.linkedin.com/in/may-habib/",
                "username": "may-habib",
                "persona_tags": [
        "AI entrepreneur",
        "Enterprise AI leader",
        "Tech founder",
        "Generative AI expert",
        "Content technology innovator",
        "B2B SaaS CEO",
        "Harvard economics graduate",
        "San Francisco tech executive"
    ],
                "content_goals": {
                    "primary_goal": "Establish thought leadership in enterprise AI and generative content technology",
                    "secondary_goal": "Build brand awareness for Writer as the leading enterprise AI platform"
                }
            },
            'is_versioned': EXECUTIVE_IS_VERSIONED,
            'is_shared': EXECUTIVE_IS_SHARED,
            'initial_version': 'default' if EXECUTIVE_IS_VERSIONED else None,
            'is_system_entity': EXECUTIVE_IS_SYSTEM_ENTITY
        }
    ]
    
    # Cleanup configuration
    cleanup_docs = [
        {
            'namespace': f"executive_presence_{test_executive_name}", 
            'docname': EXECUTIVE_DOCNAME, 
            'is_versioned': EXECUTIVE_IS_VERSIONED, 
            'is_shared': EXECUTIVE_IS_SHARED,
            'is_system_entity': EXECUTIVE_IS_SYSTEM_ENTITY
        },
        {
            'namespace': f"executive_presence_{test_executive_name}", 
            'docname': EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME, 
            'is_versioned': EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED, 
            'is_shared': EXECUTIVE_AI_VISIBILITY_TEST_IS_SHARED,
            'is_system_entity': EXECUTIVE_AI_VISIBILITY_TEST_IS_SYSTEM_ENTITY
        },
    ]
    
    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_input,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=setup_docs,
        cleanup_docs=cleanup_docs,
        cleanup_docs_created_by_setup=False,
        validate_output_func=validate_executive_ai_visibility_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )
    
    print(f"--- {test_name} Finished ---")
    if final_run_outputs and 'visibility_report' in final_run_outputs:
        report = final_run_outputs['visibility_report']
        print(f"AI Visibility Score: {report.get('ai_visibility_score')}")
        print(f"ChatGPT Recognition: {report.get('platform_recognition', {}).get('chatgpt_recognition', 'unknown')}")
        print(f"Perplexity Recognition: {report.get('platform_recognition', {}).get('perplexity_recognition', 'unknown')}")
        print(f"Recognition Consistency: {report.get('platform_recognition', {}).get('recognition_consistency', 'unknown')}")
        print(f"Thought Leadership Topics: {len(report.get('thought_leadership_topics', []))}")
        print(f"Improvement Opportunities: {len(report.get('improvement_opportunities', []))}")
        print(f"Executive Tested: {test_executive_name}")
        print(f"Executive Profile: John Doe - Marketing Executive")
    
    return final_run_status_obj, final_run_outputs

async def validate_executive_ai_visibility_output(outputs) -> bool:
    """Validate the executive AI visibility workflow output"""
    if not outputs:
        logging.error("Validation Failed: Workflow returned no outputs")
        return False
    
    logging.info("Validating executive AI visibility workflow outputs...")
    
    # Check for required fields
    required_fields = ["visibility_report"]
    
    for field in required_fields:
        if field not in outputs:
            logging.error(f"Missing required field: {field}")
            return False
    
    visibility_report = outputs["visibility_report"]
    
    if not isinstance(visibility_report, dict):
        logging.error("visibility_report is not a dictionary")
        return False
    
    # Check for required schema fields based on ExecutiveAiVisibilityTestSchema
    required_report_fields = [
        "expert_recognition_tests",
        "biographical_accuracy",
        "platform_recognition",
        "thought_leadership_topics",
        "competitor_executive_comparison",
        "ai_visibility_score",
        "improvement_opportunities"
    ]
    
    for field in required_report_fields:
        if field not in visibility_report:
            logging.error(f"Missing required field in visibility_report: {field}")
            return False
    
    # Validate expert_recognition_tests structure
    if "expert_recognition_tests" in visibility_report:
        expert_tests = visibility_report["expert_recognition_tests"]
        if not isinstance(expert_tests, dict):
            logging.error("expert_recognition_tests should be a dict")
            return False
        
        required_expert_fields = ["industry_expert_queries", "thought_leader_queries", "topic_expert_queries"]
        for field in required_expert_fields:
            if field not in expert_tests:
                logging.error(f"Missing required field in expert_recognition_tests: {field}")
                return False
    
    # Validate biographical_accuracy structure
    if "biographical_accuracy" in visibility_report:
        bio_accuracy = visibility_report["biographical_accuracy"]
        if not isinstance(bio_accuracy, dict):
            logging.error("biographical_accuracy should be a dict")
            return False
        
        required_bio_fields = ["current_role_accuracy", "career_history_accuracy", "achievements_recognition", "missing_credentials"]
        for field in required_bio_fields:
            if field not in bio_accuracy:
                logging.error(f"Missing required field in biographical_accuracy: {field}")
                return False
    
    # Validate platform_recognition structure
    if "platform_recognition" in visibility_report:
        platform_recognition = visibility_report["platform_recognition"]
        if not isinstance(platform_recognition, dict):
            logging.error("platform_recognition should be a dict")
            return False
        
        required_platform_fields = ["chatgpt_recognition", "perplexity_recognition", "recognition_consistency"]
        for field in required_platform_fields:
            if field not in platform_recognition:
                logging.error(f"Missing required field in platform_recognition: {field}")
                return False
    
    # Validate competitor_executive_comparison structure
    if "competitor_executive_comparison" in visibility_report:
        competitor_comparison = visibility_report["competitor_executive_comparison"]
        if not isinstance(competitor_comparison, dict):
            logging.error("competitor_executive_comparison should be a dict")
            return False
        
        required_comp_fields = ["recognition_ranking", "mention_frequency", "context_quality"]
        for field in required_comp_fields:
            if field not in competitor_comparison:
                logging.error(f"Missing required field in competitor_executive_comparison: {field}")
                return False
    
    # Log successful validation details
    logging.info(f"✓ Visibility report validation successful")
    logging.info(f"✓ AI Visibility Score: {visibility_report.get('ai_visibility_score', 'unknown')}")
    logging.info(f"✓ ChatGPT Recognition: {visibility_report.get('platform_recognition', {}).get('chatgpt_recognition', 'unknown')}")
    logging.info(f"✓ Perplexity Recognition: {visibility_report.get('platform_recognition', {}).get('perplexity_recognition', 'unknown')}")
    logging.info(f"✓ Recognition Consistency: {visibility_report.get('platform_recognition', {}).get('recognition_consistency', 'unknown')}")
    logging.info(f"✓ Thought Leadership Topics: {len(visibility_report.get('thought_leadership_topics', []))}")
    logging.info(f"✓ Improvement Opportunities: {len(visibility_report.get('improvement_opportunities', []))}")
    
    logging.info("✓ Executive AI visibility workflow output validation successful")
    return True

# Entry point
if __name__ == "__main__":
    print("="*80)
    print("Executive AI Visibility Workflow Test")
    print("="*80)
    
    try:
        asyncio.run(main_test_executive_ai_visibility_workflow())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logging.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=. python kiwi_client/workflows_for_blog_teammate/wf_executive_ai_visibility.py")
