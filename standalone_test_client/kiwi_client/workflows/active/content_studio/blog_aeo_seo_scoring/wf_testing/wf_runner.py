"""
Main runner for B2B Blog Content Scoring Workflow testing.

This module handles the execution of the B2B Blog SEO/AEO scoring workflow 
with proper setup, execution, validation, and cleanup.
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
import json
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflow testing utilities
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_blog_aeo_seo_scoring_json import (
    workflow_graph_schema,
)

from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_testing.wf_inputs import (
    test_name,
    test_scenario,
)

from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_testing.sandbox_setup_docs import (
    setup_docs,
    cleanup_docs,
)

from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_testing.wf_validation import (
    validate_seo_analysis_output,
    # display_scoring_results,
)

from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_testing.wf_state_filter_mapping import (
    state_filter_mapping,
)

WORKFLOW_NAME_TO_INGEST_AS_FOR_TESTING = "test_blog_aeo_seo_scoring_workflow"

# --- Path Configuration ---
def get_workflow_paths():
    """
    Determine default paths relative to the workflow folder.
    
    Assumes the user runs the workflow from wf_runner.py folder and navigates
    to find the parent workflow folder accordingly.
    
    Returns:
        tuple: (hitl_inputs_file_path, runs_folder_path, state_filter_mapping_file_path)
    """
    # Current file is in: workflow_folder/wf_testing/wf_runner.py
    current_file_dir = Path(__file__).parent  # wf_testing folder
    workflow_folder = current_file_dir.parent  # workflow main folder (blog_aeo_seo_scoring)
    
    # Default HITL inputs file path (not needed for this workflow but maintaining structure)
    hitl_inputs_file_path = current_file_dir / "wf_run_hitl_inputs.py"
    
    # Default runs folder path
    runs_folder_path = current_file_dir / "runs"
    
    # Default state filter mapping file path (not needed but maintaining structure)
    state_filter_mapping_file_path = current_file_dir / "wf_state_filter_mapping.py"
    
    return hitl_inputs_file_path, runs_folder_path, state_filter_mapping_file_path


async def run_b2b_blog_scoring_test():
    """
    Execute the B2B Blog Content Scoring workflow test.
    
    This function handles:
    - Test setup with document creation
    - Workflow execution 
    - Output validation
    - Results display
    - Cleanup
    """
    print(f"\n--- Starting {test_name} ---")
    print(f"\n--- Running Scenario: {test_scenario['name']} ---")

    default_hitl_inputs_path, default_runs_folder_path, default_state_filter_mapping_path = get_workflow_paths()
    
    try:
        final_status, final_outputs = await run_workflow_test(
            test_name=f"{test_name} - {test_scenario['name']}",
            workflow_graph_schema=workflow_graph_schema,
            workflow_name_to_ingest_as_for_testing=WORKFLOW_NAME_TO_INGEST_AS_FOR_TESTING,
            initial_inputs=test_scenario['initial_inputs'],
            expected_final_status=WorkflowRunStatus.COMPLETED,
            hitl_inputs=[],  # No HITL inputs needed for this workflow
            runs_folder_path=default_runs_folder_path,
            state_filter_mapping=state_filter_mapping,
            setup_docs=setup_docs,
            cleanup_docs=cleanup_docs,
            cleanup_docs_created_by_setup=True,
            validate_output_func=validate_seo_analysis_output,
            stream_intermediate_results=True,
            poll_interval_sec=2,
            timeout_sec=300  # 5 minutes should be sufficient for B2B content scoring
        )
        
        # # Display results
        # if final_outputs:
        #     display_scoring_results(final_outputs)
        # else:
        #     logger.warning("No final outputs received from workflow execution.")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    
    print(f"\n--- {test_name} Completed Successfully ---")


async def main():
    """
    Main execution function.
    """
    print("="*60)
    print("B2B Blog Content Scoring Workflow Test")
    print("="*60)
    
    try:
        await run_b2b_blog_scoring_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=$(pwd):$(pwd)/services poetry run python standalone_test_client/kiwi_client/workflows/active/content_studio/blog_aeo_seo_scoring/wf_testing/wf_runner.py")


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
