"""

Flow: 
1. input node -> load_all_context_docs and load_draft_posts
2. [load_all_context_docs, load_draft_posts] -> construct_initial_concepts_prompt (enable_node_fan_in true)
3. construct_initial_concepts_prompt -> generate_content
4. generate_content -> store_customer_data
5. store_customer_data -> capture_user_choice
5. capture_user_choice -> route_on_user_choice
6. route_on_user_choice -> construct_concepts_regeneration_prompt [selection: regenerate concepts]
7. route_on_user_choice -> output_node [selection: Go back to initial ideas brief generation]
8. route_on_user_choice -> filter_selected_concepts [selection: select list of concepts]
9. construct_concepts_regeneration_prompt -> generate_content (concepts regeneration loop, generate_content reads message_history from state)
10. filter_selected_concepts -> construct_update_content_brief_prompt
11. construct_update_content_brief_prompt -> generated_updated_content_brief
12. generated_updated_content_brief -> save_updated_content_brief
13. save_updated_content_brief -> output_node
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
from kiwi_client.workflows.document_models.customer_docs import (
    ANALYSIS_OUTPUT_DOCNAME_PATTERN,
    LINKEDIN_PROFILE_DOCNAME,
    LINKEDIN_SCRAPING_NAMESPACE,
    ANALYSIS_OUTPUT_NAMESPACE,
)

# --- Workflow Configuration Constants ---
# Namespaces and storage
USER_PROFILES_NAMESPACE = "user_profiles"
LINKEDIN_SCRAPING_NAMESPACE = "linkedin_scraping"
CONTENT_PILLARS_NAMESPACE = "content_pillars"
USER_DNA_NAMESPACE = "user_dna"

# Document name patterns
USER_PREFERENCES_DOCNAME = "user_preferences_doc"
CONTENT_PILLARS_DOCNAME = "content_pillars_doc"
USER_DNA_DOCNAME_PATTERN = "user_dna_{item}"

# LLM Configuration
LLM_PROVIDER = "openai"
GENERATION_MODEL = "gpt-4.1"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4000

### SAVE DOCUMENT CONFIG ###
SAVE_DOC_NAMESPACE = USER_DNA_NAMESPACE
SAVE_DOC_DOCNAME_PATTERN = USER_DNA_DOCNAME_PATTERN
SAVE_DOCNAME_INPUT_FIELD = "entity_username"
SAVE_DOC_FILENAME_CONFIG = {
    "filename_config": {
        "static_namespace": SAVE_DOC_NAMESPACE,
        "input_docname_field": SAVE_DOCNAME_INPUT_FIELD, # Field in node's input containing the value
        "input_docname_field_pattern": SAVE_DOC_DOCNAME_PATTERN  # 'item' here will be the value of entity_name
    }
}
SAVE_DOC_GLOBAL_VERSIONING = {
    "is_versioned": True,
    "operation": "upsert_versioned",
    "version": "generated_dna_v1"
}
########################

### GENERATION SCHEMA ###
# --- Pydantic Schemas for LLM Outputs ---
class ProfessionalIdentity(BaseModel):
    """Professional background, experience, and expertise."""
    background: str = Field(..., description="Professional background and career history.")
    experience: str = Field(..., description="Key professional experiences and achievements.")
    expertise: List[str] = Field(..., description="Core areas of professional expertise.")

class LinkedInMetrics(BaseModel):
    """Key LinkedIn metrics and engagement data."""
    likes_per_post: Optional[float] = Field(None, description="Average likes per post.")
    comments_per_post: Optional[float] = Field(None, description="Average comments per post.")
    shares_per_post: Optional[float] = Field(None, description="Average shares per post.")
    top_performing_content_types: List[str] = Field(default_factory=list, description="Types of content with highest engagement.")
    audience_demographics: Optional[str] = Field(None, description="Summary of audience demographics if available.")

class LinkedInProfileAnalysis(BaseModel):
    """Analysis of LinkedIn profile metrics and engagement data."""
    follower_count: Optional[int] = Field(None, description="Number of LinkedIn followers.")
    engagement_rate: Optional[float] = Field(None, description="Average engagement rate on LinkedIn content.")
    post_frequency: Optional[str] = Field(None, description="Typical posting frequency.")
    key_metrics: LinkedInMetrics = Field(..., description="Other relevant LinkedIn metrics and engagement data.")

class BrandVoiceStyle(BaseModel):
    """Brand voice, tone, and communication preferences."""
    voice: str = Field(..., description="Overall voice characteristics (e.g., authoritative, conversational).")
    tone: str = Field(..., description="Tone preferences (e.g., professional, inspirational).")
    communication_style: str = Field(..., description="Preferred communication style and patterns.")
    content_preferences: List[str] = Field(..., description="Content format and style preferences.")

class ContentStrategyGoals(BaseModel):
    """Content strategy objectives, audience, and topics."""
    objectives: List[str] = Field(..., description="Primary content strategy objectives.")
    target_audience: List[str] = Field(..., description="Target audience segments and personas.")
    core_topics: List[str] = Field(..., description="Core content topics and themes.")
    ideal_outcomes: List[str] = Field(..., description="Desired outcomes from content strategy.")

class PersonalContext(BaseModel):
    """Personal values, influences, and narrative elements."""
    values: List[str] = Field(..., description="Core personal and professional values.")
    influences: List[str] = Field(..., description="Key influences on professional perspective.")
    story_elements: List[str] = Field(..., description="Narrative elements that could be incorporated into content.")

class EngagementPatterns(BaseModel):
    """Patterns in audience engagement."""
    best_times: List[str] = Field(default_factory=list, description="Best times for posting based on engagement.")
    best_days: List[str] = Field(default_factory=list, description="Best days for posting based on engagement.")
    content_types: List[str] = Field(default_factory=list, description="Content types with highest engagement.")
    engagement_triggers: List[str] = Field(default_factory=list, description="Topics or approaches that trigger engagement.")

class AnalyticsInsights(BaseModel):
    """Performance data and engagement patterns."""
    best_performing_content: List[str] = Field(..., description="Types or examples of best-performing content.")
    engagement_patterns: EngagementPatterns = Field(..., description="Patterns in audience engagement.")
    improvement_areas: List[str] = Field(..., description="Areas for potential improvement in content strategy.")

class SuccessMetrics(BaseModel):
    """KPIs, timeline, and benchmarks."""
    kpis: List[str] = Field(..., description="Key performance indicators for content strategy.")
    timeline: str = Field(..., description="Expected timeline for achieving goals.")
    benchmarks: List[str] = Field(..., description="Specific benchmarks to measure success against.")

class UserDNA(BaseModel):
    """
    Complete user DNA profile based on LinkedIn data analysis.
    """
    professional_identity: ProfessionalIdentity = Field(..., description="Professional background, experience, and expertise.")
    linkedin_profile_analysis: LinkedInProfileAnalysis = Field(..., description="Analysis of LinkedIn profile metrics and engagement data.")
    brand_voice_style: BrandVoiceStyle = Field(..., description="Brand voice, tone, and communication preferences.")
    content_strategy_goals: ContentStrategyGoals = Field(..., description="Content strategy objectives, audience, and topics.")
    personal_context: PersonalContext = Field(..., description="Personal values, influences, and narrative elements.")
    analytics_insights: AnalyticsInsights = Field(..., description="Performance data and engagement patterns.")
    success_metrics: SuccessMetrics = Field(..., description="KPIs, timeline, and benchmarks.")

GENERATION_SCHEMA = UserDNA.model_json_schema()
########################

### USER PROMPT TEMPLATE ###
USER_PROMPT_TEMPLATE = """Gather and analyze the following information about the user to build their User DNA.

LinkedIn Profile for: {entity_username}

**Available Data to Analyze:**
- LinkedIn Profile Data: {linkedin_profile}
- Content Analysis Results: {content_analysis}
- User Preferences: {user_preferences}
- Content Pillars: {content_pillars}

**Task:**
Create a comprehensive User DNA profile based on the provided data. Include all required sections:
1. Professional Identity (background, experience, expertise)
2. LinkedIn Profile Analysis (metrics, engagement data)
3. Brand Voice & Style (communication preferences)
4. Content Strategy Goals (objectives, audience, topics)
5. Personal Context (values, influences, story elements)
6. Analytics Insights (performance data, patterns)
7. Success Metrics (KPIs, timeline, benchmarks)

Respond ONLY with the JSON object matching the specified schema.
"""

USER_PROMPT_TEMPLATE_VARIABLES = {
    "linkedin_profile": None,
    "content_analysis": None,
    "user_preferences": None,
    "content_pillars": None,
    "entity_username": None
}

USER_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {
    "linkedin_profile": "linkedin_profile",
    "content_analysis": "content_analysis",
    "user_preferences": "user_preferences",
    "content_pillars": "content_pillars",
    "entity_username": "entity_username"
}
##############################

### SYSTEM PROMPT TEMPLATE ###
SYSTEM_PROMPT_TEMPLATE = "You are an expert in professional branding and LinkedIn strategy. Gather and analyze information about the user to build their User DNA profile. Use the provided LinkedIn profile, content analysis, and additional materials to complete the User DNA Template. Focus on extracting meaningful insights that can inform an effective content strategy. Respond strictly with the JSON output conforming to the schema: ```json\n{schema}\n```"

SYSTEM_PROMPT_TEMPLATE_VARIABLES = {
    "schema": GENERATION_SCHEMA
}

SYSTEM_PROMPT_TEMPLATE_CONSTRUCT_OPTIONS = {}
##############################

### EDGES CONFIG ###
field_mappings_from_state_to_prompt_constructor = [
    { "src_field": "linkedin_profile", "dst_field": "linkedin_profile"},
    { "src_field": "content_analysis", "dst_field": "content_analysis" },
    { "src_field": "user_preferences", "dst_field": "user_preferences" },
    { "src_field": "content_pillars", "dst_field": "content_pillars" },
    { "src_field": "entity_username", "dst_field": "entity_username" },
]

field_mappings_from_input_to_state = [
    { "src_field": "customer_context_doc_configs", "dst_field": "customer_context_doc_configs" },
    { "src_field": "entity_username", "dst_field": "entity_username" },
]

field_mappings_from_input_to_load_all_context_docs = [
    { "src_field": "customer_context_doc_configs", "dst_field": "customer_context_doc_configs" },
    { "src_field": "entity_username", "dst_field": "entity_username" },
]

field_mappings_from_load_all_context_docs_to_state = [
    { "src_field": "linkedin_profile", "dst_field": "linkedin_profile"},
    { "src_field": "content_analysis", "dst_field": "content_analysis"},
    { "src_field": "user_preferences", "dst_field": "user_preferences"},
    { "src_field": "content_pillars", "dst_field": "content_pillars"},
]

field_mappings_from_state_to_store_customer_data = [
    { "src_field": "entity_username", "dst_field": "entity_username"}
]

#############

### INPUTS ###

INPUT_FIELDS = {
    "customer_context_doc_configs": {
        "type": "list",
        "required": True,
        "description": "List of document identifiers (namespace/docname pairs) for customer context like LinkedIn profile, content analysis, etc."
    },
    "entity_username": { "type": "str", "required": True, "description": "LinkedIn username to generate User DNA for."},
}

INPUT_DOCS_TO_BE_LOADED_IN_WORKFLOW = [
    {
        "filename_config": {
            "static_namespace": LINKEDIN_SCRAPING_NAMESPACE,
            "input_docname_field": "entity_username", 
            "input_docname_field_pattern": LINKEDIN_PROFILE_DOCNAME
        },
        "output_field_name": "linkedin_profile",
        "is_shared": False,
        "is_system_entity": False
    },
    {
        "filename_config": {
            "static_namespace": ANALYSIS_OUTPUT_NAMESPACE,
            "input_docname_field": "entity_username",
            "input_docname_field_pattern": ANALYSIS_OUTPUT_DOCNAME_PATTERN
        },
        "output_field_name": "content_analysis",
        "is_shared": False,
        "is_system_entity": False
    },
    {
        "filename_config": {
            "static_namespace": USER_PROFILES_NAMESPACE, 
            "static_docname": USER_PREFERENCES_DOCNAME,
        },
        "output_field_name": "user_preferences",
        "is_shared": False,
        "is_system_entity": False
    },
    {
        "filename_config": {
            "static_namespace": CONTENT_PILLARS_NAMESPACE,
            "static_docname": CONTENT_PILLARS_DOCNAME,
        },
        "output_field_name": "content_pillars",
        "is_shared": True,
        "is_system_entity": True
    },
]

##############


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
                # Outputs: user_id, weeks_to_generate, customer_context_doc_configs, past_context_posts_limit -> $graph_state
        },

        # --- 2. Load Customer Context Documents and Scraped Posts (Single Node) ---
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

        # --- 9. Construct Brief Prompt (Inside Map Branch) ---
        "construct_prompt": {
            "node_id": "construct_prompt",
            "node_name": "prompt_constructor",
            "enable_node_fan_in": True,  # Wait for all data loads before proceeding
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

        # --- 10. Generate Brief (LLM - Inside Map Branch) ---
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
                    "schema_definition": GENERATION_SCHEMA
                },
            }
        },

        # --- 5. Store Concepts ---
        "store_customer_data": {
            "node_id": "store_customer_data",
            "node_name": "store_customer_data",
            "node_config": {
                    "global_versioning": SAVE_DOC_GLOBAL_VERSIONING,
                "store_configs": [
                {
                    "input_field_path": "structured_output", # Field name in node input containing the value to save
                    "target_path": SAVE_DOC_FILENAME_CONFIG
                }
                ]
            }
            },


        # --- 12. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {},
            # "dynamic_input_schema": { # Define expected final inputs
            #     "fields": {
            #         "final_briefs_list": { "type": "list", "required": True, "description": "The complete list of generated content briefs." },
            #         "brief_paths_processed": { "type": "list", "required": False, "description": "Confirmation/path from the storage operation." }
            #     }
            # }
            # Reads: updated_brief (mapped to final_briefs_list), paths_processed (mapped to save_confirmation)
        },

    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # --- Initial Setup ---
        # Input -> State: Store initial inputs globally
        { "src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": field_mappings_from_input_to_state
        },
        
        # Input -> Load operations
        { "src_node_id": "input_node", "dst_node_id": "load_all_context_docs", "mappings": field_mappings_from_input_to_load_all_context_docs, "description": "Trigger context docs loading."
        },


        # --- State Updates from Loaders ---
        { "src_node_id": "load_all_context_docs", "dst_node_id": "$graph_state", "mappings": field_mappings_from_load_all_context_docs_to_state
        },

        # --- Trigger Initial Concept Generation ---
        { "src_node_id": "load_all_context_docs", "dst_node_id": "construct_prompt" },

        # --- Mapping State to Initial Concepts Prompt ---
        { "src_node_id": "$graph_state", "dst_node_id": "construct_prompt", "mappings": field_mappings_from_state_to_prompt_constructor
        },

        # --- Construct Prompt → Generate Concepts ---
        { "src_node_id": "construct_prompt", "dst_node_id": "generate_content", "mappings": [
            { "src_field": "user_prompt", "dst_field": "user_prompt"},
            { "src_field": "system_prompt", "dst_field": "system_prompt"}
          ], "description": "Send prompts to LLM for concept generation."
        },

        # --- State -> Generate Concepts ---
        { "src_node_id": "$graph_state", "dst_node_id": "generate_content", "mappings": [
            { "src_field": "messages_history", "dst_field": "messages_history"}
          ]
        },

        # # --- Generate Concepts -> Store & State ---
        # { "src_node_id": "generate_content", "dst_node_id": "$graph_state", "mappings": [
        #     { "src_field": "structured_output", "dst_field": "current_generated_concepts"},
        #     { "src_field": "current_messages", "dst_field": "messages_history"}
        #   ]
        # },

        { "src_node_id": "generate_content", "dst_node_id": "store_customer_data", "mappings": [
            { "src_field": "structured_output", "dst_field": "structured_output"},
          ]
        },

        { "src_node_id": "generate_content", "dst_node_id": "$graph_state", "mappings": [
            { "src_field": "structured_output", "dst_field": "generated_output"},
          ]
        },

        # --- State -> Store Concepts ---
        { "src_node_id": "$graph_state", "dst_node_id": "store_customer_data", "mappings": field_mappings_from_state_to_store_customer_data
        },

        # --- Store Concepts -> User Choice ---
        { "src_node_id": "store_customer_data", "dst_node_id": "output_node", "mappings": [
            { "src_field": "paths_processed", "dst_field": "paths_processed"}
          ]
        },

        # --- State -> User Choice ---
        { "src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
            { "src_field": "generated_output", "dst_field": "generated_output"}
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
                # NOTE: If you set collect_values reducer here, it distorts / nests the concepts structure and fails the FILTER NODE!
                # "current_generated_concepts": "collect_values",
                # "messages_history": "add_messages"
            }
        }
    }
}

# --- Test Execution Logic ---
async def main_test_idea_to_brief_workflow():
    """
    Test for User DNA Generation Workflow.
    """
    test_name = "User DNA Generation Workflow Test"
    print(f"--- Starting {test_name} --- ")

    # Example Inputs
    test_context_docs = INPUT_DOCS_TO_BE_LOADED_IN_WORKFLOW
    
    entity_username = "johndoe123"
    
    test_inputs = {
        "customer_context_doc_configs": test_context_docs,
        "entity_username": entity_username
    }

    # Define setup documents
    setup_docs: List[SetupDocInfo] = [
        {
            'namespace': LINKEDIN_SCRAPING_NAMESPACE, 
            'docname': LINKEDIN_PROFILE_DOCNAME.format(item=entity_username),
            'initial_data': {
                "profile_info": {
                    "name": "John Doe",
                    "headline": "Digital Marketing Director | Brand Strategy | Content Marketing",
                    "location": "San Francisco, CA",
                    "connections": 1450,
                    "followers": 2300
                },
                "about": "Digital marketing professional with 10+ years of experience driving growth and engagement for B2B tech companies. Passionate about leveraging data-driven strategies to connect brands with their ideal audience.",
                "experience": [
                    {
                        "title": "Marketing Director",
                        "company": "TechSolutions Inc.",
                        "duration": "2018 - Present",
                        "description": "Leading digital marketing strategy across channels."
                    },
                    {
                        "title": "Senior Marketing Manager",
                        "company": "InnovateX",
                        "duration": "2015 - 2018",
                        "description": "Managed content strategy and marketing campaigns."
                    }
                ],
                "education": [
                    {
                        "school": "Stanford University",
                        "degree": "MBA, Marketing",
                        "year": "2013 - 2015"
                    }
                ],
                "skills": ["Digital Marketing", "Content Strategy", "Brand Development", "Marketing Analytics", "Team Leadership"]
            }, 
            'is_versioned': False, 
            'is_shared': False,
            'initial_version': None,
            'is_system_entity': False
        },
        {
            'namespace': ANALYSIS_OUTPUT_NAMESPACE, 
            'docname': ANALYSIS_OUTPUT_DOCNAME_PATTERN.format(item=entity_username),
            'initial_data': {
                "post_analysis": {
                    "post_frequency": "2-3 times per week",
                    "average_engagement": {
                        "likes": 45,
                        "comments": 12,
                        "shares": 8
                    },
                    "top_performing_content": [
                        "Thought leadership articles on industry trends",
                        "Case studies with measurable results",
                        "Behind-the-scenes content about team culture"
                    ]
                },
                "content_themes": [
                    "Digital marketing strategy",
                    "Marketing technology adoption",
                    "Team management and leadership",
                    "Data-driven decision making"
                ],
                "audience_insights": {
                    "most_engaged_segments": ["Marketing Professionals", "Tech Industry Leaders", "Startup Founders"],
                    "common_industries": ["Technology", "Marketing & Advertising", "SaaS"]
                },
                "content_format_analysis": {
                    "text_posts": "40% (average engagement: medium)",
                    "image_posts": "35% (average engagement: high)",
                    "video_content": "15% (average engagement: very high)",
                    "document_shares": "10% (average engagement: medium-low)"
                }
            }, 
            'is_versioned': False, 
            'is_shared': False,
            'initial_version': None,
            'is_system_entity': False
        },
        {
            'namespace': USER_PROFILES_NAMESPACE, 
            'docname': USER_PREFERENCES_DOCNAME,
            'initial_data': {
                "preferred_posting_schedule": {
                    "frequency": "3 times per week",
                    "best_days": ["Monday", "Wednesday", "Friday"],
                    "best_times": ["8:30 AM", "12:00 PM"]
                },
                "content_preferences": {
                    "tone": "Professional with occasional humor",
                    "length": "Medium to long-form content",
                    "media_types": ["Images", "Infographics", "Short videos"]
                },
                "strategy_goals": [
                    "Establish thought leadership in digital marketing",
                    "Grow LinkedIn following to 5,000 within 6 months",
                    "Generate more speaking opportunities at industry events",
                    "Connect with potential clients and partners"
                ],
                "content_topics": [
                    "Marketing strategy trends",
                    "Team leadership in creative fields",
                    "Marketing technology tools and adoption",
                    "Case studies and success stories"
                ]
            }, 
            'is_versioned': False, 
            'is_shared': False,
            'initial_version': None,
            'is_system_entity': False
        },
        {
            # NOTE: this can only be created by a superuser!
            'namespace': CONTENT_PILLARS_NAMESPACE,
            'docname': CONTENT_PILLARS_DOCNAME,
            'initial_data': {
                "recommended_pillars": [
                    {
                        "pillar_name": "Thought Leadership",
                        "description": "Content that establishes authority and unique perspective in your industry",
                        "suggested_formats": ["Long-form articles", "Industry analysis", "Prediction posts"],
                        "recommended_frequency": "25-30% of content"
                    },
                    {
                        "pillar_name": "Educational Content",
                        "description": "Content that teaches your audience valuable skills or knowledge",
                        "suggested_formats": ["How-to guides", "Tips and tricks", "Tutorials"],
                        "recommended_frequency": "30-35% of content"
                    },
                    {
                        "pillar_name": "Community Engagement",
                        "description": "Content that builds connections with your audience",
                        "suggested_formats": ["Questions", "Polls", "Discussion starters"],
                        "recommended_frequency": "15-20% of content"
                    },
                    {
                        "pillar_name": "Personal Brand",
                        "description": "Content that humanizes your brand and shares your story",
                        "suggested_formats": ["Behind-the-scenes", "Career journey posts", "Values-focused content"],
                        "recommended_frequency": "10-15% of content"
                    },
                    {
                        "pillar_name": "Social Proof",
                        "description": "Content that demonstrates credibility through results and testimonials",
                        "suggested_formats": ["Case studies", "Testimonials", "Results showcases"],
                        "recommended_frequency": "10-15% of content"
                    }
                ],
                "implementation_framework": {
                    "step_1": "Identify your unique value proposition",
                    "step_2": "Analyze audience needs and pain points",
                    "step_3": "Map content pillars to audience needs",
                    "step_4": "Create content calendar based on pillars",
                    "step_5": "Track performance and adjust strategy"
                },
                "success_indicators": [
                    "Engagement growth over time",
                    "Follower growth rate",
                    "Conversion to website visits",
                    "Lead generation",
                    "Network quality improvement"
                ]
            },
            'is_versioned': False,
            'is_shared': True,
            'initial_version': None,
            'is_system_entity': True
        }
    ]

    # Define cleanup docs
    cleanup_docs: List[CleanupDocInfo] = [
        {'namespace': LINKEDIN_SCRAPING_NAMESPACE, 'docname': LINKEDIN_PROFILE_DOCNAME.format(item=entity_username), 'is_versioned': False, 'is_shared': False, 'is_system_entity': False},
        {'namespace': ANALYSIS_OUTPUT_NAMESPACE, 'docname': ANALYSIS_OUTPUT_DOCNAME_PATTERN.format(item=entity_username), 'is_versioned': False, 'is_shared': False, 'is_system_entity': False},
        {'namespace': USER_PROFILES_NAMESPACE, 'docname': USER_PREFERENCES_DOCNAME, 'is_versioned': False, 'is_shared': False, 'is_system_entity': False},
        {'namespace': CONTENT_PILLARS_NAMESPACE, 'docname': CONTENT_PILLARS_DOCNAME, 'is_versioned': False, 'is_shared': True, 'is_system_entity': True},
        {'namespace': USER_DNA_NAMESPACE, 'docname': USER_DNA_DOCNAME_PATTERN.format(item=entity_username), 'is_versioned': True, 'is_shared': False, 'is_system_entity': False},
    ]

    # Predefined HITL inputs
    predefined_hitl_inputs = []

    # Output validation function
    async def validate_user_dna_output(outputs):
        """
        Validates the output from the User DNA generation workflow against expected schema.
        
        Args:
            outputs: The workflow output dictionary to validate
            
        Returns:
            bool: True if validation passes, raises AssertionError otherwise
        """
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        assert 'generated_output' in outputs, "Validation Failed: 'generated_output' missing."
        assert 'paths_processed' in outputs, "Validation Failed: 'paths_processed' missing."
        
        # Validate the User DNA structure
        if 'generated_output' in outputs:
            user_dna = outputs['generated_output']
            
            # Validate the top-level sections
            assert 'professional_identity' in user_dna, "User DNA is missing 'professional_identity' section"
            assert 'linkedin_profile_analysis' in user_dna, "User DNA is missing 'linkedin_profile_analysis' section"
            assert 'brand_voice_style' in user_dna, "User DNA is missing 'brand_voice_style' section"
            assert 'content_strategy_goals' in user_dna, "User DNA is missing 'content_strategy_goals' section"
            assert 'personal_context' in user_dna, "User DNA is missing 'personal_context' section"
            assert 'analytics_insights' in user_dna, "User DNA is missing 'analytics_insights' section"
            assert 'success_metrics' in user_dna, "User DNA is missing 'success_metrics' section"
            
            # Validate a few key fields in each section
            prof_id = user_dna['professional_identity']
            assert 'background' in prof_id, "Professional identity missing 'background'"
            assert 'expertise' in prof_id, "Professional identity missing 'expertise'"
            
            brand_voice = user_dna['brand_voice_style']
            assert 'voice' in brand_voice, "Brand voice & style missing 'voice'"
            assert 'content_preferences' in brand_voice, "Brand voice & style missing 'content_preferences'"
            
            # Log success message
            print(f"✓ User DNA validated successfully")
            print(f"✓ Professional background: {prof_id.get('background', 'unknown')[:100]}...")
            print(f"✓ Brand voice: {brand_voice.get('voice', 'unknown')}")
        
        return True

    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        hitl_inputs=predefined_hitl_inputs,
        setup_docs=setup_docs,
        cleanup_docs=cleanup_docs,
        validate_output_func=validate_user_dna_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=600
    )

    print(f"--- {test_name} Finished --- ")
    if final_run_outputs and 'generated_output' in final_run_outputs:
        user_dna = final_run_outputs['generated_output']
        print(f"Professional Identity: {user_dna.get('professional_identity', {}).get('background', 'unknown')[:100]}...")
        print(f"Brand Voice: {user_dna.get('brand_voice_style', {}).get('voice', 'unknown')}")
        print(f"Top Content Strategy Goal: {user_dna.get('content_strategy_goals', {}).get('objectives', ['unknown'])[0]}")
        print(f"Key Success Metric: {user_dna.get('success_metrics', {}).get('kpis', ['unknown'])[0]}")

if __name__ == "__main__":
    try:
        asyncio.run(main_test_idea_to_brief_workflow())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")

