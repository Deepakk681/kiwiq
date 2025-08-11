"""
Content Gap Analysis Workflow

This workflow analyzes a company's current content strategy against industry best practices
and business goals to identify gaps and provide strategic recommendations.

Workflow Steps:
1. Input: company name/identifier, business goals
2. Load three documents: blog content analysis, deep dive report, company data
3. Construct prompt with all data and business goals
4. Analyze with LLM to identify gaps and generate recommendations
5. Store analysis results
6. Output analysis path and summary

"""

from kiwi_client.workflows_for_blog_teammate.document_models.customer_docs import (
    BLOG_CONTENT_ANALYSIS_DOCNAME,
    BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    DEEP_DIVE_REPORT_DOCNAME,
    DEEP_DIVE_REPORT_NAMESPACE_TEMPLATE,
    COMPANY_DOCUMENT_DOCNAME,
    COMPANY_DOCUMENT_NAMESPACE_TEMPLATE,
    CONTENT_GAP_ANALYSIS_DOCNAME,
    CONTENT_GAP_ANALYSIS_NAMESPACE_TEMPLATE,
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.user_content_gap_analysis import (
    CONTENT_GAP_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
    CONTENT_GAP_ANALYSIS_USER_PROMPT_TEMPLATE,
    CONTENT_GAP_ANALYSIS_SCHEMA,
)

import json
import asyncio
from typing import List, Optional, Dict, Any

# --- Workflow Constants ---
LLM_PROVIDER = "openai"
ANALYSIS_MODEL = "gpt-4o"  # Using GPT-4o for comprehensive analysis
LLM_TEMPERATURE = 0.3  # Slightly higher for more creative strategic thinking
LLM_MAX_TOKENS = 8000  # Large output for comprehensive analysis

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
              "company_name": { "type": "str", "required": True, "description": "Name of the company to analyze" }
          }
        }
    },

    # --- 2. Load Documents ---
    "load_documents": {
      "node_id": "load_documents",
      "node_name": "load_customer_data",
      "node_config": {
          "load_paths": [
              {
                  "filename_config": {
                      "input_namespace_field_pattern": BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE, 
                      "input_namespace_field": "company_name",
                      "static_docname": BLOG_CONTENT_ANALYSIS_DOCNAME,
                  },
                  "output_field_name": "blog_content_analysis_data"
              },
              {
                  "filename_config": {
                      "input_namespace_field_pattern": DEEP_DIVE_REPORT_NAMESPACE_TEMPLATE, 
                      "input_namespace_field": "company_name",
                      "static_docname": DEEP_DIVE_REPORT_DOCNAME,
                  },
                  "output_field_name": "deep_dive_report_data"
              },
              {
                  "filename_config": {
                      "input_namespace_field_pattern": COMPANY_DOCUMENT_NAMESPACE_TEMPLATE, 
                      "input_namespace_field": "company_name",
                      "static_docname": COMPANY_DOCUMENT_DOCNAME,
                  },
                  "output_field_name": "company_data"
              },
          ]
      },
        "global_is_shared": False,
        "global_is_system_entity": False,
        "global_schema_options": {"load_schema": False},
    },

    # --- 3. Construct Analysis Prompt ---
    "construct_gap_analysis_prompt": {
      "node_id": "construct_gap_analysis_prompt",
      "node_name": "prompt_constructor",
      "node_config": {
        "prompt_templates": {
          "gap_analysis_user_prompt": {
            "id": "gap_analysis_user_prompt",
            "template": CONTENT_GAP_ANALYSIS_USER_PROMPT_TEMPLATE,
            "variables": {
              "company_name": None,  # From input
              "company_data": None,  # From load_documents
              "blog_content_analysis": None,  # From load_documents
              "deep_dive_report": None,  # From load_documents
              "business_goals": None,  # From input or default
            },
            "construct_options": {
                "company_name": "company_name",
                "company_data": "company_data",
                "blog_content_analysis": "blog_content_analysis_data",
                "deep_dive_report": "deep_dive_report_data",
                "business_goals": "processed_business_goals",  # From transform_input output
            }
          },
          "gap_analysis_system_prompt": {
            "id": "gap_analysis_system_prompt",
            "template": CONTENT_GAP_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
            "variables": { "schema": json.dumps(CONTENT_GAP_ANALYSIS_SCHEMA, indent=2) },
            "construct_options": {}
          }
        }
      }
      # Input: company_name, company_data, blog_content_analysis_data, deep_dive_report_data, processed_business_goals
      # Output: gap_analysis_user_prompt, gap_analysis_system_prompt
    },

    # --- 4. Run Content Gap Analysis ---
    "analyze_content_gaps": {
        "node_id": "analyze_content_gaps",
        "node_name": "llm",
        "node_config": {
            "llm_config": {
              "model_spec": {"provider": LLM_PROVIDER, "model": ANALYSIS_MODEL},
              "temperature": LLM_TEMPERATURE,
              "max_tokens": LLM_MAX_TOKENS
            },
            "output_schema": {
                "schema_definition": CONTENT_GAP_ANALYSIS_SCHEMA,
                "convert_loaded_schema_to_pydantic": False
            }
        }
        # Input: gap_analysis_user_prompt, gap_analysis_system_prompt
        # Output: structured_output (ContentStrategyAnalysisSchema)
    },

    # --- 5. Store Analysis Results ---
    "store_gap_analysis": {
      "node_id": "store_gap_analysis",
      "node_name": "store_customer_data",
      "node_config": {
        "global_versioning": { "is_versioned": False, "operation": "upsert" },
        "global_is_shared": False,
        "store_configs": [
          {
            "input_field_path": "structured_output", # From analyze_content_gaps
            "target_path": {
              "filename_config": {
                "input_namespace_field_pattern": CONTENT_GAP_ANALYSIS_NAMESPACE_TEMPLATE, 
                "input_namespace_field": "company_name",
                "static_docname": CONTENT_GAP_ANALYSIS_DOCNAME,
              }
            }
          }
        ]
      }
    },

    # --- 7. Output Node ---
    "output_node": {
      "node_id": "output_node",
      "node_name": "output_node",
      "node_config": {},
      "dynamic_output_schema": {}
    }
  },

  # --- Edges Defining Data Flow ---
  "edges": [
    # --- Input & Setup ---
    { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "company_name", "dst_field": "company_name", "description": "Store company name globally" }      ]
    },

    # --- Input to Load Documents ---
    { "src_node_id": "input_node", "dst_node_id": "load_documents", "mappings": [
        { "src_field": "company_name", "dst_field": "company_name", "description": "Pass company name to load documents" }
      ]
    },

    # --- Load Documents to Prompt Constructor ---
    { "src_node_id": "load_documents", "dst_node_id": "construct_gap_analysis_prompt", "mappings": [
        { "src_field": "blog_content_analysis_data", "dst_field": "blog_content_analysis_data" },
        { "src_field": "deep_dive_report_data", "dst_field": "deep_dive_report_data" },
        { "src_field": "company_data", "dst_field": "company_data" }
      ]
    },

    # --- Prompt Constructor to LLM ---
    { "src_node_id": "construct_gap_analysis_prompt", "dst_node_id": "analyze_content_gaps", "mappings": [
        { "src_field": "gap_analysis_user_prompt", "dst_field": "user_prompt" },
        { "src_field": "gap_analysis_system_prompt", "dst_field": "system_prompt" }
      ]
    },

    # --- State to LLM (Message History) ---
    { "src_node_id": "$graph_state", "dst_node_id": "analyze_content_gaps", "mappings": [
        { "src_field": "gap_analysis_messages_history", "dst_field": "messages_history" }
      ]
    },

    # --- LLM to State ---
    { "src_node_id": "analyze_content_gaps", "dst_node_id": "$graph_state", "mappings": [
        { "src_field": "structured_output", "dst_field": "gap_analysis_result", "description": "Store analysis result" },
        { "src_field": "current_messages", "dst_field": "gap_analysis_messages_history", "description": "Update message history" }
      ]
    },

    # --- LLM to Store ---
    { "src_node_id": "analyze_content_gaps", "dst_node_id": "store_gap_analysis", "mappings": [
        { "src_field": "structured_output", "dst_field": "structured_output" }
      ]
    },

    # --- State to Store ---
    { "src_node_id": "$graph_state", "dst_node_id": "store_gap_analysis", "mappings": [
        { "src_field": "company_name", "dst_field": "company_name" }
      ]
    },

    # --- Store to Output Node ---
    { "src_node_id": "store_gap_analysis", "dst_node_id": "output_node", "mappings": [
        { "src_field": "structured_output", "dst_field": "structured_output" }
      ]
    },

  ],

  # --- Define Start and End ---
  "input_node_id": "input_node",
  "output_node_id": "output_node",

  # --- State Reducers ---
  "metadata": {
      "$graph_state": {
        "reducer": {
          # Message history for LLM node
          "gap_analysis_messages_history": "add_messages",
          # Other state variables use default (replace)
        }
      }
  }
}

# --- Test Execution Logic ---
import logging
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

logger = logging.getLogger(__name__)

# Example Test Inputs
TEST_INPUTS = {
    "company_name": "Jasper"
}

async def validate_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """Custom validation function for the workflow outputs."""
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating content gap analysis workflow outputs...")
    
    assert 'structured_output' in outputs, "Validation Failed: 'structured_output' key missing."
    assert outputs['structured_output'] is not None, "Validation Failed: 'structured_output' is None."
    
    logger.info(f"   Strategic shift summary: {outputs.get('structured_output', 'N/A')}")
    logger.info("✓ Output structure and content validation passed.")
    return True

async def main_test_content_gap_analysis():
    test_name = "Content Gap Analysis Workflow Test"
    print(f"--- Starting {test_name} ---")

    CREATE_FAKE_DATA = True
    company_name = TEST_INPUTS["company_name"]
    
    # Example data for testing
    blog_analysis_namespace = BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=company_name)
    deep_dive_namespace = DEEP_DIVE_REPORT_NAMESPACE_TEMPLATE.format(item=company_name)
    company_namespace = COMPANY_DOCUMENT_NAMESPACE_TEMPLATE.format(item=company_name)
    
    # Sample data structures
    sample_blog_analysis = {
        "content_performance": {
            "total_posts": 124,
            "enterprise_focused_percentage": 35,
            "avg_word_count": 1200,
            "top_performing_topics": ["AI automation", "Content marketing", "Business processes"]
        },
        "seo_analysis": {
            "ranking_keywords": 245,
            "high_intent_keywords_ranking": 12,
            "organic_traffic_growth": 15
        },
        "content_gaps": {
            "enterprise_content_deficit": "65% gap in enterprise-focused content",
            "thought_leadership_gap": "Limited executive-authored content"
        }
    }
    
    sample_deep_dive = {
        "industry_analysis": {
            "optimal_content_distribution": {
                "awareness_stage": {"share_pct": 40, "formats": ["educational", "thought_leadership"]},
                "consideration_stage": {"share_pct": 35, "formats": ["comparative", "practical"]}, 
                "decision_stage": {"share_pct": 25, "formats": ["case_studies", "demos"]}
            },
            "enterprise_content_benchmarks": {
                "min_word_count": 2000,
                "citations_per_article": 5,
                "expert_quotes_required": 2
            }
        }
    }
    
    sample_company_data = {
        "company_profile": {
            "name": "Jasper",
            "industry": "AI Content Creation",
            "target_market": "Enterprise B2B",
            "key_products": ["AI Writing Assistant", "Brand Voice", "Content Governance"]
        },
        "current_strategy": {
            "content_team_size": 8,
            "monthly_content_target": 16,
            "primary_channels": ["blog", "social", "email"]
        }
    }
    
    setup_docs: List[SetupDocInfo] = []
    cleanup_docs: List[CleanupDocInfo] = []
    
    if CREATE_FAKE_DATA:
        setup_docs = [
            {
                'namespace': blog_analysis_namespace, 
                'docname': BLOG_CONTENT_ANALYSIS_DOCNAME, 
                'is_versioned': False,
                'initial_data': sample_blog_analysis,
                'is_shared': False, 
                'is_system_entity': False,
            },
            {
                'namespace': deep_dive_namespace, 
                'docname': DEEP_DIVE_REPORT_DOCNAME, 
                'is_versioned': False,
                'initial_data': sample_deep_dive,
                'is_shared': False, 
                'is_system_entity': False,
            },
            {
                'namespace': company_namespace, 
                'docname': COMPANY_DOCUMENT_DOCNAME, 
                'is_versioned': False,
                'initial_data': sample_company_data,
                'is_shared': False, 
                'is_system_entity': False,
            }
        ]
        
        analysis_namespace = CONTENT_GAP_ANALYSIS_NAMESPACE_TEMPLATE.format(item=company_name)
        cleanup_docs = [
            {'namespace': blog_analysis_namespace, 'docname': BLOG_CONTENT_ANALYSIS_DOCNAME, 'is_versioned': False, 'is_shared': False},
            {'namespace': deep_dive_namespace, 'docname': DEEP_DIVE_REPORT_DOCNAME, 'is_versioned': False, 'is_shared': False},
            {'namespace': company_namespace, 'docname': COMPANY_DOCUMENT_DOCNAME, 'is_versioned': False, 'is_shared': False},
            {'namespace': analysis_namespace, 'docname': CONTENT_GAP_ANALYSIS_DOCNAME, 'is_versioned': False, 'is_shared': False},
        ]

    # Execute Test
    print("\n--- Running Content Gap Analysis Workflow Test ---")
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=TEST_INPUTS,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=setup_docs,
        cleanup_docs=cleanup_docs,
        validate_output_func=validate_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=1800  # Allow time for comprehensive analysis
    )

if __name__ == "__main__":
    print("="*60)
    print("Content Gap Analysis Workflow Definition")
    print("="*60)
    logging.basicConfig(level=logging.INFO)
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("Async event loop already running. Scheduling task...")
        loop.create_task(main_test_content_gap_analysis())
    else:
        print("Starting new async event loop...")
        asyncio.run(main_test_content_gap_analysis())
