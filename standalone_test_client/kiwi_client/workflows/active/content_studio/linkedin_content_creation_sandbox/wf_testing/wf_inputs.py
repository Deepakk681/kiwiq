from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

from kiwi_client.workflows.active.content_studio.linkedin_content_creation_sandbox.wf_testing.sandbox_setup_docs import (
    test_entity_username,
    test_post_uuid,
    brief_docname,
)

# Test name for the workflow
test_name = "LinkedIn Content Creation Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test scenario configuration
test_scenario = {
    "name": "Generate LinkedIn Post from Brief",
    "initial_inputs": {
        "post_uuid": test_post_uuid,
        "brief_docname": brief_docname,
        "entity_username": test_entity_username,
        "initial_status": "draft",
        "load_additional_user_files": []
    }
}

# Keep backward compatibility with old name
POST_CREATION_WORKFLOW_INPUTS = test_scenario["initial_inputs"]