from kiwi_client.workflows.active.sandbox_identifiers import test_sandbox_company_name as test_company_name
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_AI_VISIBILITY_TEST_DOCNAME,
    BLOG_COMPANY_AI_VISIBILITY_TEST_NAMESPACE_TEMPLATE,
)

setup_docs = [
        # Blog Company Document
        {
            'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name),
            'docname': BLOG_COMPANY_DOCNAME,
            'initial_data': {
                "name": "KiwiQ",
                "website_url": "https://www.kiwiq.ai",
                "value_proposition": "AI-powered content generation platform specifically designed for B2B SaaS companies. Our platform leverages GPT-5 and proprietary algorithms to create high-quality blog posts, whitepapers, and marketing content that resonates with technical B2B audiences.",
                "company_goals": [
                    "Become the leading AI-powered content creation platform for B2B SaaS companies",
                    "Achieve 10,000 active users by end of 2025", 
                    "Expand into enterprise market with custom solutions",
                    "Build strategic partnerships with major marketing agencies",
                    "Establish thought leadership in AI content generation space"
                ],
                "target_metrics": {
                    "user_growth": "50% MoM",
                    "revenue_target": "10M ARR by 2025",
                    "customer_satisfaction": "NPS > 50"
                },
                "competitors": [
                        {
                        "name": "Frase",
                        "website_url": "https://www.frase.io"
                        },
                        {
                        "name": "Writesonic",
                        "website_url": "https://writesonic.com"
                        },
                        {
                        "name": "Rytr",
                        "website_url": "https://rytr.me"
                        }
                ]                 
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