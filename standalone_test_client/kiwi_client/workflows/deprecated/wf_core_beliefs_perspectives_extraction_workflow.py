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
    # User Preferences
    USER_PREFERENCES_DOCNAME,
    USER_PREFERENCES_NAMESPACE_TEMPLATE,
    USER_PREFERENCES_IS_VERSIONED,
    
    # LinkedIn Profile
    LINKEDIN_SCRAPING_NAMESPACE_TEMPLATE,
    LINKEDIN_PROFILE_DOCNAME,
    
    # Content Analysis Document
    CONTENT_ANALYSIS_DOCNAME,
    CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
    
    # Target Audience Framework (from previous onboarding)
    # Note: This would be a temporary document from the first onboarding workflow
    # For now, we'll assume it's stored in user_inputs namespace
)

from kiwi_client.workflows.llm_inputs.core_beliefs_perspectives_extraction import (
    CORE_BELIEFS_QUESTIONS_SCHEMA,
    PERSONALIZED_QUESTIONS_SCHEMA,
    CONTENT_INTELLIGENCE_SCHEMA,
    
    ANALYSIS_AND_QUESTIONS_SYSTEM_PROMPT,
    ANALYSIS_AND_QUESTIONS_USER_PROMPT,
    
    PERSONALIZATION_SYSTEM_PROMPT,
    PERSONALIZATION_USER_PROMPT,
    
    CONTENT_INTELLIGENCE_SYSTEM_PROMPT,
    CONTENT_INTELLIGENCE_USER_PROMPT,
)

# --- Workflow Configuration Constants ---

# LLM Configuration
LLM_PROVIDER = "openai"
GENERATION_MODEL = "gpt-4.1"
LLM_TEMPERATURE = 0.9  # Higher temperature for creative question generation
LLM_MAX_TOKENS = 2500

# --- Prompt Template Variables and Options ---

# Analysis and Questions Generation Node
ANALYSIS_AND_QUESTIONS_SYSTEM_PROMPT_VARIABLES = {
    "questions_schema": CORE_BELIEFS_QUESTIONS_SCHEMA
}

ANALYSIS_AND_QUESTIONS_USER_PROMPT_VARIABLES = {
    "content_analysis": None,
    "user_preferences": None,
    "profile_insights": None
}

ANALYSIS_AND_QUESTIONS_USER_PROMPT_CONSTRUCT_OPTIONS = {
    "content_analysis": "content_analysis",
    "user_preferences": "onboarding_responses",
    "profile_insights": "profile_insights"
}

# Personalization Node
PERSONALIZATION_SYSTEM_PROMPT_VARIABLES = {
    "personalized_schema": PERSONALIZED_QUESTIONS_SCHEMA
}

PERSONALIZATION_USER_PROMPT_VARIABLES = {
    "generated_questions": None,
    "content_analysis": None,
    "user_preferences": None,
    "profile_insights": None
}

PERSONALIZATION_USER_PROMPT_CONSTRUCT_OPTIONS = {
    "generated_questions": "core_beliefs_questions",
    "content_analysis": "content_analysis",
    "user_preferences": "onboarding_responses",
    "profile_insights": "profile_insights",
}

# Content Intelligence Node
CONTENT_INTELLIGENCE_SYSTEM_PROMPT_VARIABLES = {
    "content_intelligence_schema": CONTENT_INTELLIGENCE_SCHEMA
}

CONTENT_INTELLIGENCE_USER_PROMPT_VARIABLES = {
    "content_analysis": None
}

CONTENT_INTELLIGENCE_USER_PROMPT_CONSTRUCT_OPTIONS = {
    "content_analysis": "content_analysis"
}

# --- Edge Configurations ---

field_mappings_from_input_to_state = [
    {"src_field": "entity_username", "dst_field": "entity_username"},
]

field_mappings_from_load_docs_to_state = [
    {"src_field": "content_analysis", "dst_field": "content_analysis"},
    {"src_field": "onboarding_responses", "dst_field": "onboarding_responses"},
    {"src_field": "profile_insights", "dst_field": "profile_insights"},
]

field_mappings_from_state_to_analysis_and_questions = [
    {"src_field": "content_analysis", "dst_field": "content_analysis"},
    {"src_field": "onboarding_responses", "dst_field": "onboarding_responses"},
    {"src_field": "profile_insights", "dst_field": "profile_insights"},
]

field_mappings_from_state_to_personalization = [
    {"src_field": "core_beliefs_questions", "dst_field": "core_beliefs_questions"},
    {"src_field": "content_analysis", "dst_field": "content_analysis"},
    {"src_field": "onboarding_responses", "dst_field": "onboarding_responses"},
    {"src_field": "profile_insights", "dst_field": "profile_insights"},
]

field_mappings_from_state_to_content_intelligence = [
    {"src_field": "content_analysis", "dst_field": "content_analysis"},
]

# --- Input Fields ---

INPUT_FIELDS = {
    "entity_username": { "type": "str", "required": True, "description": "Name of the entity to extract core beliefs for."},
}

# --- Workflow Graph Schema ---

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

        # --- 2. Load Customer Context Documents ---
        "load_customer_context_docs": {
            "node_id": "load_customer_context_docs",
            "node_name": "load_customer_data",
            "node_config": {
                "load_paths": [
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": CONTENT_ANALYSIS_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": CONTENT_ANALYSIS_DOCNAME,
                        },
                        "output_field_name": "content_analysis",
                    },
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": USER_PREFERENCES_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": USER_PREFERENCES_DOCNAME,
                        },
                        "output_field_name": "onboarding_responses",
                    },
                    {
                        "filename_config": {
                            "input_namespace_field_pattern": LINKEDIN_SCRAPING_NAMESPACE_TEMPLATE,
                            "input_namespace_field": "entity_username",
                            "static_docname": LINKEDIN_PROFILE_DOCNAME,
                        },
                        "output_field_name": "profile_insights",
                    },
                ],
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False}
            },
        },

        # --- 3. Construct Analysis and Questions Prompt ---
        "construct_analysis_and_questions_prompt": {
            "node_id": "construct_analysis_and_questions_prompt",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": ANALYSIS_AND_QUESTIONS_USER_PROMPT,
                        "variables": ANALYSIS_AND_QUESTIONS_USER_PROMPT_VARIABLES,
                        "construct_options": ANALYSIS_AND_QUESTIONS_USER_PROMPT_CONSTRUCT_OPTIONS
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": ANALYSIS_AND_QUESTIONS_SYSTEM_PROMPT,
                        "variables": ANALYSIS_AND_QUESTIONS_SYSTEM_PROMPT_VARIABLES,
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 4. Generate Core Beliefs Questions ---
        "generate_core_beliefs_questions": {
            "node_id": "generate_core_beliefs_questions",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": GENERATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": CORE_BELIEFS_QUESTIONS_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            }
        },

        # --- 5. Construct Personalization Prompt ---
        "construct_personalization_prompt": {
            "node_id": "construct_personalization_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": PERSONALIZATION_USER_PROMPT,
                        "variables": PERSONALIZATION_USER_PROMPT_VARIABLES,
                        "construct_options": PERSONALIZATION_USER_PROMPT_CONSTRUCT_OPTIONS
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": PERSONALIZATION_SYSTEM_PROMPT,
                        "variables": PERSONALIZATION_SYSTEM_PROMPT_VARIABLES,
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 6. Personalize Questions (Final Output) ---
        "personalize_questions": {
            "node_id": "personalize_questions",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": GENERATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": PERSONALIZED_QUESTIONS_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            }
        },

        # --- 7. Construct Content Intelligence Prompt ---
        "construct_content_intelligence_prompt": {
            "node_id": "construct_content_intelligence_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": CONTENT_INTELLIGENCE_USER_PROMPT,
                        "variables": CONTENT_INTELLIGENCE_USER_PROMPT_VARIABLES,
                        "construct_options": CONTENT_INTELLIGENCE_USER_PROMPT_CONSTRUCT_OPTIONS
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": CONTENT_INTELLIGENCE_SYSTEM_PROMPT,
                        "variables": CONTENT_INTELLIGENCE_SYSTEM_PROMPT_VARIABLES,
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 8. Generate Content Intelligence ---
        "generate_content_intelligence": {
            "node_id": "generate_content_intelligence",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": GENERATION_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                },
                "output_schema": {
                    "schema_definition": CONTENT_INTELLIGENCE_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False
                },
            }
        },

        # --- 9. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {},
        },
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # --- Initial Setup ---
        # Input -> State: Store initial inputs globally
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": field_mappings_from_input_to_state
        },

        # --- Load Documents Flow ---
        # Input -> Load Customer Context Documents
        {
            "src_node_id": "input_node",
            "dst_node_id": "load_customer_context_docs",
            "mappings": [
                {"src_field": "entity_username", "dst_field": "entity_username"}
            ]
        },

        # Load Documents -> State: Store loaded documents
        {
            "src_node_id": "load_customer_context_docs",
            "dst_node_id": "$graph_state",
            "mappings": field_mappings_from_load_docs_to_state
        },

        # --- Belief Analysis Flow ---
        # Load Documents -> Belief Analysis Prompt
        {
            "src_node_id": "load_customer_context_docs",
            "dst_node_id": "construct_analysis_and_questions_prompt"
        },

        # State -> Belief Analysis Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_analysis_and_questions_prompt",
            "mappings": field_mappings_from_state_to_analysis_and_questions
        },

        # Belief Analysis Prompt -> LLM
        {
            "src_node_id": "construct_analysis_and_questions_prompt",
            "dst_node_id": "generate_core_beliefs_questions",
            "mappings": [
                {"src_field": "user_prompt", "dst_field": "user_prompt"},
                {"src_field": "system_prompt", "dst_field": "system_prompt"}
            ],
            "description": "Send prompts to LLM for belief analysis"
        },

        # State -> Generate Core Beliefs Questions (for messages_history)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "generate_core_beliefs_questions",
            "mappings": [
                {"src_field": "messages_history", "dst_field": "messages_history"}
            ]
        },

        # Questions Generation -> State
        {
            "src_node_id": "generate_core_beliefs_questions",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "core_beliefs_questions"}
            ]
        },

        # --- Personalization Flow ---
        # Belief Analysis -> Personalization Prompt
        {
            "src_node_id": "generate_core_beliefs_questions",
            "dst_node_id": "construct_personalization_prompt"
        },

        # State -> Personalization Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_personalization_prompt",
            "mappings": field_mappings_from_state_to_personalization
        },

        # Personalization Prompt -> LLM
        {
            "src_node_id": "construct_personalization_prompt",
            "dst_node_id": "personalize_questions",
            "mappings": [
                {"src_field": "user_prompt", "dst_field": "user_prompt"},
                {"src_field": "system_prompt", "dst_field": "system_prompt"}
            ],
            "description": "Send prompts to LLM for personalization"
        },

        # State -> Personalize Questions (for messages_history)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "personalize_questions",
            "mappings": [
                {"src_field": "messages_history", "dst_field": "messages_history"}
            ]
        },

        # Personalization -> State
        {
            "src_node_id": "personalize_questions",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "personalized_questions"}
            ]
        },

        # --- Content Intelligence Flow ---
        # Personalization -> Content Intelligence Prompt
        {
            "src_node_id": "personalize_questions",
            "dst_node_id": "construct_content_intelligence_prompt"
        },

        # State -> Content Intelligence Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_content_intelligence_prompt",
            "mappings": field_mappings_from_state_to_content_intelligence
        },

        # Content Intelligence Prompt -> LLM
        {
            "src_node_id": "construct_content_intelligence_prompt",
            "dst_node_id": "generate_content_intelligence",
            "mappings": [
                {"src_field": "user_prompt", "dst_field": "user_prompt"},
                {"src_field": "system_prompt", "dst_field": "system_prompt"}
            ],
            "description": "Send prompts to LLM for content intelligence"
        },

        # Content Intelligence -> State
        {
            "src_node_id": "generate_content_intelligence",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "content_intelligence"}
            ]
        },

        # --- Final Output ---
        # Personalization -> Output
        {
            "src_node_id": "personalize_questions",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "personalized_questions"}
            ]
        },

        # Content Intelligence -> Output
        {
            "src_node_id": "generate_content_intelligence",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "content_intelligence"}
            ]
        },

        # State -> Output (for additional context)
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "core_beliefs_questions", "dst_field": "core_beliefs_questions"},
                {"src_field": "content_intelligence", "dst_field": "content_intelligence"}
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
                # No special reducers needed for this workflow
            }
        }
    }
}


# --- Test Execution Logic ---
async def main_test_core_beliefs_perspectives_extraction():
    """
    Test for Core Beliefs and Perspectives Extraction Workflow.
    """
    test_name = "Core Beliefs and Perspectives Extraction Workflow Test"
    print(f"--- Starting  ---")

    # Example test inputs
    test_inputs = {
        "entity_username": "test_user_ai_founder"
    }

    # Setup documents (create test documents that will be loaded)
    entity_username = test_inputs["entity_username"]
    setup_docs = [
        # User Preferences / Onboarding Responses
        SetupDocInfo(
            namespace=USER_PREFERENCES_NAMESPACE_TEMPLATE.format(item=entity_username),
            docname=USER_PREFERENCES_DOCNAME,
            initial_data={
      "created_at": "2025-05-15T11:20:19.225000",
      "updated_at": "2025-05-24T05:16:20.700000",
      "goals": {
        "selected": [
          {
            "goal_id": "personal-branding",
            "name": "Personal Branding",
            "description": "Cultivate a distinctive professional identity that makes you instantly recognizable in your field."
          },
          {
            "goal_id": "career-development",
            "name": "Career Development",
            "description": "Demonstrate your professional growth journey and expertise to attract better opportunities and connections."
          },
          {
            "goal_id": "knowledge-sharing",
            "name": "Establish Thought Leadership",
            "description": "Establish yourself as an industry authority by sharing valuable insights your network can't find elsewhere."
          }
        ],
        "custom_goals": None
      },
      "audience": {
        "segments": [
          {
            "name": "Industry Professionals"
          },
          {
            "name": "Customers & Prospects"
          },
          {
            "name": "Business Stakeholders"
          }
        ]
      }
    },
            is_versioned=USER_PREFERENCES_IS_VERSIONED,
            is_shared=False,
            initial_version="default",
            is_system_entity=False
        ),
        # LinkedIn Profile
        SetupDocInfo(
            namespace=LINKEDIN_SCRAPING_NAMESPACE_TEMPLATE.format(item=entity_username),
            docname=LINKEDIN_PROFILE_DOCNAME,
            initial_data={
      "geo": {
        "country": "United States",
        "city": "San Francisco Bay Area",
        "full": "San Francisco Bay Area",
        "countryCode": "us"
      },
      "username": "example-user",
      "summary": "Entrepreneurial product leader passionate about building futuristic customer solutions, using technology, behavioral understanding, a lot of enthusiasm and some patience. I get energized by bold ideas, smart cross-functional teams and meaningful problem spaces. \n\nIf you want to connect, feel free to drop me a line on user9@example.com.",
      "firstName": "Founder B",
      "headline": "Founder at KiwiQ AI | Building Intelligent Teammates for Marketers",
      "lastName": "Bharadwaj",
      "educations": [
        {
          "end": {
            "year": 2017,
            "month": 0,
            "day": 0
          },
          "fieldOfStudy": "Business Administration and Management, General",
          "start": {
            "year": 2015,
            "month": 0,
            "day": 0
          },
          "degree": "MBA",
          "schoolName": "University of Michigan - Stephen M. Ross School of Business"
        },
        {
          "end": {
            "year": 2011,
            "month": 0,
            "day": 0
          },
          "fieldOfStudy": "Mechanical Engineering",
          "start": {
            "year": 2007,
            "month": 0,
            "day": 0
          },
          "degree": "B.Tech",
          "schoolName": "National Institute of Technology, Tiruchirappalli"
        }
      ],
      "position": [
        {
          "location": "San Francisco Bay Area",
          "companyName": "Pavilion",
          "companyIndustry": "Think Tanks"
        },
        {
          "location": "San Francisco Bay Area",
          "description": "Building Agent helpers for Marketing teams",
          "companyName": "KiwiQ AI",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "San Francisco Bay Area",
          "description": "OnDeck Founder Fellow",
          "companyName": "On Deck",
          "companyIndustry": "Computer Software"
        },
        {
          "description": "Advising B2B startups with their GTM\n\nAngel invested in a few startups (B2B, Deeptech)",
          "companyName": "Various Startups",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "San Francisco, California, United States",
          "description": "Led research, planning, and delivery of 0-to-1 self-serve product targeting Brand Managers and Ad Agencies, scaling to 15 beta users first $100K ARR. \n\nWorked closely with the Founders, leading a cross-functional team of 4 Engineers and 1 UX Designer.",
          "companyName": "Swayable",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "San Francisco Bay Area",
          "description": "Closely partnered with an enterprise beta client to deliver Sounding Board's first SaaS product (0-to-1),\nmanaging a team of 9 engineers and 2 designers.",
          "companyName": "Sounding Board, Inc",
          "companyIndustry": "Professional Training & Coaching"
        },
        {
          "location": "Cupertino, California, United States",
          "description": "Single-threaded leader of the 3P fulfillment workstream for Amazon B2B; developed multi-\nyear product roadmap, driving feature prioritization and technical delivery plan.",
          "companyName": "Amazon",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "Santa Clara, California, United States",
          "description": "Led the internal GTM for a 0-to-1 customer insights product using NLP, growing to 50+ internal team users",
          "companyName": "Amazon",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "Luxembourg",
          "description": "Led product for personalization and customer experience for Amazon's launch in the Netherlands.",
          "companyName": "Amazon",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "Greater Seattle Area",
          "description": "Set up an NLP-powered Voice of Customer product function within Amazon's used products business.",
          "companyName": "Amazon",
          "companyIndustry": "Computer Software"
        },
        {
          "location": "Austin, Texas Area",
          "companyName": "Dell",
          "companyIndustry": "Computer Hardware"
        },
        {
          "location": "São Paulo Area, Brazil",
          "companyName": "Bunzl plc",
          "companyIndustry": "Wholesale"
        },
        {
          "location": "Bengaluru Area, India",
          "description": "Launched the company's fastest growing category (0-to-1), wearing multiple hats to make it happen.",
          "companyName": "Urban Ladder",
          "companyIndustry": "Computer Software"
        }
      ],
      "created_at": "2025-05-24T05:10:33.407000",
      "updated_at": "2025-05-24T05:10:33.407000"
    },
            is_versioned=False,
            is_shared=False,
            initial_version="default",
            is_system_entity=False
        ),
    ]

    # Cleanup documents - explicitly clean up all test documents created during setup
    cleanup_docs = [
        # User Preferences Document
        CleanupDocInfo(
            namespace=USER_PREFERENCES_NAMESPACE_TEMPLATE.format(item=entity_username),
            docname=USER_PREFERENCES_DOCNAME,
            is_versioned=USER_PREFERENCES_IS_VERSIONED,
            is_shared=False,
            is_system_entity=False
        ),
        # LinkedIn Profile Document
        CleanupDocInfo(
            namespace=LINKEDIN_SCRAPING_NAMESPACE_TEMPLATE.format(item=entity_username),
            docname=LINKEDIN_PROFILE_DOCNAME,
            is_versioned=False,
            is_shared=False,
            is_system_entity=False
        ),
    ]

    try:
        # Run the workflow test
        final_run_status_obj, final_run_outputs = await run_workflow_test(
            test_name=test_name,
            workflow_graph_schema=workflow_graph_schema,
            initial_inputs=test_inputs,
            expected_final_status=WorkflowRunStatus.COMPLETED,
            hitl_inputs=[],
            setup_docs=setup_docs,
            cleanup_docs_created_by_setup=True,  # Auto-cleanup setup docs
            cleanup_docs=cleanup_docs,  # Explicit cleanup docs for safety
            validate_output_func=validate_core_beliefs_perspectives_extraction_output,
            stream_intermediate_results=True,
            poll_interval_sec=5,
            timeout_sec=600
        )

        print(f"---Finished ---")
        if final_run_status_obj.status == WorkflowRunStatus.COMPLETED:
            print(f"completed successfully!")
            
            # Display the personalized questions output
            if final_run_outputs:
                personalized_output = final_run_outputs.get("personalized_questions", {})
                if personalized_output:
                    print("\n--- TOP QUESTIONS FOR CONTENT CREATION ---")
                    print(f"Introduction: {personalized_output.get('introduction', '')[:200]}...")
                    
                    top_questions = personalized_output.get("top_questions", [])
                    print(f"✓ Selected {len(top_questions)} top questions for content creation")
                    
                    # Show first few questions as examples
                    for i, question in enumerate(top_questions[:3]):
                        print(f"\nQuestion {i+1}:")
                        print(f"  Text: {question.get('question_text', '')}")
                        print(f"  Context: {question.get('context_explanation', '')[:100]}...")
                    
                    selection_reasoning = personalized_output.get('selection_reasoning', '')
                    if selection_reasoning:
                        print(f"\nSelection Reasoning: {selection_reasoning[:200]}...")
                
                # Display content intelligence output
                content_intelligence = final_run_outputs.get("content_intelligence", {})
                if content_intelligence:
                    print("\n--- CONTENT INTELLIGENCE SUMMARY ---")
                    print(f"📊 Total Themes: {content_intelligence.get('total_themes_identified', 0)}")
                    print(f"🏆 Top Theme: {content_intelligence.get('top_theme_name', 'N/A')}")
                    
                    top_3_themes = content_intelligence.get("top_3_themes", [])
                    if top_3_themes:
                        print(f"\n🎯 TOP 3 CONTENT THEMES:")
                        for i, theme in enumerate(top_3_themes[:3]):
                            print(f"\n{i+1}. {theme.get('theme_name', 'Unknown')}")
                            print(f"   📈 Avg Likes: {theme.get('avg_engagement_likes', 0)}")
                            print(f"   💬 Avg Comments: {theme.get('avg_engagement_comments', 0)}")
                            print(f"   🎭 Tone: {theme.get('dominant_tone', 'N/A')}")
                    
                    writing_dna = content_intelligence.get("writing_dna", {})
                    if writing_dna:
                        print(f"\n📝 WRITING DNA:")
                        signature_phrases = writing_dna.get("signature_phrases", [])
                        if signature_phrases:
                            print(f"   🎨 Signature Phrases: {', '.join(signature_phrases[:3])}")
                        print(f"   ✍️ Writing Style: {writing_dna.get('writing_style', 'N/A')}")
                        print(f"   📊 Data Usage: {writing_dna.get('data_usage_level', 'N/A')}")
                        print(f"   😊 Emoji Style: {writing_dna.get('emoji_style', 'N/A')}")
                    
                    winning_formulas = content_intelligence.get("winning_formulas", {})
                    if winning_formulas:
                        print(f"\n🚀 WINNING FORMULAS:")
                        opening_patterns = winning_formulas.get("top_opening_patterns", [])
                        if opening_patterns:
                            print(f"   🎯 Top Openings: {', '.join(opening_patterns[:2])}")
                        closing_patterns = winning_formulas.get("top_closing_patterns", [])
                        if closing_patterns:
                            print(f"   🏁 Top Closings: {', '.join(closing_patterns[:2])}")
                        power_words = winning_formulas.get("power_words", [])
                        if power_words:
                            print(f"   💪 Power Words: {', '.join(power_words[:5])}")
                
                # Show core questions structure
                core_questions = final_run_outputs.get("core_beliefs_questions", {})
                if core_questions:
                    total_questions = sum(len(questions) for questions in core_questions.values() if isinstance(questions, list))
                    print(f"\n✓ Generated {total_questions} initial questions, filtered to top {len(top_questions)} for content creation")
            
            return final_run_status_obj, final_run_outputs
        else:
            print(f"failed with status: {final_run_status_obj.status}")
            print(f"Error: {final_run_status_obj.error}")
            return final_run_status_obj, final_run_outputs

    except Exception as e:
        logging.error("failed with exception: {str(e)}")
        print(f"failed with exception: {str(e)}")
        return None, None


async def validate_core_beliefs_perspectives_extraction_output(
    outputs: Optional[Dict[str, Any]]
) -> bool:
    """
    Validate the core beliefs and perspectives extraction workflow output.
    """
    if not outputs:
        logging.error("No outputs received from workflow")
        return False

    # Check for required output fields
    required_fields = ["personalized_questions", "core_beliefs_questions", "content_intelligence"]
    
    for field in required_fields:
        if field not in outputs:
            logging.error(f"Missing required output field: {field}")
            return False

    # Validate personalized questions output structure
    personalized_output = outputs.get("personalized_questions", {})
    if not isinstance(personalized_output, dict):
        logging.error("personalized_questions is not a dictionary")
        return False

    # Check for required personalized output fields
    required_personalized_fields = ["top_questions"]
    for field in required_personalized_fields:
        if field not in personalized_output:
            logging.error(f"Missing required personalized output field: {field}")
            return False

    # Validate questions
    top_questions = personalized_output.get("top_questions", [])
    if not isinstance(top_questions, list) or len(top_questions) == 0:
        logging.error("top_questions should be a non-empty list")
        return False

    # Validate that each question has the required fields
    for i, question in enumerate(top_questions):
        if not isinstance(question, dict):
            logging.error(f"Question {i} is not a dictionary")
            return False
        
        required_question_fields = ["question_text", "context_explanation"]
        for field in required_question_fields:
            if field not in question:
                logging.error(f"Question {i} missing required field: {field}")
                return False
            
            if not question[field] or len(question[field].strip()) < 10:
                logging.error(f"Question {i} field '{field}' should be substantial")
                return False

    # Validate core beliefs questions structure
    core_questions = outputs.get("core_beliefs_questions", {})
    if not isinstance(core_questions, dict):
        logging.error("core_beliefs_questions is not a dictionary")
        return False

    # Validate content intelligence output structure
    content_intelligence = outputs.get("content_intelligence", {})
    if not isinstance(content_intelligence, dict):
        logging.error("content_intelligence is not a dictionary")
        return False

    # Check for required content intelligence fields
    required_intelligence_fields = ["total_themes_identified", "top_theme_name", "top_3_themes", "writing_dna", "winning_formulas"]
    for field in required_intelligence_fields:
        if field not in content_intelligence:
            logging.error(f"Missing required content intelligence field: {field}")
            return False

    # Validate top_3_themes is a list
    top_3_themes = content_intelligence.get("top_3_themes", [])
    if not isinstance(top_3_themes, list):
        logging.error("top_3_themes should be a list")
        return False

    # Validate writing_dna structure
    writing_dna = content_intelligence.get("writing_dna", {})
    if not isinstance(writing_dna, dict):
        logging.error("writing_dna should be a dictionary")
        return False

    # Validate winning_formulas structure
    winning_formulas = content_intelligence.get("winning_formulas", {})
    if not isinstance(winning_formulas, dict):
        logging.error("winning_formulas should be a dictionary")
        return False

    logging.info("Core beliefs and perspectives extraction output validation passed")
    return True


# --- Main Execution ---
if __name__ == "__main__":
    try:
        asyncio.run(main_test_core_beliefs_perspectives_extraction())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")
        logging.error(f"Error running test: {e}") 