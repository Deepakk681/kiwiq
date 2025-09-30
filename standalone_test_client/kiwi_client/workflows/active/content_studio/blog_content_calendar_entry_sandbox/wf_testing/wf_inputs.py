from datetime import datetime, timedelta

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

test_name = "Blog Content Calendar Entry Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test scenario
test_scenario = {
    "name": "Generate Blog Content Calendar",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "start_date": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end_date": (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
}