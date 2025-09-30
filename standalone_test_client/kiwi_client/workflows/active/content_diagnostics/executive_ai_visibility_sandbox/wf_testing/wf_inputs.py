from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
    test_sandbox_entity_username,
)

# Test configuration
test_name = "Executive AI Visibility Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Analyze Executive AI Visibility",
    "initial_inputs": {
        "entity_username": test_sandbox_entity_username,  # LinkedIn username for the executive
        "enable_cache": True,
        "cache_lookback_days": 7,
    }
}

# Legacy test_inputs for backward compatibility
test_inputs = test_scenario["initial_inputs"]