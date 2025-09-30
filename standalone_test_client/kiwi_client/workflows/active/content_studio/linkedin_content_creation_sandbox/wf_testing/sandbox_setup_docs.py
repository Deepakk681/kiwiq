# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the LinkedIn content creation workflow:
# 1. User Profile - User preferences and information
# 2. Content Playbook - Content strategy and guidelines
# 3. LinkedIn Brief - Content brief for post creation
# These documents are loaded during the workflow for post generation.

from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,
    LINKEDIN_DRAFT_DOCNAME,
    LINKEDIN_DRAFT_NAMESPACE_TEMPLATE,
    LINKEDIN_DRAFT_IS_VERSIONED,
    LINKEDIN_BRIEF_NAMESPACE_TEMPLATE,
    LINKEDIN_BRIEF_IS_VERSIONED,
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
)

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Define test entity username
test_entity_username = test_sandbox_company_name

# Test document names
linkedin_user_profile_docname = LINKEDIN_USER_PROFILE_DOCNAME
linkedin_content_playbook_docname = LINKEDIN_CONTENT_PLAYBOOK_DOCNAME
brief_docname = f"linkedin_content_brief_{test_entity_username}_test"

# Test post UUID for draft storage
test_post_uuid = f"test_draft_{test_entity_username}_001"

# Namespace configurations
linkedin_user_profile_namespace = LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.replace("{entity_username}", test_entity_username)
content_brief_namespace = LINKEDIN_BRIEF_NAMESPACE_TEMPLATE.replace("{entity_username}", test_entity_username)
linkedin_content_playbook_namespace = LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.replace("{entity_username}", test_entity_username)
draft_storage_namespace = LINKEDIN_DRAFT_NAMESPACE_TEMPLATE.replace("{entity_username}", test_entity_username)

setup_docs: List[SetupDocInfo] = [
        # LinkedIn User Profile Document
        {
            'namespace': linkedin_user_profile_namespace,
            'docname': linkedin_user_profile_docname,
            'initial_data': {
                "name": "Example User",
                "headline": "Digital Marketing Expert | B2B SaaS Growth Strategist | Content Creator",
                "location": "San Francisco, CA",
                "industry": "Marketing & Advertising",
                "professional_background": "Digital marketing expert with 10+ years experience in B2B SaaS",
                "expertise_areas": ["Content Marketing", "Brand Development", "Social Media Strategy", "B2B Growth"],
                "target_audience": "Marketing directors and CMOs in technology companies",
                "content_goals": "Establish thought leadership and drive engagement on LinkedIn",
                "writing_style": {
                    "tone": "Professional yet conversational",
                    "voice": "Authentic and data-driven",
                    "preferred_format": "Story-driven with actionable insights"
                },
                "personal_brand_statement": "Helping tech companies build authentic marketing narratives that drive results",
                "preferred_hashtags": ["#MarketingStrategy", "#ContentCreation", "#B2BTech", "#SaaS", "#GrowthMarketing"]
            },
            'is_shared': False,
            'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
            'initial_version': "default",
            'is_system_entity': False
        },
        
        # Content Brief Document
        {
            'namespace': content_brief_namespace,
            'docname': brief_docname,
            'initial_data': {
                "uuid": brief_docname,
                "title": "Effective Content Strategy for B2B SaaS Companies",
                "core_perspective": "Content strategy should align with customer journey touchpoints",
                "key_messages": [
                    "Quality content drives better conversions than quantity",
                    "Technical content must be accessible to non-technical decision makers",
                    "Case studies with quantifiable results are the most effective B2B content"
                ],
                "target_audience": {
                    "primary": "B2B SaaS Marketing Directors",
                    "secondary": "Product Managers interested in go-to-market strategy"
                },
                "content_pillar": "B2B Content Strategy",
                "post_objectives": ["Educate audience", "Position as thought leader", "Generate discussion"],
                "tone_and_style": "Professional but approachable, data-backed with practical insights",
                "call_to_action": "Share your experience with B2B content strategy in the comments",
                "hashtags": ["#B2BMarketing", "#ContentStrategy", "#SaaS", "#MarketingROI"],
                "evidence_and_examples": ["Recent McKinsey report on B2B marketing", "HubSpot study on SaaS content"],
                "scheduled_date": "2025-05-26T10:00:00Z",
                "structure_outline": {
                    "opening_hook": "Most B2B companies treat content as a checkbox, not a conversion tool",
                    "core_perspective": "Effective B2B content aligns with specific stages of the customer journey",
                    "supporting_evidence": "Companies with documented content strategies have 3x higher conversion rates",
                    "practical_framework": "The 3T approach: Target, Tailor, Track",
                    "engagement_question": "What's your biggest challenge with B2B content development?"
                },
                "suggested_hook_options": [
                    "73% of B2B buyers don't read most of the content they download. Here's why...",
                    "If your content strategy doesn't segment by buying stage, you're leaving money on the table.",
                    "Tech companies consistently make one critical content mistake that costs them qualified leads."
                ],
                "post_length": {
                    "min": 400,
                    "max": 700
                }
            },
            'is_shared': False,
            'is_versioned': LINKEDIN_BRIEF_IS_VERSIONED,
            'initial_version': "default",
            'is_system_entity': False
        },
                 # LinkedIn Content Playbook Document - Content strategy guidelines and templates
         {
             'namespace': linkedin_content_playbook_namespace,
             'docname': linkedin_content_playbook_docname,
             'initial_data': {
                 "uuid": linkedin_content_playbook_docname,
                 "user_id": "example-user",
                 "content_strategy": {
                     "brand_positioning": "B2B SaaS marketing expert who bridges the gap between technical complexity and business results",
                     "content_pillars": [
                         "Content Strategy & ROI",
                         "B2B SaaS Marketing",
                         "Technical Content for Business Audiences",
                         "Marketing Leadership & Team Building"
                     ],
                     "posting_frequency": "3-4 posts per week",
                     "optimal_posting_times": ["Tuesday 9AM PST", "Wednesday 11AM PST", "Thursday 2PM PST"]
                 },
                 "content_templates": {
                     "hook_formulas": [
                         "{Statistic}% of {audience} {action/don't action}. Here's why...",
                         "After {time period} in {industry}, I've learned that {insight}",
                         "Most {target audience} treat {topic} as {wrong approach}. Here's what works instead:",
                         "If your {process/strategy} doesn't {key element}, you're {negative outcome}."
                     ],
                     "structure_templates": [
                         {
                             "name": "Statistical Insight Post",
                             "structure": "Hook with statistic → Personal experience → Core insight → Framework/Solution → Call to action",
                             "ideal_length": "450-600 words"
                         },
                         {
                             "name": "Framework Teaching Post",
                             "structure": "Problem statement → Personal credibility → Numbered framework → Real-world application → Engagement question",
                             "ideal_length": "400-550 words"
                         },
                         {
                             "name": "Contrarian Take Post",
                             "structure": "Common belief → Why it's wrong → Better approach → Supporting evidence → Community question",
                             "ideal_length": "350-500 words"
                         }
                     ]
                 },
                 "engagement_strategies": {
                     "question_types": [
                         "What's your biggest challenge with {topic}?",
                         "How do you handle {situation} at your company?",
                         "What's your experience with {methodology}?",
                         "Agree or disagree? {controversial statement}"
                     ],
                     "call_to_action_patterns": [
                         "Share your experience in the comments",
                         "Let's connect if you're dealing with {specific challenge}",
                         "What would you add to this framework?",
                         "Tag someone who needs to see this"
                     ]
                 },
                 "content_guidelines": {
                     "do_use": [
                         "Specific percentages and data points",
                         "Personal anecdotes with professional context",
                         "Actionable frameworks with clear steps",
                         "Industry-specific terminology when appropriate",
                         "Contrarian viewpoints backed by evidence"
                     ],
                     "avoid": [
                         "Generic motivational content",
                         "Overly technical jargon without explanation",
                         "Controversial political or social topics",
                         "Direct product promotion",
                         "Unsubstantiated claims"
                     ],
                     "hashtag_strategy": {
                         "primary_hashtags": ["#B2BMarketing", "#ContentStrategy", "#SaaS"],
                         "secondary_hashtags": ["#MarketingROI", "#B2BTech", "#ContentMarketing"],
                         "niche_hashtags": ["#SaaSMarketing", "#B2BContent", "#TechMarketing"],
                         "max_hashtags_per_post": 5,
                         "hashtag_placement": "End of post"
                     }
                 },
                 "performance_benchmarks": {
                     "engagement_targets": {
                         "likes": "50+ for tactical posts, 100+ for strategic insights",
                         "comments": "5+ meaningful conversations per post",
                         "shares": "10+ for framework/template posts"
                     },
                     "content_mix": {
                         "educational": "60%",
                         "personal_insights": "25%",
                         "industry_commentary": "15%"
                     }
                 }
             },
             'is_shared': False,
             'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
             'initial_version': "default",
             'is_system_entity': False
         }
    ]

    # Define the documents that should be cleaned up after workflow execution
cleanup_docs: List[CleanupDocInfo] = [
        # Clean up LinkedIn User Profile document
        {
            'namespace': linkedin_user_profile_namespace,
            'docname': linkedin_user_profile_docname,
            'is_shared': False,
            'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
            'is_system_entity': False
        },
        # Clean up Content Brief document
        {
            'namespace': content_brief_namespace,
            'docname': brief_docname,
            'is_shared': False,
            'is_versioned': LINKEDIN_BRIEF_IS_VERSIONED,
            'is_system_entity': False
        },
        # Clean up LinkedIn Content Playbook document
        {
            'namespace': linkedin_content_playbook_namespace,
            'docname': linkedin_content_playbook_docname,
            'is_shared': False,
            'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,
            'is_system_entity': False
        },
        # Clean up Draft document that the workflow creates
        {
            'namespace': draft_storage_namespace,
            'docname': test_post_uuid,  # Using the post_uuid as docname
            'is_shared': False,
            'is_versioned': LINKEDIN_DRAFT_IS_VERSIONED,
            'is_system_entity': False
        }
    ]