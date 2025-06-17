from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import asyncio
import logging
import json
from enum import Enum

# Import test workflow utilities
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

# Import document model constants
from kiwi_client.workflows.document_models.customer_docs import (
    USER_PREFERENCES_DOCNAME,
    USER_PREFERENCES_NAMESPACE_TEMPLATE,
    USER_PREFERENCES_IS_VERSIONED,
    CONTENT_STRATEGY_DOCNAME,
    CONTENT_STRATEGY_NAMESPACE_TEMPLATE,
    CONTENT_STRATEGY_IS_VERSIONED
)

# Import prompts and schema from update_customer_documents.py
from kiwi_client.workflows.llm_inputs.update_customer_documents import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    DOCUMENT_UPDATE_SCHEMA,
    DOCUMENT_UPDATE_USER_PROMPT,
    DOCUMENT_UPDATE_SYSTEM_PROMPT
)

# Import schema variables from workflow_schemas.py
from kiwi_client.workflows.llm_inputs.workflow_schemas import (
    USER_PREFERENCES_DOC,
    CONTENT_STRATEGY_DOC
)

# LLM Configuration
llm_provider = "anthropic"
generation_model_name = "claude-3-7-sonnet-20250219"
temperature = 0.5
max_tokens = 2000

# Workflow Graph Schema
workflow_graph_schema = {
    "nodes": {
        # Input Node
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "entity_username": {
                        "type": "str",
                        "required": True,
                        "description": "Username of the entity for which documents are being updated"
                    },
                    "user_input": {
                        "type": "str",
                        "required": True,
                        "description": "User's input describing what needs to be updated"
                    },
                    "customer_context_doc_configs": {
                            "type": "list",
                            "required": True,
                            "description": "List of document identifiers (namespace/docname pairs) for customer context like DNA, strategy docs."
                    },
                }
            }
        },

        # Prompt Constructor for Initial Analysis
        "construct_analysis_prompt": {
            "node_id": "construct_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "user_prompt": {
                        "id": "user_prompt",
                        "template": USER_PROMPT,
                        "variables": {
                            "user_input": None,
                            "user_preferences_schema": USER_PREFERENCES_DOC,
                            "content_strategy_schema": CONTENT_STRATEGY_DOC
                        },
                        "construct_options": {
                            "user_input": "user_input"
                        }
                    },
                    "system_prompt": {
                        "id": "system_prompt",
                        "template": SYSTEM_PROMPT,
                        "variables": {"schema": json.dumps(DOCUMENT_UPDATE_SCHEMA, indent=2)}
                    }
                }
            }
        },

        # Initial Document Analysis Node
        "analyze_document_updates": {
            "node_id": "analyze_document_updates",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": llm_provider,
                        "model": generation_model_name
                    },
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                "output_schema": {
                    "schema_definition": DOCUMENT_UPDATE_SCHEMA
                }
            }
        },

        # Filter Documents Node
        "filter_documents": {
            "node_id": "filter_documents",
            "node_name": "filter_data",
            "enable_node_fan_in": True,  # Added fan-in to ensure all inputs are available
            "node_config": {
                "non_target_fields_mode": "deny",
                "targets": [
                    {
                        "filter_target": "input_configs",
                        "condition_groups": [
                            {
                                "conditions": [
                                    {
                                        "field": "input_configs.filename_config.static_docname",
                                        "operator": "equals_any_of",
                                        "value_path": "document_update_analysis.documents.document_name"
                                    }
                                ]
                            }
                        ],
                        "filter_mode": "allow"
                    }
                ]
            }
            
        },

        # Load Customer Documents Node
        "load_customer_docs": {
            "node_id": "load_customer_docs",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "load_configs.input_configs",
                "global_is_shared": False,
                "global_is_system_entity": False,
                "global_schema_options": {"load_schema": False}
            }
        },

        # Map and Route Documents for Updates
        "map_and_route_documents": {
            "node_id": "map_and_route_documents",
            "node_name": "map_list_router_node",
            "enable_node_fan_in": True,  # Added fan-in to ensure all inputs are available
            "node_config": {
                "choices": ["construct_document_update_prompt"],
                "map_targets": [
                    {
                        "source_path": "loaded_documents",
                        "destinations": ["construct_document_update_prompt"],
                        "batch_size": 1,
                        "batch_field_name": "document_to_update"
                    }
                ]
            }
        },

        # Construct Document Update Prompt
        "construct_document_update_prompt": {
            "node_id": "construct_document_update_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "node_config": {
                "prompt_templates": {
                    "update_user_prompt": {
                        "id": "update_user_prompt",
                        "template": DOCUMENT_UPDATE_USER_PROMPT,
                        "variables": {
                            "document": None,
                            "update_analysis": None,
                        },
                        "construct_options": {
                            "document": "document_to_update",
                            "update_analysis": "document_update_analysis"                        }
                    },
                    "update_system_prompt": {
                        "id": "update_system_prompt",
                        "template": DOCUMENT_UPDATE_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    }
                }
            }
        },

        # Update Document Content
        "update_document_content": {
            "node_id": "update_document_content",
            "node_name": "llm",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": llm_provider,
                        "model": generation_model_name
                    },
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
            "output_schema": {
                "schema_definition": {}
            }
            }
        },

        # Save Updated Documents
        "save_updated_documents": {
            "node_id": "save_updated_documents",
            "node_name": "store_customer_data",
            "private_input_mode": True,
            "enable_node_fan_in": True,  # Added fan-in to ensure all inputs are available
            "node_config": {
                "global_versioning": { "is_versioned": True, "operation": "upsert_versioned" },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "updated_content",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": "{document_namespace}",
                                "input_namespace_field": "entity_username",
                                "static_docname": "{document_name}"
                            }
                        }
                    }
                ]
            }
        },

        # Output Node
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {},
            "dynamic_input_schema": {
                "fields": {
                    "updated_document_paths": {
                        "type": "list",
                        "required": True,
                        "description": "Paths of the updated documents"
                    },
                    "processed_entity_username": {
                        "type": "str",
                        "required": True,
                        "description": "Username of the processed entity"
                    },
                    "updated_documents": {
                        "type": "list",
                        "required": True,
                        "description": "List of updated documents with their content"
                    }
                }
            }
        }
    },

    # Edges defining data flow
    "edges": [
        # Input Node -> State: Store initial inputs
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {
                    "src_field": "entity_username",
                    "dst_field": "entity_username",
                    "description": "Store the entity username for later use"
                },
                {
                    "src_field": "user_input",
                    "dst_field": "user_input",
                    "description": "Store the user's input for analysis"
                },
                {
                    "src_field": "customer_context_doc_configs",
                    "dst_field": "customer_context_doc_configs",
                    "description": "Store the document configurations"
                }
            ]
        },

        # Input Node -> Prompt Constructor: Direct mapping of user input
        {
            "src_node_id": "input_node",
            "dst_node_id": "construct_analysis_prompt",
            "mappings": [
                {
                    "src_field": "user_input",
                    "dst_field": "user_input",
                    "description": "Pass user input directly to prompt construction"
                }
            ]
        },

        # Prompt Constructor -> Document Analysis: Provide constructed prompts
        {
            "src_node_id": "construct_analysis_prompt",
            "dst_node_id": "analyze_document_updates",
            "mappings": [
                {
                    "src_field": "user_prompt",
                    "dst_field": "user_prompt",
                    "description": "Pass constructed user prompt"
                },
                {
                    "src_field": "system_prompt",
                    "dst_field": "system_prompt",
                    "description": "Pass constructed system prompt"
                }
            ]
        },

        # Document Analysis -> State: Store analysis results
        {
            "src_node_id": "analyze_document_updates",
            "dst_node_id": "$graph_state",
            "mappings": [
                {
                    "src_field": "structured_output",
                    "dst_field": "document_update_analysis",
                    "description": "Store the analysis of which documents need updates"
                }
            ]
        },

        { "src_node_id": "analyze_document_updates", "dst_node_id": "filter_documents"},
        
        # State -> Filter Documents
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "filter_documents",
            "mappings": [
                {
                    "src_field": "customer_context_doc_configs",
                    "dst_field": "input_configs",
                    "description": "Pass document configurations for filtering"
                },
                {
                    "src_field": "document_update_analysis",
                    "dst_field": "document_update_analysis",
                    "description": "Pass document update analysis for filtering"
                }
            ]
        },

        # Filter Documents -> Load Customer Docs
        {
            "src_node_id": "filter_documents",
            "dst_node_id": "load_customer_docs",
            "mappings": [
                {
                    "src_field": "filtered_data",
                    "dst_field": "load_configs",
                    "description": "Pass filtered document configurations"
                }
            ]
        },

        {
            "src_node_id": "filter_documents",
            "dst_node_id": "$graph_state",
            "mappings": [
                {
                    "src_field": "filtered_data",
                    "dst_field": "load_configs",
                    "description": "Pass filtered document configurations"
                }
            ]
        },

        # State -> Load Customer Docs
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "load_customer_docs",
            "mappings": [
                {
                    "src_field": "entity_username",
                    "dst_field": "entity_username",
                    "description": "Pass entity username for document loading"
                }
            ]
        },

        # Load Customer Docs -> Map and Route
        {
            "src_node_id": "load_customer_docs",
            "dst_node_id": "map_and_route_documents",
            "mappings": [
                {
                    "src_field": "loaded_documents",
                    "dst_field": "loaded_documents",
                    "description": "Pass loaded documents for processing"
                }
            ]
        },

        # State -> Map and Route
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "map_and_route_documents",
            "mappings": [
                {
                    "src_field": "document_update_analysis",
                    "dst_field": "document_update_analysis",
                    "description": "Pass document update analysis"
                }
            ]
        },

        # Map and Route -> Construct Update Prompt
        {
            "src_node_id": "map_and_route_documents",
            "dst_node_id": "construct_document_update_prompt",
            "mappings": []
        },

        # State -> Construct Update Prompt
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "construct_document_update_prompt",
            "mappings": [
                {
                    "src_field": "document_update_analysis",
                    "dst_field": "document_update_analysis",
                    "description": "Pass update analysis for prompt construction"
                }
            ]
        },

        # Construct Update Prompt -> Update Document Content
        {
            "src_node_id": "construct_document_update_prompt",
            "dst_node_id": "update_document_content",
            "mappings": [
                {
                    "src_field": "update_user_prompt",
                    "dst_field": "user_prompt",
                    "description": "Pass constructed update prompt"
                },
                {
                    "src_field": "update_system_prompt",
                    "dst_field": "system_prompt",
                    "description": "Pass system prompt"
                }
            ]
        },

        # Update Document Content -> State
        {
            "src_node_id": "update_document_content",
            "dst_node_id": "$graph_state",
            "mappings": [
                {
                    "src_field": "structured_output",
                    "dst_field": "updated_documents",
                    "description": "Store updated documents"
                }
            ]
        },

        # Update Document Content -> Save Updated Documents
        {
            "src_node_id": "update_document_content",
            "dst_node_id": "save_updated_documents",
            "mappings": [
                {
                    "src_field": "structured_output",
                    "dst_field": "updated_content",
                    "description": "Pass updated content for saving"
                }
            ]
        },

        # State -> Save Updated Documents
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_updated_documents",
            "mappings": [
                {
                    "src_field": "entity_username",
                    "dst_field": "entity_username",
                    "description": "Pass entity username for saving"
                }
            ]
        },

        # Save Updated Documents -> Output
        {
            "src_node_id": "save_updated_documents",
            "dst_node_id": "output_node",
            "mappings": [
                {
                    "src_field": "paths_processed",
                    "dst_field": "updated_document_paths",
                    "description": "Pass paths of updated documents"
                }
            ]
        },

        # State -> Output
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "output_node",
            "mappings": [
                {
                    "src_field": "entity_username",
                    "dst_field": "processed_entity_username",
                    "description": "Pass processed entity username"
                },
                {
                    "src_field": "updated_documents",
                    "dst_field": "updated_documents",
                    "description": "Pass updated documents"
                }
            ]
        }
    ],

    # Define Start and End
    "input_node_id": "input_node",
    "output_node_id": "output_node",

    # State Reducers
    "metadata": {
        "$graph_state": {
            "reducer": {
                "document_update_analysis": "replace",  # Analysis should be replaced with latest
                "updated_documents": "append_list",     # Documents should be accumulated
                "entity_username": "replace",           # Username should be replaced
                "customer_context_doc_configs": "replace",             # Configs should be replaced
                "user_input": "replace"               # User input should be replaced
            }
        }
    }
}

# --- Test Execution Logic ---
async def main_test_workflow():
    """
    Test for Document Update Workflow.
    
    This function sets up test data, executes the workflow, and validates the output.
    The workflow analyzes user input to determine which documents and fields need to be updated.
    """
    test_name = "Document Update Workflow Test"
    print(f"--- Starting {test_name} --- ")

    # Test entity and document names
    test_entity_username = "test_entity"
    
    # Example Inputs
    test_inputs = {
        "entity_username": test_entity_username,
        "user_input": "I want to update my content strategy to focus more on video content and increase my posting frequency to 3 times per week.",
        "customer_context_doc_configs": [
            {
                "filename_config": {
                    "input_namespace_field_pattern": USER_PREFERENCES_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": USER_PREFERENCES_DOCNAME
                },
                "output_field_name": "loaded_documents"
            },
            {
                "filename_config": {
                    "input_namespace_field_pattern": CONTENT_STRATEGY_NAMESPACE_TEMPLATE,
                    "input_namespace_field": "entity_username",
                    "static_docname": CONTENT_STRATEGY_DOCNAME
                },
                "output_field_name": "loaded_documents"
            }
        ]
    }

    # Define setup documents
    setup_docs = [
        # User Preferences Document
        {
            'namespace': USER_PREFERENCES_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': USER_PREFERENCES_DOCNAME,
            'initial_data': {
                "audience": {
                    "segments": [
                        {
                            "name": "Marketing Professionals",
                            "description": "Marketing professionals and leaders in the industry",
                            "industry": "Marketing",
                            "experience_level": "Mid to Senior",
                            "position": "Marketing Manager and above",
                            "company_size": "Medium to Large",
                            "knowledge_level": "Advanced"
                        }
                    ]
                },
                "posting_schedule": {
                    "posts_per_week": 2,
                    "posting_days": ["MON", "WED"],
                    "exclude_weekends": True
                },
                "automation_level": {
                    "time_commitment_minutes": "30"
                }
            }, 
            'is_versioned': USER_PREFERENCES_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'default'
        },
        # Content Strategy Document
        {
            'namespace': CONTENT_STRATEGY_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': CONTENT_STRATEGY_DOCNAME,
            'initial_data': {
                "title": "Digital Marketing Leadership Strategy",
                "foundation_elements": {
                    "expertise": ["Digital Marketing", "Leadership", "Innovation"],
                    "core_beliefs": [
                        "Data-driven decision making",
                        "Continuous learning and adaptation",
                        "Customer-centric approach"
                    ],
                    "objectives": [
                        "Establish thought leadership",
                        "Drive engagement",
                        "Build professional network"
                    ]
                },
                "core_perspectives": [
                    "Digital transformation in marketing",
                    "Leadership in the digital age",
                    "Innovation in marketing strategies"
                ],
                "content_pillars": [
                    {
                        "name": "Digital Marketing",
                        "pillar": "Digital Marketing Excellence",
                        "sub_topic": ["Social Media", "Content Marketing", "Digital Analytics"]
                    },
                    {
                        "name": "Leadership",
                        "pillar": "Leadership Insights",
                        "sub_topic": ["Team Management", "Strategic Planning", "Change Management"]
                    },
                    {
                        "name": "Innovation",
                        "pillar": "Marketing Innovation",
                        "sub_topic": ["Emerging Technologies", "Trend Analysis", "Future of Marketing"]
                    }
                ],
                "implementation": {
                    "thirty_day_targets": {
                        "goal": "Establish consistent posting schedule",
                        "method": "Regular content creation and engagement",
                        "targets": "8 posts, 100 likes per post, 20 comments per post"
                    },
                    "ninety_day_targets": {
                        "goal": "Build engaged audience",
                        "method": "Quality content and active engagement",
                        "targets": "24 posts, 150 likes per post, 30 comments per post"
                    }
                }
            }, 
            'is_versioned': CONTENT_STRATEGY_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'default'
        }
    ]

    # Define cleanup docs
    cleanup_docs = [
        {
            'namespace': USER_PREFERENCES_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': USER_PREFERENCES_DOCNAME, 
            'is_versioned': USER_PREFERENCES_IS_VERSIONED, 
            'is_shared': False
        },
        {
            'namespace': CONTENT_STRATEGY_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': CONTENT_STRATEGY_DOCNAME, 
            'is_versioned': CONTENT_STRATEGY_IS_VERSIONED, 
            'is_shared': False
        }
    ]

    # Output validation function
    async def validate_update_output(outputs):
        """Validates the workflow output to ensure it meets expected structure and content requirements."""
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        
        # Check required output fields
        assert 'updated_document_paths' in outputs, "Validation Failed: 'updated_document_paths' missing."
        assert 'processed_entity_username' in outputs, "Validation Failed: 'processed_entity_username' missing."
        assert 'updated_documents' in outputs, "Validation Failed: 'updated_documents' missing."
        
        # Validate entity username
        assert outputs['processed_entity_username'] == test_entity_username, "Validation Failed: Entity username mismatch."
        
        # Validate document paths
        assert isinstance(outputs['updated_document_paths'], list), "Validation Failed: updated_document_paths should be a list."
        assert len(outputs['updated_document_paths']) > 0, "Validation Failed: No documents were updated."
        
        # Validate updated documents
        assert isinstance(outputs['updated_documents'], list), "Validation Failed: updated_documents should be a list."
        assert len(outputs['updated_documents']) > 0, "Validation Failed: No documents were updated."
        
        # Validate each updated document
        for doc in outputs['updated_documents']:
            assert 'document_name' in doc, "Validation Failed: document_name missing in updated document."
            assert doc['document_name'] in [USER_PREFERENCES_DOCNAME, CONTENT_STRATEGY_DOCNAME], \
                f"Invalid document name: {doc['document_name']}"
            
            # Validate document content structure
            if doc['document_name'] == USER_PREFERENCES_DOCNAME:
                assert 'audience' in doc, "Validation Failed: audience missing in user preferences."
                assert 'posting_schedule' in doc, "Validation Failed: posting_schedule missing in user preferences."
                assert 'automation_level' in doc, "Validation Failed: automation_level missing in user preferences."
            elif doc['document_name'] == CONTENT_STRATEGY_DOCNAME:
                assert 'title' in doc, "Validation Failed: title missing in content strategy."
                assert 'foundation_elements' in doc, "Validation Failed: foundation_elements missing in content strategy."
                assert 'content_pillars' in doc, "Validation Failed: content_pillars missing in content strategy."
                assert 'implementation' in doc, "Validation Failed: implementation missing in content strategy."
        
        print("✓ Document update validation passed successfully")
        return True

    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=setup_docs,
        cleanup_docs=cleanup_docs,
        cleanup_docs_created_by_setup=False,
        validate_output_func=validate_update_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=300
    )

    print(f"--- {test_name} Finished --- ")
    if final_run_outputs:
        print(f"Updated Document Paths: {final_run_outputs.get('updated_document_paths')}")
        print(f"Processed Entity: {final_run_outputs.get('processed_entity_username')}")
        print(f"Number of Documents Updated: {len(final_run_outputs.get('updated_documents', []))}")

if __name__ == "__main__":
    try:
        asyncio.run(main_test_workflow())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")
