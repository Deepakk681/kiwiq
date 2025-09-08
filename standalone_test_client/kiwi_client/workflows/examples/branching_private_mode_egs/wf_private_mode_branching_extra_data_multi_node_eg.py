"""
Private Mode Branching with Extra Data Example Workflow

This workflow demonstrates:
1. Taking a list of items with ID, name, and user_prompt fields as input
2. Using map_list_router_node to route each item to parallel prompt construction branches
3. Prompt constructor nodes building structured prompts with ID, name, and user_prompt in private mode
4. LLM nodes processing the constructed prompts in private mode with passthrough data configuration
5. Using private_output_passthrough_data_to_central_state_key to preserve ID and name fields through the pipeline
6. Collecting all outputs in graph state with format: {output: text_content, id: original_id, name: description}
7. Validating that all items were processed correctly with passthrough data intact

Input: List of items (each with 'id', 'name', and 'user_prompt' fields)
Output: Processed results with LLM text content and original metadata preserved
"""

import json
import asyncio
from typing import List, Optional, Dict, Any, Literal
import logging

# --- Workflow Constants ---
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"  # Using a lighter model for the example
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1000

# --- Custom System Prompt ---
SYSTEM_PROMPT = """You are a helpful AI assistant that processes user prompts and provides comprehensive responses.

For each prompt you receive, you should:
1. Understand the user's question or request
2. Provide a detailed, helpful response
3. Analyze the response to provide metadata including word count, sentiment, and category

Please be thorough and informative in your responses."""

# Note: No structured schema needed - LLM will output text_content directly

private_output_passthrough_data_to_central_state_keys = ["id", "name", "description"]

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
                    "items_to_process": {
                        "type": "list",
                        "required": False,
                        "default": [
                            {
                                "id": "item_1",
                                "name": "Renewable Energy Benefits",
                                "user_prompt": "What are the benefits of renewable energy sources?"
                            },
                            {
                                "id": "item_2",
                                "name": "Machine Learning Basics", 
                                "user_prompt": "Explain the concept of machine learning in simple terms."
                            },
                            {
                                "id": "item_3",
                                "name": "Time Management Tips",
                                "user_prompt": "How can I improve my time management skills?"
                            },
                            {
                                "id": "item_4",
                                "name": "Sustainable Development Principles",
                                "user_prompt": "What are the key principles of sustainable development?"
                            }
                        ],
                        "description": "List of items to process, each with 'id', 'name', and 'user_prompt' fields"
                    },
                }
            }
        },

        # --- 2. Map List Router Node - Routes each item to parallel prompt construction ---
        "route_items_to_llm": {
            "node_id": "route_items_to_llm",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["construct_item_prompt"],
                "map_targets": [
                    {
                        "source_path": "items_to_process",
                        "destinations": ["construct_item_prompt"],
                        "batch_size": 1,
                        # Note: Each item goes to a separate branch for prompt construction
                    }
                ]
            }
        },

        # --- 3. Prompt Constructor - Builds prompts for each item in private mode ---
        "construct_item_prompt": {
            "node_id": "construct_item_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_mode": True,
            "private_output_passthrough_data_to_central_state_keys": private_output_passthrough_data_to_central_state_keys,  # Pass through ID and name
            "node_config": {
                "prompt_templates": {
                    "item_user_prompt": {
                        "id": "item_user_prompt",
                        "template": """Item Information:
- ID: {item_id}
- Name: {item_name}
- User Prompt: {user_prompt}

Please provide a comprehensive and helpful response to the user prompt above. Your response should be detailed, informative, and directly address the question or request.""",
                        "variables": {
                            "item_id": None,
                            "item_name": None,
                            "user_prompt": None
                        },
                        "construct_options": {
                            "item_id": "id",
                            "item_name": "name",
                            "user_prompt": "user_prompt"
                        }
                    },
                    "item_system_prompt": {
                        "id": "item_system_prompt",
                        "template": SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    }
                }
            }
        },

        # --- 4. LLM Node - Processes individual items in private mode ---
        "process_individual_item": {
            "node_id": "process_individual_item",
            "node_name": "llm",
            "private_input_mode": True,  # Enable private mode for branching
            "output_private_output_to_central_state": True,  # Send output to central state
            "private_output_passthrough_data_to_central_state_keys": private_output_passthrough_data_to_central_state_keys,  # Pass through ID and name
            "private_output_to_central_state_node_output_key": "output",  # Use 'output' as the key for LLM response
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER, "model": LLM_MODEL},
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS
                }
                # Note: No structured output schema - will use text_content field
                # System and user prompts will come from the prompt constructor
            }
        },

        # --- 5. Output Node with Fan-In ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "enable_node_fan_in": True,  # Enable fan-in to collect all parallel results
            "node_config": {}
        }
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # Input to state and router
        {"src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "items_to_process", "dst_field": "items_to_process"},
        ]},
        
        # Input to router
        {"src_node_id": "input_node", "dst_node_id": "route_items_to_llm", "mappings": [
            {"src_field": "items_to_process", "dst_field": "items_to_process"}
        ]},
        
        # Router to prompt constructor (private mode) - each item goes to prompt construction
        {"src_node_id": "route_items_to_llm", "dst_node_id": "construct_item_prompt", "mappings": []},
        
        # Prompt constructor to LLM
        {"src_node_id": "construct_item_prompt", "dst_node_id": "process_individual_item", "mappings": [
            {"src_field": "item_user_prompt", "dst_field": "user_prompt"},
            {"src_field": "item_system_prompt", "dst_field": "system_prompt"}
        ]},
        
        # LLM to graph state (collect all results with passthrough data)
        {"src_node_id": "process_individual_item", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "text_content", "dst_field": "all_processed_items"}
        ]},
        
        # LLM to output (with fan-in)
        {"src_node_id": "process_individual_item", "dst_node_id": "output_node", "mappings": [
        ]},
        
        # State to output for final collection
        {"src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
            {"src_field": "all_processed_items", "dst_field": "all_results"},
            {"src_field": "items_to_process", "dst_field": "original_items"}
        ]}
    ],

    # Define start and end
    "input_node_id": "input_node",
    "output_node_id": "output_node",

    # State reducers - collect all LLM outputs
    "metadata": {
        "$graph_state": {
            "reducer": {
                "all_processed_items": "collect_values"
            }
        }
    }
}

# --- Test Execution Logic ---
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

logger = logging.getLogger(__name__)

# Example Test Inputs
TEST_INPUTS = {
    "items_to_process": [
        {
            "id": "test_item_1",
            "name": "Python for Data Science",
            "user_prompt": "What are the main advantages of using Python for data science?"
        },
        {
            "id": "test_item_2",
            "name": "Blockchain Technology Explanation", 
            "user_prompt": "How does blockchain technology work?"
        },
        {
            "id": "test_item_3",
            "name": "Remote Team Collaboration Strategies",
            "user_prompt": "What are some effective strategies for remote team collaboration?"
        }
    ],
}

async def validate_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Custom validation function for the workflow outputs.
    
    Validates that:
    1. All input items were processed
    2. Each item has a corresponding LLM output with passthrough data
    3. The output structure is correct: {output: text_content, id: original_id, name: description}
    4. All required fields are present
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating private mode branching workflow outputs...")
    
    # Check if we have the expected output fields
    assert 'all_results' in outputs, "Validation Failed: 'all_results' key missing."
    assert 'original_items' in outputs, "Validation Failed: 'original_items' key missing."
    
    original_items = outputs.get('original_items', [])
    processed_results = outputs.get('all_results', [])
    
    logger.info(f"Original items count: {len(original_items)}")
    logger.info(f"Processed results count: {len(processed_results)}")
    
    # Validate that all items were processed
    assert len(processed_results) == len(original_items), \
        f"Validation Failed: Expected {len(original_items)} processed results, got {len(processed_results)}"
    
    # Create sets of IDs for comparison
    original_ids = {item.get('id') for item in original_items}
    processed_ids = {result.get('id') for result in processed_results}
    
    logger.info(f"Original IDs: {sorted(original_ids)}")
    logger.info(f"Processed IDs: {sorted(processed_ids)}")
    
    # Check that all original IDs have corresponding processed results
    missing_ids = original_ids - processed_ids
    assert not missing_ids, f"Validation Failed: Missing processed results for IDs: {missing_ids}"
    
    # Validate the structure of each processed result
    # Expected format: {output: text_content, id: original_id, name: description}
    required_fields = ['output', 'id', 'name']
    for i, result in enumerate(processed_results):
        logger.info(f"Validating result {i+1}: ID={result.get('id')}")
        
        # Check required fields
        for field in required_fields:
            assert field in result, f"Validation Failed: Missing field '{field}' in result {i+1}"
        
        # Validate data types
        assert isinstance(result['id'], str), f"Validation Failed: id should be string in result {i+1}"
        assert isinstance(result['name'], str), f"Validation Failed: name should be string in result {i+1}"
        assert isinstance(result['output'], str), f"Validation Failed: output should be string in result {i+1}"
        assert len(result['output']) > 0, f"Validation Failed: output should not be empty in result {i+1}"
        
        logger.info(f"  ✓ Item ID: {result['id']}")
        logger.info(f"  ✓ Item Name: {result['name']}")
        logger.info(f"  ✓ Output length: {len(result['output'])} chars")
        logger.info(f"  ✓ Output preview: {result['output'][:100]}...")
    
    logger.info("✓ All validation checks passed successfully!")
    return True

async def main_test_private_mode_branching():
    """Main test function for the private mode branching workflow."""
    test_name = "Private Mode Branching with Extra Data Example"
    print(f"--- Starting {test_name} ---")
    
    print("\n--- Running Workflow Test ---")
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=TEST_INPUTS,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=None,
        cleanup_docs=None,
        validate_output_func=validate_output,
        stream_intermediate_results=True,
        poll_interval_sec=3,
        timeout_sec=300  # 5 minutes should be enough for this simple workflow
    )
    
    print(f"\n--- Test completed with status: {final_run_status_obj} ---")
    return final_run_status_obj, final_run_outputs

if __name__ == "__main__":
    print("="*60)
    print("Private Mode Branching with Extra Data Example Workflow")
    print("="*60)
    logging.basicConfig(level=logging.INFO)
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("Async event loop already running. Scheduling task...")
        loop.create_task(main_test_private_mode_branching())
    else:
        print("Starting new async event loop...")
        asyncio.run(main_test_private_mode_branching())
