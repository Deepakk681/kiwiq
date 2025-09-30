from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_entity_username,
)

# Test configuration
test_name = "LinkedIn Scraping Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Scraping LinkedIn profile and posts data with filtering",
    "initial_inputs": {
        # Replace with a valid LinkedIn profile URL for testing
        "entity_url": "https://www.linkedin.com/in/joyeedesigner/",
        "entity_username": test_sandbox_entity_username,  # Used for document naming in the workflow
    }
}

# Legacy LINKEDIN_SCRAPING_WORKFLOW_INPUTS for backward compatibility
LINKEDIN_SCRAPING_WORKFLOW_INPUTS = test_scenario["initial_inputs"]