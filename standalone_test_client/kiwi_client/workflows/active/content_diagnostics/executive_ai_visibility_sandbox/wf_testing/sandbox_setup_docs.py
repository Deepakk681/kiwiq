from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name as test_company_name,
    test_sandbox_entity_username as test_entity_username
)
from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_SCRAPED_PROFILE_DOCNAME,
    LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_AI_VISIBILITY_TEST_DOCNAME,
    LINKEDIN_USER_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE
)

# Test entity username is imported from sandbox_identifiers

setup_docs = [
        # LinkedIn User Profile Document
        {
            'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username),
            'docname': LINKEDIN_USER_PROFILE_DOCNAME,
            'initial_data': {
                "username": test_entity_username,
                "full_name": "Jayaram M",
                "headline": "AI Sales & GTM Leader | Revenue Orchestration | RevOps Strategy",
                "summary": "Go-to-market and revenue operations leader focused on AI-driven workflows, data quality, and pipeline execution.",
                "experience": [
                    {"title": "Head of GTM", "company": "Momentum", "duration": "2+ years"},
                    {"title": "Revenue Operations Leader", "company": "Prior Companies", "duration": "5+ years"}
                ],
                "skills": ["Revenue Operations", "Sales Strategy", "AI in GTM", "Salesforce"],
            },
            'is_versioned': False,
            'is_shared': False
        },
        # LinkedIn Scraped Profile Document
        {
            'namespace': LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username),
            'docname': LINKEDIN_SCRAPED_PROFILE_DOCNAME,
            'initial_data': {
                "recent_posts": [
                    {
                        "content": "How to operationalize AI in your revenue workflows without breaking your CRM.",
                        "date": "2025-07-20",
                        "engagement": {"likes": 120, "comments": 15, "shares": 10}
                    },
                    {
                        "content": "3 steps to turn conversations into structured data that actually updates Salesforce.",
                        "date": "2025-07-10",
                        "engagement": {"likes": 95, "comments": 12, "shares": 8}
                    }
                ],
                "follower_count": 15000,
                "connection_count": 500,
                "engagement_rate": 0.045
            },
            'is_versioned': False,
            'is_shared': False
        },
    ]

    # Define cleanup docs
cleanup_docs = [
        {'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username), 'docname': LINKEDIN_USER_PROFILE_DOCNAME, 'is_versioned': False, 'is_shared': False},
        {'namespace': LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username), 'docname': LINKEDIN_SCRAPED_PROFILE_DOCNAME, 'is_versioned': False, 'is_shared': False},
        # Cleanup generated test documents
        {'namespace': LINKEDIN_USER_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=test_entity_username), 'docname': LINKEDIN_USER_AI_VISIBILITY_TEST_DOCNAME, 'is_versioned': True, 'is_shared': False},
    ]