# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the blog content calendar entry workflow:
# 1. Company Documentation - Company information and target audience
# 2. Content Strategy - Blog content strategy and playbook
# 3. Previous Blog Posts - Historical posts for reference
# These documents are loaded during the workflow for calendar generation.

from typing import List
from kiwi_client.test_run_workflow_client import SetupDocInfo, CleanupDocInfo

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_IS_VERSIONED,
    BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_STRATEGY_DOCNAME,
    BLOG_CONTENT_STRATEGY_IS_VERSIONED,
    BLOG_POST_NAMESPACE_TEMPLATE,
    BLOG_POST_DOCNAME,
    BLOG_POST_IS_VERSIONED,
    BLOG_POST_IS_SHARED,
)

# Use sandbox company name
test_company_name = test_sandbox_company_name

# Create realistic test data for setup
setup_docs: List[SetupDocInfo] = [
        # Company Profile Document
        {
            'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name), 
            'docname': BLOG_COMPANY_DOCNAME,
            'initial_data': {
                "company_name": "Acme Corp",
                "company_description": "Leading B2B SaaS platform for enterprise resource planning",
                "industry": "Enterprise Software",
                "target_audience": {
                    "primary": "IT Directors and CTOs at mid-market companies",
                    "secondary": "Operations managers looking for efficiency tools",
                    "industries": ["Manufacturing", "Retail", "Healthcare"]
                },
                "value_proposition": "Streamline operations with AI-powered ERP that reduces manual work by 60%",
                "content_goals": {
                    "primary": "Establish thought leadership in enterprise automation",
                    "secondary": ["Generate qualified leads", "Improve SEO rankings for key terms"]
                },
                "expertise_areas": [
                    "Enterprise resource planning",
                    "AI and machine learning in operations",
                    "Supply chain optimization",
                    "Business process automation",
                    "Data analytics and reporting"
                ],
                "pain_points_addressed": [
                    "Manual data entry and errors",
                    "Lack of real-time visibility",
                    "Disconnected systems",
                    "Compliance and reporting challenges",
                    "Scaling operations efficiently"
                ]
            }, 
            'is_versioned': BLOG_COMPANY_IS_VERSIONED, 
            'is_shared': False,
        },
        # Content Strategy/Playbook Document
        {
            'namespace': BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE.format(item=test_company_name), 
            'docname': BLOG_CONTENT_STRATEGY_DOCNAME,
            'initial_data': {
                "title": "Acme Corp Blog Content Strategy",
                "content_pillars": [
                    {
                        "name": "Enterprise Automation Insights",
                        "description": "Deep dives into automation strategies and best practices",
                        "topics": [
                            "ROI of automation",
                            "Implementation roadmaps",
                            "Change management",
                            "Case studies and success stories"
                        ]
                    },
                    {
                        "name": "Industry Trends & Analysis",
                        "description": "Market trends and future of enterprise software",
                        "topics": [
                            "AI adoption in enterprises",
                            "Digital transformation trends",
                            "Regulatory updates",
                            "Market research and reports"
                        ]
                    },
                    {
                        "name": "Product Innovation & Features",
                        "description": "Product updates and feature deep-dives",
                        "topics": [
                            "New feature announcements",
                            "Product roadmap insights",
                            "Integration guides",
                            "Best practices for platform usage"
                        ]
                    },
                    {
                        "name": "Customer Success Stories",
                        "description": "Real-world implementations and results",
                        "topics": [
                            "Customer case studies",
                            "Implementation journeys",
                            "ROI achievements",
                            "Industry-specific solutions"
                        ]
                    }
                ],
                "seo_strategy": {
                    "primary_keywords": [
                        "enterprise resource planning",
                        "ERP software",
                        "business automation",
                        "supply chain management software"
                    ],
                    "long_tail_keywords": [
                        "best ERP for manufacturing companies",
                        "how to automate business processes",
                        "enterprise software implementation guide"
                    ]
                },
                "content_format_preferences": [
                    "Long-form guides (2000+ words)",
                    "Industry reports with data",
                    "How-to tutorials",
                    "Case studies with metrics",
                    "Thought leadership pieces"
                ],
                "posts_per_week": 2
            }, 
            'is_versioned': BLOG_CONTENT_STRATEGY_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'default'
        },
        # Seed Blog Post Draft Document (ensures tools can find a recent post)
        {
            'namespace': BLOG_POST_NAMESPACE_TEMPLATE.format(item=test_company_name),
            'docname': BLOG_POST_DOCNAME.format(item=test_company_name),
            'initial_data': {
                "title": "AI in ERP: 5 Ways to Accelerate Implementation",
                "summary": "Practical strategies to cut ERP rollout time using AI-powered automation.",
                "content": "In this post we explore how AI reduces implementation timelines, improves data migration, and automates testing...",
                
            },
            'is_versioned': BLOG_POST_IS_VERSIONED,
            'is_shared': BLOG_POST_IS_SHARED,
            'initial_version': 'default'
        },
    ]

    # Define cleanup docs to remove test artifacts after test completion
cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name), 
            'docname': BLOG_COMPANY_DOCNAME, 
            'is_versioned': BLOG_COMPANY_IS_VERSIONED, 
            'is_shared': False
        },
        {
            'namespace': BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE.format(item=test_company_name), 
            'docname': BLOG_CONTENT_STRATEGY_DOCNAME, 
            'is_versioned': BLOG_CONTENT_STRATEGY_IS_VERSIONED, 
            'is_shared': False
        },
        {
            'namespace': BLOG_POST_NAMESPACE_TEMPLATE.format(item=test_company_name), 
            'docname': BLOG_POST_DOCNAME.format(item=test_company_name), 
            'is_versioned': BLOG_POST_IS_VERSIONED, 
            'is_shared': BLOG_POST_IS_SHARED
        },
    ]