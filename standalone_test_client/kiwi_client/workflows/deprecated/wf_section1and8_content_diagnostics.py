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

from kiwi_client.workflows_for_blog_teammate.document_models.customer_docs import (
    # Section 2-7 document configurations
    BLOG_CONTENT_DIAGNOSTIC_SECTION2_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION2_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION2_IS_VERSIONED,
    BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION3_IS_VERSIONED,
    BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION4_IS_VERSIONED,
    BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION5_IS_VERSIONED,
    BLOG_CONTENT_DIAGNOSTIC_SECTION6_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION6_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION6_IS_VERSIONED,
    BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION7_IS_VERSIONED,
    # Section 1 and 8 output document
    BLOG_CONTENT_DIAGNOSTIC_SECTION1_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION1_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION1_IS_VERSIONED,
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.section1and8_content_diagnostics import (
    GENERATION_SCHEMA,
    USER_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE,
)

# --- Workflow Configuration Constants ---

# LLM Configuration
LLM_PROVIDER = "openai"
GENERATION_MODEL = "gpt-4.1"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 6000

# Use the imported schema directly
GENERATION_SCHEMA_JSON = GENERATION_SCHEMA

# Prompt template variables and construct options
USER_PROMPT_TEMPLATE_VARIABLES = {
    "section2_data": None,
    "section3_data": None,
    "section4_data": None,
    "section5_data": None,
    "section6_data": None,
    "section7_data": None
}

USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {
    "section2_data": "section2_data",
    "section3_data": "section3_data",
    "section4_data": "section4_data",
    "section5_data": "section5_data",
    "section6_data": "section6_data",
    "section7_data": "section7_data"
}

SYSTEM_PROMPT_TEMPLATE_VARIABLES = {
    "schema": GENERATION_SCHEMA_JSON
}

SYSTEM_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {}

### INPUTS ###
INPUT_FIELDS = {
    "customer_context_doc_configs": {
        "type": "list",
        "required": True,
        "description": "List of document identifiers (namespace/docname pairs) for customer context like DNA, strategy docs."
    },
    "entity_username": {
        "type": "str",
        "required": True,
        "description": "Name of the entity to analyze content diagnostics for."
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

        # --- 2. Load All Section Data (Single Node) ---
        "load_all_context_docs": {
            "node_id": "load_all_context_docs",
            "node_name": "load_customer_data",
            "node_config": {
                # Configure to load multiple documents based on the input list
                "load_configs_input_path": "customer_context_doc_configs", # Use the list from input node
                # Global defaults (can be overridden if needed per doc type via input structure)
                "global_is_shared": False,
                "global_is_system_entity": False,
                # "global_version_config": {"version": "default"},
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 3. Construct Prompt ---
        "construct_prompt": {
            "node_id": "construct_prompt",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,
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

        # --- 4. Generate Diagnostic Analysis ---
        "generate_diagnostic": {
            "node_id": "generate_diagnostic",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": GENERATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": GENERATION_SCHEMA_JSON,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 5. Store Results ---
        "store_results": {
            "node_id": "store_results",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": BLOG_CONTENT_DIAGNOSTIC_SECTION1_IS_VERSIONED, "operation": "upsert"},
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "diagnostic_results",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION1_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION1_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },

        # --- 6. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {
                "dynamic_input_schema": {
                    "fields": {
                        "passthrough_data": {
                            "type": "dict",
                            "required": True,
                            "description": "The complete diagnostic analysis results"
                        }
                    }
                }
            }
        },
    },

    "edges": [
        # Input -> State
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "customer_context_doc_configs", "dst_field": "customer_context_doc_configs" },
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },
        
        # Input -> Load All Section Data
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_all_context_docs", 
            "mappings": [
                { "src_field": "customer_context_doc_configs", "dst_field": "customer_context_doc_configs" },
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },

        # Load All Section Data -> State
        { 
            "src_node_id": "load_all_context_docs", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "section2_data", "dst_field": "section2_data" },
                { "src_field": "section3_data", "dst_field": "section3_data" },
                { "src_field": "section4_data", "dst_field": "section4_data" },
                { "src_field": "section5_data", "dst_field": "section5_data" },
                { "src_field": "section6_data", "dst_field": "section6_data" },
                { "src_field": "section7_data", "dst_field": "section7_data" }
            ]
        },

        # Load All Section Data -> Construct Prompt
        { 
            "src_node_id": "load_all_context_docs", 
            "dst_node_id": "construct_prompt",
            "mappings": []
        },

        # State -> Construct Prompt
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_prompt", 
            "mappings": [
                { "src_field": "section2_data", "dst_field": "section2_data" },
                { "src_field": "section3_data", "dst_field": "section3_data" },
                { "src_field": "section4_data", "dst_field": "section4_data" },
                { "src_field": "section5_data", "dst_field": "section5_data" },
                { "src_field": "section6_data", "dst_field": "section6_data" },
                { "src_field": "section7_data", "dst_field": "section7_data" }
            ]
        },
        
        # Construct Prompt -> Generate Diagnostic
        { 
            "src_node_id": "construct_prompt", 
            "dst_node_id": "generate_diagnostic", 
            "mappings": [
                { "src_field": "user_prompt", "dst_field": "user_prompt" },
                { "src_field": "system_prompt", "dst_field": "system_prompt" }
            ]
        },
        
        # Generate Diagnostic -> Store Results
        { 
            "src_node_id": "generate_diagnostic", 
            "dst_node_id": "store_results", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "diagnostic_results" }
            ]
        },

        # Store Results -> Output
        { 
            "src_node_id": "store_results", 
            "dst_node_id": "output_node", 
            "mappings": [
                { "src_field": "passthrough_data", "dst_field": "passthrough_data" }
            ]
        }
    ],

    "input_node_id": "input_node",
    "output_node_id": "output_node"
}

# --- Test Execution Logic ---
async def main_test_section1and8_diagnostics_workflow():
    """
    Test for Section 1 and 8 Content Diagnostics Workflow.
    """
    test_name = "Section 1 and 8 Content Diagnostics Workflow Test"
    print(f"--- Starting {test_name} --- ")

    entity_username = "test_company"
    
    test_inputs = {
        "customer_context_doc_configs": [
            {
                "filename_config": {
                    "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION2_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION2_DOCNAME,
                },
                "output_field_name": "section2_data"
            },
            {
                "filename_config": {
                    "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME,
                },
                "output_field_name": "section3_data"
            },
            {
                "filename_config": {
                    "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME,
                },
                "output_field_name": "section4_data"
            },
            {
                "filename_config": {
                    "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME,
                },
                "output_field_name": "section5_data"
            },
            {
                "filename_config": {
                    "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION6_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION6_DOCNAME,
                },
                "output_field_name": "section6_data"
            },
            {
                "filename_config": {
                    "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME,
                },
                "output_field_name": "section7_data"
            }
        ],
        "entity_username": entity_username
    }

    # Define setup documents for sections 2-7
    setup_docs: List[SetupDocInfo] = [
        # Section 2 - Content Analysis
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION2_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION2_DOCNAME,
            'initial_data': {
                "content_audit": {
                    "total_posts": 45,
                    "avg_word_count": 1200,
                    "top_performing_topics": ["AI", "Digital Marketing", "Leadership"],
                    "engagement_metrics": {
                        "avg_views": 2500,
                        "avg_shares": 45,
                        "avg_comments": 12
                    }
                }
            }, 
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION2_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        # Section 3 - Digital Authority
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME,
            'initial_data': {
                "executive_thought_leadership_score": 6.5,
                "linkedin_metrics": {
                    "follower_count": 8500,
                    "posting_frequency": "3 posts/week",
                    "engagement_rate": 4.2,
                    "content_themes": ["Leadership", "Innovation", "Strategy"],
                    "best_performing_post": "The Future of AI in Business"
                }
            }, 
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION3_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        # Section 4 - SEO Performance
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME,
            'initial_data': {
                "seo_metrics": {
                    "organic_traffic": 15000,
                    "ranking_keywords": 125,
                    "avg_position": 8.5,
                    "click_through_rate": 3.2
                },
                "technical_seo": {
                    "page_speed_score": 75,
                    "mobile_friendly": True,
                    "ssl_secure": True
                }
            }, 
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION4_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        # Section 5 - AI Visibility
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME,
            'initial_data': {
                "ai_visibility_score": 7.2,
                "ai_citations": 23,
                "ai_queries_performance": {
                    "total_queries": 150,
                    "positive_results": 89,
                    "neutral_results": 45,
                    "negative_results": 16
                }
            }, 
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION5_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        # Section 6 - Competitive Analysis
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION6_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION6_DOCNAME,
            'initial_data': {
                "competitor_analysis": {
                    "main_competitors": ["Competitor A", "Competitor B", "Competitor C"],
                    "content_gaps": ["AI Ethics", "Digital Transformation", "Remote Work"],
                    "competitive_advantages": ["Thought Leadership", "Technical Expertise"]
                }
            }, 
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION6_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        # Section 7 - Content Strategy
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME,
            'initial_data': {
                "content_strategy": {
                    "target_audience": ["C-level executives", "Marketing professionals", "Tech leaders"],
                    "content_pillars": ["Leadership", "Innovation", "Digital Strategy"],
                    "publishing_frequency": "Weekly",
                    "content_distribution": ["LinkedIn", "Company Blog", "Industry Publications"]
                }
            }, 
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION7_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]

    # Define cleanup docs
    cleanup_docs: List[CleanupDocInfo] = [
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION2_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION2_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION2_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION3_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION4_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION4_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION4_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION5_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION6_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION6_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION6_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION7_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION1_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION1_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION1_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
    ]

    # Output validation function
    async def validate_diagnostic_output(outputs) -> bool:
        """
        Validates the output from the section 1 and 8 diagnostics workflow.
        """
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        
        # Check for passthrough_data first
        assert 'passthrough_data' in outputs, "Validation Failed: 'passthrough_data' missing."
        
        passthrough_data = outputs['passthrough_data']
        assert 'diagnostic_results' in passthrough_data, "Validation Failed: 'diagnostic_results' missing from passthrough_data."
        
        results = passthrough_data['diagnostic_results']
        assert 'executive_summary' in results, "Output missing 'executive_summary' field"
        assert 'immediate_opportunities' in results, "Output missing 'immediate_opportunities' field"
        
        # Validate executive summary
        exec_summary = results['executive_summary']
        assert 'current_position' in exec_summary, "Executive summary missing 'current_position'"
        assert 'biggest_opportunity' in exec_summary, "Executive summary missing 'biggest_opportunity'"
        assert 'critical_risk' in exec_summary, "Executive summary missing 'critical_risk'"
        assert 'overall_diagnostic_score' in exec_summary, "Executive summary missing 'overall_diagnostic_score'"
        
        # Validate immediate opportunities
        opportunities = results['immediate_opportunities']
        assert 'top_content_opportunities' in opportunities, "Opportunities missing 'top_content_opportunities'"
        assert 'seo_quick_wins' in opportunities, "Opportunities missing 'seo_quick_wins'"
        assert 'executive_visibility_actions' in opportunities, "Opportunities missing 'executive_visibility_actions'"
        assert 'ai_optimization_priorities' in opportunities, "Opportunities missing 'ai_optimization_priorities'"
        
        print(f"✓ Diagnostic results validated successfully")
        print(f"✓ Executive summary score: {exec_summary['overall_diagnostic_score']}")
        print(f"✓ Content opportunities: {len(opportunities['top_content_opportunities'])}")
        print(f"✓ SEO quick wins: {len(opportunities['seo_quick_wins'])}")
        print(f"✓ Executive visibility actions: {len(opportunities['executive_visibility_actions'])}")
        print(f"✓ AI optimization priorities: {len(opportunities['ai_optimization_priorities'])}")
        
        return True

    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        hitl_inputs=[],
        setup_docs=setup_docs,
        cleanup_docs_created_by_setup=True,
        cleanup_docs=cleanup_docs,
        validate_output_func=validate_diagnostic_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )

    print(f"--- {test_name} Finished --- ")
    if final_run_outputs and 'passthrough_data' in final_run_outputs and 'diagnostic_results' in final_run_outputs['passthrough_data']:
        results = final_run_outputs['passthrough_data']['diagnostic_results']
        print("\nExecutive Summary:")
        exec_summary = results['executive_summary']
        print(f"Current Position: {exec_summary['current_position']}")
        print(f"Biggest Opportunity: {exec_summary['biggest_opportunity']}")
        print(f"Critical Risk: {exec_summary['critical_risk']}")
        print(f"Overall Score: {exec_summary['overall_diagnostic_score']}/10")
        
        print("\nTop Content Opportunities:")
        for i, opp in enumerate(results['immediate_opportunities']['top_content_opportunities'][:3], 1):
            print(f"{i}. {opp['title']} ({opp['content_type']})")

if __name__ == "__main__":
    try:
        asyncio.run(main_test_section1and8_diagnostics_workflow())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")
