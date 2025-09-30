# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the LinkedIn user input to brief workflow:
# 1. Content Playbook - Content strategy and guidelines
# 2. User Profile - User preferences and information
# These documents are loaded during the workflow for brief generation.

from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,
)

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_entity_username,
)

# Define test entity username
test_entity_username = test_sandbox_entity_username

# Create test content strategy document data
content_strategy_data = {
        "content_strategy": {
            "primary_content_pillars": [
                "Thought Leadership in Project Management",
                "AI and Automation Best Practices",
                "Team Productivity and Efficiency",
                "Remote Work Solutions"
            ],
            "target_audience": {
                "primary": "Operations Managers and Project Managers",
                "secondary": "Team Leads and CTOs at growing tech companies",
                "demographics": "50-500 employee companies in the tech sector"
            },
            "brand_voice": {
                "tone": "Expert yet approachable",
                "style": "Data-driven insights with practical examples",
                "personality": "Innovative, reliable, and forward-thinking"
            },
            "content_goals": [
                "Establish thought leadership in AI-powered project management",
                "Generate qualified leads from target audience",
                "Build brand awareness in the project management space",
                "Drive product adoption through educational content"
            ],
            "content_types": [
                "Blog posts", "LinkedIn articles", "Whitepapers", "Case studies"
            ],
            "distribution_channels": [
                "Company blog", "LinkedIn", "Industry publications", "Email newsletter"
            ]
        }
    }
    
    # Create test executive profile document data
executive_profile_data = {
        "executive_profile": {
            "name": "Alex Johnson",
            "title": "CEO & Founder",
            "company": "TechSolutions Pro",
            "industry_experience": "15 years in project management and SaaS",
            "expertise_areas": [
                "AI-powered project management",
                "Team productivity optimization",
                "Remote work culture",
                "SaaS product development"
            ],
            "thought_leadership_focus": [
                "The future of work and AI integration",
                "Building efficient remote teams",
                "Project management best practices",
                "Technology adoption in growing companies"
            ],
            "writing_style": {
                "tone": "Conversational yet authoritative",
                "approach": "Story-driven with actionable insights",
                "perspective": "Practical experience-based advice"
            },
            "personal_interests": [
                "Technology innovation",
                "Team building",
                "Work-life balance",
                "Continuous learning"
            ]
        }
    }

setup_docs: List[SetupDocInfo] = [
        {
            'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=test_entity_username),
            'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
            'initial_data': content_strategy_data,
            'is_shared': False,
            'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
            'initial_version': "default",
            'is_system_entity': False
        },
        {
            'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username),
            'docname': LINKEDIN_USER_PROFILE_DOCNAME,
            'initial_data': executive_profile_data,
            'is_shared': False,
            'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
            'initial_version': "default",
            'is_system_entity': False
        }
    ]
    
    # Cleanup configuration
cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=test_entity_username),
            'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
            'is_shared': False,
            'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
            'is_system_entity': False
        },
        {
            'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username),
            'docname': LINKEDIN_USER_PROFILE_DOCNAME,
            'is_shared': False,
            'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
            'is_system_entity': False
        }
    ]