"""
Document setup and cleanup configuration for LinkedIn Content Playbook Generation workflow testing.
"""

from typing import List
from kiwi_client.test_run_workflow_client import SetupDocInfo, CleanupDocInfo

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_SHARED,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,
    LINKEDIN_USER_PROFILE_IS_SYSTEM_ENTITY,
    LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_DOCNAME,
    LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_VERSIONED,
    LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_SHARED,
    LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_SYSTEM_ENTITY,
)

# Test parameters
test_entity_username = "test_linkedin_user_sarah_chen"

# Create test LinkedIn profile document data
linkedin_profile_data = {
    "entity_username": test_entity_username,
    "company_name": "TechVenture Solutions",
    "industry": "B2B SaaS",
    "company_size": "50-200 employees",
    "target_audience": "C-suite executives and decision makers in mid-market companies",
    "business_model": "SaaS subscription with professional services",
    "business_goals": [
        "Build founder personal brand and thought leadership",
        "Generate enterprise leads through LinkedIn content",
        "Establish industry authority in digital transformation",
        "Attract top-tier talent and strategic partnerships"
    ],
    "current_content_challenges": [
        "Low LinkedIn engagement rates (under 2%)",
        "Difficulty converting connections to qualified leads",
        "Inconsistent posting schedule and content quality",
        "Limited reach beyond existing network"
    ],
    "competitive_landscape": "Competing with established enterprise players like Salesforce and emerging AI-first startups",
    "unique_value_proposition": "Only platform combining AI automation with human expertise specifically for mid-market digital transformation",
    "founder_profile": {
        "name": "Sarah Chen",
        "title": "CEO & Founder",
        "background": "Former CTO at Fortune 500 company, 15+ years in enterprise technology",
        "expertise": ["Digital transformation", "AI implementation", "Scaling operations", "Enterprise architecture"],
        "personality": "Technical but approachable, data-driven decision maker, authentic thought leader",
        "linkedin_followers": 3500,
        "current_posting_frequency": "2-3 times per week",
        "top_content_topics": ["AI trends", "Leadership lessons", "Company updates"]
    },
    "content_preferences": {
        "preferred_content_types": ["Educational posts", "Behind-the-scenes stories", "Industry insights"],
        "tone_of_voice": "Professional yet conversational, authentic, data-backed",
        "content_pillars": ["Innovation", "Leadership", "Digital Transformation", "Team Building"],
        "posting_frequency_goal": "Daily during weekdays"
    },
    "business_context": {
        "recent_milestones": ["Series A funding", "50% team growth", "Major enterprise client wins"],
        "upcoming_goals": ["Product launch", "Market expansion", "Team scaling"],
        "key_metrics": {
            "monthly_revenue": "$2.5M ARR",
            "customer_count": 150,
            "team_size": 85
        }
    }
}

# Create comprehensive diagnostic report data for LinkedIn
diagnostic_report_data = {
    "executive_summary": {
        "current_position": "TechVenture Solutions founder has moderate LinkedIn presence but lacks strategic content approach, missing significant thought leadership opportunities in the competitive B2B SaaS space.",
        "biggest_opportunity": "Building authentic founder-led content strategy leveraging technical expertise and recent business milestones to drive qualified enterprise leads and attract top talent.",
        "critical_risk": "Competitors are rapidly building LinkedIn authority while TechVenture remains underutilized in key industry conversations, potentially losing market positioning.",
        "overall_diagnostic_score": 6.2,
        "key_findings": [
            "Strong technical credibility but limited personal brand visibility",
            "Inconsistent content strategy limiting reach and engagement",
            "Untapped potential for thought leadership in AI/digital transformation"
        ]
    },
    "immediate_opportunities": {
        "top_content_opportunities": [
            {
                "title": "Founder Journey & Transparency",
                "content_type": "Personal Stories + Business Lessons",
                "impact_score": 9.5,
                "implementation_effort": "Low",
                "timeline": "2-3 weeks",
                "reasoning": "Authentic founder stories resonate strongly with target audience and build trust"
            },
            {
                "title": "Technical Deep Dives & Education",
                "content_type": "Educational Posts & Tutorials",
                "impact_score": 8.8,
                "implementation_effort": "Medium",
                "timeline": "4-6 weeks",
                "reasoning": "Technical expertise differentiates from competitors and establishes authority"
            },
            {
                "title": "Customer Success Spotlights",
                "content_type": "Case Studies & Success Stories",
                "impact_score": 9.0,
                "implementation_effort": "Medium",
                "timeline": "3-4 weeks",
                "reasoning": "Social proof drives conversion and showcases real business value"
            },
            {
                "title": "Industry Contrarian Views",
                "content_type": "Opinion Leadership",
                "impact_score": 8.5,
                "implementation_effort": "High",
                "timeline": "6-8 weeks",
                "reasoning": "Well-reasoned contrarian views generate engagement and position as thought leader"
            }
        ],
        "linkedin_quick_wins": [
            {
                "action": "Optimize founder profile with strategic keywords and compelling headline",
                "estimated_impact": "3x profile views in 30 days",
                "timeline": "1 week",
                "effort": "Low"
            },
            {
                "action": "Launch weekly thought leadership series on AI in enterprise",
                "estimated_impact": "5x engagement rate increase",
                "timeline": "2 weeks",
                "effort": "Medium"
            },
            {
                "action": "Create content calendar with consistent posting schedule",
                "estimated_impact": "Improved reach and follower growth",
                "timeline": "1 week",
                "effort": "Low"
            }
        ],
        "executive_visibility_actions": [
            {
                "platform": "LinkedIn",
                "action": "Daily engagement with target audience posts and industry conversations",
                "frequency": "30 minutes daily",
                "timeline": "Immediate",
                "impact": "Increased visibility and network growth"
            },
            {
                "platform": "LinkedIn Newsletter",
                "action": "Launch bi-weekly industry insights newsletter",
                "frequency": "Bi-weekly",
                "timeline": "3 weeks",
                "impact": "Direct communication channel with audience"
            },
            {
                "platform": "LinkedIn Events",
                "action": "Host monthly virtual events on digital transformation",
                "frequency": "Monthly",
                "timeline": "6 weeks",
                "impact": "Position as industry convener and expert"
            }
        ]
    },
    "content_audit_summary": {
        "analysis_period": "Last 90 days",
        "total_posts_last_90_days": 24,
        "avg_engagement_rate": 3.2,
        "follower_growth_rate": 8.5,
        "reach_metrics": {
            "avg_impressions_per_post": 1250,
            "avg_clicks_per_post": 45,
            "avg_comments_per_post": 8
        },
        "top_performing_topics": [
            {"topic": "AI Implementation", "avg_engagement": 4.8},
            {"topic": "Team Building", "avg_engagement": 4.2},
            {"topic": "Product Updates", "avg_engagement": 3.1}
        ],
        "content_gaps": [
            "Thought Leadership on industry trends",
            "Personal insights and founder journey",
            "Customer success stories and case studies",
            "Technical tutorials and educational content"
        ],
        "posting_patterns": {
            "best_posting_times": ["Tuesday 9AM", "Thursday 2PM", "Friday 10AM"],
            "content_type_performance": {
                "text_posts": 3.8,
                "image_posts": 2.9,
                "video_posts": 5.2,
                "document_posts": 4.1
            }
        }
    },
    "competitive_analysis": {
        "main_competitors_linkedin": [
            {
                "name": "TechCorp CEO",
                "followers": 52000,
                "posting_frequency": "Daily",
                "engagement_rate": 4.2,
                "content_focus": "Industry trends and company culture"
            },
            {
                "name": "InnovateSoft Founder",
                "followers": 38000,
                "posting_frequency": "3-4x per week",
                "engagement_rate": 3.8,
                "content_focus": "Technical deep dives and product demos"
            }
        ],
        "competitive_advantages": [
            "Deep technical expertise with business acumen",
            "Authentic founder story with recent milestones",
            "Unique positioning in mid-market digital transformation",
            "Strong customer success stories and case studies"
        ],
        "content_opportunities": [
            "Technical tutorials that competitors avoid",
            "Contrarian viewpoints on industry trends",
            "Behind-the-scenes content from scaling a startup",
            "Data-driven insights from customer implementations"
        ],
        "market_positioning": {
            "current_position": "Under-recognized technical expert",
            "target_position": "Leading voice in mid-market digital transformation",
            "differentiation_strategy": "Combine technical depth with business results"
        }
    },
    "recommendations": {
        "content_strategy": "Focus on authentic founder journey combined with technical expertise",
        "posting_frequency": "5-7 posts per week with mix of content types",
        "engagement_strategy": "Proactive commenting and conversation starting",
        "growth_targets": {
            "followers": "10K in 6 months",
            "engagement_rate": "5%+ average",
            "leads_generated": "50+ qualified leads per quarter"
        }
    },
    "has_insufficient_blog_and_page_count": False  # Set to False to test the normal flow (not starting from scratch)
}

# Setup test documents
setup_docs: List[SetupDocInfo] = [
    {
        'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username),
        'docname': LINKEDIN_USER_PROFILE_DOCNAME,
        'initial_data': linkedin_profile_data,
        'is_shared': LINKEDIN_USER_PROFILE_IS_SHARED,
        'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
        'initial_version': None,
        'is_system_entity': LINKEDIN_USER_PROFILE_IS_SYSTEM_ENTITY
    },
    {
        'namespace': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_NAMESPACE_TEMPLATE.format(item=test_entity_username),
        'docname': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_DOCNAME,
        'initial_data': diagnostic_report_data,
        'is_shared': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_SHARED,
        'is_versioned': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_VERSIONED,
        'initial_version': None,
        'is_system_entity': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_SYSTEM_ENTITY
    }
]

# Cleanup configuration
cleanup_docs: List[CleanupDocInfo] = [
    {
        'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username),
        'docname': LINKEDIN_USER_PROFILE_DOCNAME,
        'is_shared': LINKEDIN_USER_PROFILE_IS_SHARED,
        'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED,
        'is_system_entity': LINKEDIN_USER_PROFILE_IS_SYSTEM_ENTITY
    },
    {
        'namespace': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_NAMESPACE_TEMPLATE.format(item=test_entity_username),
        'docname': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_DOCNAME,
        'is_shared': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_SHARED,
        'is_versioned': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_VERSIONED,
        'is_system_entity': LINKEDIN_CONTENT_DIAGNOSTIC_REPORT_IS_SYSTEM_ENTITY
    }
]
