from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
    test_sandbox_entity_username,
)

# Test configuration
test_name = "LinkedIn Content Analysis Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Analyze LinkedIn Content Performance",
    "initial_inputs": {
        "entity_username": test_sandbox_entity_username,
        "entity_url": "https://www.linkedin.com/in/test-user/",
        "company_name": test_sandbox_company_name,
    }
}

# Legacy LINKEDIN_CONTENT_ANALYSIS_WORKFLOW_INPUTS for backward compatibility
LINKEDIN_CONTENT_ANALYSIS_WORKFLOW_INPUTS = test_scenario["initial_inputs"]