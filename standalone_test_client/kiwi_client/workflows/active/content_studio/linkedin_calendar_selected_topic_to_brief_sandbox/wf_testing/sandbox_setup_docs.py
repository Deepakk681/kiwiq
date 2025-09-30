# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the LinkedIn calendar selected topic to brief workflow:
# 1. Executive Profile - Executive's information and preferences
# 2. LinkedIn Playbook - Content strategy and best practices
# These documents are loaded during the workflow for generating content briefs.

from typing import List

# Import test utilities
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    # LinkedIn User Profile
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,

    # LinkedIn playbook
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
)

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Use test entity username (for LinkedIn, we use entity_username instead of company_name)
test_entity_username = test_sandbox_company_name

# Create test executive profile data
executive_profile_data = {
    "name": "John Doe",
    "title": "Chief Revenue Officer",
    "company": test_sandbox_company_name,
    "linkedin_profile": "https://www.linkedin.com/in/johndoe",
    "bio": "Experienced CRO with 15+ years in SaaS revenue leadership.",
    "expertise": [
        "Revenue Operations",
        "Sales Strategy",
        "SaaS Growth",
        "Team Building"
    ],
    "tone_of_voice": "Professional yet approachable",
    "content_pillars": [
        "Revenue efficiency",
        "Sales automation",
        "Team leadership",
        "Industry insights"
    ],
    "target_audience": {
        "primary": "Revenue leaders and sales executives",
        "secondary": "SaaS founders and CEOs",
        "company_size": "Mid-market to Enterprise"
    }
}

# Create test playbook document data
playbook_data = {
    "playbook_name": "LinkedIn Content Best Practices",
    "content_guidelines": {
        "tone_and_voice": {
            "tone": "Professional yet conversational",
            "voice": "Expert and thought-provoking",
            "style": "Concise and actionable"
        },
        "structure_guidelines": [
            "Start with a bold statement or question",
            "Use short paragraphs and line breaks",
            "Include personal anecdotes",
            "End with a call to action or question",
            "Optimal post length: 1300 characters",
            "Use emojis sparingly and strategically",
            "Include 3-5 hashtags at the end",
            "Tag relevant people only when adding value"
        ],
        "engagement_strategies": [
            "Post during peak hours (Tue-Thu, 7:30-8:30 AM, 12 PM)",
            "Respond to comments within first hour",
            "Ask questions to encourage discussion",
            "Share insights not found elsewhere",
            "Use data and statistics to support points",
            "Include contrarian takes when appropriate"
        ]
    },
    "content_themes": {
        "thought_leadership": "Share unique perspectives on industry trends",
        "personal_stories": "Connect personal experiences to business lessons",
        "educational": "Teach something valuable in every post",
        "commentary": "Add expert analysis to current events"
    },
    "performance_metrics": {
        "engagement_benchmarks": {
            "likes": "2-5% of impressions",
            "comments": "0.5-1% of impressions",
            "shares": "0.1-0.5% of impressions"
        },
        "growth_targets": {
            "follower_growth": "10% monthly",
            "engagement_rate": "3% average"
        }
    }
}

# Define setup docs
setup_docs: List[SetupDocInfo] = [
    {
        'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': LINKEDIN_USER_PROFILE_DOCNAME,
        'initial_data': executive_profile_data,
        'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
        'is_shared': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    {
        'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
        'initial_data': playbook_data,
        'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
        'is_shared': False,
        'initial_version': "default",
        'is_system_entity': False
    }
]

# Define cleanup docs
cleanup_docs: List[CleanupDocInfo] = [
    {
        'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': LINKEDIN_USER_PROFILE_DOCNAME,
        'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
        'is_shared': False,
        'is_system_entity': False
    },
    {
        'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
        'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
        'is_shared': False,
        'is_system_entity': False
    }
]