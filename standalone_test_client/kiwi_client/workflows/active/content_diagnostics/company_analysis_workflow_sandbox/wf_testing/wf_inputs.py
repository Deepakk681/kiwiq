from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test configuration
test_name = "Company Analysis Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Analyze Company Documents and Market Research",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "scraped_data": [],  # Will be populated from web scraping
        "has_insufficient_blog_and_page_count": False  # Test insufficient content path
    }
}

# Legacy TEST_INPUTS for backward compatibility
TEST_INPUTS = test_scenario["initial_inputs"]