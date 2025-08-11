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
from kiwi_client.workflows.document_models.customer_docs import (
    # Content Analysis
    CONTENT_ANALYSIS_DOCNAME,
    CONTENT_ANALYSIS_NAMESPACE_TEMPLATE
)

from kiwi_client.workflows_for_blog_teammate.document_models.customer_docs import (
    # Content Analysis
    # Web Audit
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_DOCNAME,
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_VERSIONED,
    # AI Visibility Test
    BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED,
    # Section 3 Diagnostic Report
    BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_SECTION3_IS_VERSIONED,
)

from kiwi_client.workflows_for_blog_teammate.llm_inputs.blog_web_AI_visibility_content_diagnostics import (
    GENERATION_SCHEMA,
    USER_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_TEMPLATE,
)

# --- Workflow Configuration Constants ---

# LLM Configuration
LLM_PROVIDER = "openai"
GENERATION_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4000

# Use the imported schema directly
GENERATION_SCHEMA_JSON = GENERATION_SCHEMA

# Prompt template variables and construct options
USER_PROMPT_TEMPLATE_VARIABLES = {
    "web_presence_audit": None,
    "ai_visibility_test": None  
}

USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {
    "web_presence_audit": "web_presence_audit",
    "ai_visibility_test": "ai_visibility_test"
}

SYSTEM_PROMPT_TEMPLATE_VARIABLES = {
    "schema": GENERATION_SCHEMA_JSON
}

### INPUTS ###
INPUT_FIELDS = {
    "customer_context_doc_configs": {
        "type": "list",
        "required": True,
        "description": "List of document identifiers (namespace/docname pairs) for customer context documents."
    },
    "entity_username": { 
        "type": "str", 
        "required": True, 
        "description": "Name of the entity to analyze digital authority for."
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

        # --- 2. Load All Context Documents ---
        "load_all_context_docs": {
            "node_id": "load_all_context_docs",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "customer_context_doc_configs",
                "global_is_shared": False,
                "global_is_system_entity": False,
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
                    }
                }
            }
        },

        # --- 4. Generate Digital Authority Analysis ---
        "generate_content": {
            "node_id": "generate_content",
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

        # --- 5. Store Analysis Results ---
        "store_analysis": {
            "node_id": "store_analysis",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {"is_versioned": BLOG_CONTENT_DIAGNOSTIC_SECTION3_IS_VERSIONED, "operation": "upsert"},
                "global_is_shared": False,
                "global_is_system_entity": False,
                "store_configs": [
                    {
                        "input_field_path": "structured_output",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "entity_username",
                                "static_docname": BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME,
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
                        "digital_authority_analysis": {
                            "type": "dict",
                            "required": True,
                            "description": "The comprehensive digital authority status analysis"
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
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },
        
        # Input -> Load All Context Docs
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "load_all_context_docs", 
            "mappings": [
                { "src_field": "customer_context_doc_configs", "dst_field": "customer_context_doc_configs" },
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },
        
        # Load All Context Docs -> State
        { 
            "src_node_id": "load_all_context_docs", 
            "dst_node_id": "$graph_state", 
            "mappings": [
                { "src_field": "web_presence_audit", "dst_field": "web_presence_audit" },
                { "src_field": "ai_visibility_test", "dst_field": "ai_visibility_test" }
            ]
        },

        # Load All Context Docs -> Construct Prompt (Direct connection)
        { 
            "src_node_id": "load_all_context_docs", 
            "dst_node_id": "construct_prompt"
        },
        
        # State -> Construct Prompt
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "construct_prompt", 
            "mappings": [
                { "src_field": "web_presence_audit", "dst_field": "web_presence_audit" },
                { "src_field": "ai_visibility_test", "dst_field": "ai_visibility_test" }
            ]
        },
        
        # Construct Prompt -> Generate Content
        { 
            "src_node_id": "construct_prompt", 
            "dst_node_id": "generate_content", 
            "mappings": [
                { "src_field": "user_prompt", "dst_field": "user_prompt" },
                { "src_field": "system_prompt", "dst_field": "system_prompt" }
            ]
        },
        
        # Generate Content -> Store Analysis
        { 
            "src_node_id": "generate_content", 
            "dst_node_id": "store_analysis", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "structured_output" }
            ]
        },
        
        # State -> Store Analysis
        { 
            "src_node_id": "$graph_state", 
            "dst_node_id": "store_analysis", 
            "mappings": [
                { "src_field": "entity_username", "dst_field": "entity_username" }
            ]
        },
        
        # Store Analysis -> Output
        { 
            "src_node_id": "store_analysis", 
            "dst_node_id": "output_node", 
            "mappings": [
                { "src_field": "paths_processed", "dst_field": "storage_paths" }
            ]
        },
        
        # Generate Content -> Output (for direct access)
        { 
            "src_node_id": "generate_content", 
            "dst_node_id": "output_node", 
            "mappings": [
                { "src_field": "structured_output", "dst_field": "digital_authority_analysis" }
            ]
        }
    ],

    "input_node_id": "input_node",
    "output_node_id": "output_node"
}

# --- Test Execution Logic ---
async def main_test_section3_content_diagnostics():
    """
    Test for Section 3 Content Diagnostics Workflow.
    """
    test_name = "Section 3 Content Diagnostics Workflow Test"
    print(f"--- Starting {test_name} --- ")

    # Example Inputs
    entity_username = "test_entity"
    
    test_context_docs = [
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_NAMESPACE_TEMPLATE, 
                "input_namespace_field": "entity_username",
                "static_docname": BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_DOCNAME,
            },
            "output_field_name": "web_presence_audit"
        },
        {
            "filename_config": {
                "input_namespace_field_pattern": BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE, 
                "input_namespace_field": "entity_username",
                "static_docname": BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
            },
            "output_field_name": "ai_visibility_test"
        }
    ]
    
    test_inputs = {
        "customer_context_doc_configs": test_context_docs,
        "entity_username": entity_username
    }

    # Define setup documents
    setup_docs: List[SetupDocInfo] = [
        {
            'namespace': CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': CONTENT_ANALYSIS_DOCNAME,
            'initial_data': {
        "theme_reports": [
          {
            "theme_id": "theme_1",
            "theme_name": "Enterprise Agentic AI Transformation",
            "hook_analysis": {
              "hook_text": "This is it. \n\nThis is the conversation every leadership team needs to be having right now.",
              "hook_type": {
                "type": "Bold Claim / Urgency",
                "metrics": [
                  {
                    "metric_name": "Hooks starting with bold claim or urgency",
                    "metric_value": 6
                  },
                  {
                    "metric_name": "Hooks with open questions",
                    "metric_value": 2
                  },
                  {
                    "metric_name": "Hooks using metaphor/analogy",
                    "metric_value": 3
                  }
                ]
              },
              "hook_description": "Posts commonly start with bold, attention-grabbing claims (\"This is it.\"), urgent calls-to-action, or provocative industry analogies (assembly lines, trains, 'life suck', 'the factory is over'). Questions and challenge frames ('Why hasn't your company transformed yet?') are sometimes used to spark curiosity. These openings set stakes high, challenge the status quo, and quickly establish the post’s relevance for decision-makers.",
              "engagement_correlation": [
                {
                  "average_likes": 900,
                  "average_reposts": 50,
                  "average_comments": 72
                }
              ]
            },
            "recent_topics": [
              {
                "date": "2025-07-17",
                "topic": "Orchestration Graph as new enterprise map",
                "summary": "Argues for a fundamental shift for enterprises to rewire around AI-powered orchestration graphs, not traditional org charts.",
                "engagement": {
                  "average_likes": 375,
                  "average_reposts": 29,
                  "average_comments": 36
                }
              },
              {
                "date": "2025-06-25",
                "topic": "Rewriting SDLC for agentic AI",
                "summary": "Highlights how software engineering practices must evolve when managing agentic systems, with a call for new standards like 'Agile for Agents.'",
                "engagement": {
                  "average_likes": 402,
                  "average_reposts": 55,
                  "average_comments": 38
                }
              },
              {
                "date": "2025-06-10",
                "topic": "Recognition for AI transformation (CNBC Disruptor 50)",
                "summary": "Celebrates inclusion on the CNBC Disruptor 50 and reflects on progress in enabling agentic AI for business transformation.",
                "engagement": {
                  "average_likes": 767,
                  "average_reposts": 36,
                  "average_comments": 63
                }
              },
              {
                "date": "2025-05-29",
                "topic": "Interoperability, agent builders, A2A",
                "summary": "Discusses real-world requirements (interoperability, builder experience) for enterprise agentic AI platforms and the marketing hype.",
                "engagement": {
                  "average_likes": 981,
                  "average_reposts": 52,
                  "average_comments": 79
                }
              },
              {
                "date": "2025-05-15",
                "topic": "Deep-dive: Research agent for workflow automation",
                "summary": "Showcases a concrete example agent that automates research, producing actionable decision support.",
                "engagement": {
                  "average_likes": 236,
                  "average_reposts": 24,
                  "average_comments": 12
                }
              },
              {
                "date": "2025-01-27",
                "topic": "Market disruption, true AI transformation, DeepSeek",
                "summary": "Debunks market overreaction to new models and stresses that business process transformation is the true bottleneck.",
                "engagement": {
                  "average_likes": 1755,
                  "average_reposts": 86,
                  "average_comments": 145
                }
              }
            ],
            "tone_analysis": {
              "sentiment": {
                "label": "Positive / Visionary",
                "average_score": 0.74
              },
              "dominant_tones": [
                "Visionary",
                "Urgent",
                "Confident",
                "Challenging",
                "Instructive"
              ],
              "tone_description": "Posts promote a sense of radical possibility (visionary) while issuing strong challenges to conventional thinking (challenging/urgent). There’s an undercurrent of optimism for what well-implemented AI can achieve, with an authoritative, confident voice. Explicit calls to action and imperative language are used to motivate enterprise audiences to act swiftly and rethink core processes.",
              "tone_distribution": [
                {
                  "tone": "Visionary",
                  "percentage": 40
                },
                {
                  "tone": "Urgent/Challenging",
                  "percentage": 30
                },
                {
                  "tone": "Instructive",
                  "percentage": 15
                },
                {
                  "tone": "Positive",
                  "percentage": 10
                },
                {
                  "tone": "Neutral",
                  "percentage": 5
                }
              ]
            },
            "linguistic_style": {
              "emoji_usage": {
                "metrics": [
                  {
                    "emoji": "🔥",
                    "average_frequency": 0.4
                  },
                  {
                    "emoji": "👉",
                    "average_frequency": 0.2
                  },
                  {
                    "emoji": "🤯",
                    "average_frequency": 0.2
                  },
                  {
                    "emoji": "💼",
                    "average_frequency": 0.1
                  }
                ],
                "category": "Sometimes"
              },
              "unique_terms": [
                {
                  "term": "Agentic",
                  "example": "Agentic orchestration for marketing is here...",
                  "frequency": 14
                },
                {
                  "term": "Orchestration",
                  "example": "The real map is the Orchestration Graph...",
                  "frequency": 9
                },
                {
                  "term": "AI-first",
                  "example": "Destination: becoming an AI-first company.",
                  "frequency": 8
                },
                {
                  "term": "Rewiring",
                  "example": "...rewiring their business to be AI-first.",
                  "frequency": 6
                },
                {
                  "term": "Supervision",
                  "example": "...new bottleneck is our ability to direct, govern, and orchestrate...",
                  "frequency": 5
                },
                {
                  "term": "Continuous learning",
                  "example": "...continuous iteration...learning fast + iterating.",
                  "frequency": 3
                }
              ],
              "linguistic_description": "The style leans formal but is notably modern, energetic, and accessible. Long, structured sentences are used alongside punchy fragments.\n- Bullet points and numbered lists organize information.\n- Repetition of thematically loaded terms strengthens key concepts ('agentic', 'orchestration', 'AI-first', etc).\n- Occasional bold formatting for emphasis; rare mild profanity for effect.\n- Limited but impactful emoji use (especially in signposting key ideas and adding energy)."
            },
            "theme_description": "- Main topics: Transitioning enterprises to AI-first operations, implementation of agentic AI systems, orchestration layers, and rewiring business processes with AI-driven automation and decision-making.\n- Purpose/intent: To articulate the fundamental changes required for enterprises to fully leverage AI—moving beyond simple productivity gains to wholesale transformation of workflows and organizational structure.\n- Recurring patterns: Focus on the need for new structures (like orchestration graphs), emphasis on controls, governance, continuous learning, and scalable systems; repeated use of terms like 'AI-first', 'rewiring', 'orchestration', and 'agentic'.",
            "structure_analysis": {
              "conciseness": {
                "level": "Moderately Concise",
                "metrics": [
                  {
                    "metric_name": "Average words per post",
                    "metric_value": 350
                  },
                  {
                    "metric_name": "Average paragraph length (sentences)",
                    "metric_value": 2.5
                  }
                ],
                "description": "While posts are longer than typical LinkedIn updates, they are well-organized, relying on concise ideas per paragraph and frequent line breaks. Bullets and lists enhance scannability. Short, emphatic openings and conclusions bookend longer exposition in the body."
              },
              "post_format": {
                "example": "Structure:\u0000How do we manage systems, not just people?\nStrategy:\u0000What work do we insource...?",
                "metrics": [
                  {
                    "metric_name": "Posts with lists/bullets",
                    "metric_value": 80
                  },
                  {
                    "metric_name": "Posts with headline-style section labels",
                    "metric_value": 45
                  }
                ],
                "primary_format": "Bulleted/sectioned analysis with bolded headings and punchy line breaks"
              },
              "data_intensity": {
                "level": "Moderate",
                "example": "With just binary feedback and reinforcement learning on the skill of reflection itself, the models got better at reasoning on their own – and even outperformed models 10x their size.",
                "metrics": [
                  {
                    "metric_name": "Posts referencing data, research, or benchmarks",
                    "metric_value": 4
                  },
                  {
                    "metric_name": "Industry jargon per post (avg.)",
                    "metric_value": 7
                  }
                ]
              },
              "common_structures": [
                {
                  "frequency": "Frequent",
                  "structure": "Opening with strong claim or context → description of current state → vision for future state → specific actionable examples or requirements (bullets/lists) → call to action"
                },
                {
                  "frequency": "Occasional",
                  "structure": "Metaphor-based framing followed by explanation (e.g., 'train line', 'factory to OS', 'assembly line analogy')"
                },
                {
                  "frequency": "Occasional",
                  "structure": "Mini-case studies or anecdotes ('In this video, the Palmyra X5 agent...')"
                }
              ],
              "structure_description": "Posts favor a logical, layered flow from context through challenge to resolution: (1) Start with a bold statement or a metaphor, (2) introduce a business/market problem, (3) detail industry requirements or showcase real-world use, (4) end with an imperative or call to action. Bullets and headings break up text, allowing dense concepts to stay readable. References to research, benchmarks, or external articles add credibility."
            }
          },
          {
            "theme_id": "theme_2",
            "theme_name": "Customer Success Stories & Platform Use Cases",
            "hook_analysis": {
              "hook_text": "There's a reason +150 of the F500 are either customers of Writer already or are on our waitlist.",
              "hook_type": {
                "type": "Bold Claim/Statistic",
                "metrics": [
                  {
                    "metric_name": "Hooks with bold statistics or numbers",
                    "metric_value": 4
                  },
                  {
                    "metric_name": "Hooks using event countdown or urgency",
                    "metric_value": 2
                  },
                  {
                    "metric_name": "Hooks referencing customer wins by name",
                    "metric_value": 3
                  }
                ]
              },
              "hook_description": "Hooks often immediately state impressive metrics, customer adoption figures, or notable client names to capture attention. This is highly effective for building credibility and priming the reader for deeper examples or invitations. Most successful posts blend a high-impact number (e.g., '150 of the F500') with a clear, confident assertion or industry trigger ('mission-critical work', 'LIVE now!'). To replicate: Open with a verifiable, concrete number or a direct nod to a respected customer, then quickly bridge to a specific product demonstration or business result.",
              "engagement_correlation": [
                {
                  "average_likes": 420,
                  "average_reposts": 30,
                  "average_comments": 33
                }
              ]
            },
            "recent_topics": [
              {
                "date": "2025-04-15",
                "topic": "F500 Adoption and Live Demo",
                "summary": "Highlighted 150+ Fortune 500 companies using or waiting for Writer, with real customer demos.",
                "engagement": {
                  "average_likes": 300,
                  "average_reposts": 29,
                  "average_comments": 17
                }
              },
              {
                "date": "2025-04-10",
                "topic": "Forbes Coverage and AI HQ Event Launch",
                "summary": "Thanked Forbes for featuring Writer's impact; promoted AI HQ demonstration event.",
                "engagement": {
                  "average_likes": 1539,
                  "average_reposts": 31,
                  "average_comments": 121
                }
              },
              {
                "date": "2025-03-28",
                "topic": "Customer Examples – Marriott & Commvault",
                "summary": "Shared shipped agentic AI projects by notable enterprise customers.",
                "engagement": {
                  "average_likes": 334,
                  "average_reposts": 24,
                  "average_comments": 24
                }
              },
              {
                "date": "2025-02-04",
                "topic": "Internal NDA App – Writer Use Case",
                "summary": "Described app for automating NDAs internally, showing non-engineer empowerment.",
                "engagement": {
                  "average_likes": 308,
                  "average_reposts": 23,
                  "average_comments": 15
                }
              },
              {
                "date": "2025-02-03",
                "topic": "Salesforce Case Study",
                "summary": "Details on Salesforce's internal use, ROI, adoption, and change management using Writer.",
                "engagement": {
                  "average_likes": 340,
                  "average_reposts": 28,
                  "average_comments": 13
                }
              },
              {
                "date": "2024-12-13",
                "topic": "Customer Community Event – AI Leaders Forum",
                "summary": "Recap of customer forum with enterprise leaders and notable keynote (Katzenberg).",
                "engagement": {
                  "average_likes": 328,
                  "average_reposts": 8,
                  "average_comments": 8
                }
              }
            ],
            "tone_analysis": {
              "sentiment": {
                "label": "Positive",
                "average_score": 0.85
              },
              "dominant_tones": [
                "Confident",
                "Celebratory",
                "Inspirational",
                "Grateful"
              ],
              "tone_description": "Posts in this theme are consistently upbeat, projecting confidence in Writer's market impact and gratitude toward customers and partners. Language is motivating ('SO excited', 'absolutely LOVE', 'incredible leadership'), highlighting big wins and ambitious outcomes. Emotional highs are underscored by warmth (shoutouts, thank-yous, excitement for the future). To replicate this tone, interweave facts with positive adjectives and acknowledge collaborators.",
              "tone_distribution": [
                {
                  "tone": "Confident",
                  "percentage": 40
                },
                {
                  "tone": "Inspirational",
                  "percentage": 20
                },
                {
                  "tone": "Grateful",
                  "percentage": 20
                },
                {
                  "tone": "Celebratory",
                  "percentage": 15
                },
                {
                  "tone": "Neutral/Informative",
                  "percentage": 5
                }
              ]
            },
            "linguistic_style": {
              "emoji_usage": {
                "metrics": [
                  {
                    "emoji": "🙏",
                    "average_frequency": 0.3
                  },
                  {
                    "emoji": "🚀",
                    "average_frequency": 0.2
                  },
                  {
                    "emoji": "💥",
                    "average_frequency": 0.3
                  },
                  {
                    "emoji": "🧑‍💼",
                    "average_frequency": 0.1
                  },
                  {
                    "emoji": "🤲",
                    "average_frequency": 0.1
                  }
                ],
                "category": "Sometimes"
              },
              "unique_terms": [
                {
                  "term": "mission-critical",
                  "example": "agentic AI for mission-critical work",
                  "frequency": 4
                },
                {
                  "term": "real ROI",
                  "example": "DELIVERING ON THE PROMISE OF GENERATIVE AI in their companies — at scale, with real ROI",
                  "frequency": 3
                },
                {
                  "term": "agentic AI",
                  "example": "You all have seen me tease agentic AI from Writer for months.",
                  "frequency": 5
                },
                {
                  "term": "adoption",
                  "example": "3,000 active users, including 50 champions using Writer's AI Studio to build new apps",
                  "frequency": 2
                }
              ],
              "linguistic_description": "Style is informal yet professional, with conversational phrasing ('you all', 'so excited'), imperative calls to action, and strong, vivid language. Posts blend technical terms (agentic AI, adoption, workflows) with easily digestible benefits. Parentheticals and em-dashes add emphasis or clarification. Use of emojis is moderate, mainly to magnify excitement or gratitude."
            },
            "theme_description": "This theme showcases real-world case studies and customer testimonials to highlight how large enterprises deploy Writer's agentic AI tools. Posts emphasize the value delivered—often quantified in saved time, increased adoption, and business impact—and frequently name-drop impressive customer brands or cover live events, demos, or community gatherings. The purpose is clear: build credibility, illustrate transformation, and encourage others to follow suit.",
            "structure_analysis": {
              "conciseness": {
                "level": "Moderately Concise",
                "metrics": [
                  {
                    "metric_name": "Average word count",
                    "metric_value": 180
                  },
                  {
                    "metric_name": "Average paragraph count",
                    "metric_value": 4.5
                  }
                ],
                "description": "Posts tend to lay out detailed examples and multiple points, but avoid overly long paragraphs. Bulleted or emoji-led highlights break up information. Conciseness is balanced: enough detail for credibility, but punchy enough to maintain interest."
              },
              "post_format": {
                "example": "💥 Mission-critical use cases: To support the launch of Agentforce... 💥 ROI: One work day saved per person per week...",
                "metrics": [
                  {
                    "metric_name": "Format with bulleting (emoji or hyphen)",
                    "metric_value": "60%"
                  },
                  {
                    "metric_name": "Single-story, narrative format",
                    "metric_value": "40%"
                  }
                ],
                "primary_format": "Bulleted Lists with Emojis & Inline Narratives"
              },
              "data_intensity": {
                "level": "High",
                "example": "One work day saved per person per week... 3,000 active users, including 50 champions...",
                "metrics": [
                  {
                    "metric_name": "Average statistics/case metrics per post",
                    "metric_value": 3
                  },
                  {
                    "metric_name": "Named customers per post",
                    "metric_value": 2
                  }
                ]
              },
              "common_structures": [
                {
                  "frequency": "Very Common",
                  "structure": "Opening bold claim/stat, followed by 2-4 customer ROI or workflow metrics, and call-to-action link."
                },
                {
                  "frequency": "Common",
                  "structure": "Screenshot or demo/video announcement, supported with quotable customer outcomes."
                },
                {
                  "frequency": "Sometimes",
                  "structure": "Single, longer-form customer story weaving narrative and data with personal reflection."
                }
              ],
              "structure_description": "Most posts open with a high-impact claim or reference, move quickly into customer names and metrics, and wrap with a link to a live demo, event, or downloadable story. Bulleted highlight sections using emojis draw the eye to results. To emulate: Start with a jaw-dropping stat or customer, summarize 2-3 key impacts using short bulleted phrases, and finish with a strong, actionable link or CTA."
            }
          },
          {
            "theme_id": "theme_3",
            "theme_name": "Product Innovation and Technical Differentiation",
            "hook_analysis": {
              "hook_text": "How COOL?!\n\nWRITER was just named a Cool Vendor in the 2025 Gartner® Cool Vendors™ report for AI Agent Development.",
              "hook_type": {
                "type": "Bold Claim or Announcement",
                "metrics": [
                  {
                    "metric_name": "Bold Claims/Announcements in Openings",
                    "metric_value": 5
                  },
                  {
                    "metric_name": "Questions in Hooks",
                    "metric_value": 2
                  },
                  {
                    "metric_name": "Hooks beginning with technical comparison",
                    "metric_value": 2
                  }
                ]
              },
              "hook_description": "Most posts use bold announcements, technical firsts, or industry recognition as their hook, often paired with rhetorical or leading questions to frame the post's core differentiation. These opening lines immediately establish authority, spark curiosity, and signal innovation, which drives higher engagement. Replicating this involves starting with a clear, high-impact milestone, then transitioning into relevance and evidence.",
              "engagement_correlation": [
                {
                  "average_likes": 400,
                  "average_reposts": 30,
                  "average_comments": 15
                }
              ]
            },
            "recent_topics": [
              {
                "date": "2025-06-05",
                "topic": "Gartner Cool Vendor Award & Enterprise AI Platform Differentiation",
                "summary": "Announcement of Gartner recognition, discussion of fragmentation in AI agent tooling, and summary of unique value in AI HQ and Agent Builder platforms.",
                "engagement": {
                  "average_likes": 253,
                  "average_reposts": 15,
                  "average_comments": 9
                }
              },
              {
                "date": "2025-04-28",
                "topic": "Launch of Palmyra X5 on AWS Bedrock",
                "summary": "Detailed breakdown of Palmyra X5 technical features (speed, cost, scale), context window capabilities, and AWS partnership.",
                "engagement": {
                  "average_likes": 899,
                  "average_reposts": 69,
                  "average_comments": 38
                }
              },
              {
                "date": "2025-03-27",
                "topic": "Self-Evolving Models & Future of AI Learning",
                "summary": "Explains technical leap to self-evolving LLMs, their business implications, and differentiators for enterprise use.",
                "engagement": {
                  "average_likes": 268,
                  "average_reposts": 29,
                  "average_comments": 19
                }
              },
              {
                "date": "2025-02-27",
                "topic": "Knowledge Graphs & Graph-based RAG for Agentic AI",
                "summary": "Insight into knowledge graph construction, graph-based retrieval-augmented generation, and uniqueness of Writer’s LLMs for complex enterprise data.",
                "engagement": {
                  "average_likes": 288,
                  "average_reposts": 21,
                  "average_comments": 21
                }
              },
              {
                "date": "2025-02-21",
                "topic": "AI Engineer Summit — Launch of FailSafeQA Benchmark",
                "summary": "Highlights event presence, describes new benchmarking methodology for finance-specific AI tasks, and model comparisons.",
                "engagement": {
                  "average_likes": 263,
                  "average_reposts": 9,
                  "average_comments": 4
                }
              },
              {
                "date": "2025-02-13",
                "topic": "OpenAI Model Updates & Writer’s Financial Compliance Benchmarking",
                "summary": "Technical critique of OpenAI’s approach, unveiling of FailSafeQA, compliance-focused innovation, and results from domain-specific models.",
                "engagement": {
                  "average_likes": 447,
                  "average_reposts": 39,
                  "average_comments": 18
                }
              },
              {
                "date": "2024-12-19",
                "topic": "Launch of Palmyra Creative LLM",
                "summary": "Introduction of a new LLM for creativity, with a focus on accuracy and context-rich outputs, including demonstrations in financial scenarios.",
                "engagement": {
                  "average_likes": 176,
                  "average_reposts": 5,
                  "average_comments": 4
                }
              }
            ],
            "tone_analysis": {
              "sentiment": {
                "label": "Positive",
                "average_score": 0.79
              },
              "dominant_tones": [
                "Confident",
                "Authoritative",
                "Visionary",
                "Analytical"
              ],
              "tone_description": "The posts consistently present with a confident and authoritative tone, underpinned by an analytical and sometimes visionary outlook. Emotional expression centers on excitement about innovation and pride in technical leadership, often paired with subtle competitive critique. The posts feel credible by supporting claims with measurable results, industry benchmarks, and real-world impact. This tone can be replicated by openly quantifying achievements, comparing with alternatives, being direct about industry issues, and projecting optimism about enterprise AI progress.",
              "tone_distribution": [
                {
                  "tone": "Confident",
                  "percentage": 70
                },
                {
                  "tone": "Analytical",
                  "percentage": 60
                },
                {
                  "tone": "Visionary",
                  "percentage": 30
                },
                {
                  "tone": "Critical",
                  "percentage": 25
                },
                {
                  "tone": "Positive",
                  "percentage": 90
                }
              ]
            },
            "linguistic_style": {
              "emoji_usage": {
                "metrics": [
                  {
                    "emoji": "🤝",
                    "average_frequency": 0.3
                  },
                  {
                    "emoji": "💡",
                    "average_frequency": 0.2
                  },
                  {
                    "emoji": "🧭",
                    "average_frequency": 0.1
                  }
                ],
                "category": "Sparingly"
              },
              "unique_terms": [
                {
                  "term": "agentic",
                  "example": "Agentic work orchestrations requires real-time agentic collaboration...",
                  "frequency": 7
                },
                {
                  "term": "RAG",
                  "example": "RAG still incredibly powerful tool in the tool belt but... our approach to this massive context window simplifies the approach...",
                  "frequency": 12
                },
                {
                  "term": "self-evolving",
                  "example": "But that was before self-evolving LLMs.",
                  "frequency": 6
                },
                {
                  "term": "context window",
                  "example": "Palmyra X5 can process a full million-token prompt...",
                  "frequency": 8
                },
                {
                  "term": "knowledge graphs",
                  "example": "Enterprises will need knowledge graphs for agentic AI quality and autonomy...",
                  "frequency": 5
                }
              ],
              "linguistic_description": "Language is formal and specialized, leveraging enterprise AI and technical jargon (e.g., 'agentic', 'RAG', 'context window', 'self-evolving'). Occasional enthusiasm is signaled by capitalization ('BLAZING FAST'), rhetorical questions, and exclamation marks. Posts are structured for clarity, using bullet points, short paragraphs, and in-line bolding/star formatting for emphasis. Emoji and informal punctuation are used sparingly, typically for contextual highlights or celebration."
            },
            "theme_description": "- Main topics: Introduction of new models (e.g., Palmyra X5, Palmyra Creative), AI platform features (AI HQ, Agent Builder), groundbreaking research (self-evolving models, FailSafeQA), and industry benchmarks.\n- Purpose/intent: To communicate Writer’s relentless product development, technical leadership, and deep specialization for enterprise AI needs, with an emphasis on accuracy, speed, low hallucination, interoperability, and new industry standards.\n- Recurring patterns: Technical breakdowns of platform improvements, claims of industry-first or best-in-class abilities, critiques/comparisons with other vendors or approaches, and focus on solving real enterprise problems.",
            "structure_analysis": {
              "conciseness": {
                "level": "Moderately Concise",
                "metrics": [
                  {
                    "metric_name": "Average Sentence Length (words)",
                    "metric_value": 18
                  },
                  {
                    "metric_name": "Average Paragraph Length (lines)",
                    "metric_value": 3
                  },
                  {
                    "metric_name": "Average Word Count (per post)",
                    "metric_value": 340
                  }
                ],
                "description": "Posts are moderately concise, generally ranging from 250–400 words, with succinct paragraphs. Sentences are clear but may get technical and detailed, especially when breaking down specific features or comparisons."
              },
              "post_format": {
                "example": "- Problem statement\n- Claim/announcement\n- Technical breakdown (features/metrics)\n- Comparison/critique\n- Call to action/demonstration link",
                "metrics": [
                  {
                    "metric_name": "Number of Posts Using Bullet/Numbered Lists",
                    "metric_value": 4
                  },
                  {
                    "metric_name": "Posts with Links to Demos or Research",
                    "metric_value": 5
                  }
                ],
                "primary_format": "Multi-section narrative with technical breakdowns and bulleted feature lists"
              },
              "data_intensity": {
                "level": "High",
                "example": "Palmyra X5 can process a full million-token prompt in ~22 seconds and fire off multi-turn function-calls in ~300 milliseconds, while costing 3–4× less than GPT-4.1.",
                "metrics": [
                  {
                    "metric_name": "Average Quantitative Claims per Post",
                    "metric_value": 5
                  },
                  {
                    "metric_name": "Benchmark/Performance Reference Frequency",
                    "metric_value": 4
                  }
                ]
              },
              "common_structures": [
                {
                  "frequency": "Very Frequent",
                  "structure": "Opening statement with bold claim or recognition (award, launch, industry first)"
                },
                {
                  "frequency": "Frequent",
                  "structure": "Section with clear technical details and data (metrics, benchmarks, cost/speed numbers)"
                },
                {
                  "frequency": "Frequent",
                  "structure": "Comparison to competitor or market status quo"
                },
                {
                  "frequency": "Sometimes",
                  "structure": "Rhetorical question or call to action at end (link to resources or demo)"
                }
              ],
              "structure_description": "Posts consistently lead with a high-impact announcement, followed by an in-depth technical breakdown. There is logical ordering—problem/pain point, innovative solution, quantitative backing, then competitive context. Bullets and paragraph breaks are used to aid readability. High data density and well-placed CTAs (demo/video link, research download) serve to establish credibility and drive audience action."
            }
          },
          {
            "theme_id": "theme_4",
            "theme_name": "Collaboration, Culture, and Organizational Change",
            "hook_analysis": {
              "hook_text": "Hiring a Chief People Officer for WRITER felt heavy, because Waseem Alshikh and I didn't feel like we were just hiring for ourselves.",
              "hook_type": {
                "type": "Personal Reflection/Provocative Statement",
                "metrics": [
                  {
                    "metric_name": "Percent of posts opening with a personal or rhetorical reflection",
                    "metric_value": 71
                  },
                  {
                    "metric_name": "Percent of posts that start with a job/news announcement",
                    "metric_value": 29
                  }
                ]
              },
              "hook_description": "Hooks most often launch with a personal reflection, an emotional statement, or a rhetorical question, setting a conversational and authentic tone. Others open with major news or milestones ('COMPANY MILESTONE ALERT', 'I'm hiring for a chief of staff...'). These approaches draw readers into the narrative by signaling impact or inviting contemplation. Engagement is higher on posts starting with reflective, personal hooks or big news. To replicate: begin with a direct statement about people, impact, or purpose; ask 'what does it mean'–type questions; or make milestone/job posts feel like cultural events, not just announcements.",
              "engagement_correlation": [
                {
                  "average_likes": 1090,
                  "average_reposts": 30,
                  "average_comments": 68
                },
                {
                  "average_likes": 400,
                  "average_reposts": 10,
                  "average_comments": 20
                }
              ]
            },
            "recent_topics": [
              {
                "date": "2025-07-15",
                "topic": "Hiring Chief People Officer/AI-first culture",
                "summary": "Announcing new Chief People Officer hire, reflecting on the cultural mission of AI companies and the importance of breaking down silos.",
                "engagement": {
                  "average_likes": 807,
                  "average_reposts": 8,
                  "average_comments": 44
                }
              },
              {
                "date": "2025-06-03",
                "topic": "AI Leaders Forum NYC: Cross-company collaboration",
                "summary": "Highlighting business and IT coming together for visionary leadership in AI.",
                "engagement": {
                  "average_likes": 290,
                  "average_reposts": 11,
                  "average_comments": 8
                }
              },
              {
                "date": "2025-05-12",
                "topic": "EMEA expansion and hiring",
                "summary": "Opening European office, underscoring organizational growth and investment in local tech talent.",
                "engagement": {
                  "average_likes": 552,
                  "average_reposts": 5,
                  "average_comments": 13
                }
              },
              {
                "date": "2025-04-16",
                "topic": "Customer leader joins org",
                "summary": "Welcoming a customer-side leader into a central organizational/product role, linking leadership to AI adoption.",
                "engagement": {
                  "average_likes": 993,
                  "average_reposts": 6,
                  "average_comments": 59
                }
              },
              {
                "date": "2025-03-18",
                "topic": "Organizational obstacles in AI adoption",
                "summary": "Data-driven exploration of IT/business friction, using survey results to spotlight silos and the need for collaborative models.",
                "engagement": {
                  "average_likes": 324,
                  "average_reposts": 20,
                  "average_comments": 27
                }
              },
              {
                "date": "2025-03-06",
                "topic": "Global organizational growth and advisory board",
                "summary": "Announcing new hubs, advisory board, and global hiring with a focus on supporting enterprise AI worldwide.",
                "engagement": {
                  "average_likes": 930,
                  "average_reposts": 22,
                  "average_comments": 57
                }
              },
              {
                "date": "2025-01-16",
                "topic": "GTM team spotlight & cross-functional culture",
                "summary": "Team offsite highlights collaboration, 'ONE WRITER' culture, and the role of end-to-end transformation.",
                "engagement": {
                  "average_likes": 858,
                  "average_reposts": 24,
                  "average_comments": 21
                }
              },
              {
                "date": "2024-12-28",
                "topic": "Hiring Chief of Staff/Scaling culture",
                "summary": "Deep dive into CoS role, high-performance culture, and leadership principles during rapid team scale-up.",
                "engagement": {
                  "average_likes": 1546,
                  "average_reposts": 81,
                  "average_comments": 111
                }
              }
            ],
            "tone_analysis": {
              "sentiment": {
                "label": "Positive",
                "average_score": 0.72
              },
              "dominant_tones": [
                "Inclusive",
                "Aspirational",
                "Mission-driven",
                "Candid"
              ],
              "tone_description": "The posts have an overwhelmingly positive, mission-driven, and inclusive tone. Writers express enthusiasm and excitement about team achievements, leadership hires, and organizational growth. There is frequent use of collective language (\"we're hiring\", \"our team\", \"ONE WRITER\") that emphasizes unity and shared purpose. Candid reflections on industry challenges (e.g., friction, silos) lend authenticity, while aspirational language stresses the mission of 'empowering people' and 'transforming work.' Replicating this tone means blending honest acknowledgment of obstacles with a bias for optimism and shared ambition.",
              "tone_distribution": [
                {
                  "tone": "Positive/Motivational",
                  "percentage": 62
                },
                {
                  "tone": "Candid/Authentic",
                  "percentage": 25
                },
                {
                  "tone": "Data-driven/Analytical",
                  "percentage": 13
                }
              ]
            },
            "linguistic_style": {
              "emoji_usage": {
                "metrics": [
                  {
                    "emoji": "🔥",
                    "average_frequency": 0.6
                  },
                  {
                    "emoji": "🌍",
                    "average_frequency": 0.3
                  },
                  {
                    "emoji": "⚡",
                    "average_frequency": 1.1
                  },
                  {
                    "emoji": "🙌",
                    "average_frequency": 0.2
                  }
                ],
                "category": "Occasional, for emphasis"
              },
              "unique_terms": [
                {
                  "term": "AI-first",
                  "example": "what does it mean to be an AI-first company?",
                  "frequency": 7
                },
                {
                  "term": "Cross-functional team",
                  "example": "cross-functional teams that are best suited to deploy AI",
                  "frequency": 4
                },
                {
                  "term": "Agentic AI",
                  "example": "The opportunity for agentic AI to help retailers help customers is MASSIVE",
                  "frequency": 2
                },
                {
                  "term": "ONE WRITER",
                  "example": "Our theme this week is ONE WRITER and it's not a tagline",
                  "frequency": 3
                },
                {
                  "term": "Connect, Challenge, Own",
                  "example": "Our values at Writer that you'd be living and evangelizing daily are Connect, Challenge, Own.",
                  "frequency": 2
                }
              ],
              "linguistic_description": "Writing is energetic, direct, and purpose-driven. Language is informal yet professional, using contractions and exclamations. List markers (numbers or emoji bullets), short paragraphs, and rhetorical questions increase engagement and rhythm. Jargon like 'AI-native', 'agentic AI', and 'GTM' is included for audience specificity, balanced with explanations when unpacking survey findings. Emojis appear periodically for emphasis or to evoke team spirit, but aren't overused. Calls to action ('JOIN US!', 'Check out our roles') are direct."
            },
            "theme_description": "- Main topics: Breaking down silos between IT and business, importance of cross-functional teams, leadership and hiring (e.g., CPO, Chief of Staff), cultural values (e.g., 'Connect, Challenge, Own'), and change management in AI adoption.\n- Purpose/intent: To stress that genuine AI transformation is as much about people, process, and culture as it is about technology, and that successful enterprise AI requires new models of organizational alignment and leadership.\n- Recurring patterns: Job announcements, team spotlights, discussions of leadership principles, advocacy for building internal human capital and cross-disciplinary teams.",
            "structure_analysis": {
              "conciseness": {
                "level": "Moderate (detailed but not verbose)",
                "metrics": [
                  {
                    "metric_name": "Average word count per post",
                    "metric_value": 430
                  },
                  {
                    "metric_name": "Average paragraph length (lines)",
                    "metric_value": 2.2
                  }
                ],
                "description": "Posts typically run moderately long (300-550 words), broken into compact paragraphs. Paragraphs often are just 1-3 lines, making them skimmable. Rhetorical questions and bullet points break up blocks of text for visual ease. Writing is precise with minimal fluff, but richer detail is included for stories of leadership, hiring, and culture transformation."
              },
              "post_format": {
                "example": "'Hiring a Chief People Officer for WRITER...What does it mean to bust through the artificial silos...What does it mean for EVERY employee...And that's why I am SO excited...We're hiring for everything—JOIN US!'",
                "metrics": [
                  {
                    "metric_name": "Percent of posts using lists/structured points",
                    "metric_value": 65
                  }
                ],
                "primary_format": "Mini-essay with lists and/or Q&A elements"
              },
              "data_intensity": {
                "level": "Moderate",
                "example": "\"Our survey of 1,600 knowledge workers (including 800 c-suite execs and 800 employees)...2 out of 3 c-suite execs say generative AI adoption has caused division...Friction between IT and business leaders: 68%...\"",
                "metrics": [
                  {
                    "metric_name": "Posts containing statistics or research findings",
                    "metric_value": 2
                  },
                  {
                    "metric_name": "Posts with technical or cultural jargon",
                    "metric_value": 8
                  }
                ]
              },
              "common_structures": [
                {
                  "frequency": "Most posts (70%)",
                  "structure": "Narrative/opening story + list/question sequence + closing call to action"
                },
                {
                  "frequency": "About 25%",
                  "structure": "Milestone or announcement format with recipient spotlight (hires, new locations, board, teams)"
                },
                {
                  "frequency": "One in cluster",
                  "structure": "Data-driven commentary with bullet-pointed findings and analysis"
                }
              ],
              "structure_description": "The most common structure melds storytelling with listed reflections or actions. Announcements are often crafted as narrative journeys (why this hire matters, what the culture means, what change looks like) rather than a dry update. Lists and bullet points are frequently used, particularly after a narrative intro, to crystallize principles or cite data. All posts close with a strong call to action ('JOIN US', 'Check out roles'), and sometimes reference company values or invite direct contact (e.g., for senior recruitment)."
            }
          },
          {
            "theme_id": "theme_5",
            "theme_name": "Industry Thought Leadership and Market Education",
            "hook_analysis": {
              "hook_text": "Some false narratives that smart enterprise AI leaders are finally coming around to unwinding on their own:",
              "hook_type": {
                "type": "Bold Claim/Myth-Busting Statement",
                "metrics": [
                  {
                    "metric_name": "Posts starting with a claim, myth, or problem statement",
                    "metric_value": 0.67
                  },
                  {
                    "metric_name": "Posts using event-based openings",
                    "metric_value": 0.33
                  }
                ]
              },
              "hook_description": "Most posts open with either a bold, contrarian stance (e.g., myth-busting, surfacing industry misconceptions) or a direct reference to an event/panel participation. This approach quickly signals insight, and helps establish authority. Such hooks drive higher engagement by inviting the audience to reconsider accepted narratives or by leveraging FOMO from industry events.",
              "engagement_correlation": [
                {
                  "average_likes": 377,
                  "average_reposts": 29,
                  "average_comments": 25
                },
                {
                  "average_likes": 284,
                  "average_reposts": 9,
                  "average_comments": 13
                }
              ]
            },
            "recent_topics": [
              {
                "date": "2025-07-16",
                "topic": "LLMs and Search Traffic Decline",
                "summary": "Highlights drop in search traffic due to shift towards LLM-driven discovery; announces partnership with Accenture.",
                "engagement": {
                  "average_likes": 242,
                  "average_reposts": 8,
                  "average_comments": 9
                }
              },
              {
                "date": "2025-06-16",
                "topic": "AEO/Agentic Panel at Cannes",
                "summary": "Promotes Answer Engine Optimization at Cannes, showcases practical agentic solutions, encourages leaders to act.",
                "engagement": {
                  "average_likes": 467,
                  "average_reposts": 6,
                  "average_comments": 17
                }
              },
              {
                "date": "2025-03-03",
                "topic": "Myth-Busting LLM Industry Narratives",
                "summary": "Challenges hype-driven claims around LLMs/OpenAI; argues for AI systems over chasing new models.",
                "engagement": {
                  "average_likes": 377,
                  "average_reposts": 29,
                  "average_comments": 25
                }
              },
              {
                "date": "2025-01-21",
                "topic": "CIO as CEO",
                "summary": "Observes new trend of CIOs being considered for CEO roles, highlighting executive evolution.",
                "engagement": {
                  "average_likes": 284,
                  "average_reposts": 0,
                  "average_comments": 13
                }
              },
              {
                "date": "2025-01-20",
                "topic": "AI Skepticism at WEF / Spreading Education",
                "summary": "Describes executive skepticism around AI, participation at WEF to educate on transformative potential.",
                "engagement": {
                  "average_likes": 403,
                  "average_reposts": 6,
                  "average_comments": 16
                }
              },
              {
                "date": "2025-01-06",
                "topic": "CES Participation / Conference Diversity",
                "summary": "Announces speaking roles at CES, calls for gender diversity at tech conferences.",
                "engagement": {
                  "average_likes": 369,
                  "average_reposts": 9,
                  "average_comments": 22
                }
              }
            ],
            "tone_analysis": {
              "sentiment": {
                "label": "Positive",
                "average_score": 0.72
              },
              "dominant_tones": [
                "Confident",
                "Challenging",
                "Educational"
              ],
              "tone_description": "Posts combine confident assertions with a challenging/call-to-action tone, often directly debunking prevalent myths and urging industry leaders toward more ambitious, future-oriented thinking. There is an authoritative, educational undercurrent—aimed at sharing knowledge, raising standards, and equipping leaders to make better decisions. The voice remains positive even when critiquing the status quo.",
              "tone_distribution": [
                {
                  "tone": "Confident/Assertive",
                  "percentage": 62
                },
                {
                  "tone": "Educational",
                  "percentage": 24
                },
                {
                  "tone": "Challenging/Critical",
                  "percentage": 14
                }
              ]
            },
            "linguistic_style": {
              "emoji_usage": {
                "metrics": [
                  {
                    "emoji": "\u001f4a5",
                    "average_frequency": 0.17
                  },
                  {
                    "emoji": "\u001f4c5",
                    "average_frequency": 0.17
                  }
                ],
                "category": "Rarely"
              },
              "unique_terms": [
                {
                  "term": "AEO (Answer Engine Optimization)",
                  "example": "Our agenda is firmly AEO \u001f4c5 answer engine optimization.",
                  "frequency": 2
                },
                {
                  "term": "Agentic",
                  "example": "architecting the ecosystem that is bringing agentic to enterprise teams everywhere.",
                  "frequency": 2
                },
                {
                  "term": "LLM",
                  "example": "We're hearing 10-15% search traffic declines... discovery is moving to LLMs, fast.",
                  "frequency": 3
                },
                {
                  "term": "Test-time compute",
                  "example": "(2) \u001cTest-time compute models are the future\u001d",
                  "frequency": 2
                },
                {
                  "term": "CIO/CTO/C-suite",
                  "example": "the CIO was considered for the top CEO job at a top 30 global bank.",
                  "frequency": 2
                }
              ],
              "linguistic_description": "The language is professional yet accessible, with minimal use of jargon unless industry-specific context demands it (e.g., agentic, LLMs, AEO). Occasional use of emojis for emphasis, but sparingly. Bullet points and numbering are commonly used for clarity, especially in myth-busting or when introducing new conceptual frameworks. Some playful wordplay and calls for community interaction soften direct critiques, making posts feel more approachable."
            },
            "theme_description": "This theme connects major trends, myths, and future-oriented commentary in enterprise AI, SEO/AEO, and leadership roles. The writer uses these posts to set narratives, challenge misconceptions, and educate both industry insiders and the wider customer base. The content draws from events, published research, and firsthand experience in panels and conferences, presenting a balanced mix of critique and actionable guidance aimed at tech and business leaders.",
            "structure_analysis": {
              "conciseness": {
                "level": "Moderate (well-structured, some longer posts)",
                "metrics": [
                  {
                    "metric_name": "Average sentences per post",
                    "metric_value": 10
                  },
                  {
                    "metric_name": "Average paragraphs per post",
                    "metric_value": 5
                  }
                ],
                "description": "Most posts are moderately dense, with some lengthy but well-organized deep-dives especially when tackling myths or explaining frameworks (running 200–400 words). Event/announcement posts are concise, usually under 150 words."
              },
              "post_format": {
                "example": "Some false narratives that smart enterprise AI leaders are finally coming around to unwinding on their own: \n\n(1) ... \n(2) ...",
                "metrics": [
                  {
                    "metric_name": "Bullet/numbered lists usage",
                    "metric_value": "2 out of 6"
                  }
                ],
                "primary_format": "Numbered list or point/counterpoint breakdown"
              },
              "data_intensity": {
                "level": "Moderate",
                "example": "We're hearing 10-15% search traffic declines across the board on consumer brand sites...",
                "metrics": [
                  {
                    "metric_name": "Posts citing statistics or quantitative trends",
                    "metric_value": 2
                  },
                  {
                    "metric_name": "Posts referencing research/events",
                    "metric_value": 3
                  }
                ]
              },
              "common_structures": [
                {
                  "frequency": "33%",
                  "structure": "Myth-busting: Intro statement, numbered or bullet-listed misconceptions, followed by counter-explanation"
                },
                {
                  "frequency": "33%",
                  "structure": "Event promotion: Conference/panel intro, schedule/Speaker details, call for engagement"
                },
                {
                  "frequency": "33%",
                  "structure": "Trend/market shift announcement: State recent trend or shift, explain consequences/next steps"
                }
              ],
              "structure_description": "Most posts follow a recognizable template: open with a bold statement or myth, unpack with lists or outlined logic, and close with actionable or reflective calls-to-action. Event-based posts follow a formulaic promotion structure: highlight presence/contribution, then encourage audience interaction (comment, DM, meet-up). Shorter posts are used for tactical updates; longer ones address industry misconceptions."
            }
          }
        ]
      },
            'is_versioned': False, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        {
            'namespace': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_DOCNAME,
            'initial_data': {
      "test_queries": [
        {
          "query_text": "may habib generative AI",
          "query_type": "branded_authority",
          "ranking_position": 1,
          "competitor_analysis": "Competitors such as Todd Jackson, Waseem Alshikh, and Vivek Ramaswami appear in related contexts, primarily through their roles at major investment firms or as AI startup founders. They often rank due to thought leadership contributions, visibility on industry podcasts, and authored content on major platforms.",
          "result_quality_assessment": "The results are highly relevant, with multiple first-page placements including podcasts and company mentions. Authority is established (CEO of Writer, enterprise AI leader, $100M funding round, 2023 IA40 winner). However, most top content is via executive interviews and podcasts, not authored articles or mainstream business publications.",
          "executive_found_in_results": True
        }
      ],
      "competitor_benchmark": {
        "competitor_names": [
          "Todd Jackson",
          "Waseem Alshikh",
          "Vivek Ramaswami"
        ],
        "content_volume_gap": "May Habib has significant branded presence in industry and podcast platforms, but content is concentrated and lacks breadth. Competitors feature more regularly across mainstream media, appear in more 'AI thought leader' lists, and have a higher number of authored thought pieces on third-party sites.",
        "authority_signal_gaps": [
          "No major industry awards or recognitions featured",
          "Few, if any, authored articles in top-tier business/tech publications",
          "Lack of consistent presence in 'AI thought leader' industry roundups",
          "Limited mainstream media (e.g., Forbes, TechCrunch, WSJ) coverage"
        ],
        "search_dominance_gaps": [
          "'AI thought leader' queries on Google favor competitors",
          "'Enterprise AI expert' and broad industry expertise queries are more likely to surface competitor profiles",
          "Mainstream business searches (e.g., 'top AI founders') tend to prioritize other executives"
        ],
        "positioning_advantages": [
          "Strong association as CEO and co-founder of a leading enterprise AI platform (Writer)",
          "Highly visible in the generative AI and SaaS industry podcasting ecosystem",
          "Well-documented success in company fundraising and industry-specific awards (e.g., 2023 IA40 winner)"
        ]
      },
      "web_content_analysis": {
        "brand_consistency_score": 8,
        "content_themes_from_web": [
          "Enterprise AI leadership",
          "Generative AI product scaling",
          "Content technology innovation",
          "Startup fundraising and growth",
          "Advice for AI founders"
        ],
        "primary_content_platforms": [
          "podcast_platform",
          "industry_publication",
          "linkedin_profile"
        ],
        "external_validation_signals": [
          "Podcast guest features (industry-specific)",
          "Third-party references to Writer's $100M funding round",
          "Recognition as a '2023 IA40 winner'",
          "Consistent mention as CEO/founder",
          "Industry panel speaking engagements"
        ]
      },
      "search_result_metrics": {
        "google_total_results": 156000,
        "branded_query_dominance": 1.0,
        "average_ranking_position": 2,
        "first_page_controlled_results": 3
      },
      "visibility_opportunities": {
        "quick_wins_30_days": [
          "Publish authored articles on major industry and third-party tech/business publications",
          "Optimize LinkedIn headline and about section with 'Enterprise AI leader' and 'Generative AI expert'",
          "Update Writer and personal website with schema markup for enhanced search snippets"
        ],
        "power_moves_90_days": [
          "Pursue guest podcast appearances on major AI/business shows (beyond industry niche)",
          "Submit proposals and secure speaking slots at top AI/tech conferences",
          "Collaborate for co-authored pieces with other thought leaders in AI business media"
        ],
        "game_changers_6_months": [
          "Establish a recurring thought leadership series on Medium or Forbes",
          "Develop a signature report (e.g., 'State of Enterprise Generative AI') for annual media push",
          "Position for industry awards and recognitions (AI influencer, top founder, etc.)"
        ],
        "seo_optimization_opportunities": [
          "Target keywords like 'AI Thought Leader', 'GenAI in Enterprise', 'Top Content AI CEO'",
          "Enhance structured data on personal/company websites for better result richness",
          "Pursue high-authority backlinks through syndication and influencer collaborations"
        ],
        "missing_credentials_from_search": [
          "Harvard economics degree is not readily visible in top search results",
          "No clear evidence of mainstream business awards",
          "Formal recognition as industry keynote/speaker underrepresented"
        ]
      },
      "digital_authority_metrics": {
        "guest_articles": 0,
        "authority_signals": [
          "Co-founder and CEO of Writer",
          "Raised $100M at $500M valuation",
          "2023 IA40 winner",
          "Enterprise generative AI leader",
          "Advice for AI founders"
        ],
        "industry_mentions": 2,
        "podcast_appearances": 3,
        "first_page_dominance": 3,
        "google_results_count": 156000,
        "speaking_engagements": 1,
        "web_visibility_score": 6.2,
        "content_freshness_score": 7
      },
      "overall_web_visibility_score": 6.2,
      "created_at": "2025-07-18T13:02:20.680471Z",
      "updated_at": "2025-07-18T13:02:20.680471Z"
    },
            'is_versioned': BLOG_EXECUTIVE_WEB_VISIBILITY_TEST_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        },
        {
            'namespace': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=entity_username), 
            'docname': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME,
            'initial_data': {
      "biographical_gaps": [
        "Limited mention of professional journey and previous roles before founding Writer",
        "No reference to notable speaking engagements, published articles, or board memberships",
        "Minimal detail on milestones achieved with Writer or prior ventures"
      ],
      "missing_credentials": [
        "Awards or industry recognitions (if any) are missing from AI knowledge",
        "Specific technology patents or publications are not mentioned",
        "No mention of advisory roles or industry council memberships"
      ],
      "competitive_analysis": {
        "executive_ai_advantages": [
          "Strong and consistent authority signals as CEO of Writer and Harvard graduate",
          "Clear association with enterprise AI and generative content technology domains",
          "High ranking within the enterprise/generative AI expert niche"
        ],
        "missing_from_ai_knowledge": [
          "Broader AI leadership recognition outside the enterprise/generative content niche",
          "Lack of detail on entrepreneurial achievements beyond founding Writer",
          "No reference to media appearances or influential thought leadership content"
        ],
        "ai_recognition_vs_competitors": "May Habib is well-positioned in specific enterprise and generative AI contexts but lacks the broader AI and industry-wide recognition that competitors like Sam Altman, Fei-Fei Li, and Andrew Ng receive. She is prominent among enterprise-focused queries but less visible in general AI expert lists.",
        "competitor_ai_strategies_to_emulate": [
          "Broader thought leadership across general AI topics, not just enterprise content",
          "More frequent citation in news/media and cross-industry AI roundups",
          "Comprehensive biographical details and achievement highlights in online profiles and features"
        ],
        "competitors_with_better_ai_visibility": [
          "Sam Altman",
          "Andrew Ng",
          "Fei-Fei Li",
          "Yoshua Bengio",
          "Geoffrey Hinton"
        ]
      },
      "platform_recognition": {
        "weakest_platform": "Claude",
        "best_performing_platform": "ChatGPT",
        "claude_recognition_score": 2,
        "gemini_recognition_score": 3,
        "chatgpt_recognition_score": 5,
        "platform_consistency_score": 3,
        "perplexity_recognition_score": 4
      },
      "ai_recognition_metrics": {
        "name_recognition_rate": 0.25,
        "expert_query_performance": 5.5,
        "biographical_accuracy_score": 8,
        "overall_ai_recognition_score": 5,
        "thought_leadership_recognition": 5
      },
      "improvement_opportunities": {
        "quick_wins_30_days": [
          "Update LinkedIn headline and summary with clear keywords: 'enterprise AI', 'generative content technology', and 'AI entrepreneur'",
          "Add detailed descriptions of Writer’s achievements and quantifiable business impact to bio",
          "Create a visible list of awards, keynotes, and thought leadership milestones in the Experience and Featured sections"
        ],
        "power_moves_90_days": [
          "Launch a LinkedIn article series addressing trends and challenges in enterprise AI and generative content technology",
          "Collaborate with other well-known AI leaders for joint content or panel webinars to broaden association with general AI topics",
          "Ensure coverage of May Habib in authoritative AI publications and include those features in LinkedIn profile"
        ],
        "game_changers_6_months": [
          "Lead or co-lead a major LinkedIn Live event or virtual summit on generative AI for enterprise with high-profile industry guests",
          "Publish in-depth thought leadership pieces on major AI industry platforms and link them in LinkedIn activity",
          "Develop shareable industry reports or research papers with original insights, widely distributed and cited"
        ],
        "expertise_positioning_gaps": [
          "General AI industry leadership",
          "AI entrepreneurship and innovation at scale",
          "Cross-industry AI implications beyond enterprise content"
        ],
        "biographical_updates_needed": [
          "Highlight early career milestones, entrepreneurial ventures, or advisory roles",
          "Add awards, recognitions, or patents (if applicable)",
          "Include links to interviews, keynote sessions, and articles"
        ],
        "content_optimization_for_ai": [
          "Structure LinkedIn About and Experience sections with rich, machine-readable keywords and clear achievement statements",
          "Pin key articles and interviews to LinkedIn Featured area using relevant AI and leadership tags",
          "Consistently update activity with original content on trending AI topics to boost cross-platform AI visibility"
        ]
      },
      "expertise_recognition_tests": [
        {
          "expertise_query": "Who are the top enterprise AI experts?",
          "platforms_tested": [
            "ChatGPT",
            "Perplexity",
            "Claude",
            "Gemini"
          ],
          "executive_mentioned_count": 1,
          "average_ranking_vs_competitors": 4,
          "accuracy_of_executive_information": 8,
          "thought_leadership_indicators_found": [
            "CEO of Writer",
            "Enterprise AI innovator"
          ]
        },
        {
          "expertise_query": "Best generative AI thought leaders",
          "platforms_tested": [
            "ChatGPT",
            "Perplexity",
            "Claude",
            "Gemini"
          ],
          "executive_mentioned_count": 1,
          "average_ranking_vs_competitors": 5,
          "accuracy_of_executive_information": 8,
          "thought_leadership_indicators_found": [
            "Included as a thought leader",
            "Focus on content technology"
          ]
        },
        {
          "expertise_query": "May Habib expertise",
          "platforms_tested": [
            "ChatGPT",
            "Perplexity",
            "Claude",
            "Gemini"
          ],
          "executive_mentioned_count": 4,
          "average_ranking_vs_competitors": 1,
          "accuracy_of_executive_information": 9,
          "thought_leadership_indicators_found": [
            "Described as AI entrepreneur",
            "CEO of Writer",
            "Harvard economics graduate"
          ]
        },
        {
          "expertise_query": "May Habib background",
          "platforms_tested": [
            "ChatGPT",
            "Perplexity",
            "Claude",
            "Gemini"
          ],
          "executive_mentioned_count": 4,
          "average_ranking_vs_competitors": 1,
          "accuracy_of_executive_information": 9,
          "thought_leadership_indicators_found": [
            "Leading AI entrepreneur",
            "Innovator in enterprise AI"
          ]
        },
        {
          "expertise_query": "May Habib vs Sam Altman",
          "platforms_tested": [
            "ChatGPT",
            "Perplexity",
            "Claude",
            "Gemini"
          ],
          "executive_mentioned_count": 2,
          "average_ranking_vs_competitors": 2,
          "accuracy_of_executive_information": 8,
          "thought_leadership_indicators_found": [
            "Specialized in enterprise AI",
            "Compared with broader AI leader"
          ]
        },
        {
          "expertise_query": "Who should I follow for enterprise content technology insights?",
          "platforms_tested": [
            "ChatGPT",
            "Perplexity",
            "Claude",
            "Gemini"
          ],
          "executive_mentioned_count": 2,
          "average_ranking_vs_competitors": 2,
          "accuracy_of_executive_information": 8,
          "thought_leadership_indicators_found": [
            "Recommended expert for content tech",
            "Leadership of Writer"
          ]
        }
      ],
      "thought_leadership_topic_gaps": [
        "General AI innovation and industry-wide leadership",
        "AI entrepreneurship and building successful AI ventures",
        "Ethical AI and responsible AI governance",
        "Broader cross-industry impact of AI beyond content and enterprise applications"
      ],
      "created_at": "2025-07-18T13:04:41.285210Z",
      "updated_at": "2025-07-18T13:04:41.285210Z"
    },
            'is_versioned': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]

    # Define cleanup docs
    cleanup_docs: List[CleanupDocInfo] = [
        {'namespace': CONTENT_ANALYSIS_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': CONTENT_ANALYSIS_DOCNAME, 'is_versioned': False, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_DOCNAME, 'is_versioned': BLOG_EXECUTIVE_AI_VISIBILITY_TEST_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
        {'namespace': BLOG_CONTENT_DIAGNOSTIC_SECTION3_NAMESPACE_TEMPLATE.format(item=entity_username), 'docname': BLOG_CONTENT_DIAGNOSTIC_SECTION3_DOCNAME, 'is_versioned': BLOG_CONTENT_DIAGNOSTIC_SECTION3_IS_VERSIONED, 'is_shared': False, 'is_system_entity': False},
    ]

    # Output validation function
    async def validate_digital_authority_output(outputs) -> bool:
        """
        Validates the output from the digital authority analysis workflow.
        """
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        assert 'digital_authority_analysis' in outputs, "Validation Failed: 'digital_authority_analysis' missing."
        assert 'storage_paths' in outputs, "Validation Failed: 'storage_paths' missing."
        
        if 'digital_authority_analysis' in outputs:
            analysis = outputs['digital_authority_analysis']
            assert 'executive_thought_leadership_score' in analysis, "Output missing 'executive_thought_leadership_score' field"
            assert 'linkedin_metrics' in analysis, "Output missing 'linkedin_metrics' field"
            assert 'web_presence_audit' in analysis, "Output missing 'web_presence_audit' field"
            assert 'ai_recognition_gaps' in analysis, "Output missing 'ai_recognition_gaps' field"
            assert 'authority_opportunities' in analysis, "Output missing 'authority_opportunities' field"
            
            print(f"✓ Digital authority analysis validated successfully")
            print(f"✓ Thought leadership score: {analysis['executive_thought_leadership_score']}")
            print(f"✓ LinkedIn follower count: {analysis['linkedin_metrics']['follower_count']}")
            print(f"✓ Number of opportunities: {len(analysis['authority_opportunities'])}")
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
        validate_output_func=validate_digital_authority_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )

    print(f"--- {test_name} Finished --- ")
    if final_run_outputs and 'digital_authority_analysis' in final_run_outputs:
        analysis = final_run_outputs['digital_authority_analysis']
        print(f"\nDigital Authority Analysis:")
        print(f"Executive Thought Leadership Score: {analysis['executive_thought_leadership_score']}/10")
        print(f"LinkedIn Followers: {analysis['linkedin_metrics']['follower_count']}")
        print(f"Web Presence Score: {analysis['web_presence_audit']['google_results_count']} Google results")
        print(f"AI Recognition: {'Yes' if analysis['ai_recognition_gaps']['recognized_as_expert'] else 'No'}")
        print(f"Authority Opportunities: {len(analysis['authority_opportunities'])} identified")

if __name__ == "__main__":
    try:
        asyncio.run(main_test_section3_content_diagnostics())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")
