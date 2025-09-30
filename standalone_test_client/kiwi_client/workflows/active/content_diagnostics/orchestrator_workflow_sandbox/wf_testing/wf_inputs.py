from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
    test_sandbox_entity_username,
)

# Test configuration
test_name = "Orchestrator Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Orchestrate Multiple Content Analysis Workflows",
    "initial_inputs": {
        # LinkedIn parameters
        "entity_username": test_sandbox_entity_username,
        "entity_url": "https://www.linkedin.com/in/test-user/",
        "run_linkedin_exec": True,

        # Blog parameters
        "company_name": test_sandbox_company_name,
        "blog_start_urls": ["https://blog.example.com"],
        "run_blog_analysis": True,

        # Common parameters
        "exclude_paths": [],
        "include_only_paths": [],
        "use_cached_scraping_results": True,
        "cache_lookback_period_days": 7,
    }
}

# Legacy ORCHESTRATOR_WORKFLOW_INPUTS for backward compatibility
ORCHESTRATOR_WORKFLOW_INPUTS = test_scenario["initial_inputs"]