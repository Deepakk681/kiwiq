# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the LinkedIn alternate text suggestion workflow:
# 1. LinkedIn Content Playbook - User's style and tone preferences
# These documents are loaded during the workflow for generating contextual alternatives.

from typing import List

# Import test utilities
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
)

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Use sandbox company name as entity username
entity_username = test_sandbox_company_name

# Define setup docs
setup_docs: List[SetupDocInfo] = [
    {
        'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=entity_username),
        'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
        'initial_data': {
            "background": "Experienced content strategist with 10+ years in digital marketing",
            "expertise": ["Content Strategy", "Digital Marketing", "Social Media"],
            "tone_preferences": {
                "style": "Professional yet conversational",
                "voice": "Authoritative but approachable",
                "formality": "Semi-formal"
            },
            "content_goals": [
                "Establish thought leadership",
                "Share industry insights",
                "Engage with professional community"
            ],
            "target_audience": {
                "primary": "Marketing professionals",
                "secondary": "Business leaders",
                "tertiary": "Industry enthusiasts"
            }
        },
        'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
        'is_shared': False,
        'initial_version': "default",
        'is_system_entity': False
    }
]

# Define cleanup docs
cleanup_docs: List[CleanupDocInfo] = [
    {
        'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=entity_username),
        'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
        'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
        'is_shared': False,
        'is_system_entity': False
    },
]