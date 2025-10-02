"""
it costs ~15 cents / final filtered enriched lead, $10.39 for 73 leads, pretty expensive honestly; I processed 100 leads in parallel in ~10-11 mins

Lead Scoring and Personalized Talking Points Generation Workflow

This workflow demonstrates:
1. Taking a list of lead items with LinkedIn URL, Company, First Name, Last Name, Company website, Email ID, Job Title
2. Step 1: Parallel company qualification assessment using Perplexity LLM with structured output
3. Filtering qualified leads based on qualification_check_passed = True
4. Steps 2-4: Sequential LLM processing for each qualified lead:
   - Step 2: ContentQ scoring + content gap analysis
   - Step 3: Strategic content opportunity identification  
   - Step 4: Personalized talking points + pitch generation
5. Using private mode passthrough data to preserve context across all steps
6. Collecting final results with comprehensive lead insights and talking points

Input: List of lead items with required fields
Output: Qualified leads with ContentQ scores, content opportunities, and personalized talking points





# Setup instructions:

you can set it up and play around with prompts if you want (chatgpt / cursor / claude will guide you how to do it step by step)

0. `git clone https://github.com/KiwiQAI/standalone_client `
1. install python 3.12,
2. poetry instlal from repo standalone_test_client
3. setup .env file as below in folder like this standalone_test_client/kiwi_client/.env
4. download leads.csv from your sheet in folder (export to csv and rename file form google sheets) standalone_test_client/kiwi_client/workflows/active/sdr/
5. run file with diff limits (start and end row) to process diff rows in leads.csv https://github.com/KiwiQAI/standalone_client/blob/main/kiwi_client/workflows/active/sdr/wf_lead_scoring_personalized_talking_points.py


cursor is great to play around with it

.env file for step 3)
```
TEST_ENV=
TEST_USER_EMAIL=
TEST_USER_PASSWORD=
TEST_ORG_ID=
TEST_USER_ID=
```

NOTE: entries in leads.csv must be in same format as : https://docs.google.com/spreadsheets/d/10fgZhj7vQll-TkYMSKr5ogA0G3MSJ0BteZ8o1ETyGEM/edit?gid=0#gid=0

# Some key improvements:
some companies are not from US, eg from Nigeria, etc; we can include location in column and qualification criterion
we can scrape linkedin / posts and blogs too and use that to summarize / add richer detail instead of perplexity pulling all the weight research wise (unknown delta)
"""

from kiwi_client.workflows.active.sdr.lead_scoring_personalized_talking_points_sandbox.wf_llm_inputs import (
    STEP1_SYSTEM_PROMPT, STEP_1_QUALIFICATION_USER_PROMPT, STEP_1_QUALIFICATION_OUTPUT_SCHEMA, 
    STEP2_SYSTEM_PROMPT, STEP_2_CONTENTQ_USER_PROMPT, 
    STEP3_SYSTEM_PROMPT, STEP_3_STRATEGIC_USER_PROMPT, 
    STEP4_SYSTEM_PROMPT, STEP_4_TALKING_POINTS_USER_PROMPT, STEP4_TALKING_POINTS_OUTPUT_SCHEMA,
    LLM_PROVIDER_RESEARCH, LLM_MODEL_RESEARCH, LLM_TEMPERATURE_RESEARCH, LLM_MAX_TOKENS_RESEARCH,
    LLM_PROVIDER_WRITER, LLM_MODEL_WRITER, LLM_TEMPERATURE_WRITER, LLM_MAX_TOKENS_WRITER
)

# --- Private mode passthrough data keys for preserving context across steps ---
# Step 1 outputs that need to be preserved through all subsequent steps
step1_passthrough_keys = ["linkedinUrl", "Company", "firstName", "lastName", "companyWebsite", "emailId", "jobTitle", "qualification_result", "qualification_result_citations"]

# Step 2 outputs that need to be preserved through steps 3-4  
step2_passthrough_keys = ["linkedinUrl", "Company", "firstName", "lastName", "companyWebsite", "emailId", "jobTitle", "qualification_result", "qualification_result_citations", "contentq_and_content_analysis", "contentq_and_content_analysis_citations"]

# Step 3 outputs that need to be preserved through step 4
step3_passthrough_keys = ["linkedinUrl", "Company", "firstName", "lastName", "companyWebsite", "emailId", "jobTitle", "qualification_result", "qualification_result_citations", "contentq_and_content_analysis", "contentq_and_content_analysis_citations", "strategic_analysis", "strategic_analysis_citations"]

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
                    "leads_to_process": {
                        "type": "list",
                        "required": False,
                        "default": [
                            {
                                "linkedinUrl": "https://www.linkedin.com/in/ACoAAAGSbXUBOy1FuiRw9wcaJ-_24TnS_u4dgS8",
                                "Company": "Metadata.Io",
                                "firstName": "Dee", 
                                "lastName": "Acosta 🤖",
                                "companyWebsite": "metadata.io",
                                "emailId": "dee.acosta@metadata.io",
                                "jobTitle": "Ad AI, Sales, and GTM	"
                            },
                            {
                                "linkedinUrl": "https://www.linkedin.com/in/ACoAAAAMYK4BCyNT23Ui4i6ijdr7-Xu2s8H1pa4",
                                "Company": "Stacklok",
                                "firstName": "Christine",
                                "lastName": "Simonini", 
                                "companyWebsite": "stacklok.com",
                                "emailId": "csimonini@appomni.com",
                                "jobTitle": "Advisor"
                            },
                            {
                                "linkedinUrl": "https://www.linkedin.com/in/ACoAACngUhwBxcSAdAIis1EyHyGe0oSxoLg0lVE",
                                "Company": "Cresta",
                                "firstName": "Kurtis",
                                "lastName": "Wagner",
                                "companyWebsite": "cresta.com", 
                                "emailId": "kurtis@cresta.ai",
                                "jobTitle": "AI Agent Architect"
                            }
                        ],
                        "description": "List of leads with LinkedIn URL, Company, First Name, Last Name, Company website, Email ID, Job Title"
                    }
                }
            }
        },

        # --- 2. Map List Router Node - Routes each lead to Step 1 qualification ---
        "route_leads_to_qualification": {
            "node_id": "route_leads_to_qualification",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["step1_qualification_prompt"],
                "map_targets": [
                    {
                        "source_path": "leads_to_process",
                        "destinations": ["step1_qualification_prompt"],
                        "batch_size": 1
                    }
                ]
            }
        },

        # --- 3. Step 1: Prompt Constructor for Qualification Assessment ---
        "step1_qualification_prompt": {
            "node_id": "step1_qualification_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step1_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "qualification_system_prompt": {
                        "id": "qualification_system_prompt",
                        "template": STEP1_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "qualification_user_prompt": {
                        "id": "qualification_user_prompt", 
                        "template": STEP_1_QUALIFICATION_USER_PROMPT,
                        "variables": {
                            "Company": None,
                            "firstName": None,
                            "lastName": None,
                            "jobTitle": None,
                            "linkedinUrl": None,
                            "companyWebsite": None,
                            "emailId": None
                        },
                        "construct_options": {
                            "Company": "Company",
                            "firstName": "firstName",
                            "lastName": "lastName", 
                            "jobTitle": "jobTitle",
                            "linkedinUrl": "linkedinUrl",
                            "companyWebsite": "companyWebsite",
                            "emailId": "emailId"
                        }
                    }
                }
            }
        },

        # --- 4. Step 1: Company Qualification Assessment ---
        "step1_qualification_assessment": {
            "node_id": "step1_qualification_assessment",
            "node_name": "llm",
            "private_input_mode": True,
            # "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step1_passthrough_keys,
            "private_output_to_central_state_node_output_key": "qualification_result",
            "write_to_private_output_passthrough_data_from_output_mappings": {
                "web_search_result": "qualification_result_citations"
            },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_RESEARCH, "model": LLM_MODEL_RESEARCH},
                    "temperature": LLM_TEMPERATURE_RESEARCH,
                    "max_tokens": LLM_MAX_TOKENS_RESEARCH
                },
                "output_schema": {
                    "dynamic_schema_spec": STEP_1_QUALIFICATION_OUTPUT_SCHEMA
                }
            }
        },

        # --- 5. Filter Node - Keep only qualified leads ---
        "filter_qualified_leads": {
            "node_id": "filter_qualified_leads", 
            "node_name": "filter_data",
            "enable_node_fan_in": True,
            "node_config": {
                "targets": [
                    {
                        "filter_target": "qualification_results",
                        "filter_mode": "allow",
                        "condition_groups": [
                            {
                                "conditions": [
                                    {
                                        "field": "qualification_results.qualification_result.qualification_check_passed",
                                        "operator": "equals",
                                        "value": True
                                    }
                                ],
                                "logical_operator": "and"
                            }
                        ],
                        "group_logical_operator": "and"
                    }
                ],
                "non_target_fields_mode": "allow"
            }
        },

        # --- 6. Map List Router Node - Route qualified leads to Step 2 ---
        "route_qualified_to_step2": {
            "node_id": "route_qualified_to_step2",
            "node_name": "map_list_router_node", 
            "node_config": {
                "choices": ["step2_contentq_prompt"],
                "map_targets": [
                    {
                        "source_path": "filtered_data.qualification_results",
                        "destinations": ["step2_contentq_prompt"],
                        "batch_size": 1
                    }
                ]
            }
        },

        # --- 7. Step 2: Prompt Constructor for ContentQ Scoring ---
        "step2_contentq_prompt": {
            "node_id": "step2_contentq_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,  # Don't write to central state, pass to next step
            "private_output_passthrough_data_to_central_state_keys": step2_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "contentq_system_prompt": {
                        "id": "contentq_system_prompt",
                        "template": STEP2_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "contentq_user_prompt": {
                        "id": "contentq_user_prompt",
                        "template": STEP_2_CONTENTQ_USER_PROMPT,
                        "variables": {
                            "company_name": None,
                            "first_name": None,
                            "last_name": None,
                            "title": None,
                            "website_url": None,
                            "company_research": None,
                            "research_citations": ""
                        },
                        "construct_options": {
                            "company_name": "Company",
                            "first_name": "firstName",
                            "last_name": "lastName",
                            "title": "jobTitle",
                            "website_url": "companyWebsite", 
                            "company_research": "qualification_result",
                            "research_citations": "qualification_result_citations"
                        }
                    }
                }
            }
        },

        # --- 8. Step 2: ContentQ Scoring + Content Gap Analysis ---
        "step2_contentq_scoring": {
            "node_id": "step2_contentq_scoring",
            "node_name": "llm",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,  # Don't write to central state, pass to next step
            "private_output_passthrough_data_to_central_state_keys": step2_passthrough_keys,
            "write_to_private_output_passthrough_data_from_output_mappings": {
                "text_content": "contentq_and_content_analysis",
                "web_search_result": "contentq_and_content_analysis_citations"
            },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_RESEARCH, "model": LLM_MODEL_RESEARCH},
                    "temperature": LLM_TEMPERATURE_RESEARCH,
                    "max_tokens": LLM_MAX_TOKENS_RESEARCH
                }
            }
        },

        # --- 9. Step 3: Prompt Constructor for Strategic Content Opportunity ---
        "step3_strategic_prompt": {
            "node_id": "step3_strategic_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "strategic_system_prompt": {
                        "id": "strategic_system_prompt",
                        "template": STEP3_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "strategic_user_prompt": {
                        "id": "strategic_user_prompt",
                        "template": STEP_3_STRATEGIC_USER_PROMPT,
                        "variables": {
                            "company_name": None,
                            "first_name": None,
                            "last_name": None,
                            "title": None,
                            "website_url": None,
                            "qualification_analysis": None,
                            "qualification_citations": "",
                            "contentq_analysis": None,
                            "contentq_citations": ""
                        },
                        "construct_options": {
                            "company_name": "Company",
                            "first_name": "firstName",
                            "last_name": "lastName",
                            "title": "jobTitle",
                            "website_url": "companyWebsite",
                            "qualification_analysis": "qualification_result",
                            "qualification_citations": "qualification_result_citations",
                            "contentq_analysis": "contentq_and_content_analysis",
                            "contentq_citations": "contentq_and_content_analysis_citations"
                        }
                    }
                }
            }
        },

        # --- 10. Step 3: Strategic Content Opportunity Identification ---
        "step3_strategic_opportunity": {
            "node_id": "step3_strategic_opportunity",
            "node_name": "llm",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "write_to_private_output_passthrough_data_from_output_mappings": {
                "text_content": "strategic_analysis",
                "web_search_result": "strategic_analysis_citations"
            },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_RESEARCH, "model": LLM_MODEL_RESEARCH},
                    "temperature": LLM_TEMPERATURE_RESEARCH,
                    "max_tokens": LLM_MAX_TOKENS_RESEARCH
                }
            }
        },

        # --- 11. Step 4: Prompt Constructor for Talking Points ---
        "step4_talking_points_prompt": {
            "node_id": "step4_talking_points_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "talking_points_system_prompt": {
                        "id": "talking_points_system_prompt",
                        "template": STEP4_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "talking_points_user_prompt": {
                        "id": "talking_points_user_prompt",
                        "template": STEP_4_TALKING_POINTS_USER_PROMPT,
                        "variables": {
                            "company_name": None,
                            "first_name": None,
                            "last_name": None,
                            "title": None,
                            "website_url": None,
                            "qualification_analysis": None,
                            "qualification_citations": "",
                            "contentq_analysis": None,
                            "contentq_citations": "",
                            "strategic_analysis": None,
                            "strategic_citations": ""
                        },
                        "construct_options": {
                            "company_name": "Company",
                            "first_name": "firstName",
                            "last_name": "lastName",
                            "title": "jobTitle",
                            "website_url": "companyWebsite",
                            "qualification_analysis": "qualification_result",
                            "qualification_citations": "qualification_result_citations",
                            "contentq_analysis": "contentq_and_content_analysis",
                            "contentq_citations": "contentq_and_content_analysis_citations",
                            "strategic_analysis": "strategic_analysis",
                            "strategic_citations": "strategic_analysis_citations"
                        }
                    }
                }
            }
        },

        # --- 12. Step 4: Personalized Talking Points + Pitch Generation ---
        "step4_talking_points": {
            "node_id": "step4_talking_points",
            "node_name": "llm",
            "private_input_mode": True,
            # "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "private_output_to_central_state_node_output_key": "talking_points_result",
            # "write_to_private_output_passthrough_data_from_output_mappings": {
            #     "structured_output": "final_talking_points"
            # },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_WRITER, "model": LLM_MODEL_WRITER},
                    "temperature": LLM_TEMPERATURE_WRITER,
                    "max_tokens": LLM_MAX_TOKENS_WRITER
                },
                "output_schema": STEP4_TALKING_POINTS_OUTPUT_SCHEMA
            }
        },

        # --- 13. Output Node with Fan-In ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "enable_node_fan_in": True,
            "node_config": {}
        }
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # Input to state and router
        {"src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "leads_to_process", "dst_field": "original_leads"}
        ]},
        
        # Input to Step 1 router
        {"src_node_id": "input_node", "dst_node_id": "route_leads_to_qualification", "mappings": [
            {"src_field": "leads_to_process", "dst_field": "leads_to_process"}
        ]},
        
        # Step 1 router to qualification prompt constructor (private mode)
        {"src_node_id": "route_leads_to_qualification", "dst_node_id": "step1_qualification_prompt", "mappings": []},
        
        # Step 1 prompt constructor to qualification LLM
        {"src_node_id": "step1_qualification_prompt", "dst_node_id": "step1_qualification_assessment", "mappings": [
            {"src_field": "qualification_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "qualification_user_prompt", "dst_field": "user_prompt"}
        ]},

        {"src_node_id": "step1_qualification_assessment", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "qualification_results"},
        ]},

        {"src_node_id": "step1_qualification_assessment", "dst_node_id": "filter_qualified_leads", "mappings": []},
        
        # State to filter (collect all qualification results)
        {"src_node_id": "$graph_state", "dst_node_id": "filter_qualified_leads", "mappings": [
            {"src_field": "qualification_results", "dst_field": "qualification_results"}
        ]},
        
        # Filter to Step 2 router
        {"src_node_id": "filter_qualified_leads", "dst_node_id": "route_qualified_to_step2", "mappings": [
            {"src_field": "filtered_data", "dst_field": "filtered_data"}
        ]},
        
        # Step 2 router to ContentQ prompt constructor (private mode)
        {"src_node_id": "route_qualified_to_step2", "dst_node_id": "step2_contentq_prompt", "mappings": []},
        
        # Step 2 prompt constructor to ContentQ scoring LLM
        {"src_node_id": "step2_contentq_prompt", "dst_node_id": "step2_contentq_scoring", "mappings": [
            {"src_field": "contentq_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "contentq_user_prompt", "dst_field": "user_prompt"}
        ]},
        
        # Step 2 to Step 3 prompt constructor (private mode with passthrough data)
        {"src_node_id": "step2_contentq_scoring", "dst_node_id": "step3_strategic_prompt", "mappings": []},
        
        # Step 3 prompt constructor to strategic opportunity LLM
        {"src_node_id": "step3_strategic_prompt", "dst_node_id": "step3_strategic_opportunity", "mappings": [
            {"src_field": "strategic_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "strategic_user_prompt", "dst_field": "user_prompt"}
        ]},
        
        # Step 3 to Step 4 prompt constructor (private mode with passthrough data)
        {"src_node_id": "step3_strategic_opportunity", "dst_node_id": "step4_talking_points_prompt", "mappings": []},
        
        # Step 4 prompt constructor to talking points LLM
        {"src_node_id": "step4_talking_points_prompt", "dst_node_id": "step4_talking_points", "mappings": [
            {"src_field": "talking_points_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "talking_points_user_prompt", "dst_field": "user_prompt"}
        ]},
        
        # Step 4 to output (with fan-in)
        {"src_node_id": "step4_talking_points", "dst_node_id": "output_node", "mappings": []},

        {"src_node_id": "step4_talking_points", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "final_results"},
        ]},
        
        # State to output for final collection
        {"src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
            {"src_field": "final_results", "dst_field": "processed_leads"},
            # {"src_field": "original_leads", "dst_field": "original_leads"}
        ]}
    ],

    # Define start and end
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    "runtime_config": {
        "db_concurrent_pool_tier": "large"
    },

    # State reducers - collect all results
    "metadata": {
        "$graph_state": {
            "reducer": {
                "qualification_results": "collect_values",
                "final_results": "collect_values"
            }
        }
    }
}
