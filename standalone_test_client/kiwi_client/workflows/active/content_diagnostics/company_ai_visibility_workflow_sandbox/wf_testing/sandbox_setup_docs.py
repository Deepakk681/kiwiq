from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.workflows.active.sandbox_identifiers import test_sandbox_company_name as test_company_name
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE
)

setup_docs = [
        # Blog Company Document
        {
            'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name),
            'docname': BLOG_COMPANY_DOCNAME,
            'initial_data': {
                "company_name": test_company_name,
                "industry": "AI Revenue Orchestration Platform",
                "primary_products": [
                    "Deal Execution Agent",
                    "Customer Retention Agent",
                    "Coaching Agent",
                    "AI CRO"
                ],
                "target_market": "B2B GTM teams (Sales, CS, RevOps)",
                "competitors": ["Gong", "Clari", "Salesforce Einstein", "People.ai"],
                "unique_value_proposition": "Capture structured data from every customer interaction, update CRM, route insights, and automate GTM workflows",
                "blog_topics": ["AI for Revenue Ops", "Deal Execution", "Churn Prevention", "AI Coaching"],
                "key_differentiators": ["AI Signals + Alerts", "MEDDIC Autopilot", "Executive Briefs", "Slack-first orchestration"],
            },
            'is_versioned': False,
            'is_shared': False
        },
    ]

    # Define cleanup docs
cleanup_docs = [
        {'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name), 'docname': BLOG_COMPANY_DOCNAME, 'is_versioned': False, 'is_shared': False},
        # Cleanup generated test documents
        {'namespace': BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=test_company_name), 'docname': BLOG_AI_VISIBILITY_TEST_DOCNAME, 'is_versioned': True, 'is_shared': False},
        {'namespace': BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE.format(item=test_company_name), 'docname': BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME, 'is_versioned': True, 'is_shared': False},
    ]