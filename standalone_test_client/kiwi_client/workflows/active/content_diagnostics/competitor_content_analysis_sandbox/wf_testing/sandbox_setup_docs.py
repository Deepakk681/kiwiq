company_data = {
        "company_name": "Writer",
        "website_url": "https://writer.com",
        "positioning_headline": "Writer is an AI writing platform built for teams, helping enterprises ensure consistent, on-brand, and high-quality content across all departments.",
        "icp": {
            "icp_name": "Enterprise Marketing and Operations Teams",
            "target_industry": "Technology, Financial Services, Healthcare, and Professional Services",
            "company_size": "Mid-market to Enterprise (500+ employees)",
            "buyer_persona": "CMO, Head of Content, VP of Marketing, Operations Lead",
            "pain_points": [
                "Inconsistent brand voice across departments",
                "Low content velocity",
                "Difficulty scaling content creation while maintaining quality",
                "Inefficiencies in cross-functional communication and documentation"
            ],
            "goals": [
                "Standardize brand voice across all content",
                "Improve writing quality at scale",
                "Enable all team members to write clearly and efficiently",
                "Speed up content production processes"
            ]
        },
        "content_distribution_mix": {
            "awareness_percent": 40.0,
            "consideration_percent": 30.0,
            "purchase_percent": 20.0,
            "retention_percent": 10.0
        },
        "competitors": [
            {
                "website_url": "https://grammarly.com",
                "name": "Grammarly Business"
            },
            {
                "website_url": "https://jasper.ai",
                "name": "Jasper"
            },
            {
                "website_url": "https://copy.ai",
                "name": "Copy.ai"
            }
        ]
    }

from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.workflows.active.sandbox_identifiers import test_sandbox_company_name as test_company_name
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_VERSIONED
)

setup_docs: List[SetupDocInfo] = [
        {
            'namespace': f"blog_company_profile_{test_company_name}",
            'docname': BLOG_COMPANY_DOCNAME,
            'initial_data': company_data,
            'is_shared': False,
            'is_versioned': BLOG_COMPANY_IS_VERSIONED,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]
    
    # Cleanup configuration
cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': f"blog_company_profile_{test_company_name}",
            'docname': BLOG_COMPANY_DOCNAME,
            'is_shared': False,
            'is_versioned': BLOG_COMPANY_IS_VERSIONED,
            'is_system_entity': False
        }
    ]