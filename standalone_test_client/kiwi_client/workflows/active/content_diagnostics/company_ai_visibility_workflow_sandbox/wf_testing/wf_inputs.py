from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test configuration
test_name = "Company AI Visibility Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Analyze Company AI Visibility and Competitive Positioning",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "enable_cache": True,
        "cache_lookback_days": 7,
    }
}

# Legacy test_inputs for backward compatibility
test_inputs = test_scenario["initial_inputs"]