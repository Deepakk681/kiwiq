"""
Section 7 AI Discoverability Gaps Workflow

This workflow combines multiple AI visibility data sources to analyze discoverability gaps:
1. Loads blog AI visibility data
2. Loads company AI visibility data
3. Loads executive AI visibility data  
4. Loads competitor AI visibility data (multiple documents)
5. Analyzes all data sources using LLM to generate structured AI discoverability insights

The workflow generates insights including:
- Current visibility status across AI platforms
- Missing elements for AI citations
- Content format improvements needed
- Platform-specific opportunities

Input: Document configurations for the 4 AI visibility data sources
Output: Structured AI discoverability gaps analysis
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
    # Blog AI Visibility
    BLOG_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_AI_VISIBILITY_TEST_IS_VERSIONED,
    
    # Company AI Visibility
    BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_AI_VISIBILITY_TEST_IS_VERSIONED,
    
    # Executive AI Visibility
    BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED,
    
    # Competitor AI Visibility
    BLOG_COMPETITOR_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_COMPETITOR_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
    
    # Section 7 Diagnostic Report
    BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION7_IS_VERSIONED,
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.section7_content_diagnostics import (
    GENERATION_SCHEMA,
    USER_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE,
    USER_PROMPT_TEMPLATE_VARIABLES,
    USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS,
    SYSTEM_PROMPT_TEMPLATE_VARIABLES,
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
# SECTION7_ANALYSIS_DOCNAME = "section7_ai_discoverability_gaps_analysis"
# SECTION7_ANALYSIS_NAMESPACE_TEMPLATE = "blog_ai_discoverability_{item}"

### INPUTS ###
INPUT_FIELDS = {
    "ai_visibility_doc_configs": {
        "type": "list",
        "required": True,
        "description": "List of document configurations for AI visibility data sources"
    },
    "competitor_ai_visibility_namespace": {
        "type": "str",
        "required": True,
        "description": "Namespace for competitor AI visibility documents"
    },
    "company_name": { 
        "type": "str", 
        "required": True, 
        "description": "Name of the company for AI discoverability analysis"
    }
}

# --- Field Mappings Configuration ---
field_mappings_from_input_to_state = [
    { "src_field": "ai_visibility_doc_configs", "dst_field": "ai_visibility_doc_configs" },
    { "src_field": "competitor_ai_visibility_namespace", "dst_field": "competitor_ai_visibility_namespace" },
    { "src_field": "company_name", "dst_field": "company_name" }
]

field_mappings_from_input_to_load_ai_visibility_docs = [
    { "src_field": "ai_visibility_doc_configs", "dst_field": "ai_visibility_doc_configs" },
    { "src_field": "company_name", "dst_field": "company_name" }
]

field_mappings_from_load_ai_visibility_docs_to_state = [
    { "src_field": "blog_ai_visibility", "dst_field": "blog_ai_visibility" },
    { "src_field": "company_ai_visibility", "dst_field": "company_ai_visibility" },
    { "src_field": "executive_ai_visibility", "dst_field": "executive_ai_visibility" }
]

field_mappings_from_state_to_prompt_constructor = [
    { "src_field": "blog_ai_visibility", "dst_field": "blog_ai_visibility" },
    { "src_field": "company_ai_visibility", "dst_field": "company_ai_visibility" },
    { "src_field": "executive_ai_visibility", "dst_field": "executive_ai_visibility" },
    { "src_field": "competitor_ai_visibility", "dst_field": "competitor_ai_visibility" }
]

field_mappings_from_state_to_store_analysis = [
    { "src_field": "company_name", "dst_field": "company_name" }
]

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

        # --- 2. Load AI Visibility Documents (Consolidated) ---
        "load_ai_visibility_docs": {
            "node_id": "load_ai_visibility_docs",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "ai_visibility_doc_configs",
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False},
            },
        },

        # --- 3. Load Multiple Competitor AI Visibility Documents ---
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

        # --- 4. Construct Prompt ---
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
                        "variables": SYSTEM_PROMPT_TEMPLATE_VARIABLES                    }
                }
            }
        },

        # --- 5. Generate AI Discoverability Gaps Analysis ---
        "generate_ai_discoverability_analysis": {
            "node_id": "generate_ai_discoverability_analysis",
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

        # --- 6. Store Analysis Results ---
        "store_analysis": {
            "node_id": "store_analysis",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": BLOG_CONTENT_DIAGNOSTIC_SECTION7_IS_VERSIONED, "operation": "upsert"},
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME,
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
            "node_config": {
                "dynamic_input_schema": {
                    "fields": {
                        "ai_discoverability_gaps_analysis": {
                            "type": "dict",
                            "required": True,
                            "description": "The structured AI discoverability gaps analysis"
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
        # --- Initial Setup ---
        # Input -> State: Store initial inputs globally
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "$graph_state", 
            "mappings": field_mappings_from_input_to_state
        },
        
        # Input -> Load AI Visibility Documents
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_ai_visibility_docs", 
            "mappings": field_mappings_from_input_to_load_ai_visibility_docs
        },
        
        # Input -> Load Competitor AI Visibility
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_competitor_ai_visibility", 
            "mappings": [
                { "src_field": "competitor_ai_visibility_namespace", "dst_field": "competitor_ai_visibility_namespace" },
                { "src_field": "company_name", "dst_field": "company_name" }
            ]
        },
        
        # --- State Updates from Loaders ---
        { 
            "src_node_id": "load_ai_visibility_docs", 
            "dst_node_id": "$graph_state", 
            "mappings": field_mappings_from_load_ai_visibility_docs_to_state
        },
        
        { 
            "src_node_id": "load_competitor_ai_visibility", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "competitor_ai_visibility_list", "dst_field": "competitor_ai_visibility" }
            ]
        },

        # --- Trigger Prompt Construction ---
        { 
            "src_node_id": "load_ai_visibility_docs", 
            "dst_node_id": "construct_prompt" 
        },
        
        { 
            "src_node_id": "load_competitor_ai_visibility", 
            "dst_node_id": "construct_prompt" 
        },
        
        # --- State -> Construct Prompt ---
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_prompt", 
            "mappings": field_mappings_from_state_to_prompt_constructor
        },
        
        # --- Construct Prompt -> Generate Analysis ---
        { 
            "src_node_id": "construct_prompt", 
            "dst_node_id": "generate_ai_discoverability_analysis", 
            "mappings": [
                { "src_field": "user_prompt", "dst_field": "user_prompt" },
                { "src_field": "system_prompt", "dst_field": "system_prompt" }
            ]
        },
        
        # --- Generate Analysis -> Store ---
        { 
            "src_node_id": "generate_ai_discoverability_analysis", 
            "dst_node_id": "store_analysis", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "structured_output" }
            ]
        },
        
        # --- State -> Store ---
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "store_analysis", 
            "mappings": field_mappings_from_state_to_store_analysis
        },
        
        # --- Store -> Output ---
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
async def main_test_section7_ai_discoverability_gaps_workflow():
    """
    Test for Section 7 AI Discoverability Gaps Workflow.
    """
    test_name = "Section 7 AI Discoverability Gaps Workflow Test"
    print(f"--- Starting {test_name} ---")

    # Example Document Configurations
    company_name = "test_company"
    
    # Consolidated AI visibility document configurations
    ai_visibility_doc_configs = [
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                "input_namespace_field": "company_name",
                "static_docname": BLOG_AI_VISIBILITY_TEST_DOCNAME,
            },
            "output_field_name": "blog_ai_visibility"
        },
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                "input_namespace_field": "company_name",
                "static_docname": BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
            },
            "output_field_name": "company_ai_visibility"
        },
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
                "input_namespace_field": "company_name",
                "static_docname": BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
            },
            "output_field_name": "executive_ai_visibility"
        }
    ]
    
    # For multiple competitor documents, use namespace approach
    competitor_ai_visibility_namespace = BLOG_COMPETITOR_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name)
    
    test_inputs = {
        "ai_visibility_doc_configs": ai_visibility_doc_configs,
        "competitor_ai_visibility_namespace": competitor_ai_visibility_namespace,
        "company_name": company_name
    }

    # Define setup documents with sample data
    setup_docs: List[SetupDocInfo] = [
        # Blog AI Visibility
        {
            'namespace': BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_AI_VISIBILITY_TEST_DOCNAME,
            'initial_data': {
                "chatgpt_results": [
        {
          "user_intent": "Find an enterprise AI writing platform that ensures consistent brand voice.",
          "visibility_gaps": [
            "No company blog content from Writer found directly in ChatGPT answers.",
            "Main product pages or third-party summaries (if any) may be summarized, but blog content is not surfaced."
          ],
          "citation_context": "No blog content from Writer is cited on ChatGPT because search integration is absent; ChatGPT uses its training data and may summarize Writer's features, but does not reference or cite blogs.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Grammarly",
            "Jasper",
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "https://writer.com/blog/enterprise-ai-features/"
          ]
        },
        {
          "user_intent": "Learn how to scale content creation in enterprise marketing teams.",
          "visibility_gaps": [
            "Writer's blog content is not referenced/cited directly by ChatGPT.",
            "Details from main site or known summaries may appear in responses, but blog depth is missing."
          ],
          "citation_context": "High-level overviews may mention Writer's platform but lack in-depth blog detail. Blog case studies or guides on scaling content are not surfaced.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Solution-heavy posts on content scaling, case studies with data"
          ]
        },
        {
          "user_intent": "Discover AI tools for improving cross-functional documentation in large organizations.",
          "visibility_gaps": [
            "Writer blog posts on documentation and internal workflows are absent.",
            "General tool listings may appear, but not tailored, blog-driven solutions from Writer."
          ],
          "citation_context": "ChatGPT may describe generic use cases or mention Writer as a tool, but misses citation of specific, workflow-focused Writer blogs.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "How-to guides on documentation at scale for enterprises"
          ]
        },
        {
          "user_intent": "Find best practices for maintaining brand voice at scale with AI.",
          "visibility_gaps": [
            "Writer's authoritative blog posts on brand voice enforcement are not surfaced.",
            "No in-depth best practice posts or frameworks from Writer are cited."
          ],
          "citation_context": "ChatGPT may summarize general best practices for brand voice but does not cite or link to Writer content.",
          "specific_posts_cited": [],
          "competitors_mentioned": [],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Deep-dive or checklist blog posts on brand voice at scale"
          ]
        },
        {
          "user_intent": "Compare Writer vs Grammarly for enterprise content teams.",
          "visibility_gaps": [
            "No direct comparison blog posts or pages from Writer appear in ChatGPT answers.",
            "Generic product comparisons may be drafted from known data, limiting depth and specificity."
          ],
          "citation_context": "ChatGPT may mention both platforms, summarizing known competitive advantages without referencing blogs.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Grammarly"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Writer vs competitor deep-dives, use case analyses"
          ]
        },
        {
          "user_intent": "Learn about AI solutions for content velocity in financial services marketing.",
          "visibility_gaps": [
            "No blog content or industry-specific case studies from Writer found in ChatGPT answers.",
            "Responses may discuss AI in FS generically, omitting specific Writer expertise."
          ],
          "citation_context": "Platform may include high-level Writer use cases, but without blog context, depth and relevance are lost.",
          "specific_posts_cited": [],
          "competitors_mentioned": [],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Industry-tailored blog content, especially for regulated sectors"
          ]
        },
        {
          "user_intent": "Standardize marketing content quality with AI.",
          "visibility_gaps": [
            "No practical, actionable guides or Writer blog citations in ChatGPT.",
            "General platform positioning included, but best practice blog resources aren't surfaced."
          ],
          "citation_context": "Generic mention of Writer may appear in answers, but not enriched by citation of relevant blog articles or guides.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Blog guides on content audit frameworks, team training templates"
          ]
        }
      ],
      "perplexity_results": [
        {
          "user_intent": "Find an enterprise AI writing platform that ensures consistent brand voice.",
          "visibility_gaps": [
            "Writer's blog content appears, but is not consistently the top result; main site is prioritized.",
            "Competitor reviews (notably Copy.ai's review of Writer) often visible directly after or even before blog articles."
          ],
          "citation_context": "Writer's blog post (https://writer.com/blog/enterprise-ai-features/) is visible in some queries, occasionally cited for AI features and brand voice, but lacks dominance.",
          "specific_posts_cited": [
            "https://writer.com/blog/enterprise-ai-features/"
          ],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "true",
          "citation_opportunities": [
            "Enterprise feature deep-dives",
            "Practical on-brand content playbooks"
          ]
        },
        {
          "user_intent": "Learn how to scale content creation in enterprise marketing teams.",
          "visibility_gaps": [
            "Writer's blog content does not rank as the top result; overview and main site are shown first.",
            "Competitor review (Copy.ai's review of Writer) is frequently adjacent, benefiting from detailed analysis."
          ],
          "citation_context": "Company positioning is summarized from main site/overview; practical blog-based case studies or frameworks do not surface at the top.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "true",
          "citation_opportunities": [
            "Case studies or customer stories on content scaling—industry-specific for tech, FS, healthcare"
          ]
        },
        {
          "user_intent": "Discover AI tools for improving cross-functional documentation in large organizations.",
          "visibility_gaps": [
            "No direct blog content from Writer is surfaced; overview/product pages and reviews are prioritized.",
            "Copy.ai's reviews appear as recurring competitors."
          ],
          "citation_context": "Writer's site is cited as a recommended platform, but blog best practices/guides on cross-team documentation are missing.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Process/automation blog posts tied to cross-functional documentation"
          ]
        },
        {
          "user_intent": "Find best practices for maintaining brand voice at scale with AI.",
          "visibility_gaps": [
            "Writer's blog content appears but is still not the initial link—main site dominates.",
            "Copy.ai review remains a secondary competitor."
          ],
          "citation_context": "Writer's blog (https://writer.com/blog/enterprise-ai-features/) is referenced for brand voice at scale but loses share to home/overview pages.",
          "specific_posts_cited": [
            "https://writer.com/blog/enterprise-ai-features/"
          ],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "true",
          "citation_opportunities": [
            "Visual frameworks or downloadable templates for brand voice"
          ]
        },
        {
          "user_intent": "Compare Writer vs Grammarly for enterprise content teams.",
          "visibility_gaps": [
            "No dedicated comparison blog/page from Writer surfaces; only main overview is shown.",
            "Copy.ai review with comparison elements appears directly after."
          ],
          "citation_context": "No blog content specifically comparing Writer to Grammarly exists in search.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "SEO-optimized comparison posts: Writer vs Grammarly, vs Jasper, etc."
          ]
        },
        {
          "user_intent": "Learn about AI solutions for content velocity in financial services marketing.",
          "visibility_gaps": [
            "Blog content/case studies on financial services from Writer are missing from search results.",
            "Only main site and reviews are shown."
          ],
          "citation_context": "Financial services use case is described from the main site; targeted blog content is missing.",
          "specific_posts_cited": [],
          "competitors_mentioned": [],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Industry-tailored blog posts or white papers for FS, healthcare, etc."
          ]
        },
        {
          "user_intent": "Standardize marketing content quality with AI.",
          "visibility_gaps": [
            "No direct Writer blog post on this topic ranks high—main site/review pages dominate.",
            "Copy.ai review is a consistent competitor."
          ],
          "citation_context": "Writer is positioned as a solution, but not reinforced with actionable blog content.",
          "specific_posts_cited": [],
          "competitors_mentioned": [
            "Copy.ai"
          ],
          "blog_content_mentioned": "false",
          "citation_opportunities": [
            "Practical how-to blog posts, user guides, and audit templates"
          ]
        }
      ]},
            'is_versioned': BLOG_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Company AI Visibility
        {
            'namespace': BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
            'initial_data': {
      "visibility_score": 8.3,
      "brand_recognition": {
        "direct_query_accuracy": 9.5,
        "competitor_differentiation": "Writer is consistently described as an enterprise-focused, team-oriented AI writing platform with a strong emphasis on brand consistency and security. However, in comparison and review-heavy queries, differentiation is sometimes reduced as review sites tend to group all solutions together.",
        "feature_description_accuracy": 9.0
      },
      "category_presence": {
        "context_quality": "Positive and accurate for enterprise/industry/feature-specific queries; context is occasionally diluted when grouped with competitors in review/comparison searches.",
        "ranking_position": "Typically 1st for solution and feature queries, 3rd-5th for competitive comparisons and industry round-ups.",
        "mentioned_in_category": "true"
      },
      "content_citations": {
        "help_docs_cited": 2,
        "blog_content_cited": 3,
        "third_party_citations": 9
      },
      "baseline_timestamp": "2025-07-17T12:05:00.000Z",
      "competitive_comparison": {
        "market_position": "Writer is a top-tier, enterprise-oriented AI writing solution, excelling in security, compliance, and brand consistency. It is most visible in intent-driven, branded, and solution-specific queries but less dominant in broad, general comparison/review queries where platforms like Grammarly, Jasper, and Copy.ai are more referenced via third parties.",
        "top_competitors": [
          "Grammarly Business",
          "Jasper",
          "Copy.ai",
          "Anyword",
          "Writesonic",
          "Articleforge"
        ],
        "competitive_gaps": [
          "Visibility in broad, non-branded comparison queries where third-party review lists (G2, Capterra, TechRadar, HuffPost) outrank official content.",
          "Lower citation rate for in-depth, third-party blog or analyst content compared to some competitors.",
          "Occasional lack of direct company content for highly general 'best AI writer' searches, especially on ChatGPT."
        ],
        "visibility_ranking": 2,
        "competitive_advantages": [
          "Strong authority and top rankings for enterprise, security, and agentic AI/platform-specific queries.",
          "Clear messaging around compliance and industry solutions.",
          "Rich, up-to-date solution, security, and feature pages targeting ICP needs."
        ]
      },
      "platform_specific_results": {
        "chatgpt": {
          "accuracy_score": 8.0,
          "context_quality": "Clear and consistent when Writer is mentioned; however, context is heavily influenced by third-party reviews which sometimes group Writer with consumer and non-enterprise solutions.",
          "company_mentions": 1,
          "content_citations": 1,
          "competitor_comparisons": [
            "Grammarly",
            "Jasper",
            "Copy.ai",
            "Anyword",
            "Writesonic",
            "Articleforge"
          ]
        },
        "perplexity": {
          "accuracy_score": 9.5,
          "context_quality": "Highly accurate and contextually relevant for enterprise, feature, industry, and branded queries. Company content is prioritized in authoritative searches, especially when queries are specific to enterprise needs.",
          "company_mentions": 7,
          "content_citations": 5,
          "competitor_comparisons": [
            "Grammarly Business",
            "Jasper",
            "Copy.ai"
          ]
        }
      }},
            'is_versioned': BLOG_COMPANY_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Executive AI Visibility
        {
            'namespace': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
            'initial_data': {
      "ai_visibility_score": 9,
      "platform_recognition": {
        "chatgpt_recognition": {
          "role_accuracy_score": 10,
          "search_result_quality": "high",
          "executive_name_recognized": "true",
          "content_citation_frequency": 9,
          "visibility_gaps_identified": [
            "Direct comparison queries (e.g. 'Writer AI vs Jasper AI') lack May Habib-authored content.",
            "Broader innovation and AI leader lists sometimes mix executive mentions with other leaders, making individual achievements less differentiated."
          ],
          "expertise_recognition_score": 9,
          "thought_leadership_mentions": 8,
          "company_association_accuracy": 10,
          "competitor_comparison_ranking": "top 10%"
        },
        "perplexity_recognition": {
          "role_accuracy_score": 10,
          "search_result_quality": "high",
          "executive_name_recognized": "true",
          "content_citation_frequency": 8,
          "visibility_gaps_identified": [
            "Direct product comparison queries like 'Writer AI platform vs Jasper AI for enterprise' lack executive-authored commentary or responses from May Habib.",
            "General AI platform and innovation category queries sometimes prioritize third-party or competitor content over executive-led materials."
          ],
          "expertise_recognition_score": 9,
          "thought_leadership_mentions": 8,
          "company_association_accuracy": 10,
          "web_search_integration_score": 9,
          "competitor_comparison_ranking": "top 10%"
        },
        "recognition_consistency": 9
      },
      "biographical_accuracy": {
        "missing_credentials": [
          "Detailed academic distinctions (beyond Harvard economics degree)",
          "Previous entrepreneurial ventures (before Writer) or early career highlights",
          "Key patents, publications, or press not explicitly cited in top search results"
        ],
        "current_role_accuracy": 10,
        "career_history_accuracy": 8,
        "achievements_recognition": 9
      },
      "expert_recognition_tests": {
        "topic_expert_queries": [
          "May Habib generative content technology",
          "May Habib generative AI expert",
          "Best practices for enterprise generative AI adoption May Habib"
        ],
        "thought_leader_queries": [
          "May Habib enterprise AI thought leadership",
          "May Habib AI entrepreneur thought leadership"
        ],
        "industry_expert_queries": [
          "Top enterprise AI leaders 2025",
          "Enterprise AI content technology innovators"
        ]
      },
      "improvement_opportunities": [
        "Publish executive-authored comparative reviews addressing Writer vs key competitors (e.g. Jasper AI, OpenAI) and ensure these are indexed and referenced by third-party review sites.",
        "Increase frequency and citation of executive commentary in general AI innovation lists and market analysis articles—submit guest posts or bylined articles to recognized industry media.",
        "Enhance executive bio and credentials on external profiles (TEDAI, Milken Institute, Forbes, LinkedIn) to reinforce unique differentiators that other platforms and AIs will index.",
        "Update and structure all existing interviews and talks with schema markup (structured data) for better indexing by search engines and AI crawlers.",
        "Participate in comparison webinars/panels with other leading AI founders to increase cross-company citation and web presence.",
        "Create an authoritative 'Executive Q&A' or knowledge base addressing frequent enterprise AI and Writer platform comparison queries.",
        "Integrate more citations linking back to original executive interviews in third-party reviews and aggregate lists."
      ],
      "thought_leadership_topics": [
        "Enterprise AI leadership",
        "Generative AI adoption and best practices",
        "Content technology innovation",
        "Scaling AI in B2B SaaS",
        "Fundraising and AI platform growth strategy",
        "Women in AI and technology leadership"
      ],
      "competitor_executive_comparison": {
        "context_quality": "Executive content is more actionable and specific to enterprise AI best practices; however, in direct product comparison and innovation category searches, competitors sometimes achieve more neutral or broader coverage.",
        "mention_frequency": 0.9,
        "recognition_ranking": "top 10%"
      }},
            'is_versioned': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Multiple Competitor AI Visibility Documents
        {
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor1_ai_visibility",
            'initial_data': {
        "competitor_name": "Copy.ai",
        "platform_results": [
          {
            "query_results": [
              {
                "query_text": "best AI copywriting tools for marketing teams",
                "result_summary": "Copy.ai content appeared in the top results, typically in comparison articles and reviews of AI copywriting tools. Other prominent tools mentioned included Writer, Jasper, and Type.ai. Copy.ai was often highlighted for its team collaboration features and template variety.",
                "search_results": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer",
                  "https://blog.type.ai/post/type-ai-vs-copy-ai",
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://www.perplexity.ai/page/copy-ai-vs-writer-which-ai-too-siVQr5JOQNiyHdkbcIWM4w"
                ],
                "other_content_found": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://blog.type.ai/post/type-ai-vs-copy-ai",
                  "https://www.perplexity.ai/page/copy-ai-vs-writer-which-ai-too-siVQr5JOQNiyHdkbcIWM4w"
                ],
                "competitor_urls_found": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 2,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Comparison articles and reviews discuss features, pricing, and user experience of Copy.ai versus other platforms. Writer and Type.ai are frequently compared.",
                "information_from_competitor_content": "Copy.ai is highlighted for its AI-driven content generation, team collaboration, and template variety."
              },
              {
                "query_text": "Copy.ai vs Writer for enterprise content teams",
                "result_summary": "Nearly all results directly compared Copy.ai and Writer, with Copy.ai content present in the top results. These included feature tables, pros and cons, and recommendations for different use cases. Copy.ai was recognized for language support and template diversity, while Writer was noted for advanced SEO and collaboration.",
                "search_results": [
                  "https://www.perplexity.ai/page/copy-ai-vs-writer-which-ai-too-siVQr5JOQNiyHdkbcIWM4w",
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "other_content_found": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://www.perplexity.ai/page/copy-ai-vs-writer-which-ai-too-siVQr5JOQNiyHdkbcIWM4w"
                ],
                "competitor_urls_found": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 2,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Comparisons focus on enterprise features, collaboration, and SEO tools. Writer is often recommended for editorial teams, while Copy.ai is suggested for rapid content generation.",
                "information_from_competitor_content": "Copy.ai is positioned as a fast, template-rich platform with strong language support for enterprise teams."
              },
              {
                "query_text": "Copy.ai pricing and features for large organizations",
                "result_summary": "Copy.ai content appeared in the top results, often through third-party review and comparison sites. Pricing details and enterprise features were discussed, but official Copy.ai URLs were less prominent than review sites.",
                "search_results": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer",
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer"
                ],
                "other_content_found": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer"
                ],
                "competitor_urls_found": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 2,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Third-party sites provide detailed breakdowns of Copy.ai's pricing tiers and features for large teams.",
                "information_from_competitor_content": "Copy.ai offers scalable pricing and features for organizations, including collaboration and unlimited word generation."
              },
              {
                "query_text": "AI content automation for ecommerce product descriptions",
                "result_summary": "Copy.ai was mentioned in the context of ecommerce automation, but not always as the primary result. Other platforms and human writing services were also referenced.",
                "search_results": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer",
                  "https://draft.co/comparisons/comparing-draft-and-copyai-human-writers-vs-ai-copywriting"
                ],
                "other_content_found": [
                  "https://draft.co/comparisons/comparing-draft-and-copyai-human-writers-vs-ai-copywriting"
                ],
                "competitor_urls_found": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 2,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Draft.co and other services compare human versus AI-generated product descriptions.",
                "information_from_competitor_content": "Copy.ai is described as a tool for generating ecommerce content at scale."
              },
              {
                "query_text": "Copy.ai customer reviews and ratings",
                "result_summary": "Copy.ai reviews and ratings appeared on third-party platforms, with some direct competitor content present. Review sites provided user feedback, G2 ratings, and feature breakdowns.",
                "search_results": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "other_content_found": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer"
                ],
                "competitor_urls_found": [
                  "https://www.peerspot.com/products/comparisons/copy-ai_vs_writer"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 2,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Wittypen and other review aggregators provide user ratings and testimonials for Copy.ai and alternatives.",
                "information_from_competitor_content": "Copy.ai receives positive ratings for ease of use, template variety, and team features."
              },
              {
                "query_text": "alternatives to Copy.ai for content automation",
                "result_summary": "Most results focused on listing and comparing Copy.ai with other tools. Copy.ai content was present but often in the context of alternatives, with Writer, Jasper, and Type.ai frequently mentioned.",
                "search_results": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://blog.type.ai/post/type-ai-vs-copy-ai"
                ],
                "other_content_found": [
                  "https://wittypen.com/ai-alternatives/copyai-vs-writer",
                  "https://blog.type.ai/post/type-ai-vs-copy-ai"
                ],
                "competitor_urls_found": [],
                "competitor_content_found": "false",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 0,
                "information_from_other_content": "Alternatives to Copy.ai are discussed, with feature and pricing comparisons.",
                "information_from_competitor_content": ""
              }
            ],
            "overall_findings": "Copy.ai content is highly visible in comparison and review queries, especially when directly compared to Writer or other AI writing tools. Its presence is strongest on third-party review and aggregator sites, with fewer direct links to official Copy.ai pages. Copy.ai is consistently recognized for its collaboration features, template diversity, and suitability for marketing and enterprise teams. However, in queries about alternatives or broader automation solutions, other platforms like Writer, Jasper, and Type.ai often share or dominate visibility. There is a clear pattern of Copy.ai being positioned as a leading solution in the AI writing space, but with significant competition and frequent direct comparison to Writer.",
            "queries_with_other_content": 6,
            "queries_with_competitor_content": 5
          }
        ]
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
        "competitor_name": "Jasper",
        "platform_results": [
          {
            "query_results": [
              {
                "query_text": "best ai writing tools for marketing teams",
                "result_summary": "Jasper is mentioned as a leading AI copywriting tool, especially for content creation at scale and for small teams. It is compared to Writer, which is positioned for larger teams and brand-focused content. Other tools like Writesonic and Draft are also discussed in comparison articles.",
                "search_results": [
                  "https://www.alexbirkett.com/jasper-vs-writer/",
                  "https://zapier.com/blog/writesonic-vs-jasper/",
                  "https://wittypen.com/ai-alternatives/jasperai-vs-writer",
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "other_content_found": [
                  "https://www.alexbirkett.com/jasper-vs-writer/",
                  "https://zapier.com/blog/writesonic-vs-jasper/",
                  "https://wittypen.com/ai-alternatives/jasperai-vs-writer",
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "competitor_urls_found": [
                  "https://jasper.ai"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Comparisons between Jasper, Writer, Writesonic, and Draft, highlighting strengths and weaknesses for different team sizes and use cases.",
                "information_from_competitor_content": "Jasper is positioned as a flexible, scalable AI writing tool with strong template support and content personalization features."
              },
              {
                "query_text": "jasper ai vs writer ai for enterprise content",
                "result_summary": "Multiple comparison articles directly address Jasper vs Writer for enterprise and team use cases. Jasper is noted for flexibility and control, while Writer is preferred for larger organizations with strict brand guidelines.",
                "search_results": [
                  "https://www.alexbirkett.com/jasper-vs-writer/",
                  "https://wittypen.com/ai-alternatives/jasperai-vs-writer"
                ],
                "other_content_found": [
                  "https://www.alexbirkett.com/jasper-vs-writer/",
                  "https://wittypen.com/ai-alternatives/jasperai-vs-writer"
                ],
                "competitor_urls_found": [
                  "https://jasper.ai"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Writer is described as better for large teams and brand consistency, Jasper for flexibility and content creation at scale.",
                "information_from_competitor_content": "Jasper is recommended for small teams, marketers, and those seeking scalable content creation with template-driven workflows."
              },
              {
                "query_text": "jasper ai features and pricing",
                "result_summary": "Jasper's features such as Brand IQ, template library, and content personalization are described in depth. Pricing is referenced in comparison articles but not detailed in the snippets.",
                "search_results": [
                  "https://zapier.com/blog/writesonic-vs-jasper/",
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "other_content_found": [
                  "https://zapier.com/blog/writesonic-vs-jasper/",
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "competitor_urls_found": [
                  "https://jasper.ai"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Comparisons highlight Jasper's Brand IQ, template flexibility, and workflow features.",
                "information_from_competitor_content": "Jasper offers advanced control over content creation, brand voice configuration, and a variety of templates for marketers."
              },
              {
                "query_text": "alternatives to jasper ai for content marketing",
                "result_summary": "Jasper is consistently listed alongside Writer, Writesonic, and Draft as a top AI writing tool. Articles compare features, pricing, and ideal use cases.",
                "search_results": [
                  "https://wittypen.com/ai-alternatives/jasperai-vs-writer",
                  "https://zapier.com/blog/writesonic-vs-jasper/",
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "other_content_found": [
                  "https://wittypen.com/ai-alternatives/jasperai-vs-writer",
                  "https://zapier.com/blog/writesonic-vs-jasper/",
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "competitor_urls_found": [
                  "https://jasper.ai"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Writer, Writesonic, and Draft are positioned as Jasper alternatives with different strengths for enterprise, SEO, or human-written content.",
                "information_from_competitor_content": "Jasper is recognized as a leading AI copywriting tool, especially for small businesses and marketers."
              },
              {
                "query_text": "how does jasper ai compare to human writers",
                "result_summary": "Jasper is compared to services like Draft, which uses human writers. Jasper is praised for speed and scalability, but human writers are noted for brand voice and nuance.",
                "search_results": [
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "other_content_found": [
                  "https://draft.co/comparisons/draft-vs-jasper-ai-human-writers-or-ai-copywriting-a-comprehensive-comparison"
                ],
                "competitor_urls_found": [
                  "https://jasper.ai"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Draft is highlighted for human-written content, while Jasper is praised for AI-driven speed and flexibility.",
                "information_from_competitor_content": "Jasper enables users to generate content quickly with AI, but may lack the nuanced brand voice of human writers."
              },
              {
                "query_text": "jasper ai for scaling blog content",
                "result_summary": "Jasper is specifically recommended for scaling blog content, especially for small teams and marketers. Its template-driven approach and workflow flexibility are highlighted.",
                "search_results": [
                  "https://www.alexbirkett.com/jasper-vs-writer/",
                  "https://zapier.com/blog/writesonic-vs-jasper/"
                ],
                "other_content_found": [
                  "https://www.alexbirkett.com/jasper-vs-writer/",
                  "https://zapier.com/blog/writesonic-vs-jasper/"
                ],
                "competitor_urls_found": [
                  "https://jasper.ai"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Jasper is compared to Writer and Writesonic for blog content scaling, with Jasper noted for its templates and ease of use.",
                "information_from_competitor_content": "Jasper is highlighted as a top choice for marketers and small teams needing to produce large volumes of blog content efficiently."
              }
            ],
            "overall_findings": "Jasper demonstrates strong visibility across all tested queries, consistently appearing in top positions within comparison articles, reviews, and feature breakdowns. Its own website is frequently linked or referenced. Jasper is recognized as a leading AI writing tool for marketers, small businesses, and teams focused on scaling content. Competing tools like Writer, Writesonic, and Draft are also visible, often in direct comparison to Jasper. There are no significant gaps in Jasper's AI visibility for its core market positioning.",
            "queries_with_other_content": 6,
            "queries_with_competitor_content": 6
          }
        ]
      },
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        {
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor3_ai_visibility",
            'initial_data': {
        "competitor_name": "Grammarly Business",
        "platform_results": [
          {
            "query_results": [
              {
                "query_text": "best AI writing assistant for enterprise teams",
                "result_summary": "Grammarly Business is referenced in several comparison articles and review platforms as a leading AI writing assistant for enterprise teams, but it is often compared side-by-side with other AI writing tools. Its own content does not dominate the results, but it is consistently mentioned and reviewed.",
                "search_results": [
                  "https://www.yomu.ai/resources/grammarly-vs-ai-writing-assistants-which-one-is-better-for-writers",
                  "https://blog.type.ai/post/ai-writing-tools-comparison-type-vs-grammarly-premium",
                  "https://www.getapp.co.uk/compare/122355/2080225/grammarly-business/vs/wp-ai-writer",
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "other_content_found": [
                  "https://www.yomu.ai/resources/grammarly-vs-ai-writing-assistants-which-one-is-better-for-writers",
                  "https://blog.type.ai/post/ai-writing-tools-comparison-type-vs-grammarly-premium"
                ],
                "competitor_urls_found": [
                  "https://www.getapp.co.uk/compare/122355/2080225/grammarly-business/vs/wp-ai-writer",
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 3,
                "information_from_other_content": "Comparison articles and reviews discuss the strengths and weaknesses of Grammarly and other AI writing assistants for enterprise use.",
                "information_from_competitor_content": "Grammarly Business is highlighted for its grammar and style correction, team collaboration features, and brand consistency tools."
              },
              {
                "query_text": "Grammarly Business vs Writer AI",
                "result_summary": "Direct comparison pages and review platforms feature Grammarly Business and Writer AI side by side, but the results are dominated by third-party review and comparison sites rather than official product pages.",
                "search_results": [
                  "https://www.getapp.co.uk/compare/122355/2080225/grammarly-business/vs/wp-ai-writer",
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools",
                  "https://www.g2.com/compare/ai-writer-vs-grammarly"
                ],
                "other_content_found": [
                  "https://www.g2.com/compare/ai-writer-vs-grammarly"
                ],
                "competitor_urls_found": [
                  "https://www.getapp.co.uk/compare/122355/2080225/grammarly-business/vs/wp-ai-writer",
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 3,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "G2 and other review sites provide user ratings and feature breakdowns for both tools.",
                "information_from_competitor_content": "Grammarly Business is presented with its feature set, pricing, and user ratings for direct comparison."
              },
              {
                "query_text": "AI content governance platform for marketing teams",
                "result_summary": "Grammarly Business is not the primary result for this governance-focused query. Instead, other platforms and review sites discussing broader AI content governance solutions appear. Grammarly is only mentioned in passing, if at all.",
                "search_results": [
                  "https://www.yomu.ai/resources/grammarly-vs-ai-writing-assistants-which-one-is-better-for-writers"
                ],
                "other_content_found": [
                  "https://www.yomu.ai/resources/grammarly-vs-ai-writing-assistants-which-one-is-better-for-writers"
                ],
                "competitor_urls_found": [],
                "competitor_content_found": "false",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 0,
                "information_from_other_content": "Comparison articles discuss AI writing assistants but do not position Grammarly Business as a governance platform.",
                "information_from_competitor_content": ""
              },
              {
                "query_text": "Grammarly Business enterprise features",
                "result_summary": "Feature breakdowns for Grammarly Business are present on review and comparison sites, but the official Grammarly website does not appear as a top result. Third-party platforms provide detailed lists of features relevant to enterprise users.",
                "search_results": [
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "other_content_found": [
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "competitor_urls_found": [
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Capterra provides a detailed feature list and user reviews for Grammarly Business.",
                "information_from_competitor_content": "Highlights include grammar and style correction, team collaboration, brand consistency, and integration options."
              },
              {
                "query_text": "alternatives to Grammarly Business for content teams",
                "result_summary": "Comparison and review articles dominate the results, listing Grammarly Business alongside other AI writing tools. The competitor is mentioned but not always as the primary focus.",
                "search_results": [
                  "https://www.yomu.ai/resources/grammarly-vs-ai-writing-assistants-which-one-is-better-for-writers",
                  "https://blog.type.ai/post/ai-writing-tools-comparison-type-vs-grammarly-premium"
                ],
                "other_content_found": [
                  "https://www.yomu.ai/resources/grammarly-vs-ai-writing-assistants-which-one-is-better-for-writers",
                  "https://blog.type.ai/post/ai-writing-tools-comparison-type-vs-grammarly-premium"
                ],
                "competitor_urls_found": [],
                "competitor_content_found": "false",
                "ranking_of_other_content": 1,
                "ranking_of_competitor_content": 0,
                "information_from_other_content": "Articles compare Grammarly to other AI writing assistants, discussing strengths and weaknesses for content teams.",
                "information_from_competitor_content": ""
              },
              {
                "query_text": "Grammarly Business AI capabilities",
                "result_summary": "Review and comparison platforms provide information about Grammarly Business's AI features, but official product pages are not prominent. The focus is on grammar, style, and writing assistance rather than advanced generative AI.",
                "search_results": [
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools",
                  "https://www.g2.com/compare/ai-writer-vs-grammarly"
                ],
                "other_content_found": [
                  "https://www.g2.com/compare/ai-writer-vs-grammarly"
                ],
                "competitor_urls_found": [
                  "https://www.capterra.ae/compare/170306/1048595/grammarly-business/vs/ai-writer-tools"
                ],
                "competitor_content_found": "true",
                "ranking_of_other_content": 2,
                "ranking_of_competitor_content": 1,
                "information_from_other_content": "Comparison sites discuss Grammarly's AI-driven grammar and style correction.",
                "information_from_competitor_content": "Grammarly Business is described as using AI for grammar, tone, and writing style analysis."
              }
            ],
            "overall_findings": "Grammarly Business has strong visibility in third-party review and comparison sites, especially for queries focused on enterprise features, direct comparisons, and AI writing assistance. However, its own official website content is rarely the top result; instead, platforms like Capterra, G2, and independent blogs dominate. For governance- and alternative-focused queries, Grammarly is mentioned but not positioned as the primary solution. The competitor's content is present in about half of the queries, but mostly through review platforms rather than direct product pages.",
            "queries_with_other_content": 6,
            "queries_with_competitor_content": 4
          }
        ]
      },
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]

    # Define cleanup docs
    cleanup_docs: List[CleanupDocInfo] = [
        # AI Visibility Documents
        {
            'namespace': BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_AI_VISIBILITY_TEST_DOCNAME,
            'is_versioned': BLOG_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
            'is_versioned': BLOG_COMPANY_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        {
            'namespace': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
            'is_versioned': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        # Competitor AI Visibility Documents
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
            'namespace': competitor_ai_visibility_namespace,
            'docname': "competitor3_ai_visibility",
            'is_versioned': BLOG_COMPETITOR_AI_VISIBILITY_TEST_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        },
        # Output Document
        {
            'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION7_NAMESPACE_TEMPLATE.format(item=company_name),
            'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION7_DOCNAME,
            'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION7_IS_VERSIONED,
            'is_shared': False,
            'is_system_entity': False
        }
    ]

    # Output validation function
    async def validate_ai_discoverability_gaps_output(outputs) -> bool:
        """
        Validates the output from the AI discoverability gaps analysis workflow.
        """
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        assert 'ai_discoverability_gaps_analysis' in outputs, "Validation Failed: 'ai_discoverability_gaps_analysis' missing."
        assert 'storage_paths' in outputs, "Validation Failed: 'storage_paths' missing."
        
        if 'ai_discoverability_gaps_analysis' in outputs:
            analysis = outputs['ai_discoverability_gaps_analysis']
            
            # Validate required fields
            assert 'current_visibility_status' in analysis, "Output missing 'current_visibility_status' field"
            assert 'missing_ai_elements' in analysis, "Output missing 'missing_ai_elements' field"
            assert 'content_format_improvements' in analysis, "Output missing 'content_format_improvements' field"
            assert 'platform_specific_opportunities' in analysis, "Output missing 'platform_specific_opportunities' field"
            
            # Validate current visibility status
            visibility_status = analysis['current_visibility_status']
            assert 'company_ai_score' in visibility_status, "Missing 'company_ai_score' in visibility status"
            assert 'executive_ai_score' in visibility_status, "Missing 'executive_ai_score' in visibility status"
            assert 'content_citation_rate' in visibility_status, "Missing 'content_citation_rate' in visibility status"
            assert 'platform_performance' in visibility_status, "Missing 'platform_performance' in visibility status"
            
            # Validate data types
            assert isinstance(analysis['missing_ai_elements'], list), "'missing_ai_elements' should be a list"
            assert isinstance(analysis['content_format_improvements'], list), "'content_format_improvements' should be a list"
            assert isinstance(analysis['platform_specific_opportunities'], list), "'platform_specific_opportunities' should be a list"
            assert isinstance(visibility_status['platform_performance'], list), "'platform_performance' should be a list"
            
            print(f"✓ AI discoverability gaps analysis validated successfully")
            print(f"✓ Company AI Score: {visibility_status['company_ai_score']}")
            print(f"✓ Executive AI Score: {visibility_status['executive_ai_score']}")
            print(f"✓ Content Citation Rate: {visibility_status['content_citation_rate']}")
            print(f"✓ Missing AI Elements: {len(analysis['missing_ai_elements'])}")
            print(f"✓ Content Format Improvements: {len(analysis['content_format_improvements'])}")
            print(f"✓ Platform Opportunities: {len(analysis['platform_specific_opportunities'])}")
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
        validate_output_func=validate_ai_discoverability_gaps_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )

    print(f"--- {test_name} Finished ---")
    if final_run_outputs and 'ai_discoverability_gaps_analysis' in final_run_outputs:
        analysis = final_run_outputs['ai_discoverability_gaps_analysis']
        visibility_status = analysis['current_visibility_status']
        
        print("\nAI Discoverability Gaps Analysis:")
        print(f"Company AI Score: {visibility_status['company_ai_score']}")
        print(f"Executive AI Score: {visibility_status['executive_ai_score']}")
        print(f"Content Citation Rate: {visibility_status['content_citation_rate']}")
        print(f"Platform Performance: {visibility_status['platform_performance']}")
        print(f"Missing AI Elements: {analysis['missing_ai_elements']}")
        print(f"Content Format Improvements: {analysis['content_format_improvements']}")
        print(f"Platform Opportunities: {list(analysis['platform_specific_opportunities'].keys())}")
        print(f"Stored at: {final_run_outputs['storage_paths']}")

if __name__ == "__main__":
    try:
        asyncio.run(main_test_section7_ai_discoverability_gaps_workflow())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}") 