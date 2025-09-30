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

from kiwi_client.workflows.active.labs.on_demand_external_research.wf_on_demand_external_research import (
    workflow_graph_schema,
)

from kiwi_client.workflows.active.labs.on_demand_external_research.wf_testing.wf_inputs import (
    test_name,
    test_scenario,
    predefined_hitl_inputs,
)

from kiwi_client.workflows.active.labs.on_demand_external_research.wf_testing.sandbox_setup_docs import (
    setup_docs,
    cleanup_docs,
)

from kiwi_client.workflows.active.labs.on_demand_external_research.wf_testing.wf_validation import (
    validate_external_research_output,
    display_research_results,
)


WORKFLOW_NAME_TO_INGEST_AS_FOR_TESTING = "test_on_demand_external_research_workflow"


# --- Path Configuration ---
def get_workflow_paths():
    """
    Determine default paths relative to the workflow folder.
    
    Assumes the user runs the workflow from wf_runner.py folder and navigates
    to find the parent workflow folder accordingly.
    
    Returns:
        tuple: (runs_folder_path, state_filter_mapping_file_path)
    """
    # Current file is in: workflow_folder/wf_testing/wf_runner.py
    current_file_dir = Path(__file__).parent  # wf_testing folder
    workflow_folder = current_file_dir.parent  # workflow main folder
    
    # Default runs folder path
    runs_folder_path = current_file_dir / "runs"
    
    # Default state mapping file path
    state_filter_mapping_file_path = current_file_dir / "wf_state_filter_mapping.py"
    
    return str(runs_folder_path), str(state_filter_mapping_file_path)


def load_state_filter_mapping(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load state mapping from a Python file for filtering workflow state dumps.
    
    Args:
        file_path: Path to the Python file containing state_filter_mapping variable
        
    Returns:
        Dictionary mapping for state filtering, or None if file doesn't exist or has issues
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"State mapping file not found: {file_path}. Using unfiltered state dumps.")
            return None
            
        # Load the mapping file dynamically
        import importlib.util
        import sys
        
        spec = importlib.util.spec_from_file_location("wf_state_filter_mapping", file_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Could not load state mapping spec from {file_path}")
            return None
            
        mapping_module = importlib.util.module_from_spec(spec)
        sys.modules["wf_state_filter_mapping"] = mapping_module
        spec.loader.exec_module(mapping_module)
        
        # Extract the state_filter_mapping variable
        if hasattr(mapping_module, 'state_filter_mapping'):
            mapping = mapping_module.state_filter_mapping
            if mapping:
                logger.info(f"Loaded state mapping with {len(mapping)} sections from {file_path}")
                return mapping
            else:
                logger.info(f"Empty state mapping loaded from {file_path}. Using unfiltered state dumps.")
                return None
        else:
            logger.warning(f"No 'state_filter_mapping' variable found in {file_path}")
            return None
            
    except Exception as e:
        logger.warning(f"Error loading state mapping from {file_path}: {e}. Using unfiltered state dumps.")
        return None

# --- Testing Code ---

async def main_test_external_research():
    """
    Test the On-Demand External Research Workflow with enhanced functionality.
    """
    
    # Get default paths  
    default_runs_folder_path, default_state_filter_mapping_path = get_workflow_paths()
    
    # Load state mapping for filtering dumps
    state_filter_mapping = load_state_filter_mapping(default_state_filter_mapping_path)
    
    print(f"\n--- Running Scenario: {test_scenario['name']} ---")
    print(f"Runs Folder: {default_runs_folder_path}")
    print(f"State Mapping File: {default_state_filter_mapping_path}")
    if state_filter_mapping:
        print(f"State Filtering: Enabled ({len(state_filter_mapping)} sections)")
    else:
        print(f"State Filtering: Disabled (full state dumps)")
    
    try:
        final_status, final_outputs = await run_workflow_test(
            test_name=f"{test_name} - {test_scenario['name']}",
            workflow_graph_schema=workflow_graph_schema,
            workflow_name_to_ingest_as_for_testing=WORKFLOW_NAME_TO_INGEST_AS_FOR_TESTING,
            initial_inputs=test_scenario['initial_inputs'],
            expected_final_status=WorkflowRunStatus.COMPLETED,
            hitl_inputs=predefined_hitl_inputs,
            runs_folder_path=default_runs_folder_path,
            state_filter_mapping=state_filter_mapping,
            setup_docs=setup_docs,
            cleanup_docs=cleanup_docs,
            cleanup_docs_created_by_setup=False,
            validate_output_func=validate_external_research_output,
            stream_intermediate_results=True,
            poll_interval_sec=3,
            timeout_sec=1800  # 30 minutes for comprehensive research
        )
        
        # Display results
        if final_outputs:
            display_research_results(final_outputs)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    
    print(f"\n--- {test_name} Completed Successfully ---")


# Entry point
if __name__ == "__main__":
    print("="*60)
    print("On-Demand External Research Workflow Test")
    print("="*60)
    
    try:
        asyncio.run(main_test_external_research())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=$(pwd):$(pwd)/services poetry run python standalone_test_client/kiwi_client/workflows/active/labs/on_demand_external_research/wf_testing/wf_runner.py")
