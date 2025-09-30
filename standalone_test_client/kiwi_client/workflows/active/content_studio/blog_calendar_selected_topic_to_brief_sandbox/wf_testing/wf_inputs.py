"""
Test inputs and scenarios for calendar selected topic to brief workflow testing.

This file defines the test scenarios and initial inputs for the workflow.
"""

from typing import Dict, Any

# Import test identifiers
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test name
test_name = "Calendar Selected Topic to Brief Workflow Test"

# Create a test selected topic (as if selected from ContentTopicsOutput)
test_selected_topic = {
    "suggested_topics": [
        {
            "title": "The Hidden Cost of Manual CRM Data Entry: A CFO's Perspective",
            "description": "Explore the financial impact of manual data entry on revenue teams, including lost productivity, opportunity costs, and the ROI of automation solutions"
        }
    ],
    "scheduled_date": "2025-08-15T14:00:00Z",
    "theme": "Revenue Operations Efficiency",
    "play_aligned": "Thought Leadership",
    "objective": "thought_leadership",
    "why_important": "CFOs are increasingly involved in RevOps technology decisions and need to understand the financial impact of manual processes"
}

# Test scenario with initial inputs
test_scenario = {
    "name": "CFO Perspective on CRM Manual Data Entry Costs",
    "description": "Test scenario for creating a content brief about the financial impact of manual CRM data entry from a CFO's perspective",
    "initial_inputs": {
        "company_name": test_sandbox_company_name,
        "selected_topic": test_selected_topic,
        "user_instructions": "I want to create content that helps CFOs understand the financial impact of manual CRM data entry. Focus on specific cost categories, hidden opportunity costs, and ROI calculations. Include real examples from SaaS companies.",
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
            "selected_topic": {
                "suggested_topics": [
                    {
                        "title": "How Sales Teams Can Automate CRM Workflows to Increase Selling Time",
                        "description": "Practical guide for revenue teams to automate repetitive CRM tasks and focus on high-value selling activities"
                    }
                ],
                "scheduled_date": "2025-08-20T14:00:00Z",
                "theme": "Sales Productivity",
                "play_aligned": "How-to Guide",
                "objective": "education",
                "why_important": "Sales teams spend 70% of their time on non-selling activities, automation can reclaim significant productive hours"
            },
            "user_instructions": "Let's create content about how sales teams can automate their CRM workflows to spend more time selling and less time on data entry. Focus on practical tips for revenue teams.",
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
            "selected_topic": {
                "suggested_topics": [
                    {
                        "title": "Using Conversation Intelligence to Predict and Prevent Customer Churn",
                        "description": "How customer success teams can leverage AI-powered conversation analysis to identify at-risk accounts and expansion opportunities"
                    }
                ],
                "scheduled_date": "2025-08-25T14:00:00Z",
                "theme": "Customer Success Excellence",
                "play_aligned": "Thought Leadership",
                "objective": "thought_leadership",
                "why_important": "Proactive churn prevention through conversation intelligence can reduce customer attrition by 25-30%"
            },
            "user_instructions": "I want to write about how customer success teams can use conversation intelligence to predict and prevent churn. Include insights on identifying expansion opportunities through customer interactions.",
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
            "selected_topic": {
                "suggested_topics": [
                    {
                        "title": "How Revenue Intelligence Platforms Improve Pipeline Visibility and Forecast Accuracy",
                        "description": "Explore the benefits of real-time data and automated insights for revenue teams' pipeline management and forecasting"
                    }
                ],
                "scheduled_date": "2025-08-30T14:00:00Z",
                "theme": "Revenue Operations",
                "play_aligned": "Case Study",
                "objective": "awareness",
                "why_important": "Companies using revenue intelligence platforms see 15-20% improvement in forecast accuracy and 30% faster deal cycles"
            },
            "user_instructions": "Create content exploring how revenue intelligence platforms help teams get better pipeline visibility and forecast accuracy. Focus on the benefits of real-time data and automated insights.",
            "initial_status": "draft",
            "brief_uuid": "423e4567-e89b-12d3-a456-426614174003",
            "load_additional_user_files": []
        }
    }
}