"""
Test inputs for Blog Content Playbook Generation workflow.
"""

from kiwi_client.workflows.active.playbook.blog_content_playbook_generation.wf_testing.sandbox_setup_docs import (
    test_company_name,
)

test_name = "Blog Content Playbook Generation Workflow Test"

# Test scenario
test_scenario = {
    "name": "Blog Content Playbook Generation",
    "initial_inputs": {
        "company_name": test_company_name
    }
}
