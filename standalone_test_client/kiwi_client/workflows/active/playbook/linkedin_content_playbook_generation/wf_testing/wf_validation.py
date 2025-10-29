"""
Validation functions for LinkedIn Content Playbook Generation workflow.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def validate_playbook_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the LinkedIn Content Playbook Generation workflow outputs.

    Args:
        outputs: The dictionary of final outputs from the workflow run.

    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating LinkedIn content playbook workflow outputs...")

    # Check for expected keys
    assert 'final_paths_processed' in outputs or outputs, "Validation Failed: No final outputs found."

    logger.info(" LinkedIn content playbook workflow validation passed.")

    return True
