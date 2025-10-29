"""
Document setup and cleanup configuration for Blog Content Playbook Generation workflow testing.
"""

from typing import List
from kiwi_client.test_run_workflow_client import SetupDocInfo, CleanupDocInfo

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_COMPANY_IS_SHARED,
    BLOG_COMPANY_IS_VERSIONED,
    BLOG_COMPANY_IS_SYSTEM_ENTITY,
    BLOG_CONTENT_DIAGNOSTIC_REPORT_DOCNAME,
    BLOG_CONTENT_DIAGNOSTIC_REPORT_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_VERSIONED,
    BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_SHARED,
    BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_SYSTEM_ENTITY,
)

# Test parameters
test_company_name = "test_company_techventure"

# Create test company document data
company_data = {
    "company_name": "TechVenture Solutions",
    "industry": "B2B SaaS",
    "target_audience": "Small to medium businesses looking for digital transformation",
    "business_goals": [
        "Increase brand awareness in the SMB market",
        "Generate qualified leads for sales team",
        "Establish thought leadership in digital transformation"
    ],
    "current_content_challenges": [
        "Limited content creation resources",
        "Difficulty in measuring content ROI",
        "Need for more industry-specific content"
    ],
    "competitive_landscape": "Competing with larger enterprise solutions and smaller niche tools",
    "unique_value_proposition": "Enterprise-grade features at SMB pricing with exceptional customer support"
}

# Create comprehensive diagnostic report data
diagnostic_report_data = {
    "executive_summary": {
        "current_position": "TechVenture Solutions has a solid foundation in B2B SaaS content but lacks consistent thought leadership presence and measurable ROI tracking across digital channels.",
        "biggest_opportunity": "Establishing executive thought leadership through strategic content positioning and AI-optimized SEO approach to capture high-intent SMB prospects.",
        "critical_risk": "Limited content resources may result in inconsistent messaging and missed opportunities in the rapidly evolving digital transformation market.",
        "overall_diagnostic_score": 6.8
    },
    "immediate_opportunities": {
        "top_content_opportunities": [
            {
                "title": "Executive Thought Leadership Series",
                "content_type": "Long-form Articles",
                "impact_score": 9.2,
                "implementation_effort": "Medium",
                "timeline": "6-8 weeks"
            },
            {
                "title": "SMB Digital Transformation Guides",
                "content_type": "Practical Guides",
                "impact_score": 8.5,
                "implementation_effort": "High",
                "timeline": "8-12 weeks"
            },
            {
                "title": "Industry-Specific Case Studies",
                "content_type": "Case Studies",
                "impact_score": 8.8,
                "implementation_effort": "Medium",
                "timeline": "4-6 weeks"
            }
        ],
        "seo_quick_wins": [
            {
                "action": "Optimize existing content for 'digital transformation SMB' keyword cluster",
                "estimated_impact": "15-25% traffic increase",
                "timeline": "2-3 weeks"
            },
            {
                "action": "Create topic clusters around competitive advantage themes",
                "estimated_impact": "Enhanced topical authority",
                "timeline": "4-6 weeks"
            }
        ],
        "executive_visibility_actions": [
            {
                "platform": "LinkedIn",
                "action": "Launch weekly thought leadership posts on digital transformation trends",
                "frequency": "2-3 posts per week",
                "timeline": "Immediate"
            },
            {
                "platform": "Industry Publications",
                "action": "Contribute guest articles to key B2B SaaS publications",
                "frequency": "Monthly",
                "timeline": "2-4 weeks"
            }
        ],
        "ai_optimization_priorities": [
            {
                "priority": "High",
                "action": "Optimize content for AI search queries related to SMB digital transformation",
                "expected_benefit": "Improved AI visibility and citations"
            },
            {
                "priority": "Medium",
                "action": "Develop AI-friendly FAQ and resource sections",
                "expected_benefit": "Enhanced structured data for AI comprehension"
            }
        ]
    },
    "content_audit_summary": {
        "total_content_pieces": 32,
        "avg_engagement_rate": 4.2,
        "top_performing_topics": ["Digital Transformation", "SMB Solutions", "Customer Success"],
        "content_gaps": ["AI Implementation", "Security Compliance", "Integration Challenges"]
    },
    "competitive_analysis": {
        "main_competitors": ["Enterprise Corp", "NicheSoft", "BigTech Solutions"],
        "competitive_advantages": ["SMB focus", "Customer support", "Pricing flexibility"],
        "market_opportunities": ["Underserved mid-market", "Industry-specific solutions", "Integration partnerships"]
    },
    "has_insufficient_blog_and_page_count": False  # Set to False to test the normal flow (not starting from scratch)
}

# Setup test documents
setup_docs: List[SetupDocInfo] = [
    {
        'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name),
        'docname': BLOG_COMPANY_DOCNAME,
        'initial_data': company_data,
        'is_shared': BLOG_COMPANY_IS_SHARED,
        'is_versioned': BLOG_COMPANY_IS_VERSIONED,
        'initial_version': None,
        'is_system_entity': BLOG_COMPANY_IS_SYSTEM_ENTITY
    },
    {
        'namespace': BLOG_CONTENT_DIAGNOSTIC_REPORT_NAMESPACE_TEMPLATE.format(item=test_company_name),
        'docname': BLOG_CONTENT_DIAGNOSTIC_REPORT_DOCNAME,
        'initial_data': diagnostic_report_data,
        'is_shared': BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_SHARED,
        'is_versioned': BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_VERSIONED,
        'initial_version': None,
        'is_system_entity': BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_SYSTEM_ENTITY
    }
]

# Cleanup configuration
cleanup_docs: List[CleanupDocInfo] = [
    {
        'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_company_name),
        'docname': BLOG_COMPANY_DOCNAME,
        'is_shared': BLOG_COMPANY_IS_SHARED,
        'is_versioned': BLOG_COMPANY_IS_VERSIONED,
        'is_system_entity': BLOG_COMPANY_IS_SYSTEM_ENTITY
    },
    {
        'namespace': BLOG_CONTENT_DIAGNOSTIC_REPORT_NAMESPACE_TEMPLATE.format(item=test_company_name),
        'docname': BLOG_CONTENT_DIAGNOSTIC_REPORT_DOCNAME,
        'is_shared': BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_SHARED,
        'is_versioned': BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_VERSIONED,
        'is_system_entity': BLOG_CONTENT_DIAGNOSTIC_REPORT_IS_SYSTEM_ENTITY
    }
]
