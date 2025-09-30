# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Import from setup docs
from kiwi_client.workflows.active.content_studio.blog_content_optimization_sandbox.wf_testing.sandbox_setup_docs import (
    original_blog_content,
)

test_name = "Blog Content Optimization Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test scenario
test_scenario = {
    "name": "Optimize Blog Content",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "original_blog": original_blog_content,
        "post_uuid": "blog_post_001"
    }
}