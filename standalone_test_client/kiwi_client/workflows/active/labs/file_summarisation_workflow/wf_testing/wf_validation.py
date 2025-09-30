"""
Output validation functions for File Summarisation workflow.
"""

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_file_summarisation_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the file summarisation workflow outputs.
    
    Args:
        outputs: The dictionary of final outputs from the workflow run.
        
    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating file summarisation workflow outputs...")
    
    # Check if summary was completed and saved
    final_summary_paths = outputs.get('final_summary_paths')
    if final_summary_paths:
        logger.info("✓ Summary was successfully completed and saved")
        assert isinstance(final_summary_paths, list), "Validation Failed: final_summary_paths should be a list."
        logger.info(f"   Summary saved to: {final_summary_paths}")
    
    # Check for summary content in outputs
    summary_content = outputs.get('summary_content')
    if summary_content:
        assert isinstance(summary_content, str), "Validation Failed: summary_content should be a string."
        logger.info(f"✓ Summary content available: {len(summary_content)} characters")
        
        # Basic content quality checks
        assert len(summary_content) > 50, "Validation Failed: Summary content is too short."
        logger.info("✓ Summary content meets minimum length requirement")
        
        # Check for common summary elements
        summary_lower = summary_content.lower()
        common_summary_words = ['summary', 'key', 'important', 'main', 'conclusion', 'overview']
        has_summary_elements = any(word in summary_lower for word in common_summary_words)
        if has_summary_elements:
            logger.info("✓ Summary contains expected summary language patterns")
    
    # Check for generated summary name
    generated_summary_name = outputs.get('generated_summary_name')
    if generated_summary_name:
        logger.info(f"✓ Summary name generated: {generated_summary_name}")
        assert isinstance(generated_summary_name, str), "Validation Failed: generated_summary_name should be a string."
        assert len(generated_summary_name.strip()) > 0, "Validation Failed: generated_summary_name is empty."
        
        # Basic name quality check
        assert len(generated_summary_name) < 200, "Validation Failed: generated_summary_name is too long."
    
    # Check for save configuration
    save_config = outputs.get('save_config')
    if save_config:
        logger.info("✓ Save configuration generated")
        assert isinstance(save_config, list), "Validation Failed: save_config should be a list."
        if save_config:
            config = save_config[0]
            assert 'namespace' in config, "Validation Failed: save_config missing namespace."
            assert 'docname' in config, "Validation Failed: save_config missing docname."
    
    # Check user interaction history
    user_action = outputs.get('user_action')
    if user_action:
        assert user_action in ["approve", "request_revisions", "cancel"], f"Validation Failed: invalid user_action '{user_action}'."
        logger.info(f"✓ User action recorded: {user_action}")
    
    # Check loaded additional files
    additional_user_files = outputs.get('additional_user_files')
    if additional_user_files:
        assert isinstance(additional_user_files, str), "Validation Failed: additional_user_files should be a string."
        logger.info(f"✓ Additional context files loaded: {len(additional_user_files)} characters")
    
    logger.info("✓ File summarisation workflow validation passed.")
    
    return True


def display_summarisation_results(final_outputs: Dict[str, Any]) -> None:
    """
    Display the file summarisation results in a formatted way.
    
    Args:
        final_outputs: The final outputs from the workflow execution.
    """
    if not final_outputs:
        logger.warning("No final outputs to display.")
        return
    
    print(f"\nFile Summarisation Results:")
    
    # Summary content
    summary_content = final_outputs.get('summary_content', '')
    print(f"Summary Content Length: {len(summary_content)} characters")
    
    # Display first 200 characters of summary as preview
    if summary_content:
        preview = summary_content[:200] + "..." if len(summary_content) > 200 else summary_content
        print(f"Summary Preview: {preview}")
    
    # Generated summary name
    summary_name = final_outputs.get('generated_summary_name', 'N/A')
    print(f"Generated Summary Name: {summary_name}")
    
    # Additional context files
    additional_files = final_outputs.get('additional_user_files', '')
    if additional_files:
        print(f"Additional Context Files Used: {len(additional_files)} characters")
    
    # Save paths
    if final_outputs.get('final_summary_paths'):
        print("✓ Summary report was successfully saved")
        print(f"Saved to: {final_outputs.get('final_summary_paths')}")
    
    # User feedback
    user_action = final_outputs.get('user_action', 'N/A')
    revision_feedback = final_outputs.get('revision_feedback', '')
    print(f"Final User Action: {user_action}")
    if revision_feedback:
        print(f"User Feedback: {revision_feedback[:100]}{'...' if len(revision_feedback) > 100 else ''}")
        
    # Save configuration info
    save_config = final_outputs.get('save_config', [])
    if save_config:
        config = save_config[0] if save_config else {}
        namespace = config.get('namespace', 'N/A')
        docname = config.get('docname', 'N/A')
        print(f"Document Storage: {namespace} / {docname}")
