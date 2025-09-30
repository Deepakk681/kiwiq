# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Import from setup docs
from kiwi_client.workflows.active.content_studio.linkedin_alternate_text_suggestion_sandbox.wf_testing.sandbox_setup_docs import (
    entity_username,
)

test_name = "LinkedIn Alternate Text Suggestion Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test scenario
test_scenario = {
    "name": "Generate Alternative Text Suggestions",
    "initial_inputs": {
        "selected_text": "Military commanders never keep mission-critical information in their heads—yet 83% of founders I've advised do exactly that.",
        "complete_content_doc": """Military commanders never keep mission-critical information in their heads—yet 83% of founders I've advised do exactly that.

In the military, this approach would be considered a strategic vulnerability. No mission depends on one person knowing everything, but rather the opposite: Every soldier needs to know as much as is feasible about the mission to contribute in the best way possible.

At Wing, we implemented the military's 5-Point Operations Order for every strategic decision:

Situation: What are we facing?
Mission: What must be accomplished?
Execution: How specifically will we do it?
Support: What resources are required?
Command/Signal: Who makes decisions when things change?

As we've implemented this approach in our operations, we saw churn plummet by 60% and decisions being made faster than ever.

Your business can't scale if critical knowledge remains trapped in your head.

How do you extract and distribute your expertise across your organization?""",
        "user_feedback": "Make it more engaging and professional",
        "entity_username": entity_username
    }
}