from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test configuration
test_name = "Competitor Content Analysis Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Analyze Competitor Content Strategies",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
    }
}

# Legacy TEST_INPUTS for backward compatibility
TEST_INPUTS = test_scenario["initial_inputs"]