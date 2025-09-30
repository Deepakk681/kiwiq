"""
Setup and cleanup document configurations for calendar selected topic to brief workflow testing.

This file contains the setup_docs and cleanup_docs configurations used to prepare
and tear down test documents for the workflow execution.
"""

# =============================================================================
# SETUP DOCUMENTS FOR WORKFLOW
# =============================================================================
# This file creates the following documents required for the workflow:
# 1. Company Document - Company profile and positioning information
# 2. Content Strategy/Playbook Document - Content guidelines and strategic direction
# These documents are loaded during the context loading stage of the workflow
# and provide foundational information for research and content generation.

from typing import List
from kiwi_client.test_run_workflow_client import SetupDocInfo, CleanupDocInfo

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_IS_VERSIONED,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_STRATEGY_DOCNAME,
    BLOG_CONTENT_STRATEGY_IS_VERSIONED,
    BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE,
)

# Import test identifiers
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Type definitions are now imported from kiwi_client.test_run_workflow_client


# Company document data
company_data = {
    "name": test_sandbox_company_name,
    "website_url": "https://www.momentum.io",
    "value_proposition": "AI-native Revenue Orchestration Platform that extracts, structures, and moves GTM data automatically. Momentum tracks what's said in every customer interaction and turns it into structured, usable data, updating CRM fields in real time for cleaner pipeline, better reporting, and smarter AI agents with context.",
    "company_offerings": [
        {
            "offering": "AI-powered Revenue Orchestration Platform",
            "use_case": [
                "Automated CRM data entry and hygiene",
                "Real-time deal tracking and forecasting",
                "Customer conversation intelligence and insights",
                "Sales process automation and optimization",
                "Revenue pipeline visibility and reporting"
            ],
            "ideal_users": [
                "Chief Revenue Officers",
                "VP of Sales",
                "Sales Operations Managers",
                "VP of Customer Success",
                "Revenue Operations Teams"
            ]
        },
        {
            "offering": "Conversation Intelligence and Analytics",
            "use_case": [
                "Call transcription and sentiment analysis",
                "Customer feedback extraction and categorization",
                "Competitive intelligence gathering",
                "Product feedback and feature request tracking",
                "Risk signal identification and churn prevention"
            ],
            "ideal_users": [
                "Sales Representatives",
                "Customer Success Managers",
                "Product Marketing Managers",
                "Business Development Teams",
                "Executive Leadership"
            ]
        },
        {
            "offering": "Automated GTM Data Workflows",
            "use_case": [
                "Salesforce integration and data synchronization",
                "Multi-platform data orchestration",
                "Custom field mapping and data transformation",
                "Workflow automation and trigger management",
                "Data quality monitoring and alerts"
            ],
            "ideal_users": [
                "Sales Operations Analysts",
                "CRM Administrators",
                "Revenue Operations Directors",
                "IT and Systems Integration Teams",
                "Data Analytics Teams"
            ]
        }
    ],
    "icps": [
        {
            "icp_name": "Enterprise SaaS Revenue Teams",
            "target_industry": "SaaS/Technology",
            "company_size": "Enterprise (1000+ employees)",
            "buyer_persona": "Chief Revenue Officer (CRO)",
            "pain_points": [
                "Manual, repetitive Salesforce data entry",
                "Poor CRM data hygiene and accuracy",
                "Lack of visibility into deal progression and forecast risk",
                "Difficulty extracting insights from customer conversations",
                "Revenue team inefficiencies and administrative overhead"
            ]
        },
        {
            "icp_name": "Growth-Stage Sales Organizations",
            "target_industry": "B2B SaaS",
            "company_size": "Mid-market (200-1000 employees)",
            "buyer_persona": "VP of Sales/Sales Operations",
            "pain_points": [
                "Inconsistent sales process execution",
                "Manual deal room management and collaboration",
                "Missing customer intelligence and buying signals",
                "Time-consuming post-call administrative tasks",
                "Lack of real-time coaching and performance insights"
            ]
        },
        {
            "icp_name": "Customer Success Teams",
            "target_industry": "Technology/SaaS",
            "company_size": "Mid-market to Enterprise (500+ employees)",
            "buyer_persona": "VP of Customer Success",
            "pain_points": [
                "Inability to predict and prevent customer churn",
                "Manual tracking of customer health and satisfaction",
                "Difficulty identifying expansion opportunities",
                "Lack of visibility into customer feedback and product insights",
                "Inefficient handoff processes from sales to customer success"
            ]
        }
    ],
    "content_distribution_mix": {
        "awareness_percent": 30.0,
        "consideration_percent": 40.0,
        "purchase_percent": 20.0,
        "retention_percent": 10.0
    },
    "competitors": [
        {
            "website_url": "https://www.gong.io",
            "name": "Gong"
        },
        {
            "website_url": "https://www.outreach.io",
            "name": "Outreach"
        },
        {
            "website_url": "https://www.avoma.com",
            "name": "Avoma"
        }
    ],
    "goals": [
        "Establish thought leadership in revenue intelligence and AI-powered sales automation",
        "Educate target audience about the benefits of automated GTM data workflows",
        "Generate qualified leads through valuable content addressing CRM and sales operation challenges",
        "Build brand awareness among enterprise revenue teams and sales operations professionals",
        "Create content that drives organic traffic for high-intent keywords related to revenue orchestration and conversation intelligence"
    ]
}

# Playbook document data
playbook_data = {
            "playbook_name": "Blog Content Best Practices",
            "content_guidelines": {
                "tone_and_voice": {
                    "tone": "Professional yet approachable",
                    "voice": "Expert and authoritative",
                    "style": "Clear, concise, and actionable"
                },
                "structure_guidelines": [
                    "Start with a compelling hook or statistic",
                    "Use clear headings and subheadings",
                    "Include practical examples and case studies",
                    "End with actionable takeaways",
                    "Keep paragraphs short (3-4 sentences max)"
                ],
                "seo_best_practices": [
                    "Include primary keyword in title and first paragraph",
                    "Use semantic keywords naturally throughout",
                    "Optimize meta descriptions to 155 characters",
                    "Include internal and external links",
                    "Use alt text for all images"
                ]
            },
            "content_types": {
                "thought_leadership": {
                    "word_count": "1500-2500",
                    "structure": "Problem-Solution-Impact",
                    "elements": ["Industry insights", "Original research", "Expert opinions"]
                },
                "how_to_guides": {
                    "word_count": "1000-2000",
                    "structure": "Step-by-step process",
                    "elements": ["Clear instructions", "Screenshots/visuals", "Common pitfalls"]
                },
                "case_studies": {
                    "word_count": "1200-1800",
                    "structure": "Challenge-Solution-Results",
                    "elements": ["Metrics and data", "Customer quotes", "Lessons learned"]
                }
            },
            "quality_checklist": [
                "Fact-check all statistics and claims",
                "Include relevant internal/external links",
                "Proofread for grammar and clarity",
                "Ensure mobile-friendly formatting",
                "Add compelling CTAs"
            ]
        }

# Setup test documents
setup_docs: List[SetupDocInfo] = [
    {
        'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': BLOG_COMPANY_DOCNAME,
        'initial_data': company_data,
        'is_shared': False,
        'is_versioned': BLOG_COMPANY_IS_VERSIONED,
        'initial_version': "default",
        'is_system_entity': False
    },
    {
        'namespace': BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': BLOG_CONTENT_STRATEGY_DOCNAME,
        'initial_data': playbook_data,
        'is_shared': False,
        'is_versioned': BLOG_CONTENT_STRATEGY_IS_VERSIONED,
        'initial_version': "default",
        'is_system_entity': False
    },
    # Additional user files for input node
    {
        'namespace': "user_research_files",
        'docname': "project_management_ai_research",
        'initial_data': {
            "title": "AI in Project Management: Research Insights",
            "content": "Recent studies show that 73% of project managers report improved efficiency when using AI tools for task automation. Key findings include: 1) AI reduces time spent on status updates by 40%, 2) Automated risk detection catches issues 2.5x faster than manual review, 3) Teams using AI project tools show 25% higher completion rates. However, human oversight remains critical for stakeholder communication and strategic decision-making.",
            "research_date": "2024-01-15",
            "source": "Project Management Institute Research"
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    {
        'namespace': "user_research_files",
        'docname': "remote_team_collaboration_guide",
        'initial_data': {
            "title": "Remote Team Collaboration Best Practices",
            "content": "Effective remote team collaboration requires balancing technology with human connection. Key strategies: 1) Use AI for routine tasks (scheduling, documentation) but maintain human touch for complex problem-solving, 2) Implement 'AI-first, human-verify' workflows for quality assurance, 3) Regular video check-ins preserve team cohesion, 4) AI tools should augment, not replace, human creativity and judgment.",
            "author": "Remote Work Institute",
            "publication_date": "2024-02-01"
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    # Topic HITL context files
    {
        'namespace': "topic_context_files",
        'docname': "executive_ai_framework_guide",
        'initial_data': {
            "title": "Executive AI Framework Guide",
            "content": "A comprehensive framework for executives to evaluate AI implementation: 1) Identify repetitive tasks that can be automated (80% of the work), 2) Preserve human judgment for strategic decisions (20% of the work), 3) Implement 'AI-first, human-verify' workflows, 4) Maintain human oversight for stakeholder communication and complex problem-solving.",
            "framework_sections": ["Task Classification", "Automation Guidelines", "Human Oversight Requirements"],
            "target_audience": "C-level executives and senior managers"
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    {
        'namespace': "topic_context_files",
        'docname': "remote_leadership_best_practices",
        'initial_data': {
            "title": "Remote Leadership Best Practices",
            "content": "Essential practices for leading remote teams: 1) Use AI for routine coordination but maintain human touch for team building, 2) Implement regular video check-ins to preserve team cohesion, 3) Balance automation with personal connection, 4) Ensure AI tools augment rather than replace human creativity and judgment.",
            "key_principles": ["Human-AI Balance", "Team Cohesion", "Personal Connection"],
            "implementation_tips": ["Weekly video standups", "AI-assisted scheduling", "Human-led problem solving"]
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    # Brief HITL context files
    {
        'namespace': "brief_context_files",
        'docname': "success_metrics_examples",
        'initial_data': {
            "title": "Success Metrics Examples for AI Implementation",
            "content": "Concrete metrics for measuring AI success in project management: 1) 40% reduction in time spent on status updates, 2) 25% improvement in project completion rates, 3) 2.5x faster risk detection, 4) 73% of project managers report improved efficiency, 5) 20% faster status reporting with AI assistance.",
            "metric_categories": ["Time Savings", "Quality Improvements", "Efficiency Gains"],
            "measurement_framework": "Before/after comparisons with baseline metrics"
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    {
        'namespace': "brief_context_files",
        'docname': "concrete_scenario_templates",
        'initial_data': {
            "title": "Concrete Scenario Templates for Content",
            "content": "Template scenarios for illustrating AI-human balance in project management: 1) 'Sarah's Team' - A 12-person remote team using AI for task automation while maintaining human oversight for client communication, 2) 'The 80/20 Rule in Action' - Specific examples of what gets automated vs. what stays human, 3) 'Metrics That Matter' - Real performance improvements from AI implementation.",
            "scenario_types": ["Team Examples", "Process Illustrations", "Outcome Demonstrations"],
            "usage_guidelines": "Use specific names, numbers, and outcomes for credibility"
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    },
    {
        'namespace': "brief_context_files",
        'docname': "cta_optimization_examples",
        'initial_data': {
            "title": "CTA Optimization Examples",
            "content": "High-performing call-to-action examples for AI content: 1) 'Download the AI readiness checklist and benchmark your current process' - Outcome-oriented with clear value, 2) 'Get your personalized AI implementation roadmap' - Personalized and actionable, 3) 'Join 500+ project managers using AI effectively' - Social proof with specific numbers.",
            "cta_principles": ["Outcome-focused", "Actionable", "Value-driven"],
            "optimization_tips": ["Use specific numbers", "Focus on outcomes", "Make it personal"]
        },
        'is_shared': False,
        'is_versioned': False,
        'initial_version': "default",
        'is_system_entity': False
    }
]

# Cleanup configuration
cleanup_docs: List[CleanupDocInfo] = [
    {
        'namespace': BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': BLOG_COMPANY_DOCNAME,
        'is_shared': False,
        'is_versioned': BLOG_COMPANY_IS_VERSIONED,
        'is_system_entity': False
    },
    {
        'namespace': BLOG_CONTENT_STRATEGY_NAMESPACE_TEMPLATE.format(item=test_sandbox_company_name),
        'docname': BLOG_CONTENT_STRATEGY_DOCNAME,
        'is_shared': False,
        'is_versioned': BLOG_CONTENT_STRATEGY_IS_VERSIONED,
        'is_system_entity': False
    },
    # Cleanup additional user files
    {
        'namespace': "user_research_files",
        'docname': "project_management_ai_research",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    {
        'namespace': "user_research_files",
        'docname': "remote_team_collaboration_guide",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    # Cleanup topic HITL context files
    {
        'namespace': "topic_context_files",
        'docname': "executive_ai_framework_guide",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    {
        'namespace': "topic_context_files",
        'docname': "remote_leadership_best_practices",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    # Cleanup brief HITL context files
    {
        'namespace': "brief_context_files",
        'docname': "success_metrics_examples",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    {
        'namespace': "brief_context_files",
        'docname': "concrete_scenario_templates",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    },
    {
        'namespace': "brief_context_files",
        'docname': "cta_optimization_examples",
        'is_shared': False,
        'is_versioned': False,
        'is_system_entity': False
    }
]