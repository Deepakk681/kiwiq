from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test configuration
test_name = "Deep Research Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Perform Deep Research on Company Topics",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "run_blog_analysis": True,
        "run_linkedin_exec": True,  # Set to False to avoid needing LinkedIn data
    }
}

# Legacy TEST_INPUTS for backward compatibility
TEST_INPUTS = test_scenario["initial_inputs"]