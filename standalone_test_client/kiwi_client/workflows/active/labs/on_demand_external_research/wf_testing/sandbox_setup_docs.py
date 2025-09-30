# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the external research workflow:
# 1. Research Context Files - Initial context documents to enhance with external research
# 2. HITL Feedback Context Files - Additional documents for feedback revision iterations
# These documents provide the foundational context that the external research will
# enhance with targeted, value-added information from web sources.

from typing import Dict, Any, List, Optional
import asyncio
import logging
import json
from datetime import datetime

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    EXTERNAL_RESEARCH_REPORT_NAMESPACE_TEMPLATE,
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
test_research_uuid = "test_research_001"

# Test external research data for context
test_research_context_data = {
    "title": "AI Diagnostic Trends 2024",
    "content": "Recent advances in AI diagnostic tools have shown significant promise. Key developments include FDA approval of new AI-powered imaging systems, integration with electronic health records, and improved accuracy in early disease detection.",
    "key_statistics": [
        "73% increase in AI diagnostic tool approvals in 2024",
        "Medical imaging AI accuracy rates now exceed 95%",
        "40% reduction in diagnostic errors with AI assistance"
    ],
    "regulatory_updates": [
        "FDA released new guidelines for AI medical devices",
        "European Union updated medical device regulations for AI",
        "Increased focus on algorithm transparency and bias detection"
    ],
    "market_trends": [
        "Investment in AI healthcare startups reached $2.1B in 2024",
        "Major hospitals adopting AI diagnostic workflows",
        "Integration with telemedicine platforms accelerating"
    ]
}

# Additional regulatory context data
test_regulatory_data = {
    "title": "FDA AI Medical Device Regulations 2024",
    "content": "The FDA has implemented new regulatory frameworks for AI-powered medical devices, focusing on post-market monitoring and algorithm transparency.",
    "approved_devices": [
        "AI-powered retinal screening systems",
        "Machine learning ECG analysis tools",
        "Computer-aided pathology diagnosis platforms"
    ],
    "regulatory_challenges": [
        "Algorithm drift monitoring requirements",
        "Clinical validation standards for AI",
        "Data quality and bias mitigation protocols"
    ],
    "compliance_requirements": [
        "Software lifecycle processes",
        "Real-world performance monitoring", 
        "Risk management for AI algorithms"
    ]
}

# Setup test documents
setup_docs: List[SetupDocInfo] = [
    # Initial additional context file for research
    {
        'namespace': f"research_context_files_{test_sandbox_company_name}",
        'docname': "ai_diagnostic_trends_2024",
        'initial_data': test_research_context_data,
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "None",
        'is_system_entity': False
    },
    # HITL feedback additional context file
    {
        'namespace': f"research_context_files_{test_sandbox_company_name}",
        'docname': "fda_ai_medical_devices_2024",
        'initial_data': test_regulatory_data,
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
        'namespace': f"research_context_files_{test_sandbox_company_name}",
        'docname': "ai_diagnostic_trends_2024",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    {
        'namespace': f"research_context_files_{test_sandbox_company_name}",
        'docname': "fda_ai_medical_devices_2024",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    }
]
