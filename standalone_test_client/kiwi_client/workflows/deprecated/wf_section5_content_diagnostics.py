"""
Section 5 Content Diagnostics Workflow - Competitive Intelligence Analysis

This workflow combines multiple data sources to generate comprehensive competitive intelligence:
1. Loads company AI visibility data
2. Loads company content analysis data  
3. Loads competitor AI visibility data (multiple documents)
4. Loads competitor content analysis data (multiple documents)
5. Analyzes all data sources using LLM to generate structured competitive insights

The workflow generates insights including:
- Content positioning maps for competitors
- SEO competitive gaps analysis
- AI visibility comparisons
- Competitive vulnerabilities identification
- Market share analysis

Input: Document configurations for the 4 data sources
Output: Structured competitive intelligence analysis
"""

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
    # Company AI Visibility
    BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_AI_VISIBILITY_TEST_IS_VERSIONED,
    
    # Company Content Analysis
    BLOG_CONTENT_ANALYSIS_DOCNAME,
    BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_ANALYSIS_IS_VERSIONED,
    
    # Competitor AI Visibility
    BLOG_COMPETITOR_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_COMPETITOR_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
    
    # Competitor Content Analysis
    BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME,
    BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
    
    # Section 5 Diagnostic Report
    BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION5_IS_VERSIONED,
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.section5_content_diagnostics import (
    GENERATION_SCHEMA,
    USER_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE,
    USER_PROMPT_TEMPLATE_VARIABLES,
    USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS,
    SYSTEM_PROMPT_TEMPLATE_VARIABLES,
    SYSTEM_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS,
)

# --- Workflow Configuration Constants ---

# LLM Configuration
LLM_PROVIDER = "openai"
GENERATION_MODEL = "gpt-4.1"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 6000

# Use the imported schema directly
GENERATION_SCHEMA_JSON = GENERATION_SCHEMA

# Storage Configuration - Using correct constants
# SECTION5_ANALYSIS_DOCNAME = "section5_content_diagnostics_analysis"
# SECTION5_ANALYSIS_NAMESPACE_TEMPLATE = "blog_content_diagnostics_{item}"

### INPUTS ###
INPUT_FIELDS = {
    "company_ai_visibility_doc_config": {
        "type": "list",
        "required": True,
        "description": "Document configuration for company AI visibility data"
    },
    "company_content_analysis_doc_config": {
        "type": "list",
        "required": True,
        "description": "Document configuration for company content analysis data"
    },
    "competitor_ai_visibility_namespace": {
        "type": "str",
        "required": True,
        "description": "Namespace for competitor AI visibility documents"
    },
    "competitor_content_analysis_namespace": {
        "type": "str",
        "required": True,
        "description": "Namespace for competitor content analysis documents"
    },
    "company_name": { 
        "type": "str", 
        "required": True, 
        "description": "Name of the company for competitive intelligence analysis"
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

        # --- 2. Load Company AI Visibility ---
        "load_company_ai_visibility": {
            "node_id": "load_company_ai_visibility",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "company_ai_visibility_doc_config",
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 3. Load Company Content Analysis ---
        "load_company_content_analysis": {
            "node_id": "load_company_content_analysis",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "company_content_analysis_doc_config",
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 4. Load Multiple Competitor AI Visibility Documents ---
        "load_competitor_ai_visibility": {
            "node_id": "load_competitor_ai_visibility",
            "node_name": "load_multiple_customer_data",
            "node_config": {
                "namespace_pattern": "{item}",
                "namespace_pattern_input_path": "competitor_ai_visibility_namespace",
                "include_shared": False,
                "include_user_specific": True,
                "include_system_entities": False,
                "limit": 50,
                "sort_by": "created_at",
                "sort_order": "desc",
                "output_field_name": "competitor_ai_visibility_list",
                "global_version_config": None,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 5. Load Multiple Competitor Content Analysis Documents ---
        "load_competitor_content_analysis": {
            "node_id": "load_competitor_content_analysis",
            "node_name": "load_multiple_customer_data",
            "node_config": {
                "namespace_pattern": "{item}",
                "namespace_pattern_input_path": "competitor_content_analysis_namespace",
                "include_shared": False,
                "include_user_specific": True,
                "include_system_entities": False,
                "limit": 50,
                "sort_by": "created_at",
                "sort_order": "desc",
                "output_field_name": "competitor_content_analysis_list",
                "global_version_config": None,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 6. Construct Prompt ---
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

        # --- 7. Generate Competitive Intelligence Analysis ---
        "generate_competitive_intelligence": {
            "node_id": "generate_competitive_intelligence",
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

        # --- 8. Store Analysis Results ---
        "store_analysis": {
            "node_id": "store_analysis",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": BLOG_CONTENT_DIAGNOSTIC_SECTION5_IS_VERSIONED, "operation": "upsert"},
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },

        # --- 9. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {
                "dynamic_input_schema": {
                    "fields": {
                        "competitive_intelligence_analysis": {
                            "type": "dict",
                            "required": True,
                            "description": "The structured competitive intelligence analysis"
                        },
                        "storage_paths": {
                            "type": "list",
                            "required": True,
                            "description": "Paths where the analysis was stored"
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
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        # Input -> Load nodes
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_company_ai_visibility", 
            "mappings": [
                { "src_field": "company_ai_visibility_doc_config", "dst_field": "company_ai_visibility_doc_config" },
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_company_content_analysis", 
            "mappings": [
                { "src_field": "company_content_analysis_doc_config", "dst_field": "company_content_analysis_doc_config" },
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_competitor_ai_visibility", 
            "mappings": [
                { "src_field": "competitor_ai_visibility_namespace", "dst_field": "competitor_ai_visibility_namespace" },
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_competitor_content_analysis", 
            "mappings": [
                { "src_field": "competitor_content_analysis_namespace", "dst_field": "competitor_content_analysis_namespace" },
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        # Load nodes -> State
        { 
            "src_node_id": "load_company_ai_visibility", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "company_ai_visibility", "dst_field": "company_ai_visibility" }
            ]
        },
        
        { 
            "src_node_id": "load_company_content_analysis", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "company_content_analysis", "dst_field": "company_content_analysis" }
            ]
        },
        
        { 
            "src_node_id": "load_competitor_ai_visibility", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "competitor_ai_visibility_list", "dst_field": "competitor_ai_visibility" }
            ]
        },
        
        { 
            "src_node_id": "load_competitor_content_analysis", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "competitor_content_analysis_list", "dst_field": "competitor_content_analysis" }
            ]
        },

        # Load nodes -> Construct Prompt (Direct connections)
        { 
            "src_node_id": "load_company_ai_visibility", 
            "dst_node_id": "construct_prompt"
        },
        
        { 
            "src_node_id": "load_company_content_analysis", 
            "dst_node_id": "construct_prompt"
        },
        
        { 
            "src_node_id": "load_competitor_ai_visibility", 
            "dst_node_id": "construct_prompt"
        },
        
        { 
            "src_node_id": "load_competitor_content_analysis", 
            "dst_node_id": "construct_prompt"
        },
        
        # State -> Construct Prompt
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_prompt", 
            "mappings": [
                { "src_field": "company_ai_visibility", "dst_field": "company_ai_visibility" },
                { "src_field": "company_content_analysis", "dst_field": "company_content_analysis" },
                { "src_field": "competitor_ai_visibility", "dst_field": "competitor_ai_visibility" },
                { "src_field": "competitor_content_analysis", "dst_field": "competitor_content_analysis" }
            ]
        },
        
        # Construct Prompt -> Generate Analysis
        { 
            "src_node_id": "construct_prompt", 
            "dst_node_id": "generate_competitive_intelligence", 
            "mappings": [
                { "src_field": "user_prompt", "dst_field": "user_prompt" },
                { "src_field": "system_prompt", "dst_field": "system_prompt" }
            ]
        },
        
        # Generate Analysis -> Store
        { 
            "src_node_id": "generate_competitive_intelligence", 
            "dst_node_id": "store_analysis", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "structured_output" }
            ]
        },
        
        # State -> Store
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "store_analysis", 
            "mappings": [
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        # Generate Analysis -> Output
        { 
            "src_node_id": "generate_competitive_intelligence", 
            "dst_node_id": "output_node", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "competitive_intelligence_analysis" }
            ]
        },
        
        # Store -> Output
        { 
            "src_node_id": "store_analysis", 
            "dst_node_id": "output_node", 
            "mappings": [
                { "src_field": "paths_processed", "dst_field": "storage_paths" }
            ]
        }
    ],

    "input_node_id": "input_node",
    "output_node_id": "output_node"
}

# --- Test Execution Logic ---
async def main_test_section5_content_diagnostics_workflow():
    """
    Test for Section 5 Content Diagnostics Workflow - Competitive Intelligence Analysis.
    """
    test_name = "Section 5 Content Diagnostics Workflow Test"
    print(f"--- Starting {test_name} ---")

    # Example Document Configurations
    company_name = "test_company"
    
    company_ai_visibility_doc_config = [
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                "input_namespace_field": "company_name",
                "static_docname": BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
            },
            "output_field_name": "company_ai_visibility"
        }
    ]
    
    company_content_analysis_doc_config = [
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
                "input_namespace_field": "company_name",
                "static_docname": BLOG_CONTENT_ANALYSIS_DOCNAME,
            },
            "output_field_name": "company_content_analysis"
        }
    ]
    
    # For multiple competitor documents, use namespace approach
    competitor_ai_visibility_namespace = BLOG_COMPETITOR_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name)
    competitor_content_analysis_namespace = BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=company_name)
    
    test_inputs = {
        "company_ai_visibility_doc_config": company_ai_visibility_doc_config,
        "company_content_analysis_doc_config": company_content_analysis_doc_config,
        "competitor_ai_visibility_namespace": competitor_ai_visibility_namespace,
        "competitor_content_analysis_namespace": competitor_content_analysis_namespace,
        "company_name": company_name
    }

    # Define setup documents with sample data
    setup_docs: List[SetupDocInfo] = [
        # Company AI Visibility
        {
            'namespace': BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
            'initial_data': {
                "ai_visibility_score": 7.5,
                "platform_presence": {
                    "perplexity": 8.2,
                    "chatgpt": 6.8
                },
                "citation_opportunities": ["Content marketing", "Digital strategy"],
                "visibility_gaps": ["AI automation", "Machine learning tools"]
            },
            'is_versioned': BLOG_COMPANY_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Company Content Analysis
        {
            'namespace': BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_CONTENT_ANALYSIS_DOCNAME,
            'initial_data': {
                "content_velocity": 12,
                "content_themes": ["Digital marketing", "Content strategy", "SEO"],
                "seo_performance": 8.1,
                "engagement_metrics": {
                    "avg_time_on_page": "3:45",
                    "bounce_rate": 0.35
                }
            },
            'is_versioned': BLOG_CONTENT_ANALYSIS_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Multiple Competitor AI Visibility Documents
        {
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor1_ai_visibility",
            'initial_data': {
                "competitor_name": "competitor1",
                "ai_visibility_score": 8.7,
                "platform_presence": {
                    "perplexity": 9.1,
                    "chatgpt": 8.3
                },
                "strengths": ["Thought leadership", "Technical content"],
                "weaknesses": ["Limited social presence"]
            },
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        {
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor2_ai_visibility",
            'initial_data': {
                "competitor_name": "competitor2",
                "ai_visibility_score": 7.3,
                "platform_presence": {
                    "perplexity": 7.8,
                    "chatgpt": 6.8
                },
                "strengths": ["Video content", "Community engagement"],
                "weaknesses": ["Technical depth"]
            },
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Multiple Competitor Content Analysis Documents
        {
            'namespace': competitor_content_analysis_namespace,
            'docname': "competitor1_content_analysis",
            'initial_data': {
                "competitor_name": "competitor1",
                "content_velocity": 18,
                "content_themes": ["AI automation", "Machine learning", "Data analytics"],
                "seo_performance": 9.2,
                "market_position": "leader"
            },
            'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        {
            'namespace': competitor_content_analysis_namespace,
            'docname': "competitor2_content_analysis",
            'initial_data': {
                "competitor_name": "competitor2",
                "content_velocity": 14,
                "content_themes": ["Digital transformation", "Cloud computing", "Cybersecurity"],
                "seo_performance": 8.5,
                "market_position": "challenger"
            },
            'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]

    # Define cleanup docs
    cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
            'is_versioned': BLOG_COMPANY_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_CONTENT_ANALYSIS_DOCNAME,
            'is_versioned': BLOG_CONTENT_ANALYSIS_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor1_ai_visibility",
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor2_ai_visibility",
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': competitor_content_analysis_namespace,
            'docname': "competitor1_content_analysis",
            'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': competitor_content_analysis_namespace,
            'docname': "competitor2_content_analysis",
            'is_versioned': BLOG_COMPETITOR_CONTENT_ANALYSIS_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION5_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION5_DOCNAME,
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION5_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        }
    ]

    # Output validation function
    async def validate_competitive_intelligence_output(outputs) -> bool:
        """
        Validates the output from the competitive intelligence analysis workflow.
        """
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        assert 'competitive_intelligence_analysis' in outputs, "Validation Failed: 'competitive_intelligence_analysis' missing."
        assert 'storage_paths' in outputs, "Validation Failed: 'storage_paths' missing."
        
        if 'competitive_intelligence_analysis' in outputs:
            analysis = outputs['competitive_intelligence_analysis']
            
            # Validate required fields
            assert 'content_positioning_map' in analysis, "Output missing 'content_positioning_map' field"
            assert 'seo_competitive_gaps' in analysis, "Output missing 'seo_competitive_gaps' field"
            assert 'ai_visibility_comparison' in analysis, "Output missing 'ai_visibility_comparison' field"
            assert 'competitive_vulnerabilities' in analysis, "Output missing 'competitive_vulnerabilities' field"
            assert 'market_share_analysis' in analysis, "Output missing 'market_share_analysis' field"
            
            # Validate data types
            assert isinstance(analysis['content_positioning_map'], list), "'content_positioning_map' should be a list"
            assert isinstance(analysis['seo_competitive_gaps'], list), "'seo_competitive_gaps' should be a list"
            assert isinstance(analysis['ai_visibility_comparison'], list), "'ai_visibility_comparison' should be a list"
            assert isinstance(analysis['competitive_vulnerabilities'], list), "'competitive_vulnerabilities' should be a list"
            assert isinstance(analysis['market_share_analysis'], list), "'market_share_analysis' should be a list"
            
            print(f"✓ Competitive intelligence analysis validated successfully")
            print(f"✓ Number of competitors analyzed: {len(analysis['content_positioning_map'])}")
            print(f"✓ Number of SEO gaps identified: {len(analysis['seo_competitive_gaps'])}")
            print(f"✓ Number of competitive vulnerabilities: {len(analysis['competitive_vulnerabilities'])}")
            print(f"✓ Analysis stored at: {outputs['storage_paths']}")
        
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
        validate_output_func=validate_competitive_intelligence_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )

    print(f"--- {test_name} Finished ---")
    if final_run_outputs and 'competitive_intelligence_analysis' in final_run_outputs:
        analysis = final_run_outputs['competitive_intelligence_analysis']
        print("\nCompetitive Intelligence Analysis:")
        print(f"Content Positioning Map: {len(analysis['content_positioning_map'])} competitors")
        print(f"SEO Competitive Gaps: {analysis['seo_competitive_gaps']}")
        print(f"AI Visibility Comparison: {analysis['ai_visibility_comparison']}")
        print(f"Market Share Analysis: {analysis['market_share_analysis']}")
        print(f"Stored at: {final_run_outputs['storage_paths']}")

if __name__ == "__main__":
    try:
        asyncio.run(main_test_section5_content_diagnostics_workflow())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")
