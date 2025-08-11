"""
Executive Web Visibility Testing Workflow

This workflow enables comprehensive testing of executive thought leadership visibility across web platforms with:
- Executive context loading from executive profiles
- Web search query generation with expert system guidance based on executive positioning and expertise
- Comprehensive web search testing across multiple search engines (Google, Bing, LinkedIn)
- Real-time web search capabilities for current visibility data
- Search engine result analysis with ranking positions and authority signals
- Comprehensive web presence analysis and visibility gap identification
- SEO optimization opportunity detection for executive content improvement
- Structured output generation following ExecutiveWebVisibilityTestSchema
- Document storage for test results and tracking

Key Features:
- Multi-platform web search testing (Google, Bing, LinkedIn, industry platforms)
- Real web search integration for current visibility data
- Search engine ranking analysis and authority signal detection
- Brand consistency evaluation across platforms
- Expert system guidance for web search query generation
- Platform-specific visibility gap analysis and SEO opportunities
- Comprehensive test result storage and retrieval

Workflow Architecture:
1. Load executive context from executive profiles
2. Generate web search queries using expert system guidance
3. Execute comprehensive web searches across multiple platforms
4. Construct analysis prompts with web search results
5. Analyze results with search engine optimization insights
6. Store comprehensive test results and recommendations

LLM Configuration:
- Analysis LLM: gpt-4.1 (OpenAI)
- Web Search: sonar-pro model with comprehensive web search
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
    # Blog Executive Profile
    BLOG_EXECUTIVE_DOCNAME,
    BLOG_EXECUTIVE_NAMESPACE_TEMPLATE,
    BLOG_EXECUTIVE_IS_VERSIONED,
    BLOG_EXECUTIVE_IS_SHARED,
    BLOG_EXECUTIVE_IS_SYSTEM_ENTITY,
    
    # Blog Executive Web Visibility Test
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_DOCNAME,
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_VERSIONED,
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_SHARED,
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_SYSTEM_ENTITY
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.executive_web_visibility_test import (
    GENERATION_SCHEMA,
    WEB_SEARCH_GENERATION_SCHEMA,
    WEB_VISIBILITY_TEST_PROMPT,
    WEB_TEST_PROMPT_GENERATION_SYSTEM,
    SYSTEM_PROMPT_TEMPLATE,
    USER_PROMPT_TEMPLATE,
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

workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node ---
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "context_doc_configs": {
                        "type": "list",
                        "required": True,
                        "description": "List of document configurations for loading executive context like executive profile"
                    },
                    "entity_username": {
                        "type": "str",
                        "required": True,
                        "description": "Name of the executive to test web visibility for"
                    },
                }
            }
        },

        # --- 2. Load Executive Context ---
        "load_executive_context": {
            "node_id": "load_executive_context",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "context_doc_configs",
                "global_is_shared": BLOG_EXECUTIVE_IS_SHARED,
                "global_is_system_entity": BLOG_EXECUTIVE_IS_SYSTEM_ENTITY,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 3. Build Web Search Prompts ---
        "build_web_search_prompts": {
            "node_id": "build_web_search_prompts",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "web_search_user_prompt": {
                        "id": "web_search_user_prompt",
                        "template": WEB_VISIBILITY_TEST_PROMPT,
                        "variables": {
                            "full_name": None,
                            "profile_url": None,
                            "persona_tags": None
                        },
                        "construct_options": {
                            "full_name": "blog_executive_doc.username",
                            "profile_url": "blog_executive_doc.profile_url",
                            "persona_tags": "blog_executive_doc.persona_tags"
                        },
                    },
                    "web_search_system_prompt": {
                        "id": "web_search_system_prompt",
                        "template": WEB_TEST_PROMPT_GENERATION_SYSTEM,
                        "variables": { "schema": json.dumps(WEB_SEARCH_GENERATION_SCHEMA, indent=2) },
                    }
                }
            },
        },

        # --- 4. Execute Web Search Tests ---
        "execute_web_search_tests": {
            "node_id": "execute_web_search_tests",
            "node_name": "llm",
            "enable_node_fan_in": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": PERPLEXITY_PROVIDER, "model": PERPLEXITY_MODEL},
                    "temperature": PERPLEXITY_TEMPERATURE,
                    "max_tokens": PERPLEXITY_MAX_TOKENS,
                },
                "web_search_options": {
                    "search_domain_filter": [
                    ]
                },
                "output_schema": {
                    "schema_definition": WEB_SEARCH_GENERATION_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            },
        },

        # --- 5. Construct Analysis Prompt ---
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
                            "web_search_results": None,
                        },
                        "construct_options": {
                            "company_context": "company_context",
                            "web_search_results": "web_search_results",
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

        # --- 6. Analyze Web Search Results & Generate Visibility Report ---
        "analyze_web_results": {
            "node_id": "analyze_web_results",
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

        # --- 7. Store Test Results ---
        "store_test_results": {
            "node_id": "store_test_results",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_VERSIONED,
                    "operation": "upsert",
                },
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_DOCNAME,
                            }
                        },
                    }
                ],
            },
        },

        # --- 8. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {
                "output_schema": {
                    "fields": {
                        "web_visibility_report": {
                            "type": "object",
                            "description": "Complete web visibility test results following ExecutiveWebVisibilityTestSchema"
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
                {"src_field": "context_doc_configs", "dst_field": "context_doc_configs"},
                {"src_field": "entity_username", "dst_field": "entity_username"},
            ],
        },
        # Input -> State
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "context_doc_configs", "dst_field": "context_doc_configs"},
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
        # Load Executive Context -> Build Web Search Prompts
        {
            "src_node_id": "load_executive_context",
            "dst_node_id": "build_web_search_prompts",
            "mappings": [
                {"src_field": "blog_executive_doc", "dst_field": "blog_executive_doc"},
            ],
        },
        # Build Web Search Prompts -> Execute Web Search Tests
        {
            "src_node_id": "build_web_search_prompts",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "web_search_user_prompt", "dst_field": "web_search_user_prompt"},
                {"src_field": "web_search_system_prompt", "dst_field": "web_search_system_prompt"},
            ],
        },
        {
            "src_node_id": "build_web_search_prompts",
            "dst_node_id": "execute_web_search_tests",
            "mappings": [],
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "execute_web_search_tests",
            "mappings": [
                {"src_field": "web_search_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "web_search_system_prompt", "dst_field": "system_prompt"},
            ],
        },
        # Execute Web Search Tests -> State
        {
            "src_node_id": "execute_web_search_tests",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "content", "dst_field": "web_search_results"},
            ],
        },
        # Execute Web Search Tests -> Construct Analysis Prompt
        {
            "src_node_id": "execute_web_search_tests",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": [],
        },
        # State -> Construct Analysis Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": [
                {"src_field": "web_search_results", "dst_field": "web_search_results"},
                {"src_field": "blog_executive_doc", "dst_field": "company_context"},
            ],
        },
        # Construct Analysis Prompt -> Analyze Web Results
        {
            "src_node_id": "construct_analysis_prompt",
            "dst_node_id": "analyze_web_results",
            "mappings": [
                {"src_field": "analysis_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "analysis_system_prompt", "dst_field": "system_prompt"},
            ],
        },
        # Analyze Web Results -> Store Test Results
        {
            "src_node_id": "analyze_web_results",
            "dst_node_id": "store_test_results",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "structured_output"},
            ],
        },
        {
            "src_node_id": "analyze_web_results",
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
        # Store Test Results -> Output Node
        {
            "src_node_id": "store_test_results",
            "dst_node_id": "output_node",
            "mappings": [],
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "analysis_structured_output", "dst_field": "web_visibility_report"},
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
                "web_search_results": "replace",
                "web_visibility_report": "replace"
            }
        }
    }
}

# Test functions
async def main_test_executive_web_visibility_workflow():
    """Main test function for the executive web visibility workflow"""
    test_name = "Executive Web Visibility Workflow Test"
    print(f"--- Starting {test_name} ---")
    
    # Example executive context doc configs
    test_context_docs = [
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_EXECUTIVE_NAMESPACE_TEMPLATE,
                "input_namespace_field": "entity_username",
                "static_docname": BLOG_EXECUTIVE_DOCNAME,
            },
            "output_field_name": "blog_executive_doc"
        },
    ]
    
    test_executive_name = "john_doe"
    
    test_input = {
        "context_doc_configs": test_context_docs,
        "entity_username": test_executive_name,
    }
    
    # Setup test documents with comprehensive executive data
    setup_docs = [
        # Blog Executive Profile Document
        {
            'namespace': f"blog_executive_presence_{test_executive_name}",
            'docname': BLOG_EXECUTIVE_DOCNAME,
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
            'is_versioned': BLOG_EXECUTIVE_IS_VERSIONED,
            'is_shared': BLOG_EXECUTIVE_IS_SHARED,
            'initial_version': 'default' if BLOG_EXECUTIVE_IS_VERSIONED else None,
            'is_system_entity': BLOG_EXECUTIVE_IS_SYSTEM_ENTITY
        }
    ]
    
    # Cleanup configuration
    cleanup_docs = [
        {
            'namespace': f"blog_executive_presence_{test_executive_name}", 
            'docname': BLOG_EXECUTIVE_DOCNAME, 
            'is_versioned': BLOG_EXECUTIVE_IS_VERSIONED, 
            'is_shared': BLOG_EXECUTIVE_IS_SHARED,
            'is_system_entity': BLOG_EXECUTIVE_IS_SYSTEM_ENTITY
        },
        {
            'namespace': f"blog_executive_presence_{test_executive_name}", 
            'docname': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_DOCNAME, 
            'is_versioned': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_VERSIONED, 
            'is_shared': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_SHARED,
            'is_system_entity': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_SYSTEM_ENTITY
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
        validate_output_func=validate_executive_web_visibility_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )
    
    print(f"--- {test_name} Finished ---")
    if final_run_outputs and 'web_visibility_report' in final_run_outputs:
        report = final_run_outputs['web_visibility_report']
        print(f"Generated Test ID: {report.get('test_id')}")
        print(f"Test Queries Count: {len(report.get('test_queries', []))}")
        print(f"Overall Web Visibility Score: {report.get('overall_web_visibility_score', 'unknown')}")
        print(f"Search Engine Ranking: {report.get('search_engine_results', {}).get('ranking_position', 'unknown')}")
        print(f"Executive Tested: {test_executive_name}")
        print(f"Executive Profile: John Doe - Marketing Executive")
    
    return final_run_status_obj, final_run_outputs

async def validate_executive_web_visibility_output(outputs) -> bool:
    """Validate the executive web visibility workflow output"""
    if not outputs:
        logging.error("Validation Failed: Workflow returned no outputs")
        return False
    
    logging.info("Validating executive web visibility workflow outputs...")
    
    # Check for required fields
    required_fields = ["web_visibility_report"]
    
    for field in required_fields:
        if field not in outputs:
            logging.error(f"Missing required field: {field}")
            return False
    
    web_visibility_report = outputs["web_visibility_report"]
    
    if not isinstance(web_visibility_report, dict):
        logging.error("web_visibility_report is not a dictionary")
        return False
    
    # Check for required schema fields
    required_report_fields = [
        "test_id",
        "test_queries",
        "search_engine_results",
        "web_presence_analysis",
        "competitor_comparison",
        "visibility_opportunities",
        "overall_web_visibility_score",
        "test_timestamp"
    ]
    
    for field in required_report_fields:
        if field not in web_visibility_report:
            logging.error(f"Missing required field in web_visibility_report: {field}")
            return False
    
    # Validate test queries structure
    if "test_queries" in web_visibility_report:
        test_queries = web_visibility_report["test_queries"]
        if not isinstance(test_queries, list):
            logging.error("test_queries should be a list")
            return False
        
        for query in test_queries:
            if not isinstance(query, dict):
                logging.error("Invalid test_queries structure - each query should be a dict")
                return False
            
            required_query_fields = ["query_text", "query_type", "expected_relevance", "search_engine"]
            for field in required_query_fields:
                if field not in query:
                    logging.error(f"Missing required field in test query: {field}")
                    return False
    
    # Validate search engine results
    if "search_engine_results" in web_visibility_report:
        search_results = web_visibility_report["search_engine_results"]
        if not isinstance(search_results, dict):
            logging.error("search_engine_results should be a dict")
            return False
        
        required_search_fields = ["google_results", "bing_results", "linkedin_results", "ranking_position"]
        for field in required_search_fields:
            if field not in search_results:
                logging.error(f"Missing required field in search_engine_results: {field}")
                return False
    
    # Validate web presence analysis
    if "web_presence_analysis" in web_visibility_report:
        web_presence = web_visibility_report["web_presence_analysis"]
        if not isinstance(web_presence, dict):
            logging.error("web_presence_analysis should be a dict")
            return False
        
        required_presence_fields = ["primary_platforms", "content_freshness", "authority_signals", "brand_consistency"]
        for field in required_presence_fields:
            if field not in web_presence:
                logging.error(f"Missing required field in web_presence_analysis: {field}")
                return False
    
    # Validate visibility opportunities
    if "visibility_opportunities" in web_visibility_report:
        opportunities = web_visibility_report["visibility_opportunities"]
        if not isinstance(opportunities, dict):
            logging.error("visibility_opportunities should be a dict")
            return False
        
        required_opportunity_fields = ["platform_opportunities", "content_optimization", "seo_improvements"]
        for field in required_opportunity_fields:
            if field not in opportunities:
                logging.error(f"Missing required field in visibility_opportunities: {field}")
                return False
    
    # Validate overall web visibility score
    if "overall_web_visibility_score" in web_visibility_report:
        score = web_visibility_report["overall_web_visibility_score"]
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            logging.error("overall_web_visibility_score should be a number between 0 and 10")
            return False
    
    # Log successful validation details
    logging.info(f"✓ Web visibility report validation successful")
    logging.info(f"✓ Test ID: {web_visibility_report.get('test_id', 'unknown')}")
    logging.info(f"✓ Number of test queries: {len(web_visibility_report.get('test_queries', []))}")
    logging.info(f"✓ Overall web visibility score: {web_visibility_report.get('overall_web_visibility_score', 'unknown')}")
    logging.info(f"✓ Search engine ranking: {web_visibility_report.get('search_engine_results', {}).get('ranking_position', 'unknown')}")
    logging.info(f"✓ Primary platforms: {len(web_visibility_report.get('web_presence_analysis', {}).get('primary_platforms', []))}")
    logging.info(f"✓ Visibility opportunities: {len(web_visibility_report.get('visibility_opportunities', {}).get('platform_opportunities', []))}")
    
    logging.info("✓ Executive web visibility workflow output validation successful")
    return True

# Entry point
if __name__ == "__main__":
    print("="*80)
    print("Executive Web Visibility Workflow Test")
    print("="*80)
    
    try:
        asyncio.run(main_test_executive_web_visibility_workflow())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logging.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=. python kiwi_client/workflows_for_blog_teammate/wf_executive_web_visibility.py")
