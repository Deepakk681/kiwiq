from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_entity_username,
)

# Test name for the workflow
test_name = "LinkedIn User Input to Brief Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test scenario configuration
test_scenario = {
    "name": "Generate LinkedIn Content Brief",
    "initial_inputs": {
        "entity_username": test_sandbox_entity_username,
        "user_input": "I want to write about how AI is transforming project management for remote teams. I'm particularly interested in discussing the balance between automation and human leadership, and how executives can leverage AI tools without losing the personal connection with their teams. I'd also like to touch on the challenges we've seen with AI adoption in the workplace and practical tips for implementation.",
        "brief_uuid": "draft_brief_uuid",
        "load_additional_user_files": [
            {
                "namespace": "user_research_files",
                "docname": "ai_project_management_research",
                "is_shared": False
            },
            {
                "namespace": "user_research_files",
                "docname": "remote_team_leadership_guide",
                "is_shared": False
            }
        ]
    }
}