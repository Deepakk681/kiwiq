"""
Competitor Content Analysis Workflow

This workflow:
1. Loads company document with competitor information
2. Uses map_list_router_node to distribute competitors for parallel analysis
3. Analyzes each competitor's content strategy using Perplexity LLM
4. Saves analysis results to shared documents with proper naming conventions

Document Storage Convention:
- Document Name: blog_competitor_content_analysis_{competitor_name}
- Namespace: blog_competitive_intelligence_{company_name}
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME,
    BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_VERSIONED,
)

# Import LLM inputs
from kiwi_client.workflows.active.content_diagnostics.competitor_content_analysis_sandbox.wf_llm_inputs import (
    # LLM Configuration
    PERPLEXITY_PROVIDER,
    PERPLEXITY_MODEL,
    PERPLEXITY_TEMPERATURE,
    PERPLEXITY_MAX_TOKENS,
    COMPETITOR_CONTENT_ANALYSIS_SYSTEM_PROMPT,
    COMPETITOR_CONTENT_ANALYSIS_USER_PROMPT_TEMPLATE,
    COMPETITOR_CONTENT_ANALYSIS_OUTPUT_SCHEMA,
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
                        "description": "Name of the company for document operations"
                    }
                }
            }
        },
        
        # 2. Load Company Document
        "load_company_doc": {
            "node_id": "load_company_doc",
            "node_name": "load_customer_data",
            "node_config": {
                # Use dynamic configuration from input
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
        
                 # 3. Distribute Competitors for Parallel Processing
         "distribute_competitors": {
             "node_id": "distribute_competitors",
             "node_name": "map_list_router_node",
             "node_config": {
                 "choices": ["construct_analysis_prompt"],
                 "map_targets": [
                     {
                         "source_path": "company_doc.competitors",
                         "destinations": ["construct_analysis_prompt"],
                         "batch_size": 1,
                         "batch_field_name": "competitor_item"
                     }
                 ]
             }
         },
         
         # 4. Construct Analysis Prompt
         "construct_analysis_prompt": {
             "node_id": "construct_analysis_prompt",
             "node_name": "prompt_constructor",
             "private_input_mode": True,
             "output_private_output_to_central_state": True,
             "private_output_mode": True,
             "node_config": {
                 "prompt_templates": {
                     "competitor_analysis_user_prompt": {
                         "id": "competitor_analysis_user_prompt",
                         "template": COMPETITOR_CONTENT_ANALYSIS_USER_PROMPT_TEMPLATE,
                         "variables": {
                             "competitor_name": None,
                             "competitor_website": None
                         },
                         "construct_options": {
                             "competitor_name": "competitor_item.name",
                             "competitor_website": "competitor_item.website_url"
                         }
                     },
                     "competitor_analysis_system_prompt": {
                         "id": "competitor_analysis_system_prompt",
                         "template": COMPETITOR_CONTENT_ANALYSIS_SYSTEM_PROMPT,
                         "variables": {}
                     }
                 }
             }
         },
         # 5. Analyze Competitor Content Using Perplexity
         "analyze_competitor_content": {
             "node_id": "analyze_competitor_content",
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
                 "output_schema": {
                     "schema_definition": COMPETITOR_CONTENT_ANALYSIS_OUTPUT_SCHEMA,
                     "convert_loaded_schema_to_pydantic": False
                 }
             }
         },
        
        # 7. Route Structured Data for Saving
        "route_for_saving": {
            "node_id": "route_for_saving",
            "enable_node_fan_in": True,
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["save_competitor_analysis"],
                "map_targets": [
                    {
                        "source_path": "all_competitor_analysis_results",
                        "destinations": ["save_competitor_analysis"],
                        "batch_size": 1,
                        "batch_field_name": "competitor_data"
                    }
                ]
            }
        },
        
        # 8. Save Competitor Analysis to Shared Documents
        "save_competitor_analysis": {
            "node_id": "save_competitor_analysis",
            "node_name": "store_customer_data",
            "node_config": {
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "competitor_data",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_COMPETITOR_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_COMPETITOR_CONTENT_ANALYSIS_DOCNAME,
                                "input_docname_field": "competitor_data.name"
                            }
                        },
                        "versioning": {
                            "is_versioned": False,
                            "operation": "upsert"
                        },
                        "generate_uuid": True
                    }
                ]
            },
            "private_input_mode": True,
            "output_private_output_to_central_state": True
        },
        
                 # 6. Output Node
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "enable_node_fan_in": True,
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
        
        # Company Doc -> Distribute Competitors
        {
            "src_node_id": "load_company_doc",
            "dst_node_id": "distribute_competitors",
            "mappings": [
                
            ]
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "distribute_competitors",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"}
            ]
        },
                # Distribute Competitors -> Construct Analysis Prompt
        {
            "src_node_id": "distribute_competitors",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": []
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": [
                {"src_field": "company_doc", "dst_field": "company_doc"}
            ]
        },
        
        # Construct Analysis Prompt -> Analyze Competitor Content
        {
            "src_node_id": "construct_analysis_prompt",
            "dst_node_id": "analyze_competitor_content",
            "mappings": [
                {"src_field": "competitor_analysis_user_prompt", "dst_field": "user_prompt"},
                {"src_field": "competitor_analysis_system_prompt", "dst_field": "system_prompt"}
            ]
        },

        # Analyze Competitor Content -> Merge analysis with competitor metadata
        {
            "src_node_id": "analyze_competitor_content",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "all_competitor_analysis_results"}
            ]
        },

        # Merge analysis with metadata -> Route for Saving
        {
            "src_node_id": "analyze_competitor_content",
            "dst_node_id": "route_for_saving",
            "mappings": [
            ]
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "route_for_saving",
            "mappings": [
                {"src_field": "all_competitor_analysis_results", "dst_field": "all_competitor_analysis_results"}
            ]
        },
        # Route for Saving -> Save Analysis
        {
            "src_node_id": "route_for_saving",
            "dst_node_id": "save_competitor_analysis",
            "mappings": []
        },
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_competitor_analysis",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"}
            ]
        },
        
        # Save Analysis -> Output
        {
            "src_node_id": "save_competitor_analysis",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "passthrough_data", "dst_field": "competitor_analysis_passthrough_data"}
            ]
        },

        {
            "src_node_id": "save_competitor_analysis",
            "dst_node_id": "output_node",
            "mappings": []
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "competitor_analysis_passthrough_data", "dst_field": "competitor_analysis_passthrough_data"}
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "company_doc": "replace",
                "all_competitor_analysis_results": "collect_values",
                "competitor_analysis_passthrough_data": "collect_values"
            }
        }
    }
}