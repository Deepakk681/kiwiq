# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Import from setup docs
from kiwi_client.workflows.active.content_studio.linkedin_calendar_selected_topic_to_brief_sandbox.wf_testing.sandbox_setup_docs import (
    test_entity_username,
)

test_name = "LinkedIn Calendar Selected Topic to Brief Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test selected topic data
test_selected_topic = {
    "suggested_topics": [
        {
            "title": "Why Your Sales Team's CRM Adoption is Failing (And How to Fix It)",
            "description": "Explore the root causes of poor CRM adoption and share practical strategies that have worked for enterprise sales teams"
        }
    ],
    "scheduled_date": "2025-08-15T09:00:00Z",
    "theme": "Sales Operations Excellence",
    "play_aligned": "Thought Leadership",
    "objective": "thought_leadership",
    "why_important": "CRM adoption is a universal challenge that resonates with sales leaders and directly impacts revenue performance"
}

# Test scenario
test_scenario = {
    "name": "Generate LinkedIn Brief from Selected Topic",
    "initial_inputs": {
        "entity_username": test_entity_username,
        "selected_topic": test_selected_topic,
        "initial_status": "draft",
        "brief_uuid": "123489",
        "load_additional_user_files": [
            {
                "namespace": "user_research_files",
                "docname": "linkedin_content_strategy_guide",
                "is_shared": False
            },
            {
                "namespace": "user_research_files",
                "docname": "sales_team_case_studies",
                "is_shared": False
            }
        ]
    }
}