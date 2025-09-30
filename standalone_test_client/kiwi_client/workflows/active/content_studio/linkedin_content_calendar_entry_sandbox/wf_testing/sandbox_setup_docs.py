# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the LinkedIn content calendar entry workflow:
# 1. User Profile - User preferences and posting schedule
# 2. Content Playbook - Content strategy and guidelines
# 3. Scraped Posts - Previous posts for reference
# These documents are loaded during the workflow for topic generation.

from typing import List

# Import test utilities
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    # User Profile
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_IS_VERSIONED,

    # Content Playbook
    LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
    LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE,
    LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED,

    # Scraped Posts
    LINKEDIN_SCRAPED_POSTS_DOCNAME,
    LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE,
    LINKEDIN_SCRAPED_POSTS_IS_VERSIONED,

    # LinkedIn Draft
    LINKEDIN_DRAFT_DOCNAME,
    LINKEDIN_DRAFT_NAMESPACE_TEMPLATE,
    LINKEDIN_DRAFT_IS_VERSIONED,
)

# Import sandbox identifier
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Use sandbox company name as entity username
test_entity_username = test_sandbox_company_name

setup_docs: List[SetupDocInfo] = [
    
        # User Profile Document (contains preferences)
        {
            'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_USER_PROFILE_DOCNAME,
            'initial_data': {
                "profile_url": "https://www.linkedin.com/in/mahak-vedi/",
                "username": test_entity_username,
                "persona_tags": ["RevOps Expert", "Founder", "Business Consultant"],
                "content_goals": {
                    "primary_goal": "Increase brand awareness for Revology Consulting and position Mahak as a trusted RevOps expert",
                    "secondary_goal": "Educate audience about RevOps, especially in European markets where understanding is limited"
                },
                "posting_schedule": {
                    "posts_per_week": 2,
                    "posting_days": ["Monday", "Thursday"],
                    "exclude_weekends": True
                },
                "timezone": {
                    "iana_identifier": "Europe/London",
                    "display_name": "British Summer Time",
                    "utc_offset": "+01:00",
                    "supports_dst": True,
                    "current_offset": "+01:00"
                }
            }, 
            'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'default'  # Required for versioned documents
        },
        # Content Strategy Document
        {
            'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME,
            'initial_data': {
                "title": "LinkedIn Content Strategy: Test User",
                "strategy_audience": {
                    "primary": "Small to Medium B2B Companies",
                    "secondary": "Salesforce & HubSpot Business Users",
                    "tertiary": "Enterprise B2B Companies; Agency Owners (Partnership Opportunities)"
                },
                "post_performance_analysis": {
                    "current_engagement": "Follower Count: 1,495; Network composition approximately 90% US‑based with growing presence in UK, Europe and Singapore; Posting frequency historically inconsistent but moving toward structured content pillars.",
                    "content_that_resonates": "Milestone announcements with specific metrics and emoji‑bulleted achievements; Cultural posts about personal experiences; Achievement posts averaging ~16.5 likes per post.",
                    "audience_response": "Highest impact from milestone announcements (166 likes, 130 comments). Cultural content generates significant engagement (103 likes, 24 comments). Optimum content length: ~217 words for Business & Entrepreneurship posts, ~187 words for Workplace Culture posts. Preferred format includes emoji‑bulleted lists, achievement markers with visual indicators, and short paragraphs."
                },
                "foundation_elements": {
                    "expertise": [
                        "RevOps Consulting & Implementation – 10+ years in operations with ~80 different clients over 5 years specifically on RevOps; tech‑stack assessment, consolidation and optimization; CRM expertise (Salesforce, HubSpot implementation and optimization); sales‑engagement tools (Outreach, SalesLoft).",
                        "Business Process Optimization – email personalization and outreach strategies; cross‑departmental alignment (especially sales, marketing and operations); metrics identification and tracking; automation of manual processes.",
                        "Cross‑Cultural Business Understanding – experience with US, UK, European and Asian business practices; understanding of geographical and cultural nuances in business operations; multilingual capabilities and global perspective.",
                        "Early‑Stage Founder Experience – founded Revology Consulting (1 December 2024); building a business based on expertise; developing service offerings and partnerships.",
                        "Tech Stack Security & Auditing – CRM integration security audits; identifying vulnerabilities in app access permissions; preventing data leakage through unauthorized third‑party tools; access management and security governance."
                    ],
                    "core_beliefs": [
                        "Problem‑First, Tool‑Second Approach – lead with the problem statement first instead of tooling first; avoid buying tools without understanding the exact use case.",
                        "Efficiency Through Automation – tasks taking more than 20 minutes should be automated; repetitive tasks should be eliminated through technology or process changes.",
                        "Metrics Should Drive Business Outcomes – balance leading and lagging indicators; quality of engagement matters more than quantity of activities; focus on predictive leading indicators.",
                        "Cross‑Departmental Alignment Is Essential – sales and marketing must align; technical solutions must serve broader business goals; clearly defined roles (consultant vs. contractor).",
                        "Analytical Foundation Drives Success – scientific approach to business with hypothesis testing, regular assessment and optimization, cultural awareness and adaptability.",
                        "Tech Stack Security Is Non‑Negotiable – every RevOps audit should include a security review; common vulnerability is integrations with read/write CRM access; companies must regularly audit tech‑stack access."
                    ],
                    "objectives": [
                        "Increase brand awareness for Revology Consulting and position Mahak as a trusted RevOps expert.",
                        "Educate audience about RevOps, especially in European markets where understanding is limited.",
                        "Document and share founder journey and weekly lessons learned.",
                        "Develop strategic partnerships with complementary businesses (≤10% focus).",
                        "Continue generating business through referrals (preferred business source).",
                        "Grow Mahak's personal brand alongside company reputation.",
                        "Build reputation as a source of practical advice on tech‑stack security."
                    ]
                },
                "core_perspectives": [
                    "Authority Blocks",
                    "Value Blocks", 
                    "Connection Blocks",
                    "Engagement Blocks"
                ],
                "content_pillars": [
                    {
                        "name": "Pillar 1: RevOps Education & Best Practices",
                        "pillar": "RevOps Education & Best Practices",
                        "sub_topic": [
                            "Tech stack audits and optimization",
                            "Metrics selection and tracking",
                            "Email personalization and outreach strategies",
                            "Sales and marketing alignment",
                            "Automation opportunities",
                            "Data security in operations",
                            "Leading vs. lagging indicators"
                        ]
                    },
                    {
                        "name": "Pillar 2: Founder Friday",
                        "pillar": "Founder Friday",
                        "sub_topic": [
                            "Business development challenges and solutions",
                            "Leadership and decision‑making",
                            "Work‑life balance as a founder",
                            "Client relationship management",
                            "Team building and culture development",
                            "Personal growth and reflection",
                            "Client feedback frameworks and implementation",
                            "Plant care and natural growth metaphors for business development"
                        ]
                    },
                    {
                        "name": "Pillar 3: Tool Spotlights & Partner Showcases",
                        "pillar": "Tool Spotlights & Partner Showcases",
                        "sub_topic": [
                            "CRM implementation best practices",
                            "Sales engagement tool optimization",
                            "Chrome plugin recommendations",
                            "Partner tool integrations",
                            "\"Speedy setup\" service showcases",
                            "Security risks and vulnerabilities in tech stacks",
                            "Regular security audits and access reviews"
                        ]
                    },
                    {
                        "name": "Pillar 4: Event Insights & Networking",
                        "pillar": "Event Insights & Networking",
                        "sub_topic": [
                            "Event takeaways and key learnings",
                            "Speaker insights and industry predictions",
                            "Networking experiences and opportunities",
                            "Regional business practice observations",
                            "Community‑building efforts"
                        ]
                    },
                    {
                        "name": "Pillar 5: Global RevOps Perspectives",
                        "pillar": "Global RevOps Perspectives",
                        "sub_topic": [
                            "Cultural differences in business operations",
                            "Regional approaches to sales and marketing alignment",
                            "Geographic variations in tool adoption",
                            "Work culture impacts on process implementation",
                            "Cross‑border collaboration strategies"
                        ]
                    }
                ],
                "posts_per_week": 2,
                "implementation": {
                    "thirty_day_targets": {
                        "goal": "1. Establish consistent posting rhythm across all pillars; 2. Test engagement levels for each content pillar; 3. Generate at least 5 meaningful conversations with target audience members; 4. Begin building connection with European audience through targeted content; 5. Showcase at least 2 partner relationships through Tool Spotlight pillar.",
                        "method": "Execute the Content Calendar Framework (weekly schedule) and follow the Content Creation Process (weekly planning, content development, engagement management, monthly review, feedback collection).",
                        "audience_growth": "Begin building connection with European audience through targeted content.",
                        "targets": "Generate ≥5 meaningful conversations; Showcase ≥2 partner relationships."
                    },
                    "ninety_day_targets": {
                        "goal": "1. Increase follower count by 15% (target ≈1,719 followers); 2. Establish Mahak as a recognized voice in RevOps; 3. Generate at least 3 new business inquiries directly attributed to LinkedIn content; 4. Develop 2 new strategic partnerships through LinkedIn connections; 5. Create educational content foundation explaining RevOps value for European audience.",
                        "method": "Continue executing and optimizing the Content Calendar Framework; apply insights from Monthly Reviews; leverage the Content Creation Process and daily Engagement Management.",
                        "audience_growth": "Increase follower count by 15% (target ≈1,719 followers).",
                        "targets": "Generate ≥3 business inquiries; Develop ≥2 strategic partnerships."
                    }
                }
            }, 
            'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'default'  # Required for versioned documents
        },
        # Mock LinkedIn Scraped Posts
        {
            'namespace': LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_SCRAPED_POSTS_DOCNAME,
            'initial_data': [
                {
                    "urn": "post-revops-1",
                    "text": "🔓 Security audit time! Just discovered a client had 47 people with admin access to their Salesforce instance. 47! That's not access management, that's access chaos. ✅ What we fixed: Proper role hierarchy, regular access reviews, automated deprovisioning. 🚫 What we found: Shared passwords, ex-employees still active, no MFA. #WhoStillHasYourPasswords #RevOps #TechStackSecurity",
                    "publish_date": "2024-01-15T10:00:00Z",
                    "reaction_count": 89,
                    "comment_count": 23
                },
                {
                    "urn": "post-revops-2",
                    "text": "🎉 Founder Friday update! Week 3 of Revology Consulting and I'm learning that building systems for clients is very different from building systems for your own business. The irony? I'm great at optimizing other people's tech stacks but spent 2 hours yesterday trying to connect my own CRM to my email tool. 😅 Lesson learned: Even RevOps experts need to practice what they preach. What's one system you know you should optimize but keep putting off? #FounderFriday #RevOps #Entrepreneurship",
                    "publish_date": "2024-01-12T14:30:00Z",
                    "reaction_count": 156,
                    "comment_count": 41
                }
            ], 
            'is_versioned': False,  # Assuming scraped posts are not versioned
            'is_shared': False
        },
        # Mock Draft Posts (2 examples)
        {
            'namespace': LINKEDIN_DRAFT_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_DRAFT_DOCNAME.replace('{item}', 'draft-1'),
            'initial_data': {
                "title": "Leading vs Lagging Indicators in RevOps",
                "content": "🎯 Stop measuring what happened. Start measuring what's happening. Most RevOps teams are drowning in lagging indicators: ✅ Revenue closed ✅ Deal velocity ✅ Win rates But missing the leading indicators that actually drive those outcomes: 🚀 Pipeline quality scores 🚀 Engagement velocity 🚀 Process adherence rates The difference? Lagging indicators tell you if you hit your target. Leading indicators tell you if you're aiming correctly. What leading indicators are you tracking in your RevOps? #RevOps #Metrics #DataDriven",
                "created_at": "2024-01-20T10:00:00Z",
                "updated_at": "2024-01-21T14:30:00Z",
            }, 
            'is_versioned': LINKEDIN_DRAFT_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'draft'  # Required for versioned documents
        },
        {
            'namespace': LINKEDIN_DRAFT_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_DRAFT_DOCNAME.replace('{item}', 'draft-2'),
            'initial_data': {
                "title": "Tech Stack Consolidation Reality Check",
                "content": "💡 Your tech stack isn't a collection. It's an ecosystem. Just helped a client reduce their sales tools from 12 to 4. The result? 🎉 40% faster onboarding 🎉 60% fewer integration issues 🎉 £2,400/month in savings The secret wasn't finding the 'perfect' tool. It was finding tools that actually talk to each other. Before consolidating, ask: ✅ Does this tool integrate natively? ✅ Can it replace 2+ existing tools? ✅ Will it scale with our growth? Your tech stack should amplify your team, not complicate their lives. What's one tool you could eliminate today? #TechStack #RevOps #Efficiency",
                "created_at": "2024-01-18T09:15:00Z",
                "updated_at": "2024-01-19T16:45:00Z"
            }, 
            'is_versioned': LINKEDIN_DRAFT_IS_VERSIONED, 
            'is_shared': False,
            'initial_version': 'draft'  # Required for versioned documents
        },
    ]

    # Define cleanup docs to remove test artifacts after test completion
cleanup_docs: List[CleanupDocInfo] = [

        # User Profile
        {
            'namespace': LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_USER_PROFILE_DOCNAME, 
            'is_versioned': LINKEDIN_USER_PROFILE_IS_VERSIONED, 
            'is_shared': False
        },
        # Content Strategy
        {
            'namespace': LINKEDIN_CONTENT_PLAYBOOK_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_CONTENT_PLAYBOOK_DOCNAME, 
            'is_versioned': LINKEDIN_CONTENT_PLAYBOOK_IS_VERSIONED, 
            'is_shared': False
        },
        # LinkedIn Scraped Posts
        {
            'namespace': LINKEDIN_SCRAPED_POSTS_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_SCRAPED_POSTS_DOCNAME, 
            'is_versioned': False, 
            'is_shared': False
        },
        # Draft Posts
        {
            'namespace': LINKEDIN_DRAFT_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_DRAFT_DOCNAME.replace('{item}', 'draft-1'), 
            'is_versioned': LINKEDIN_DRAFT_IS_VERSIONED, 
            'is_shared': False
        },
        {
            'namespace': LINKEDIN_DRAFT_NAMESPACE_TEMPLATE.format(item=test_entity_username), 
            'docname': LINKEDIN_DRAFT_DOCNAME.replace('{item}', 'draft-2'), 
            'is_versioned': LINKEDIN_DRAFT_IS_VERSIONED, 
            'is_shared': False
        },
    ]