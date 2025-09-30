# Test configuration
test_name = "Blog Content Analysis Workflow Test"

# Test scenario configuration
test_scenario = {
    "name": "Analyze Blog Content and Classify by Funnel Stage",
    "initial_inputs": {
        "company_name": "lamatic",
        "start_urls": ["https://blog.lamatic.ai"],
        "exclude_paths": ["/announcements/*", "/resources/*", "/product-updates/*", "/about-2/*"]
    }
}

# Legacy TEST_INPUTS for backward compatibility
TEST_INPUTS = test_scenario["initial_inputs"]