# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the file summarisation workflow:
# 1. Test Document Data - Sample document to be summarized (Enterprise SaaS Revenue Operations guide)
# 2. Test Context Data - Additional context document for enhanced summarization
# These documents simulate real files that would be loaded and summarized based on
# the task-specific context provided by the user.

from typing import Dict, Any, List, Optional
import asyncio
import logging
import json
from datetime import datetime

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    DOCUMENT_SUMMARY_REPORT_NAMESPACE_TEMPLATE,
)

from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)

from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test identifiers
test_summary_uuid = "test_summary_001"

# Test document data for summarization
test_document_data = {
    "title": "Enterprise SaaS Revenue Operations Best Practices 2024",
    "content": """
    Enterprise SaaS companies are facing increasing pressure to optimize their revenue operations as market conditions become more challenging. This comprehensive guide outlines the key strategies and best practices that successful organizations are implementing to drive sustainable growth.

    1. Revenue Intelligence and Data Architecture
    Modern revenue operations require a sophisticated data architecture that can capture, process, and analyze customer interactions across all touchpoints. Leading organizations are investing in conversation intelligence platforms that automatically extract insights from sales calls, emails, and customer interactions.

    Key components include:
    - Automated CRM data entry and hygiene
    - Real-time deal tracking and forecasting
    - Customer conversation intelligence and insights
    - Sales process automation and optimization
    - Revenue pipeline visibility and reporting

    2. Sales Process Optimization
    Standardizing and optimizing sales processes is critical for scaling revenue operations. This involves creating repeatable methodologies for lead qualification, opportunity management, and deal closure.

    Best practices include:
    - Implementing MEDDIC or similar qualification frameworks
    - Creating standardized deal review processes
    - Establishing clear stage gate criteria
    - Developing competitive battle cards and sales playbooks
    - Regular pipeline review and forecasting cadences

    3. Customer Success Integration
    The most successful revenue operations strategies tightly integrate customer success metrics with sales performance. This creates a unified view of customer health and expansion opportunities.

    Integration strategies include:
    - Unified customer scoring models
    - Automated handoff processes from sales to customer success
    - Expansion revenue tracking and attribution
    - Churn prediction and prevention workflows
    - Product usage data integration with CRM systems

    4. Technology Stack Optimization
    Building an effective revenue operations technology stack requires careful consideration of tool integration and data flow. The goal is to create seamless workflows that minimize manual work and maximize insight generation.

    Core components typically include:
    - CRM platform (Salesforce, HubSpot, etc.)
    - Revenue intelligence platform
    - Customer success platform
    - Marketing automation tools
    - Data warehouse and analytics tools

    5. Performance Measurement and Analytics
    Establishing the right metrics and KPIs is essential for driving continuous improvement in revenue operations. Organizations should focus on both leading and lagging indicators.

    Key metrics include:
    - Sales velocity and cycle time
    - Win rates by stage and competitor
    - Customer acquisition cost and lifetime value
    - Net revenue retention and gross revenue retention
    - Sales rep ramp time and quota attainment

    6. Team Structure and Enablement
    Revenue operations success depends on having the right team structure and ensuring all team members have the skills and tools they need to succeed.

    This includes:
    - Clear role definitions and career progression paths
    - Regular training and certification programs
    - Cross-functional collaboration frameworks
    - Performance coaching and feedback processes
    - Technology adoption and change management support
    """,
    "document_type": "best_practices_guide",
    "word_count": 2847,
    "sections": [
        "Revenue Intelligence and Data Architecture",
        "Sales Process Optimization", 
        "Customer Success Integration",
        "Technology Stack Optimization",
        "Performance Measurement and Analytics",
        "Team Structure and Enablement"
    ],
    "key_topics": [
        "revenue operations",
        "sales process optimization",
        "customer success integration",
        "technology stack",
        "performance metrics",
        "team enablement"
    ]
}

# Additional context document for summarization
test_context_data = {
    "title": "Revenue Operations Metrics Framework",
    "content": "A comprehensive framework for measuring revenue operations effectiveness, including key performance indicators, benchmarking data, and best practices for metric tracking and reporting.",
    "metrics_categories": [
        "Sales Efficiency Metrics",
        "Customer Success Metrics", 
        "Revenue Quality Metrics",
        "Process Adoption Metrics"
    ],
    "benchmark_data": {
        "average_sales_cycle": "87 days for enterprise deals",
        "win_rate_benchmark": "22% for new business, 67% for expansion",
        "customer_churn_rate": "8% annual gross churn for enterprise SaaS"
    }
}

# Setup test documents
setup_docs: List[SetupDocInfo] = [
    # Main document to be summarized
    {
        'namespace': f"documents_to_summarize_{test_sandbox_company_name}",
        'docname': "enterprise_saas_revenue_ops_guide",
        'initial_data': test_document_data,
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "None",
        'is_system_entity': False
    },
    # Additional context file for enhanced summarization
    {
        'namespace': f"summary_context_files_{test_sandbox_company_name}",
        'docname': "revenue_ops_metrics_framework",
        'initial_data': test_context_data,
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "None",
        'is_system_entity': False
    }
]

# Cleanup configuration
# These docs are deleted after the workflow test is done!
cleanup_docs: List[CleanupDocInfo] = [
    {
        'namespace': f"documents_to_summarize_{test_sandbox_company_name}",
        'docname': "enterprise_saas_revenue_ops_guide",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    {
        'namespace': f"summary_context_files_{test_sandbox_company_name}",
        'docname': "revenue_ops_metrics_framework",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    }
]
