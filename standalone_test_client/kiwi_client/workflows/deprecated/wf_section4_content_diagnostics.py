"""
Section 4 Content Diagnostics Workflow

This workflow:
1. Loads blog content analysis and competitor content analysis documents
2. Identifies content gaps across customer journey stages (awareness, consideration, purchase, retention)
3. Validates gaps through Reddit research to check user intent and demand
4. Generates market opportunity analysis with content territories
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import json

# Internal dependencies
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

from kiwi_client.workflows_for_blog_teammate.document_models.customer_docs import (
    # Blog Content Analysis
    BLOG_CONTENT_ANALYSIS_DOCNAME,
    BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_ANALYSIS_IS_VERSIONED,
    # Competitor Content Analysis
    BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME,
    BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
    # Section 4 Diagnostic Report
    BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION4_IS_VERSIONED,
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.section4_content_diagnostics import (
    CONTENT_GAPS_SCHEMA,
    GAP_VALIDATION_SCHEMA,
    MARKET_OPPORTUNITY_SCHEMA,
    CONTENT_GAP_ANALYSIS_USER_PROMPT,
    CONTENT_GAP_ANALYSIS_SYSTEM_PROMPT,
    REDDIT_VALIDATION_USER_PROMPT,
    REDDIT_VALIDATION_SYSTEM_PROMPT,
    MARKET_OPPORTUNITY_USER_PROMPT,
    MARKET_OPPORTUNITY_SYSTEM_PROMPT,
)

# --- Workflow Configuration Constants ---

# LLM Configuration
LLM_PROVIDER = "openai"
GENERATION_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4000

# Reddit Research Configuration
PERPLEXITY_PROVIDER = "perplexity"
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_TEMPERATURE = 0.2
PERPLEXITY_MAX_TOKENS = 3000

# Customer Journey Stages
AWARENESS = "awareness"
CONSIDERATION = "consideration"
PURCHASE = "purchase"
RETENTION = "retention"

# --- Workflow Graph Definition ---

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
                        "description": "Name of the entity to analyze content gaps for."
                    }
                }
            }
        },

        # --- 2. Load Blog Content Analysis ---
        "load_blog_content_analysis": {
            "node_id": "load_blog_content_analysis",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": BLOG_CONTENT_ANALYSIS_DOCNAME,
                        },
                        "output_field_name": "blog_content_analysis"
                    }
                ]
            }
        },

        # --- 3. Load Competitor Content Analysis Documents ---
        "load_competitor_content_analysis": {
            "node_id": "load_competitor_content_analysis",
            "node_name": "load_multiple_customer_data",
            "node_config": {
                "namespace_filter": None,  # Will be dynamically set
                "namespace_pattern": BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
                "namespace_pattern_input_path": "entity_username",
                "include_shared": False,
                "include_user_specific": True,
                "include_system_entities": False,
                "limit": 50,  # Load up to 50 competitor analysis documents
                "sort_by": "created_at",
                "sort_order": "desc",
                "output_field_name": "competitor_content_analysis_docs"
            }
        },

        # --- 4. Construct Content Gap Analysis Prompt ---
        "construct_gap_analysis_prompt": {
            "node_id": "construct_gap_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "gap_analysis_user_prompt": {
                        "id": "gap_analysis_user_prompt",
                        "template": CONTENT_GAP_ANALYSIS_USER_PROMPT,
                        "variables": {
                            "blog_content_analysis": None,
                            "competitor_content_analysis": None
                        },
                        "construct_options": {
                            "blog_content_analysis": "blog_content_analysis",
                            "competitor_content_analysis": "competitor_content_analysis_docs"
                        }
                    },
                    "gap_analysis_system_prompt": {
                        "id": "gap_analysis_system_prompt",
                        "template": CONTENT_GAP_ANALYSIS_SYSTEM_PROMPT,
                        "variables": {
                            "schema": CONTENT_GAPS_SCHEMA
                        },
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 5. Generate Content Gap Analysis ---
        "generate_content_gaps": {
            "node_id": "generate_content_gaps",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": GENERATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": CONTENT_GAPS_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 6. Route Gaps for Reddit Validation ---
        "route_gaps_for_validation": {
            "node_id": "route_gaps_for_validation",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["construct_reddit_validation_prompt"],
                "map_targets": [
                    {
                        "source_path": "content_gaps_analysis.awareness_gaps",
                        "destinations": ["construct_reddit_validation_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "gap_to_validate"
                    },
                    {
                        "source_path": "content_gaps_analysis.consideration_gaps",
                        "destinations": ["construct_reddit_validation_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "gap_to_validate"
                    },
                    {
                        "source_path": "content_gaps_analysis.purchase_gaps",
                        "destinations": ["construct_reddit_validation_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "gap_to_validate"
                    },
                    {
                        "source_path": "content_gaps_analysis.retention_gaps",
                        "destinations": ["construct_reddit_validation_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "gap_to_validate"
                    }
                ]
            }
        },

        # --- 7. Construct Reddit Validation Prompt ---
        "construct_reddit_validation_prompt": {
            "node_id": "construct_reddit_validation_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "node_config": {
                "prompt_templates": {
                    "reddit_validation_user_prompt": {
                        "id": "reddit_validation_user_prompt",
                        "template": REDDIT_VALIDATION_USER_PROMPT,
                        "variables": {
                            "content_gaps": None
                        },
                        "construct_options": {
                            "content_gaps": "gap_to_validate"
                        }
                    },
                    "reddit_validation_system_prompt": {
                        "id": "reddit_validation_system_prompt",
                        "template": REDDIT_VALIDATION_SYSTEM_PROMPT,
                        "variables": {
                            "schema": GAP_VALIDATION_SCHEMA
                        },
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 8. Perform Reddit Research Validation ---
        "perform_reddit_validation": {
            "node_id": "perform_reddit_validation",
            "node_name": "llm",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": PERPLEXITY_PROVIDER,
                        "model": PERPLEXITY_MODEL
                    },
                    "temperature": PERPLEXITY_TEMPERATURE,
                    "max_tokens": PERPLEXITY_MAX_TOKENS
                },
                "web_search_options": {
                    "search_recency_filter": "month",
                    "search_context_size": "medium",
                    "search_domain_filter": [
                        "reddit.com"
                    ]
                },
                "tool_calling_config": {
                    "enable_tool_calling": True,
                    "parallel_tool_calls": True
                },
                "output_schema": {
                    "schema_definition": GAP_VALIDATION_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 9. Flatten Validation Results ---
        "flatten_validation_results": {
            "node_id": "flatten_validation_results",
            "node_name": "merge_aggregate",
            "node_config": {
                "operations": [
                    {
                        "output_field_name": "merged_data",
                        "select_paths": ["validation_results_batches"],
                        "merge_strategy": {
                            "reduce_phase": {
                                "default_reducer": "nested_merge_aggregate",
                                "error_strategy": "fail_node",
                            }
                        }
                    }
                ]
            }
        },

        # --- 10. Construct Market Opportunity Analysis Prompt ---
        "construct_market_opportunity_prompt": {
            "node_id": "construct_market_opportunity_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "market_opportunity_user_prompt": {
                        "id": "market_opportunity_user_prompt",
                        "template": MARKET_OPPORTUNITY_USER_PROMPT,
                        "variables": {
                            "validated_gaps": None
                        },
                        "construct_options": {
                            "validated_gaps": "merged_data.all_validated_gaps"
                        }
                    },
                    "market_opportunity_system_prompt": {
                        "id": "market_opportunity_system_prompt",
                        "template": MARKET_OPPORTUNITY_SYSTEM_PROMPT,
                        "variables": {
                            "schema": MARKET_OPPORTUNITY_SCHEMA
                        },
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 11. Generate Market Opportunity Analysis ---
        "generate_market_opportunity": {
            "node_id": "generate_market_opportunity",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": GENERATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": MARKET_OPPORTUNITY_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 12. Combine Final Results ---
        "combine_final_results": {
            "node_id": "combine_final_results",
            "node_name": "transform_data",
            "node_config": {
                "mappings": [
                    {"source_path": "entity_username", "destination_path": "final_report.entity_username"},
                    {"source_path": "content_gaps_analysis", "destination_path": "final_report.content_gaps_analysis"},
                    {"source_path": "all_validated_gaps", "destination_path": "final_report.validated_gaps"},
                    {"source_path": "market_opportunity_analysis", "destination_path": "final_report.market_opportunity_analysis"}
                ]
            }
        },

        # --- 13. Store Final Report ---
        "store_final_report": {
            "node_id": "store_final_report",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": BLOG_CONTENT_DIAGNOSTIC_SECTION4_IS_VERSIONED,
                    "operation": "upsert"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "transformed_data.final_report",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },

        # --- 14. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {}
        }
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # Input -> State
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },

        # Input -> Load Blog Content Analysis
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_blog_content_analysis",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },

        # Input -> Load Competitor Content Analysis
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_competitor_content_analysis",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },

        # Load Blog Content Analysis -> State
        {
            "src_node_id": "load_blog_content_analysis",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "blog_content_analysis", "dst_field": "blog_content_analysis"}
            ]
        },

        # Load Competitor Content Analysis -> State
        {
            "src_node_id": "load_competitor_content_analysis",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "competitor_content_analysis_docs", "dst_field": "competitor_content_analysis_docs"}
            ]
        },

        # Load Blog Content Analysis -> Construct Gap Analysis Prompt
        {
            "src_node_id": "load_blog_content_analysis",
            "dst_node_id": "construct_gap_analysis_prompt",
            "mappings": [
                {"src_field": "blog_content_analysis", "dst_field": "blog_content_analysis"}
            ]
        },

        # Load Competitor Content Analysis -> Construct Gap Analysis Prompt
        {
            "src_node_id": "load_competitor_content_analysis",
            "dst_node_id": "construct_gap_analysis_prompt",
            "mappings": [
                {"src_field": "competitor_content_analysis_docs", "dst_field": "competitor_content_analysis_docs"}
            ]
        },

        # Construct Gap Analysis Prompt -> Generate Content Gaps
        {
            "src_node_id": "construct_gap_analysis_prompt",
            "dst_node_id": "generate_content_gaps",
            "mappings": [
                {"src_field": "gap_analysis_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "gap_analysis_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        # Generate Content Gaps -> State
        {
            "src_node_id": "generate_content_gaps",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "content_gaps_analysis"}
            ]
        },

        # Generate Content Gaps -> Route Gaps for Validation
        {
            "src_node_id": "generate_content_gaps",
            "dst_node_id": "route_gaps_for_validation",
            "mappings": []
        },

        # State -> Route Gaps for Validation
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "route_gaps_for_validation",
            "mappings": [
                {"src_field": "content_gaps_analysis", "dst_field": "content_gaps_analysis"}
            ]
        },

        # Route Gaps for Validation -> Construct Reddit Validation Prompt
        {
            "src_node_id": "route_gaps_for_validation",
            "dst_node_id": "construct_reddit_validation_prompt",
            "mappings": []
        },

        # Construct Reddit Validation Prompt -> Perform Reddit Validation
        {
            "src_node_id": "construct_reddit_validation_prompt",
            "dst_node_id": "perform_reddit_validation",
            "mappings": [
                {"src_field": "reddit_validation_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "reddit_validation_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        # Perform Reddit Validation -> State
        {
            "src_node_id": "perform_reddit_validation",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "validation_results_batches"}
            ]
        },

        # Perform Reddit Validation -> Flatten Validation Results
        {
            "src_node_id": "perform_reddit_validation",
            "dst_node_id": "flatten_validation_results",
            "mappings": []
        },

        # State -> Flatten Validation Results
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "flatten_validation_results",
            "mappings": [
                {"src_field": "validation_results_batches", "dst_field": "validation_results_batches"}
            ]
        },

        # Flatten Validation Results -> State
        {
            "src_node_id": "flatten_validation_results",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "merged_data", "dst_field": "merged_data"}
            ]
        },

        # Flatten Validation Results -> Construct Market Opportunity Prompt
        {
            "src_node_id": "flatten_validation_results",
            "dst_node_id": "construct_market_opportunity_prompt",
            "mappings": [
                {"src_field": "merged_data", "dst_field": "merged_data"}
            ]
        },

        # Construct Market Opportunity Prompt -> Generate Market Opportunity
        {
            "src_node_id": "construct_market_opportunity_prompt",
            "dst_node_id": "generate_market_opportunity",
            "mappings": [
                {"src_field": "market_opportunity_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "market_opportunity_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        # Generate Market Opportunity -> State
        {
            "src_node_id": "generate_market_opportunity",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "market_opportunity_analysis"}
            ]
        },

        # Generate Market Opportunity -> Combine Final Results
        {
            "src_node_id": "generate_market_opportunity",
            "dst_node_id": "combine_final_results",
            "mappings": []
        },

        # State -> Combine Final Results
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "combine_final_results",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"},
                {"src_field": "content_gaps_analysis", "dst_field": "content_gaps_analysis"},
                {"src_field": "merged_data", "dst_field": "merged_data"},
                {"src_field": "market_opportunity_analysis", "dst_field": "market_opportunity_analysis"}
            ]
        },

        # Combine Final Results -> Store Final Report
        {
            "src_node_id": "combine_final_results",
            "dst_node_id": "store_final_report",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },

        # State -> Store Final Report
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "store_final_report",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },

        # Store Final Report -> Output Node
        {
            "src_node_id": "store_final_report",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "report_storage_path"}
            ]
        },

        # State -> Output Node
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "processed_entity_username"}
            ]
        }
    ],

    # --- Define Start and End ---
    "input_node_id": "input_node",
    "output_node_id": "output_node",

    # --- State Reducers ---
    "metadata": {
        "$graph_state": {
            "reducer": {
                "validation_results_batches": "collect_values",
                "entity_username": "replace",
                "blog_content_analysis": "replace",
                "competitor_content_analysis_docs": "replace",
                "content_gaps_analysis": "replace",
                "merged_data": "replace",
                "market_opportunity_analysis": "replace"
            }
        }
    }
}

# --- Test Execution Logic ---

logger = logging.getLogger(__name__)

# Example Input
TEST_INPUTS = {
    "entity_username": "test_company"
}

async def validate_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """Custom validation function for the workflow outputs."""
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating Section 4 Content Diagnostics workflow outputs...")
    
    assert 'report_storage_path' in outputs, "Validation Failed: 'report_storage_path' key missing."
    assert 'processed_entity_username' in outputs, "Validation Failed: 'processed_entity_username' key missing."
    assert outputs['processed_entity_username'] == TEST_INPUTS['entity_username'], "Validation Failed: Entity name mismatch."
    assert isinstance(outputs.get('report_storage_path'), list), "Validation Failed: report_storage_path should be a list."
    assert len(outputs.get('report_storage_path', [])) > 0, "Validation Failed: report_storage_path is empty."
    
    logger.info(f"   Storage path: {outputs.get('report_storage_path')}")
    logger.info("✓ Output structure and content validation passed.")
    return True

async def main_test_section4_content_diagnostics():
    test_name = "Section 4 Content Diagnostics Workflow Test"
    print(f"--- Starting {test_name} --- ")

    CREATE_FAKE_DATA = True
    entity_username = TEST_INPUTS["entity_username"]
    
    # Define setup and cleanup documents
    setup_docs: List[SetupDocInfo] = []
    cleanup_docs: List[CleanupDocInfo] = []

    if CREATE_FAKE_DATA:
        # Create fake blog content analysis data
        blog_analysis_namespace = BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=entity_username)
        fake_blog_content_analysis = {
            "content_themes": ["AI and Machine Learning", "Cloud Computing", "Cybersecurity"],
            "top_performing_posts": [
                {
                    "title": "Getting Started with AI in Business",
                    "engagement_rate": 0.045,
                    "views": 15000
                }
            ],
            "content_gaps": ["Advanced AI Implementation", "AI Ethics in Business"],
            "target_audience": "Technology leaders and business executives"
        }

        # Create fake competitor content analysis data
        competitor_namespace = BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=entity_username)
        fake_competitor_analysis = [
            {
                "competitor_name": "TechCorp",
                "content_themes": ["AI Implementation", "Machine Learning", "Data Science"],
                "top_topics": ["AI ROI", "ML Model Deployment", "Data Strategy"],
                "content_strengths": ["Technical depth", "Case studies", "Implementation guides"]
            },
            {
                "competitor_name": "DataFlow",
                "content_themes": ["Big Data", "Analytics", "Business Intelligence"],
                "top_topics": ["Data Pipeline Design", "Analytics Strategy", "BI Tools"],
                "content_strengths": ["Practical tutorials", "Tool comparisons", "Industry insights"]
            }
        ]

        setup_docs = [
            {
                'namespace': blog_analysis_namespace,
                'docname': BLOG_CONTENT_ANALYSIS_DOCNAME,
                'is_versioned': BLOG_CONTENT_ANALYSIS_IS_VERSIONED,
                'initial_data': fake_blog_content_analysis,
                'is_shared': False,
                'is_system_entity': False,
            },
            {
                'namespace': competitor_namespace,
                'docname': f"{BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME}_techcorp",
                'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
                'initial_data': fake_competitor_analysis[0],
                'is_shared': False,
                'is_system_entity': False,
            },
            {
                'namespace': competitor_namespace,
                'docname': f"{BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME}_dataflow",
                'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
                'initial_data': fake_competitor_analysis[1],
                'is_shared': False,
                'is_system_entity': False,
            }
        ]

        # Define cleanup documents
        report_namespace = BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE.format(item=entity_username)
        cleanup_docs = [
            {
                'namespace': blog_analysis_namespace,
                'docname': BLOG_CONTENT_ANALYSIS_DOCNAME,
                'is_versioned': BLOG_CONTENT_ANALYSIS_IS_VERSIONED,
                'is_shared': False
            },
            {
                'namespace': competitor_namespace,
                'docname': f"{BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME}_techcorp",
                'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
                'is_shared': False
            },
            {
                'namespace': competitor_namespace,
                'docname': f"{BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME}_dataflow",
                'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
                'is_shared': False
            },
            {
                'namespace': report_namespace,
                'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME,
                'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION4_IS_VERSIONED,
                'is_shared': False
            }
        ]

    # Execute test
    print("\n--- Running Workflow Test ---")
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=TEST_INPUTS,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=setup_docs if CREATE_FAKE_DATA else [],
        cleanup_docs=cleanup_docs if CREATE_FAKE_DATA else [],
        validate_output_func=validate_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=1800  # Allow time for multiple LLM calls and Reddit research
    )

    if 'final_run_status_obj' in locals():
        print(f"Final Status: {final_run_status_obj.status}")
        if final_run_outputs:
            print(f"Final Outputs: {final_run_outputs}")
        if final_run_status_obj.status != WorkflowRunStatus.COMPLETED:
            print(f"Error Message: {final_run_status_obj.error_message}")

if __name__ == "__main__":
    print("="*50)
    print("Section 4 Content Diagnostics Workflow")
    print("="*50)
    logging.basicConfig(level=logging.INFO)
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("Async event loop already running. Scheduling task...")
        loop.create_task(main_test_section4_content_diagnostics())
    else:
        print("Starting new async event loop...")
        asyncio.run(main_test_section4_content_diagnostics())
