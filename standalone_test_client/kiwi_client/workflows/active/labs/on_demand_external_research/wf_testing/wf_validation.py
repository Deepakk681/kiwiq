"""
Output validation functions for On-Demand External Research workflow.
"""

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_external_research_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the external research workflow outputs.
    
    Args:
        outputs: The dictionary of final outputs from the workflow run.
        
    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating external research workflow outputs...")
    
    # Check if research was completed and saved
    final_research_paths = outputs.get('final_research_paths')
    if final_research_paths:
        logger.info("✓ Research was successfully completed and saved")
        assert isinstance(final_research_paths, list), "Validation Failed: final_research_paths should be a list."
        logger.info(f"   Research saved to: {final_research_paths}")
    
    # Check for research content in outputs
    research_content = outputs.get('research_content')
    if research_content:
        assert isinstance(research_content, str), "Validation Failed: research_content should be a string."
        logger.info(f"✓ Research content available: {len(research_content)} characters")
        
        # Basic content quality checks
        assert len(research_content) > 100, "Validation Failed: Research content is too short."
        logger.info("✓ Research content meets minimum length requirement")
    
    # Check for web search results if present
    web_search_result = outputs.get('web_search_result')
    if web_search_result:
        logger.info("✓ Web search was conducted during research")
        assert isinstance(web_search_result, dict), "Validation Failed: web_search_result should be a dict."
        
        if 'citations' in web_search_result and web_search_result['citations']:
            citations = web_search_result['citations']
            assert isinstance(citations, list), "Validation Failed: citations should be a list."
            logger.info(f"✓ Citations found: {len(citations)} sources")
            
            # Validate citation structure
            for i, citation in enumerate(citations[:3]):  # Check first 3 citations
                assert isinstance(citation, dict), f"Validation Failed: citation {i} should be a dict."
                if 'url' in citation:
                    assert citation['url'].startswith(('http://', 'https://')), f"Validation Failed: citation {i} has invalid URL."
    
    # Check for generated research name
    generated_research_name = outputs.get('generated_research_name')
    if generated_research_name:
        logger.info(f"✓ Research name generated: {generated_research_name}")
        assert isinstance(generated_research_name, str), "Validation Failed: generated_research_name should be a string."
        assert len(generated_research_name.strip()) > 0, "Validation Failed: generated_research_name is empty."
    
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
    
    logger.info("✓ External research workflow validation passed.")
    
    return True


def display_research_results(final_outputs: Dict[str, Any]) -> None:
    """
    Display the external research results in a formatted way.
    
    Args:
        final_outputs: The final outputs from the workflow execution.
    """
    if not final_outputs:
        logger.warning("No final outputs to display.")
        return
    
    print(f"\nExternal Research Results:")
    
    # Research content
    research_content = final_outputs.get('research_content', '')
    print(f"Research Content Length: {len(research_content)} characters")
    
    # Generated research name
    research_name = final_outputs.get('generated_research_name', 'N/A')
    print(f"Generated Research Name: {research_name}")
    
    # Web search results
    web_search_result = final_outputs.get('web_search_result', {})
    citations = web_search_result.get('citations', [])
    print(f"Sources Cited: {len(citations)}")
    
    # Display first few citations
    if citations:
        print(f"Top Citations:")
        for i, citation in enumerate(citations[:3], 1):
            title = citation.get('title', 'No title')
            url = citation.get('url', 'No URL')
            print(f"  {i}. {title[:60]}{'...' if len(title) > 60 else ''}")
            print(f"     {url}")
    
    # Save paths
    if final_outputs.get('final_research_paths'):
        print("✓ Research report was successfully saved")
        print(f"Saved to: {final_outputs.get('final_research_paths')}")
    
    # User feedback
    user_action = final_outputs.get('user_action', 'N/A')
    revision_feedback = final_outputs.get('revision_feedback', '')
    print(f"Final User Action: {user_action}")
    if revision_feedback:
        print(f"User Feedback: {revision_feedback[:100]}{'...' if len(revision_feedback) > 100 else ''}")
