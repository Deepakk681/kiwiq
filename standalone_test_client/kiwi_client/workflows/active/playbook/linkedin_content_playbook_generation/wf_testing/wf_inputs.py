"""
Test inputs for LinkedIn Content Playbook Generation workflow.
"""

from kiwi_client.workflows.active.playbook.linkedin_content_playbook_generation.wf_testing.sandbox_setup_docs import (
    test_entity_username,
)

test_name = "LinkedIn Content Playbook Generation Workflow Test"

# Test scenario
test_scenario = {
    "name": "LinkedIn Content Playbook Generation",
    "initial_inputs": {
        "entity_username": test_entity_username
    }
}
