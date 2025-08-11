"""
Blog Content Analysis Workflow - Sales Funnel Stage Classification

This workflow analyzes blog content posts by:
1. Loading raw content posts
2. Batching posts into groups of 30
3. Classifying posts into sales funnel stages
4. Grouping posts by funnel stage
5. Analyzing each funnel stage group
6. Generating a comprehensive report

Input: company_name (company/blog identifier)
Output: Structured analysis report by sales funnel stage
"""



"""
1. LLM-Powered Content Intelligence (High Impact)

E-E-A-T Analysis: Evaluate expertise, authority, and trust signals
Content Quality Scoring: Readability, clarity, and professional tone
Question-Answer Extraction: Perfect for AEO/voice search
Entity Recognition: Identify people, products, topics for knowledge graphs
Content Intent Classification: Informational vs. transactional

FAQ Detection ❌

What: Detecting FAQ sections
Why Low Accuracy: Relies on text patterns that vary widely across sites
Issues:

Text patterns like "FAQ", "Q:", "A:" can appear in non-FAQ contexts
Many sites use different formats (accordions, schema markup only, etc.)
False positives from blog content discussing FAQs


just analyse if this is present for not

Table of Contents Detection ⚠️

Related Topics/Articles ❌ - 

Schema Markup Types

8. Logical Flow Analysis and readability

"""

from kiwi_client.active.document_models.customer_docs import (
    BLOG_SCRAPED_POSTS_DOCNAME,
    BLOG_SCRAPED_POSTS_NAMESPACE_TEMPLATE,
    BLOG_CLASSIFIED_POSTS_DOCNAME,
    BLOG_CLASSIFIED_POSTS_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_ANALYSIS_DOCNAME,
    BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
)

from kiwi_client.active.content_diagnostics.llm_inputs.blog_content_analysis import (
    SALES_FUNNEL_STAGES,
    BATCH_CLASSIFICATION_SCHEMA,
    FUNNEL_STAGE_ANALYSIS_SCHEMA,
    POST_CLASSIFICATION_USER_PROMPT_TEMPLATE,
    POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE,
    FUNNEL_STAGE_ANALYSIS_USER_PROMPT_TEMPLATE,
    FUNNEL_STAGE_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
)

import json
import asyncio
from typing import List, Optional, Dict, Any, Literal

# --- Workflow Constants ---
LLM_PROVIDER = "openai"
CLASSIFICATION_MODEL = "gpt-4o"
ANALYSIS_MODEL = "claude-sonnet-4-20250514"
LLM_TEMPERATURE = 0.5
LLM_MAX_TOKENS_CLASSIFY = 3000
LLM_MAX_TOKENS_ANALYSIS = 4000

POST_BATCH_SIZE = 20

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
                    "company_name": {
                        "type": "str", 
                        "required": True, 
                        "description": "Name of the company/blog entity whose content is to be analyzed."
                    },
                    "funnel_stages_input": {
                        "type": "list",
                        "required": False,
                        "default": [
                            {"stage_id": "awareness", "stage_name": "Awareness", "stage_description": "Top of funnel - building brand awareness"},
                            {"stage_id": "consideration", "stage_name": "Consideration", "stage_description": "Middle of funnel - evaluating solutions"},
                            {"stage_id": "purchase", "stage_name": "Purchase", "stage_description": "Bottom of funnel - ready to buy"},
                            {"stage_id": "retention", "stage_name": "Retention", "stage_description": "Post-purchase - customer success"}
                        ],
                        "description": "Optional override list of funnel stages to use for grouping"
                    }
                }
            }
        },

        # --- 2. Load Posts ---
        "load_posts": {
            "node_id": "load_posts",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": BLOG_SCRAPED_POSTS_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "company_name",
                            "static_docname": BLOG_SCRAPED_POSTS_DOCNAME,
                        },
                        "output_field_name": "raw_posts_data"
                    },
                ]
            },
            "dynamic_output_schema": {
                "fields": {
                    "raw_posts_data": {
                        "type": "list", 
                        "required": True, 
                        "description": "List of blog posts from the entity."
                    },
                }
            }
        },

        # --- 3. Batch Posts ---
        "batch_and_route_posts": {
            "node_id": "batch_and_route_posts",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["construct_classification_prompt"],
                "map_targets": [
                    {
                        "source_path": "raw_posts_data",
                        "destinations": ["construct_classification_prompt"],
                        "batch_size": POST_BATCH_SIZE,
                        "batch_field_name": "post_batch"
                    }
                ]
            }
        },

        # --- 4. Classify Posts per Batch ---
        "construct_classification_prompt": {
            "node_id": "construct_classification_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "node_config": {
                "prompt_templates": {
                    "classify_user_prompt": {
                        "id": "classify_user_prompt",
                        "template": POST_CLASSIFICATION_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "posts_batch_json": None
                        },
                        "construct_options": {
                            "posts_batch_json": "post_batch"
                        }
                    },
                    "classify_system_prompt": {
                        "id": "classify_system_prompt",
                        "template": POST_CLASSIFICATION_SYSTEM_PROMPT_TEMPLATE,
                        "variables": {
                            "schema": json.dumps(BATCH_CLASSIFICATION_SCHEMA, indent=2),
                            "sales_funnel_stages": json.dumps(SALES_FUNNEL_STAGES, indent=2)
                        },
                        "construct_options": {}
                    }
                }
            }
        },

        "classify_batch": {
            "node_id": "classify_batch",
            "node_name": "llm",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": CLASSIFICATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS_CLASSIFY
                },
                "output_schema": {
                    "schema_definition": BATCH_CLASSIFICATION_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 5. Flatten Classification Results ---
        "flatten_classifications": {
            "node_id": "flatten_classifications",
            "node_name": "merge_aggregate",
            "node_config": {
                "operations": [
                    {
                        "output_field_name": "flat_classifications",
                        "select_paths": ["all_classifications_batches"],
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

        # --- 6. Join Classifications to Posts ---
        "join_classifications_to_posts": {
            "node_id": "join_classifications_to_posts",
            "node_name": "data_join_data",
            "node_config": {
                "joins": [
                    {
                        "primary_list_path": "raw_posts_data",
                        "secondary_list_path": "merged_data.flat_classifications.classifications",
                        "primary_join_key": "post_url",
                        "secondary_join_key": "post_url",
                        "output_nesting_field": "funnel_classification",
                        "join_type": "one_to_one"
                    }
                ]
            }
        },

        # --- 7. Store Classified Posts ---
        "store_classified_posts": {
            "node_id": "store_classified_posts",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": False, "operation": "upsert"},
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "mapped_data.raw_posts_data",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CLASSIFIED_POSTS_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "static_docname": BLOG_CLASSIFIED_POSTS_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },

        # --- 8. Extract Funnel Stages for Grouping ---
        # Create funnel stage objects to use as primary list for grouping
        "extract_funnel_stages": {
            "node_id": "extract_funnel_stages",
            "node_name": "transform_data",
            "node_config": {
                "mappings": [
                    {
                        "source_path": "funnel_stages_input",
                        "destination_path": "funnel_stages"
                    }
                ]
            }
        },

        # --- 9. Group Posts by Sales Funnel Stage ---
        # Use data_join_data to group posts under their respective funnel stages
        "group_posts_by_funnel_stage": {
            "node_id": "group_posts_by_funnel_stage",
            "node_name": "data_join_data",
            "node_config": {
                "joins": [
                    {
                        "primary_list_path": "transformed_data.funnel_stages",  # List of funnel stage objects
                        "secondary_list_path": "mapped_data.raw_posts_data",    # List of classified posts
                        "primary_join_key": "stage_id",                         # Key in funnel stage object
                        "secondary_join_key": "funnel_classification.sales_funnel_stage",  # Nested key in post
                        "output_nesting_field": "stage_posts",                  # Nest posts under this field
                        "join_type": "one_to_many"
                    }
                ]
            }
        },

        # --- 10. Route Funnel Stage Groups for Analysis ---
        "route_funnel_stage_groups": {
            "node_id": "route_funnel_stage_groups",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["construct_analysis_prompt"],
                "map_targets": [
                    {
                        "source_path": "mapped_data.transformed_data.funnel_stages",  # List of funnel stages with posts
                        "destinations": ["construct_analysis_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "funnel_stage_group"
                    }
                ]
            }
        },

        # --- 10. Analyze Each Funnel Stage Group ---
        "construct_analysis_prompt": {
            "node_id": "construct_analysis_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "node_config": {
                "prompt_templates": {
                    "analyze_user_prompt": {
                        "id": "analyze_user_prompt",
                        "template": FUNNEL_STAGE_ANALYSIS_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "funnel_stage": None,
                            "posts_group_json": None                        },
                        "construct_options": {
                            "funnel_stage": "funnel_stage_group.stage_name",
                            "posts_group_json": "funnel_stage_group.stage_posts"                        }
                    },
                    "analyze_system_prompt": {
                        "id": "analyze_system_prompt",
                        "template": FUNNEL_STAGE_ANALYSIS_SYSTEM_PROMPT_TEMPLATE,
                        "variables": {
                            "schema": json.dumps(FUNNEL_STAGE_ANALYSIS_SCHEMA, indent=2)
                        },
                        "construct_options": {}
                    }
                }
            }
        },

        "analyze_funnel_stage_group": {
            "node_id": "analyze_funnel_stage_group",
            "node_name": "llm",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": ANALYSIS_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS_ANALYSIS
                },
                "output_schema": {
                    "schema_definition": FUNNEL_STAGE_ANALYSIS_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                }
            }
        },

        # --- 11. Combine All Analysis Reports ---
        "combine_funnel_reports": {
            "node_id": "combine_funnel_reports",
            "node_name": "transform_data",
            "node_config": {
                "mappings": [
                    {"source_path": "company_name", "destination_path": "final_report_data.company_name"},
                    {"source_path": "all_funnel_stage_reports", "destination_path": "final_report_data.funnel_analysis"}
                ]
            }
        },

        # --- 12. Store Analysis Results ---
        "store_analysis": {
            "node_id": "store_analysis",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": False, "operation": "upsert"},
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "transformed_data.final_report_data",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "static_docname": BLOG_CONTENT_ANALYSIS_DOCNAME,
                            }
                        }
                    }
                ]
            }
        },

        # --- 13. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {}
        }
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # Input & Setup
        {"src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"},
            {"src_field": "funnel_stages_input", "dst_field": "funnel_stages_input"}
        ]},
        {"src_node_id": "input_node", "dst_node_id": "load_posts", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"}
        ]},
        
        # Store posts in state for later joins
        {"src_node_id": "load_posts", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "raw_posts_data", "dst_field": "raw_posts_data"}
        ]},
        
        # Batch and classify posts
        {"src_node_id": "load_posts", "dst_node_id": "batch_and_route_posts", "mappings": [
            {"src_field": "raw_posts_data", "dst_field": "raw_posts_data"}
        ]},
        {"src_node_id": "batch_and_route_posts", "dst_node_id": "construct_classification_prompt", "mappings": []},
        {"src_node_id": "construct_classification_prompt", "dst_node_id": "classify_batch", "mappings": [
            {"src_field": "classify_user_prompt", "dst_field": "user_prompt"},
            {"src_field": "classify_system_prompt", "dst_field": "system_prompt"}
        ]},
        
        # Message history for classification
        {"src_node_id": "$graph_state", "dst_node_id": "classify_batch", "mappings": [
            {"src_field": "classify_batch_messages_history", "dst_field": "messages_history"}
        ]},
        {"src_node_id": "classify_batch", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "all_classifications_batches"},
            {"src_field": "current_messages", "dst_field": "classify_batch_messages_history"}
        ]},
        
        # Flatten and join classifications
        {"src_node_id": "classify_batch", "dst_node_id": "flatten_classifications", "mappings": []},
        {"src_node_id": "$graph_state", "dst_node_id": "flatten_classifications", "mappings": [
            {"src_field": "all_classifications_batches", "dst_field": "all_classifications_batches"}
        ]},
        {"src_node_id": "flatten_classifications", "dst_node_id": "join_classifications_to_posts", "mappings": [
            {"src_field": "merged_data", "dst_field": "merged_data"}
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "join_classifications_to_posts", "mappings": [
            {"src_field": "raw_posts_data", "dst_field": "raw_posts_data"}
        ]},
        
        # Store classified posts
        {"src_node_id": "join_classifications_to_posts", "dst_node_id": "store_classified_posts", "mappings": [
            {"src_field": "mapped_data", "dst_field": "mapped_data"}
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "store_classified_posts", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"}
        ]},
        
        # Extract funnel stages
        {"src_node_id": "store_classified_posts", "dst_node_id": "extract_funnel_stages", "mappings": []},
        {"src_node_id": "$graph_state", "dst_node_id": "extract_funnel_stages", "mappings": [
            {"src_field": "funnel_stages_input", "dst_field": "funnel_stages_input"}
        ]},
        
        # Group posts by funnel stage
        {"src_node_id": "extract_funnel_stages", "dst_node_id": "group_posts_by_funnel_stage", "mappings": [
            {"src_field": "transformed_data", "dst_field": "transformed_data"}
        ]},
        {"src_node_id": "join_classifications_to_posts", "dst_node_id": "group_posts_by_funnel_stage", "mappings": [
            {"src_field": "mapped_data", "dst_field": "mapped_data"}
        ]},
        
        # Route and analyze funnel stage groups
        {"src_node_id": "group_posts_by_funnel_stage", "dst_node_id": "route_funnel_stage_groups", "mappings": [
            {"src_field": "mapped_data", "dst_field": "mapped_data"}
        ]},
        {"src_node_id": "route_funnel_stage_groups", "dst_node_id": "construct_analysis_prompt", "mappings": []},
        {"src_node_id": "construct_analysis_prompt", "dst_node_id": "analyze_funnel_stage_group", "mappings": [
            {"src_field": "analyze_user_prompt", "dst_field": "user_prompt"},
            {"src_field": "analyze_system_prompt", "dst_field": "system_prompt"}
        ]},
        
        # Message history for analysis
        {"src_node_id": "$graph_state", "dst_node_id": "analyze_funnel_stage_group", "mappings": [
            {"src_field": "analyze_funnel_stage_group_messages_history", "dst_field": "messages_history"}
        ]},
        {"src_node_id": "analyze_funnel_stage_group", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "all_funnel_stage_reports"},
            {"src_field": "current_messages", "dst_field": "analyze_funnel_stage_group_messages_history"}
        ]},
        
        # Combine reports
        {"src_node_id": "analyze_funnel_stage_group", "dst_node_id": "combine_funnel_reports", "mappings": []},
        {"src_node_id": "$graph_state", "dst_node_id": "combine_funnel_reports", "mappings": [
            {"src_field": "all_funnel_stage_reports", "dst_field": "all_funnel_stage_reports"},
            {"src_field": "company_name", "dst_field": "company_name"}
        ]},
        
        # Store results
        {"src_node_id": "combine_funnel_reports", "dst_node_id": "store_analysis", "mappings": [
            {"src_field": "transformed_data", "dst_field": "transformed_data"}
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "store_analysis", "mappings": [
            {"src_field": "company_name", "dst_field": "company_name"}
        ]},
        
        # Output
        {"src_node_id": "store_analysis", "dst_node_id": "output_node", "mappings": [
            {"src_field": "paths_processed", "dst_field": "analysis_storage_path"}
        ]},
        {"src_node_id": "store_classified_posts", "dst_node_id": "output_node", "mappings": [
            {"src_field": "paths_processed", "dst_field": "classified_posts_storage_path"}
        ]},
        {"src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
            {"src_field": "company_name", "dst_field": "processed_company_name"}
        ]},
    ],

    # Define start and end
    "input_node_id": "input_node",
    "output_node_id": "output_node",

    # State reducers
    "metadata": {
        "$graph_state": {
            "reducer": {
                "all_classifications_batches": "collect_values",
                "all_funnel_stage_reports": "collect_values",
                "classify_batch_messages_history": "add_messages",
                "analyze_funnel_stage_group_messages_history": "add_messages"
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

# Example Input
TEST_INPUTS = {
    "company_name": "test_company",
    "funnel_stages_input": [
        {"stage_id": "awareness", "stage_name": "Awareness", "stage_description": "Top of funnel - building brand awareness"},
        {"stage_id": "consideration", "stage_name": "Consideration", "stage_description": "Middle of funnel - evaluating solutions"},
        {"stage_id": "purchase", "stage_name": "Purchase", "stage_description": "Bottom of funnel - ready to buy"},
        {"stage_id": "retention", "stage_name": "Retention", "stage_description": "Post-purchase - customer success"}
    ]
}

async def validate_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """Custom validation function for the workflow outputs."""
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating blog content analysis workflow outputs...")
    
    assert 'analysis_storage_path' in outputs, "Validation Failed: 'analysis_storage_path' key missing."
    assert 'classified_posts_storage_path' in outputs, "Validation Failed: 'classified_posts_storage_path' key missing."
    assert 'processed_company_name' in outputs, "Validation Failed: 'processed_company_name' key missing."
    assert outputs['processed_company_name'] == TEST_INPUTS['company_name'], "Validation Failed: Entity name mismatch."
    assert isinstance(outputs.get('analysis_storage_path'), list), "Validation Failed: analysis_storage_path should be a list."
    assert isinstance(outputs.get('classified_posts_storage_path'), list), "Validation Failed: classified_posts_storage_path should be a list."
    assert len(outputs.get('analysis_storage_path', [])) > 0, "Validation Failed: analysis_storage_path is empty."
    assert len(outputs.get('classified_posts_storage_path', [])) > 0, "Validation Failed: classified_posts_storage_path is empty."
    
    logger.info(f"   Analysis storage path: {outputs.get('analysis_storage_path')}")
    logger.info(f"   Classified posts storage path: {outputs.get('classified_posts_storage_path')}")
    logger.info("✓ Output structure and content validation passed.")
    return True

async def main_test_blog_analysis():
    test_name = "Blog Content Analysis Workflow Test - Sales Funnel Classification"
    print(f"--- Starting {test_name} ---")

    CREATE_FAKE_POSTS = True
    company_name = TEST_INPUTS["company_name"]
    test_scraping_namespace = BLOG_SCRAPED_POSTS_NAMESPACE_TEMPLATE.format(item=company_name)
    
    # Example blog post data
    example_posts_data = [
        {
            "post_url": "https://example.com/blog/getting-started-with-ai",
            "title": "Getting Started with AI: A Beginner's Guide",
            "content": "Artificial Intelligence is transforming industries worldwide. In this comprehensive guide, we'll explore the fundamentals of AI and how it can benefit your business...",
            "published_date": "2023-05-15",
            "word_count": 1500,
            "author": "John Smith",
            "tags": ["AI", "Machine Learning", "Technology", "Business"],
            "category": "Educational"
        },
        {
            "post_url": "https://example.com/blog/ai-vs-competitors",
            "title": "Why Our AI Platform Outperforms the Competition",
            "content": "When choosing an AI platform, it's crucial to understand the differences. Our platform offers superior accuracy, faster processing, and better integration capabilities compared to competitors...",
            "published_date": "2023-05-12",
            "word_count": 2200,
            "author": "Sarah Johnson",
            "tags": ["AI Platform", "Competition", "Comparison", "Features"],
            "category": "Product Comparison"
        },
        {
            "post_url": "https://example.com/blog/ai-customer-success",
            "title": "How AI Helped Our Customer Increase Revenue by 30%",
            "content": "Discover how one of our clients leveraged our AI platform to streamline operations and boost revenue. This case study highlights the challenges, solutions, and results achieved...",
            "published_date": "2023-04-28",
            "word_count": 1800,
            "author": "Emily Chen",
            "tags": ["Case Study", "Customer Success", "AI", "Revenue"],
            "category": "Case Studies"
        },
        {
            "post_url": "https://example.com/blog/ai-pricing-guide",
            "title": "Understanding AI Platform Pricing: What You Need to Know",
            "content": "Pricing for AI platforms can be confusing. In this post, we break down our pricing model, explain what you get at each tier, and help you choose the right plan for your business...",
            "published_date": "2023-04-20",
            "word_count": 1300,
            "author": "Michael Lee",
            "tags": ["Pricing", "AI Platform", "Business", "Guide"],
            "category": "Pricing"
        },
        {
            "post_url": "https://example.com/blog/ai-for-customer-retention",
            "title": "5 Ways AI Can Improve Customer Retention",
            "content": "Retaining customers is just as important as acquiring new ones. Learn how AI-driven insights and automation can help you keep your customers happy and loyal...",
            "published_date": "2023-03-30",
            "word_count": 1600,
            "author": "Priya Patel",
            "tags": ["Customer Retention", "AI", "Automation", "Loyalty"],
            "category": "Retention"
        },
        {
            "post_url": "https://example.com/blog/ai-vs-manual-processes",
            "title": "AI vs. Manual Processes: A Detailed Comparison",
            "content": "Is it time to automate? We compare manual business processes with AI-powered automation, looking at efficiency, cost, and scalability...",
            "published_date": "2023-03-15",
            "word_count": 2100,
            "author": "David Kim",
            "tags": ["AI", "Automation", "Comparison", "Efficiency"],
            "category": "Comparisons"
        },
        {
            "post_url": "https://example.com/blog/ai-content-marketing-trends",
            "title": "Top AI Content Marketing Trends to Watch in 2024",
            "content": "Stay ahead of the curve with these emerging trends in AI-driven content marketing. From personalization to predictive analytics, see what's shaping the future...",
            "published_date": "2023-02-28",
            "word_count": 1700,
            "author": "Linda Martinez",
            "tags": ["AI", "Content Marketing", "Trends", "Analytics"],
            "category": "Thought Leadership"
        },
    ]
    
    setup_docs: List[SetupDocInfo] = [
        {
            'namespace': test_scraping_namespace,
            'docname': BLOG_SCRAPED_POSTS_DOCNAME,
            'is_versioned': False,
            'initial_data': example_posts_data,
            'is_shared': False,
            'is_system_entity': False,
        }
    ]
    
    test_analysis_namespace = BLOG_CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=company_name)
    test_classified_posts_namespace = BLOG_CLASSIFIED_POSTS_NAMESPACE_TEMPLATE.format(item=company_name)
    cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': test_scraping_namespace,
            'docname': BLOG_SCRAPED_POSTS_DOCNAME,
            'is_versioned': False,
            'is_shared': False
        },
        {
            'namespace': test_classified_posts_namespace,
            'docname': BLOG_CLASSIFIED_POSTS_DOCNAME,
            'is_versioned': False,
            'is_shared': False
        },
        {
            'namespace': test_analysis_namespace,
            'docname': BLOG_CONTENT_ANALYSIS_DOCNAME,
            'is_versioned': False,
            'is_shared': False
        },
    ]
    
    print("\n--- Running Workflow Test ---")
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=TEST_INPUTS,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=setup_docs if CREATE_FAKE_POSTS else [],
        cleanup_docs=cleanup_docs if CREATE_FAKE_POSTS else [],
        validate_output_func=validate_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=1800
    )

if __name__ == "__main__":
    print("="*50)
    print("Blog Content Analysis Workflow - Sales Funnel Classification")
    print("="*50)
    logging.basicConfig(level=logging.INFO)
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("Async event loop already running. Scheduling task...")
        loop.create_task(main_test_blog_analysis())
    else:
        print("Starting new async event loop...")
        asyncio.run(main_test_blog_analysis())
