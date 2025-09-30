"""
Test inputs and scenarios for blog user input to brief workflow testing.

This file defines the test scenarios and initial inputs for the workflow.
"""

from typing import Dict, Any

# Import test identifiers
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test name
test_name = "Blog User Input to Brief Workflow Test"

# Test scenario with initial inputs
test_scenario = {
    "name": "AI Project Management Content Research",
    "description": "Test scenario for researching and creating a content brief about AI in project management",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "user_input": "I've been thinking about writing content around how AI is changing project management. I want to explore how small teams can leverage AI tools without losing the human touch in their workflows. Maybe something about the balance between automation and personal connection in remote teams?",
        "initial_status": "draft",
        "brief_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "load_additional_user_files": [
            {
                "namespace": "user_research_files",
                "docname": "project_management_ai_research",
                "is_shared": False
            },
            {
                "namespace": "user_research_files",
                "docname": "remote_team_collaboration_guide",
                "is_shared": False
            }
        ]
    }
}

# Alternative test scenarios (can be swapped in for different tests)
alternative_scenarios = {
    "sales_automation": {
        "name": "Sales Automation and CRM Content Research",
        "description": "Test scenario for researching content about sales automation and CRM optimization",
        "initial_inputs": {
            "company_name": test_sandbox_company_name,
            "user_input": "Let's create content about how sales teams can automate their CRM workflows to spend more time selling and less time on data entry. Focus on practical tips for revenue teams.",
            "initial_status": "draft",
            "brief_uuid": "223e4567-e89b-12d3-a456-426614174001",
            "load_additional_user_files": []
        }
    },
    "customer_success": {
        "name": "Customer Success Strategy Content Research",
        "description": "Test scenario for researching content about customer success and churn prevention",
        "initial_inputs": {
            "company_name": test_sandbox_company_name,
            "user_input": "I want to write about how customer success teams can use conversation intelligence to predict and prevent churn. Include insights on identifying expansion opportunities through customer interactions.",
            "initial_status": "draft",
            "brief_uuid": "323e4567-e89b-12d3-a456-426614174002",
            "load_additional_user_files": []
        }
    },
    "revenue_intelligence": {
        "name": "Revenue Intelligence Platform Content Research",
        "description": "Test scenario for researching content about revenue intelligence and pipeline visibility",
        "initial_inputs": {
            "company_name": test_sandbox_company_name,
            "user_input": "Create content exploring how revenue intelligence platforms help teams get better pipeline visibility and forecast accuracy. Focus on the benefits of real-time data and automated insights.",
            "initial_status": "draft",
            "brief_uuid": "423e4567-e89b-12d3-a456-426614174003",
            "load_additional_user_files": []
        }
    }
}