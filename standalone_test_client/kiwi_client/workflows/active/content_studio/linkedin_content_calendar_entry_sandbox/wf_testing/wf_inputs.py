# Import needed modules
from datetime import datetime, timedelta

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Import from setup docs
from kiwi_client.workflows.active.content_studio.linkedin_content_calendar_entry_sandbox.wf_testing.sandbox_setup_docs import (
    test_entity_username,
)

test_name = "LinkedIn Content Calendar Entry Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Configuration
PAST_CONTEXT_POSTS_LIMIT = 10

# Test scenario
test_scenario = {
    "name": "Generate LinkedIn Content Calendar Topics",
    "initial_inputs": {
        "entity_username": test_entity_username,
        "weeks_to_generate": 2,  # Generate for 2 weeks
        "past_context_posts_limit": PAST_CONTEXT_POSTS_LIMIT,  # Combined limit for context
        "start_date": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end_date": (datetime.utcnow() + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
}