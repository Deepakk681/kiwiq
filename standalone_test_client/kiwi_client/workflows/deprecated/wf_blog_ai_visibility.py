"""
Blog AI Visibility Testing Workflow

This workflow enables comprehensive testing of blog content visibility across AI platforms with:
- Company context loading from blog company profiles
- AI test prompt generation with expert system guidance based on company positioning and competitors
- Parallel testing across multiple AI platforms (Perplexity and ChatGPT)
- Real-time web search capabilities for current data
- Platform-specific result analysis with clear source attribution
- Comprehensive visibility analysis and gap identification
- Citation opportunity detection for blog content optimization
- Structured output generation following BlogAiVisibilityTestSchema
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
1. Load company context from blog company profiles
2. Generate AI test prompts using expert system guidance
3. Execute parallel testing on Perplexity and ChatGPT platforms
4. Construct analysis prompts with clearly attributed platform results
5. Analyze responses with platform-specific insights
6. Store comprehensive test results and recommendations

LLM Configuration:
- Analysis LLM: gpt-4.1 (OpenAI)
- Perplexity Testing: sonar-pro model with web search
- ChatGPT Testing: gpt-4o model with web search
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

from kiwi_client.workflows_for_blog_teammate.document_models.customer_docs import (
    # Blog Company Profile
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_VERSIONED,
    BLOG_COMPANY_IS_SHARED,
    BLOG_COMPANY_IS_SYSTEM_ENTITY,
    
    # Blog AI Visibility Test
    BLOG_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_AI_VISIBILITY_TEST_IS_VERSIONED,
    BLOG_AI_VISIBILITY_TEST_IS_SHARED,
    BLOG_AI_VISIBILITY_TEST_IS_SYSTEM_ENTITY
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.blog_ai_visibility_test import (
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
PERPLEXITY_TEMPERATURE = 0.4
PERPLEXITY_MAX_TOKENS = 3000

# OpenAI Configuration for ChatGPT testing
OPENAI_PROVIDER = "openai"
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.4
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
    "company_name": {
        "type": "str",
        "required": True,
        "description": "Name of the company to test AI visibility for"
    },
}
            }
        },

        # --- 2. Load Company Context ---
        "load_company_context": {
            "node_id": "load_company_context",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": BLOG_COMPANY_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "company_name",
                            "static_docname": BLOG_COMPANY_DOCNAME,
                        },
                        "output_field_name": "blog_company_doc"
                    }
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
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
                            "company_name": None,
                            "website_url": None,
                            "icps": None,
                            "competitors": None,
                        },
                        "construct_options": {
                            "company_name": "blog_company_doc.company_name",
                            "website_url": "blog_company_doc.website_url",
                            "icps": "blog_company_doc.icps",
                            "competitors": "blog_company_doc.competitors",
                        },
                    },
                    "ai_test_system_prompt": {
                        "id": "ai_test_system_prompt",
                        "template": AI_TEST_PROMPT_GENERATION_SYSTEM,
                    }
                }
            },
        },

        # --- 4. Execute Perplexity AI Tests ---
        "execute_perplexity_tests": {
            "node_id": "execute_perplexity_tests",
            "node_name": "llm",
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
                            "company_context": None
                        },
                        "construct_options": {
                            "company_context": "blog_company_doc"
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
                    "is_versioned": BLOG_AI_VISIBILITY_TEST_IS_VERSIONED,
                    "operation": "upsert",
                },
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "static_docname": BLOG_AI_VISIBILITY_TEST_DOCNAME,
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
        # Input -> Load Company Context
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_company_context",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
            ],
        },
        # Input -> State
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
            ],
        },
        # Load Company Context -> State
        {
            "src_node_id": "load_company_context",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "blog_company_doc", "dst_field": "blog_company_doc"},
            ],
        },
        # Load Company Context -> Build AI Test Prompts
        {
            "src_node_id": "load_company_context",
            "dst_node_id": "build_ai_test_prompts",
            "mappings": [
                {"src_field": "blog_company_doc", "dst_field": "blog_company_doc"},
            ],
        },

        {
            "src_node_id": "build_ai_test_prompts",
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
        # Build AI Test Prompts -> Execute ChatGPT Tests
        {
            "src_node_id": "execute_perplexity_tests",
            "dst_node_id": "construct_query_generation_prompt",
            "mappings": []
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_query_generation_prompt",
            "mappings": [
                {"src_field": "blog_company_doc", "dst_field": "blog_company_doc"}
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
                {"src_field": "blog_company_doc", "dst_field": "company_context"}
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

        {
            "src_node_id": "analyze_responses",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "analysis_structured_output"},
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
        # State -> Store Test Results
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "store_test_results",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
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
                "blog_company_doc": "replace",
                "perplexity_results": "replace",
                "all_single_chatgpt_query_results": "collect_values",
                "chatgpt_results": "replace",
                "visibility_report": "replace"
            }
        }
    }
}

# Test functions
async def main_test_blog_ai_visibility_workflow():
    """Main test function for the blog AI visibility workflow"""
    test_name = "Blog AI Visibility Workflow Test"
    print(f"--- Starting {test_name} ---")
    
    test_company_name = "writer"
    
    test_input = {
        "company_name": test_company_name,
    }
    
    # Setup test documents with comprehensive company data
    setup_docs = [
        # Blog Company Profile Document
        {
            'namespace': f"blog_company_profile_{test_company_name}",
            'docname': BLOG_COMPANY_DOCNAME,
            'initial_data': {
                "company_name": "Writer",
                "website_url": "https://writer.com",
                "positioning_headline": "Writer is an AI writing platform built for teams, helping enterprises ensure consistent, on-brand, and high-quality content across all departments.",
                "icps": {
                    "icp_name": "Enterprise Marketing and Operations Teams",
                    "target_industry": "Technology, Financial Services, Healthcare, and Professional Services",
                    "company_size": "Mid-market to Enterprise (500+ employees)",
                    "buyer_persona": "CMO, Head of Content, VP of Marketing, Operations Lead",
                    "pain_points": [
                        "Inconsistent brand voice across departments",
                        "Low content velocity",
                        "Difficulty scaling content creation while maintaining quality",
                        "Inefficiencies in cross-functional communication and documentation"
                    ]
                },
                "goals": [
                        "Standardize brand voice across all content",
                        "Improve writing quality at scale",
                        "Enable all team members to write clearly and efficiently",
                        "Speed up content production processes"
                    ],
                "content_distribution_mix": {
                    "awareness_percent": 40.0,
                    "consideration_percent": 30.0,
                    "purchase_percent": 20.0,
                    "retention_percent": 10.0
                },
                "competitors": [
                    {
                        "website_url": "https://grammarly.com",
                        "name": "Grammarly"
                    },
                    {
                        "website_url": "https://jasper.ai",
                        "name": "Jasper"
                    },
                    {
                        "website_url": "https://copy.ai",
                        "name": "Copy.ai"
                    }
                ]
            },
            'is_versioned': BLOG_COMPANY_IS_VERSIONED,
            'is_shared': BLOG_COMPANY_IS_SHARED,
            'initial_version': 'default' if BLOG_COMPANY_IS_VERSIONED else None,
            'is_system_entity': BLOG_COMPANY_IS_SYSTEM_ENTITY
        }
    ]
    
    # Cleanup configuration
    cleanup_docs = [
        {
            'namespace': f"blog_company_profile_{test_company_name}", 
            'docname': BLOG_COMPANY_DOCNAME, 
            'is_versioned': BLOG_COMPANY_IS_VERSIONED, 
            'is_shared': BLOG_COMPANY_IS_SHARED,
            'is_system_entity': BLOG_COMPANY_IS_SYSTEM_ENTITY
        },
        {
            'namespace': f"blog_analysis_{test_company_name}", 
            'docname': BLOG_AI_VISIBILITY_TEST_DOCNAME, 
            'is_versioned': BLOG_AI_VISIBILITY_TEST_IS_VERSIONED, 
            'is_shared': BLOG_AI_VISIBILITY_TEST_IS_SHARED,
            'is_system_entity': BLOG_AI_VISIBILITY_TEST_IS_SYSTEM_ENTITY
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
        validate_output_func=validate_blog_ai_visibility_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )
    
    print(f"--- {test_name} Finished ---")
    if final_run_outputs and 'visibility_report' in final_run_outputs:
        report = final_run_outputs['visibility_report']
        print(f"Test Queries Count: {len(report.get('test_queries', []))}")
        print(f"ChatGPT Content Mentioned: {report.get('chatgpt_results', {}).get('blog_content_mentioned', 'unknown')}")
        print(f"Perplexity Content Mentioned: {report.get('perplexity_results', {}).get('blog_content_mentioned', 'unknown')}")
        print(f"Company Tested: {test_company_name}")
        print(f"Competitors Analyzed: Grammarly, Jasper, Copy.ai")
    
    return final_run_status_obj, final_run_outputs

async def validate_blog_ai_visibility_output(outputs) -> bool:
    """Validate the blog AI visibility workflow output"""
    if not outputs:
        logging.error("Validation Failed: Workflow returned no outputs")
        return False
    
    logging.info("Validating blog AI visibility workflow outputs...")
    
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
    
    # Check for required schema fields
    required_report_fields = [
        "test_queries",
        "chatgpt_results",
        "perplexity_results",
        "visibility_gaps",
        "citation_opportunities",
        "test_timestamp"
    ]
    
    for field in required_report_fields:
        if field not in visibility_report:
            logging.error(f"Missing required field in visibility_report: {field}")
            return False
    
    # Validate test queries structure
    if "test_queries" in visibility_report:
        test_queries = visibility_report["test_queries"]
        if not isinstance(test_queries, list):
            logging.error("test_queries should be a list")
            return False
        
        for query in test_queries:
            if not isinstance(query, dict):
                logging.error("Invalid test_queries structure - each query should be a dict")
                return False
            
            required_query_fields = ["query_text", "query_type", "expected_relevance"]
            for field in required_query_fields:
                if field not in query:
                    logging.error(f"Missing required field in test query: {field}")
                    return False
    
    # Validate ChatGPT results
    if "chatgpt_results" in visibility_report:
        chatgpt_results = visibility_report["chatgpt_results"]
        if not isinstance(chatgpt_results, dict):
            logging.error("chatgpt_results should be a dict")
            return False
        
        required_chatgpt_fields = ["blog_content_mentioned", "specific_posts_cited", "citation_context", "competitors_mentioned"]
        for field in required_chatgpt_fields:
            if field not in chatgpt_results:
                logging.error(f"Missing required field in chatgpt_results: {field}")
                return False
    
    # Validate Perplexity results
    if "perplexity_results" in visibility_report:
        perplexity_results = visibility_report["perplexity_results"]
        if not isinstance(perplexity_results, dict):
            logging.error("perplexity_results should be a dict")
            return False
        
        required_perplexity_fields = ["blog_content_mentioned", "sources_ranking", "snippet_usage", "related_queries"]
        for field in required_perplexity_fields:
            if field not in perplexity_results:
                logging.error(f"Missing required field in perplexity_results: {field}")
                return False
    
    # Validate visibility gaps and citation opportunities
    if "visibility_gaps" in visibility_report:
        visibility_gaps = visibility_report["visibility_gaps"]
        if not isinstance(visibility_gaps, list):
            logging.error("visibility_gaps should be a list")
            return False
    
    if "citation_opportunities" in visibility_report:
        citation_opportunities = visibility_report["citation_opportunities"]
        if not isinstance(citation_opportunities, list):
            logging.error("citation_opportunities should be a list")
            return False
    
    # Log successful validation details
    logging.info(f"✓ Visibility report validation successful")
    logging.info(f"✓ Number of test queries: {len(visibility_report.get('test_queries', []))}")
    logging.info(f"✓ ChatGPT content mentioned: {visibility_report.get('chatgpt_results', {}).get('blog_content_mentioned', 'unknown')}")
    logging.info(f"✓ Perplexity content mentioned: {visibility_report.get('perplexity_results', {}).get('blog_content_mentioned', 'unknown')}")
    logging.info(f"✓ Visibility gaps found: {len(visibility_report.get('visibility_gaps', []))}")
    logging.info(f"✓ Citation opportunities: {len(visibility_report.get('citation_opportunities', []))}")
    
    logging.info("✓ Blog AI visibility workflow output validation successful")
    return True

# Entry point
if __name__ == "__main__":
    print("="*80)
    print("Blog AI Visibility Workflow Test")
    print("="*80)
    
    try:
        asyncio.run(main_test_blog_ai_visibility_workflow())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logging.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=. python kiwi_client/workflows_for_blog_teammate/wf_blog_ai_visibility.py")
