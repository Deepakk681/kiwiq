"""
Run workflow graph tests.

This script runs the test workflow graphs to demonstrate the workflow system's capabilities.
It imports and executes test cases from the test_workflow_graphs module.
"""
import sys
import logging
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import test functions
try:
    from workflow_service.tests.test_workflow_graphs import (
        run_simple_number_graph,
        run_router_graph,
        run_hitl_graph,
        run_complex_graph,
        run_dynamic_nodes_connected_graph,
        run_central_state_graph,
        run_all_tests
    )
except ImportError as e:
    logger.error(f"Failed to import test modules: {e}")
    sys.exit(1)

def format_result(result: Dict[str, Any]) -> str:
    """Format result dictionary for display."""
    formatted = ""
    for key, value in result.items():
        formatted += f"  {key}: {value}\n"
    return formatted

def main():
    """Run workflow tests and display results."""
    logger.info("Starting workflow tests")
    
    try:
        # Run simple number graph
        logger.info("Running simple number graph test")
        simple_result = run_simple_number_graph()
        logger.info(f"Simple graph result:\n{format_result(simple_result)}")
        
        # Run router graph with high path
        logger.info("Running router graph test (high path)")
        high_result = run_router_graph(75.0)
        logger.info(f"Router graph (high path) result:\n{format_result(high_result)}")
        
        # Run router graph with low path
        logger.info("Running router graph test (low path)")
        low_result = run_router_graph(25.0)
        logger.info(f"Router graph (low path) result:\n{format_result(low_result)}")
        
        # Run HITL graph
        logger.info("Running HITL graph test")
        hitl_result = run_hitl_graph()
        logger.info(f"HITL graph result:\n{format_result(hitl_result)}")
        
        # Run dynamic nodes connected graph
        logger.info("Running dynamic nodes connected graph test")
        dynamic_result = run_dynamic_nodes_connected_graph()
        logger.info(f"Dynamic nodes connected graph result:\n{format_result(dynamic_result)}")
        
        # Run central state graph
        logger.info("Running central state graph test")
        central_result = run_central_state_graph()
        logger.info(f"Central state graph result:\n{format_result(central_result)}")
        
        # Run complex graph tests
        logger.info("Running complex graph test (high path)")
        complex_high_result = run_complex_graph(75.0)
        logger.info(f"Complex graph (high path) result:\n{format_result(complex_high_result)}")
        
        logger.info("Running complex graph test (low path)")
        complex_low_result = run_complex_graph(25.0)
        logger.info(f"Complex graph (low path) result:\n{format_result(complex_low_result)}")
        
        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 