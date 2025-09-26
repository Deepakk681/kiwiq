"""
Content Research & Brief Generation Workflow

This workflow enables comprehensive content research and brief generation with:
- User input collection and company context loading
- Google web search research with real-time data
- Reddit research using Perplexity for user insights
- AI-generated blog topic suggestions
- Human-in-the-loop topic selection
- Comprehensive content brief generation
- Human-in-the-loop brief approval with support for manual edits
- Document storage and output management

Key Features:
- Real web search capabilities for Google and Reddit
- Structured output schemas for each research phase
- HITL approval flows for topic selection and brief approval (with manual editing support)
- Company context integration throughout the process
- Comprehensive content brief generation with SEO, brand guidelines, and structure
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflow testing utilities
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

# Import document model constants
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_IS_VERSIONED,
    BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
    BLOG_CONTENT_BRIEF_DOCNAME,
    BLOG_CONTENT_BRIEF_IS_VERSIONED,
    BLOG_CONTENT_STRATEGY_DOCNAME,
    BLOG_CONTENT_STRATEGY_IS_VERSIONED
)


BRIEF_HITL_INPUT = {
    "title": "Choosing Your First Bookkeeping Platform: Integration, Automation, and What Founders Wish They Knew",
    "content_goal": "Empower founders and operations managers at small-to-mid-sized professional services firms to confidently choose, integrate, and scale with a modern bookkeeping platform, highlighting the pitfalls of fragmented workflows and the advantages of founder-friendly, all-in-one tools (with TryFondo positioned as the best-in-class solution).",
    "seo_keywords": {
      "primary_keyword": "best bookkeeping platform for startups",
      "long_tail_keywords": [
        "bookkeeping tool for founders",
        "how to integrate bookkeeping with other tools",
        "bookkeeping vs accounting for startups",
        "automated bookkeeping software for small business",
        "bookkeeping 101 for startups"
      ],
      "secondary_keywords": [
        "simplest bookkeeping software for founders",
        "startup bookkeeping checklist",
        "monthly bookkeeping best practices",
        "startup tax credits bookkeeping",
        "streamlined bookkeeping workflows",
        "QuickBooks vs Xero vs TryFondo",
        "integrated business bookkeeping",
        "bookkeeping automation"
      ],
      "search_intent_analysis": "User searches cluster around 'how to choose bookkeeping software', 'best bookkeeping tool for startups', 'bookkeeping basics', and 'integration/automation'. Reddit users frequently ask for simple, stepwise, jargon-free advice and compare how platforms fit into daily founder workflows, with high anxiety about compliance, integration, and hidden costs. Search intent is a blend of navigational ('best platform'), informational ('how to integrate'), and comparison ('QuickBooks vs Xero vs TryFondo'), all leading to platform selection and implementation.",
      "primary_keyword_reasoning": "The primary keyword directly serves high-intent, bottom-of-funnel founders actively researching which bookkeeping solution to choose for their new or growing business—matching playbook goals around BOFU traffic, comparison, and conversion. This aligns with both Google search patterns and Reddit user language ('best bookkeeping platform for startups', 'which tool is best').",
      "reddit_language_incorporated": [
        "\"Which tool is best for...\"",
        "\"How do I keep track of...\"",
        "\"streamlined bookkeeping workflows\"",
        "\"monthly bookkeeping\"",
        "\"integrate bookkeeping with other tools\"",
        "\"bookkeeping 101 for startups\"",
        "\"automate data entry between tools\""
      ],
      "secondary_keywords_reasoning": [
        "Each reflects actual Reddit and Google phrasing and expands topical depth for semantic relevance, providing rank-potential for both main and supporting queries (e.g., 'startup bookkeeping checklist' and 'integrated business bookkeeping' are direct from user requests). 'QuickBooks vs Xero vs TryFondo' meets comparison/playbook needs. 'startup tax credits bookkeeping' and 'monthly bookkeeping best practices' serve high-urgency informational needs identified in PAA and Reddit."
      ]
    },
    "key_takeaways": [
      "Founders are overwhelmed by bookkeeping tool complexity—simple, all-in-one, integrated platforms (like TryFondo) provide massive relief and efficiency gains.",
      "Consistent, monthly bookkeeping is essential for compliance, maximizing tax credits, and keeping founders investor-ready.",
      "The right bookkeeping platform should offer seamless integrations (CRM, payroll, invoicing) to eliminate double entry and disjointed workflows.",
      "Automation and intuitive dashboards drive higher founder adoption, reduce errors, and save time—making manual spreadsheet tracking and siloed tools obsolete.",
      "Choosing a scalable, all-in-one bookkeeping solution early prevents costly migration headaches and lost visibility as your business grows."
    ],
    "call_to_action": "Ready to simplify your books and supercharge your startup’s operations? Book a demo with TryFondo today or download our founder-friendly bookkeeping checklist to get started.",
    "goal_reasoning": "This goal addresses urgent founder pain points identified in Reddit and Google research—confusion, overwhelm, and anxiety about bookkeeping and compliance—while mapping directly to TryFondo's company objectives around brand authority, user acquisition, and driving demo/bookings from comparison and educational content. The goal also supports the Migration Magnet play with a clear funnel to conversion.",
    "target_audience": "Startup founders, operations managers, and business leaders at small-to-mid-sized professional services firms (10–200 employees), especially those feeling overwhelmed by tool fragmentation and low process adoption, who are actively researching how to choose and implement their first or next bookkeeping platform.",
    "title_reasoning": "Title mirrors language directly from user research—'Choosing Your First Bookkeeping Platform', 'integration', 'automation', and 'what founders wish they knew'—addressing both educational and comparison search intent (supported by both Google PAA and Reddit phrasing). The title sets up authority and delivers a promise of both insight and actionable guidance for the target audience.",
    "brand_guidelines": {
      "tone": "Empathetic, jargon-free, practical, authoritative, and founder-centric.",
      "voice": "Mentoring, transparent, and action-oriented—speaking as an experienced operator or trusted advisor rather than a detached accountant.",
      "style_notes": [
        "Avoid jargon—explain concepts in plain language.",
        "Prioritize checklists, callouts, real founder dilemmas, and step-by-step clarity.",
        "Balance warmth and expertise; admit common mistakes, then provide clear solutions.",
        "Highlight TryFondo differentiators with evidence, not just claims.",
        "Include real/fictitious founder scenarios reflecting Reddit pain points."
      ],
      "tone_reasoning": "Reddit and Google research repeatedly signal a craving for clarity and empathy—founders are 'lost', 'overwhelmed', and fear making mistakes. The playbook demands content that feels accessible and confidence-building, fostering trust and credibility critical for BOFU content and supporting decent conversion rates.",
      "voice_reasoning": "The mentoring, practical voice positions TryFondo as a peer and advocate for the reader (e.g., 'here’s what experienced founders wish they'd done differently'), which drives differentiation versus algorithmic or technical competitor posts. This is consistent with TryFondo’s 'founder-friendly' brand and the Migration Magnet/Vertical Authority plays.",
      "differentiation_elements": [
        "Explicit, comparative discussion of how TryFondo solves founder integration pain ('one login, one dashboard, all-in-one').",
        "Highlight of workflow automation and no-spreadsheet, no-code adoption.",
        "Founder testimonial snippets or user quotes reflecting actual Reddit/Google pain points.",
        "Customization and practical roadmap checklists (not just feature lists)."
      ]
    },
    "difficulty_level": "Beginner to Intermediate (accessible for non-accountants but with intermediate options/scenarios included for scaling founders)",
    "research_sources": [
      {
        "source": "TryFondo Website (https://www.tryfondo.com)",
        "how_to_use": "Embed screenshots or descriptions of TryFondo’s core features (integrated platform, dashboard, automation, tax credits) and direct solution statements for each pain point described.",
        "key_insights": [
          "All-in-one accounting platform for startups—bookkeeping, tax, and tax credits handled in one place.",
          "Average customer receives $21,000/year in tax credits—streamlined via automated reporting.",
          "Platform includes customizable, on-demand financial reporting tailored for founder needs."
        ],
        "citations_to_include": [
          "\"Fondo is an all-in-one accounting platform for startups. We'll handle your bookkeeping, tax, and tax credits so you can focus on building your startup.\"",
          "\"The average Fondo customer gets back $21,000 each year.\""
        ]
      },
      {
        "source": "TryFondo What's New (https://www.tryfondo.com/whats-new)",
        "how_to_use": "Reference latest features (customizable financial reports, pre-set group lists for reporting), and explain how these deliver on common founder efficiency and integration needs as described in Reddit/Google research.",
        "key_insights": [
          "Customized financial reports available on demand—crucial for stakeholder communication.",
          "Easy sharing/permissions and automation for regular reporting cycles."
        ],
        "citations_to_include": [
          "\"Create customized financial reports effortlessly with our new Fondo Reporting feature.\""
        ]
      },
      {
        "source": "Y Combinator Fondo profile (https://www.ycombinator.com/companies/fondo)",
        "how_to_use": "Cite FAQ content about tax filing requirements and direct financial impact (missed credits, compliance). Reinforce urgency and stakes for not doing monthly bookkeeping.",
        "key_insights": [
          "\"Do I Need to File Taxes for My Startup?\" Yes. Once your startup is incorporated and funded, filing taxes is crucial.",
          "Failing to file on time can mean missing out on up to $500k in tax credits."
        ],
        "citations_to_include": [
          "\"Failing to file on time can mean missing out on up to $500k in tax credits.\""
        ]
      },
      {
        "source": "BetterBuyer: Overview of bookkeeping software (https://www.betterbuyer.com/accounting/x8k9i-fondo)",
        "how_to_use": "Frame TryFondo’s integrated approach against a checklist of typical SMB accounting needs (tax planning, payroll, automation, controls).",
        "key_insights": [
          "Innovation and integration as core differentiators.",
          "Broader service scope vs. single-point competitors."
        ],
        "citations_to_include": [
          "\"Fondo... is a pioneering firm known for its steadfast dedication to innovation and cutting-edge solutions.\""
        ]
      },
      {
        "source": "Reddit discussions (r/startups, r/smallbusiness, r/accounting, via post links)",
        "how_to_use": "Integrate citations and paraphrased experiences: real user pain points about integration, tool confusion, checklists, and the value of founder testimonials.",
        "key_insights": [
          "Founders use language like 'overwhelmed', 'confusing', 'need a checklist', and directly request side-by-side comparisons.",
          "There's high anxiety about compliance, monthly routines, and automation."
        ],
        "citations_to_include": [
          "\"What’s the easiest way to get started with bookkeeping?\"",
          "\"Is there a checklist for bookkeeping for founders?\"",
          "\"How do I integrate bookkeeping with my CRM and payroll systems?\""
        ]
      }
    ],
    "content_structure": [
      {
        "section": "Introduction: Why Bookkeeping is the Founder’s Blind Spot—and the Secret to Startup Success",
        "word_count": 250,
        "description": "Set the stage with emotional and practical evidence: founders are overwhelmed, and the right bookkeeping strategy is the foundation for stress-free, scalable growth. Preview that this guide blends step-by-step clarity, real founder pain points, and actionable solutions.",
        "research_support": [
          "Reddit: Founders feel 'lost' and 'overwhelmed' (14 mentions: 'Bookkeeping 101 for startups—where do I start?')",
          "Google PAA: 'What is bookkeeping and why is it important for startups?'",
          "TryFondo: Automation and stress-free reporting as differentiators"
        ],
        "section_reasoning": "Reddit/Google show high emotional urgency and confusion—an empathetic intro builds trust and sets the hook for the rest of the guide, consistent with playbook/brand guidance for founder-centric, accessible content.",
        "user_questions_answered": [
          "Why is bookkeeping such a pain point for founders?",
          "Does it really matter which tool or process I choose at the start?"
        ]
      },
      {
        "section": "Bookkeeping 101: What Founders Actually Need to Track (with Plain-Language Checklist)",
        "word_count": 350,
        "description": "Demystify basic bookkeeping concepts—revenues, expenses, tax obligations—in simple language and provide a founder-ready checklist, mapping against compliance, tax credits, and fundraising/investor needs.",
        "research_support": [
          "Reddit: Founders beg for simple, stepwise checklists ('Is there a checklist for...?', 'What do I need to track as a founder?')",
          "Google PAA: 'What are the best bookkeeping practices for new businesses?'",
          "TryFondo/YCombinator: Importance of tracking for tax credits and compliance"
        ],
        "section_reasoning": "Direct research signals that founders are anxious about missing steps and compliance— a plain-language, actionable checklist is the single most requested content type. Aligned with playbook goals for practical, authority-building BOFU assets.",
        "user_questions_answered": [
          "What do I need to track for my business bookkeeping?",
          "Is there a simple checklist for startup bookkeeping?",
          "How do I set up my books with no accounting background?"
        ]
      },
      {
        "section": "Why Consistency Matters: Monthly Bookkeeping, Compliance, and Avoiding Tax Headaches",
        "word_count": 300,
        "description": "Explain the consequences of falling behind, the importance of regular cadence (monthly/quarterly), and the risks of scrambling at year-end. Highlight TryFondo's automation and reporting features that solve these problems.",
        "research_support": [
          "Reddit: High anxiety about 'catch up', penalties, and workflow snowball ('Do I need monthly bookkeeping?', 'What happens if I skip a month?')",
          "TryFondo/YCombinator: 'Failing to file on time can mean missing out on up to $500k in tax credits.'",
          "Instagram founder tip: Monthly bookkeeping is a smart move."
        ],
        "section_reasoning": "Research and Reddit show that fear of non-compliance and the snowball effect of procrastination are top emotional pain points—addressing these directly is essential for both utility and empathy.",
        "user_questions_answered": [
          "How often should I do bookkeeping?",
          "What happens if I fall behind?",
          "How do I catch up if I’m behind on bookkeeping?"
        ]
      },
      {
        "section": "How to Pick the Right Bookkeeping Platform: Avoiding Founder Pitfalls",
        "word_count": 350,
        "description": "Stepwise, founder-first criteria for evaluating bookkeeping software—ease of use, integration, automation, and support. Transparent comparison table: TryFondo vs. QuickBooks vs. Xero. Embed real Reddit pain points and highlight TryFondo’s integration and UX advantages.",
        "research_support": [
          "Reddit: Direct requests for 'which tool is best', 'which integrates with my CRM/payroll', and desire for comparison grids.",
          "Google: BOFU search intent for 'best bookkeeping tool for startups', 'QuickBooks vs TryFondo'",
          "BetterBuyer: Feature-matrix framing for comparison."
        ],
        "section_reasoning": "Choosing a platform is the crux of the user journey and the primary search intent trigger for conversions and BOFU value. Explicit comparison and criteria tables resonate with user patterns and search demand, reflecting the Migration Magnet play.",
        "user_questions_answered": [
          "Which bookkeeping tool or software is best for my startup?",
          "How do I choose between different accounting platforms?",
          "What makes an all-in-one platform better than point solutions?",
          "How do these platforms integrate with my existing tools?"
        ]
      },
      {
        "section": "Integration & Automation: How to Connect Bookkeeping With Founder Workflows (and Why It Matters)",
        "word_count": 350,
        "description": "Show, with practical founder scenarios, how integrated platforms eliminate double entry, reduce errors, and let startups scale pain-free. Use TryFondo’s actual integrations (payroll, CRM, invoicing) and automation as the proofpoint; offer a stepwise chart/checklist for connecting key workflows.",
        "research_support": [
          "Reddit: Multiple threads and direct language ('Is there a way to automate data entry between tools?', 'How do I integrate bookkeeping with my other business workflows?')",
          "TryFondo site: Core differentiation is workflow integration and automation.",
          "Google PAA: 'How can startups maximize tax credits through bookkeeping?' (integration = error reduction = more credits)"
        ],
        "section_reasoning": "Integration and automation are the painkiller features founders ask for, and TryFondo’s core competitive advantage. Illustrating seamless integrations meets both emotional and technical needs and aligns perfectly with playbook recommendations for practical, actionable content.",
        "user_questions_answered": [
          "How do I integrate bookkeeping with my other business workflows?",
          "Is there a way to automate data entry between tools?",
          "Which platform has the best integrations for startups?"
        ]
      },
      {
        "section": "Scaling Up: Why 'Founder-Friendly' Means Thinking Beyond Today—and Preventing Future Headaches",
        "word_count": 250,
        "description": "Discuss the importance of betting on scalable, all-in-one tools (like TryFondo) to avoid future migration pain, platform fatigue, and lost visibility as more staff and tools are added.",
        "research_support": [
          "Reddit: Founders who outgrow spreadsheets or migrate complain about 'messy transitions' and regret not investing in integrated tools earlier.",
          "TryFondo: Platform designed to scale with growing teams (CRM/payroll/invoicing, inviting more users, permissioning)."
        ],
        "section_reasoning": "Reddit patterns warn of costly platform switches and loss of visibility. Playbook stresses educating users on the dangers of disjointed workflows and the value of making the right tech bets early ('defensible authority').",
        "user_questions_answered": [
          "Will I outgrow my bookkeeping tool?",
          "How do I avoid switching headaches as my startup scales?",
          "Is TryFondo actually built for agencies/consulting/staffing as well as founders?"
        ]
      },
      {
        "section": "Founder FAQs: Real-World Objections, Mistakes, and Quick Wins",
        "word_count": 300,
        "description": "A rapid-fire FAQ block answering 8–12 common Reddit/Google questions—from tool cost to compliance, tax credit requirements, integrations, and self-service resources. Link to deeper guides and offer a downloadable checklist here.",
        "research_support": [
          "Reddit: High-frequency, direct questions ('Is it risky to DIY? When do I need an accountant? How do I keep my books investor-ready?')",
          "Google PAA: Patterns dictate FAQ-format inclusion for both user utility and FAQ schema/AI citation potential.",
          "Playbook: All head-to-head, guide, and comparison content must have a robust FAQ module."
        ],
        "section_reasoning": "Addressing direct objections and mistakes captures long-tail search and user language, supports time-on-page and AI citation, and is an essential structural requirement per the playbook.",
        "user_questions_answered": [
          "Do I need a bookkeeper or accountant, or can I do it myself?",
          "How much does it cost to outsource bookkeeping?",
          "What’s"
        ]
      }
    ]
  }

TOPIC_HITL_INPUT = {
    "suggested_blog_topics": [
      {
        "angle": "How successful OnDeck companies actually handle their books—the patterns, tools, and shortcuts that we have seen work.",
        "title": "Bookkeeping for Startups: What we learned from helping 100 OnDeck founders?",
        "topic_id": "topic_01",
        "seo_opportunity": "Capture high-intent searches on 'bookkeeping 101 for startups', 'startup bookkeeping checklist', and long-tail onboarding queries.",
        "topic_reasoning": "Both Google and Reddit research make it clear that new startup founders are overwhelmed by bookkeeping jargon and crave a comprehensive, stepwise, and jargon-free beginner’s guide. High-frequency Reddit questions and PAA data demonstrate urgent need for actionable education. By mirroring the clarity and credibility of OnDeck’s handbook style, TryFondo can own the 'Bookkeeping 101' category with a best-in-class resource that answers top user intents and SEO demand.",
        "research_citations": [
          "Reddit: 'What are the absolute basics of bookkeeping for a new startup?' (14 mentions, e.g., https://www.reddit.com/r/startups/comments/18v9k8w/bookkeeping_101_for_new_startup/)",
          "Google PAA: 'What is bookkeeping and why is it important for startups?'",
          "TryFondo site: Automated, customizable onboarding and checklists (https://www.tryfondo.com/whats-new)",
          "User language pattern: frequent demand for 'simple checklist', 'first steps', 'jargon-free guidance'"
        ],
        "user_questions_addressed": [
          "How do I set up my books as a founder with no accounting background?",
          "Is there a simple checklist for startup bookkeeping?",
          "What do I need to track for my business bookkeeping?",
          "What are the first steps to get my bookkeeping right from day one?"
        ],
        "company_expertise_showcase": "Showcases TryFondo’s approach to beginner-friendly onboarding, customizable checklists, and plain-language support, affirming its reputation as an educator and trusted operational platform for startups. Leverages TryFondo’s reporting and automation capabilities to demystify bookkeeping with practical workflows."
      },
      {
        "angle": "A tactical guide for busy founders on maintaining monthly bookkeeping discipline—with recovery steps and stress-reduction tips for when you fall behind.",
        "title": "Never Fall Behind Again: Monthly Bookkeeping Habits and Catch-Up Strategies for Startups",
        "topic_id": "topic_02",
        "seo_opportunity": "Targets 'how often should I do bookkeeping?', 'monthly bookkeeping for startups', and 'what if I fall behind on bookkeeping?'—topics with both high user urgency and search volume.",
        "topic_reasoning": "Anxiety about falling behind on bookkeeping is a top emotional and practical trigger found in Reddit posts and Google’s PAA. Users seek realistic, non-judgmental guidance—both for staying on track and for fast recovery if they’re already behind. By offering rhythm, recovery, and supportive frameworks, TryFondo can position itself as both a coach and a solution.",
        "research_citations": [
          "Reddit: 'How often should I do bookkeeping, and what happens if I fall behind?' (11 mentions, e.g., https://www.reddit.com/r/accounting/comments/18w6b2a/how_often_should_bookkeeping_be_done_for_a_startup/)",
          "Instagram: 'Founder tip: Monthly bookkeeping is a smart move'",
          "TryFondo: Emphasis on automated, recurring reporting and reducing end-of-year stress (https://www.tryfondo.com/whats-new)",
          "Google PAA: 'How often should a startup do bookkeeping?'; 'What happens if I skip a month?'"
        ],
        "user_questions_addressed": [
          "Do I need to do bookkeeping every month?",
          "What’s the risk if I don’t keep up with my books?",
          "How do I catch up if I’m behind on bookkeeping?",
          "Is quarterly bookkeeping enough for a startup?"
        ],
        "company_expertise_showcase": "Highlights TryFondo’s automated monthly reporting, proactive reminders, and stress-free compliance tools—including dashboards and at-a-glance checklists for catching up. Reinforces TryFondo as a supportive partner, not just software."
      },
      {
        "angle": "An end-to-end guide on choosing, integrating, and scaling with modern bookkeeping tools—focusing on founder-friendly, all-in-one platforms.",
        "title": "Choosing Your First Bookkeeping Platform: Integration, Automation, and What Founders Wish They Knew",
        "topic_id": "topic_03",
        "seo_opportunity": "Serves queries for 'best bookkeeping tool for startups', 'QuickBooks vs Xero vs TryFondo', and 'how to integrate bookkeeping with other tools'.",
        "topic_reasoning": "Analysis of both Reddit and Google data shows that tool selection and integration are persistent pain points—users feel overwhelmed by fragmented workflows and want credible, founder-centric recommendations on what really works. A comparison-style guide—grounded in real founder experience and integration checklists—addresses deep search and user intent and sets up TryFondo's USP.",
        "research_citations": [
          "Reddit: 'Which bookkeeping tool or software is best for my startup?' (9 mentions, e.g., https://www.reddit.com/r/startups/comments/18v9k8w/bookkeeping_101_for_new_startup/)",
          "Reddit: 'How do I integrate bookkeeping with my other business workflows?' (5 mentions, e.g., https://www.reddit.com/r/smallbusiness/comments/18x7k3l/how_do_i_start_bookkeeping_for_my_small_business/)",
          "TryFondo site: All-in-one, founder-friendly workflow integration (https://www.tryfondo.com)",
          "BetterBuyer: Overview of bookkeeping software and breadth of features"
        ],
        "user_questions_addressed": [
          "What’s the simplest bookkeeping software for founders?",
          "Which tool integrates best with my other business apps?",
          "Is there a way to automate data entry between tools?",
          "Are there tools that handle everything in one place?"
        ],
        "company_expertise_showcase": "Spotlights TryFondo’s ease of integration with payroll, CRM, and invoicing; unified dashboards; and intuitive, one-login approach—all designed for founder adoption and workflow streamlining."
      },
      {
        "angle": "Educational ‘explain the difference’ guide with real-world startup scenarios, clarifying roles, risks, and decision factors for DIY vs hiring help.",
        "title": "Bookkeeper or Accountant—or DIY? Deciding What’s Best for Your Startup’s First Year",
        "topic_id": "topic_04",
        "seo_opportunity": "Rises for queries about 'do I need an accountant or bookkeeper', 'bookkeeping vs accounting startups', and 'when should I hire a bookkeeper?'",
        "topic_reasoning": "Founders are often unclear about the tipping point between DIY, a bookkeeper, and an accountant. Both Google and Reddit research cite confusion, worry about costs, and risk of doing it wrong. An honest, scenario-based guide demystifies these choices and gently coaches founders on where they can save money, and where professional help makes sense—while positioning TryFondo’s hybrid solutions.",
        "research_citations": [
          "Reddit: 'Do I need a bookkeeper or accountant, or can I do it myself?' (7 mentions)",
          "Google PAA: 'Do startups need an accountant or just a bookkeeper?'; 'Bookkeeping vs accounting for startups'",
          "TryFondo and BetterBuyer: Detailed breakdown of services (bookkeeping, payroll, tax, advisory)",
          "Reddit user pain: anxiety over risk, desire to save money, confusion about roles"
        ],
        "user_questions_addressed": [
          "Can I handle startup bookkeeping myself?",
          "When should I hire a bookkeeper or accountant?",
          "What’s the difference between a bookkeeper and an accountant for a startup?",
          "Is it risky to DIY bookkeeping as a founder?"
        ],
        "company_expertise_showcase": "Positions TryFondo as an honest educator—offering clarity on role definitions, practical decision trees, and how its blended tech/human support flexes as startups grow."
      },
      {
        "angle": "ROI-driven post connecting disciplined bookkeeping directly to tax credits and startup money-back outcomes, including a practical tax-prep checklist.",
        "title": "How Bookkeeping Earns You Money: Maximizing Startup Tax Credits and Avoiding IRS Pitfalls",
        "topic_id": "topic_05",
        "seo_opportunity": "Captures high-intent SEO on 'startup bookkeeping tax credits', 'how bookkeeping affects taxes', and 'startup tax compliance best practices'.",
        "topic_reasoning": "One of the strongest user motivators—surfacing in both research sources—is the real financial gain possible through smart bookkeeping (e.g., up to $500K in credits, average $21K refunds per TryFondo user). Users crave concrete steps to link regular bookkeeping habits to maximizing these outcomes. A transparent, step-based post (including a downloadable checklist) demonstrates TryFondo’s thought leadership and practical value.",
        "research_citations": [
          "Reddit: 'How does good bookkeeping help with taxes and maximizing credits?' (6 mentions, e.g., https://www.reddit.com/r/startups/comments/18v9k8w/bookkeeping_101_for_new_startup/)",
          "TryFondo homepage: 'Maintain eligibility for up to $500,000 in startup tax credits. Average customer gets $21,000 back.'",
          "Google PAA: 'How can startups maximize tax credits through bookkeeping?'; 'How does bookkeeping affect my startup’s tax filing?'"
        ],
        "user_questions_addressed": [
          "How does bookkeeping affect my startup’s tax filing?",
          "What records do I need to claim tax credits?",
          "Can good bookkeeping really save me money on taxes?",
          "How do I make sure I don’t miss out on tax credits?"
        ],
        "company_expertise_showcase": "Emphasizes TryFondo’s expertise in tax credit optimization, compliance, and real financial ROI—showcasing proprietary data and tax-season readiness tools."
      }
    ],
    "topic_strategy_summary": "These five topics are drawn directly from overlapping Reddit and Google intent patterns, mapping to real founder/operations manager pain points—confusion, overwhelm, tool frustration, and desire for tangible outcomes. Each topic is anchored in both SEO demand and high emotional urgency, explicitly connecting to proven user questions and TryFondo’s own product differentiators (automation, integration, ROI/tax credits, clear onboarding). This strategy positions TryFondo as the authoritative, founder-centric resource for startup operations, blending education, actionable frameworks, and transparent, ROI-focused solutions. Each post will serve as a defensible, high-value asset supporting multiple business goals: awareness, consideration, and conversion."
  }
# Workflow JSON structure
workflow_graph_schema = {
    "nodes": {
        # 1. Input Node - Remove company_context_doc from dynamic output schema
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "company_name": {
                        "type": "str",
                        "required": True,
                        "description": "Name of the company for document operations"
                    },
                    "user_input": {
                        "type": "str",
                        "required": True,
                        "description": "User's content ideas, brainstorm, or transcript"
                    },
                    "initial_status": {
                        "type": "str",
                        "required": False,
                        "default": "draft",
                        "description": "Initial status of the workflow"
                    },
                    "brief_uuid": {
                        "type": "str",
                        "required": True,
                        "description": "UUID of the brief being generated"
                    },
                    "topic_hitl_input": {
                        "type": "dict",
                        "required": False,
                        "default": TOPIC_HITL_INPUT,
                        "description": "Topic HITL input"
                    },
                    "brief_hitl_input": {
                        "type": "dict",
                        "required": False,
                        "default": BRIEF_HITL_INPUT,
                        "description": "Brief HITL input"
                    }
                }
            }
        },
        
        # 9. Topic Selection - HITL Node
        "topic_selection_hitl": {
            "node_id": "topic_selection_hitl",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_action": {
                        "type": "enum",
                        "enum_values": ["complete", "provide_feedback", "cancel_workflow"],
                        "required": True,
                        "description": "User's decision on topic selection"
                    },
                    "selected_topic_id": {
                        "type": "str",
                        "required": False,
                        "description": "Single topic_id selected by user (required if accept_topic)"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for topic regeneration (required if regenerate_topics)"
                    }
                }
            }
        },
        
        # # 10. Route Topic Selection
        "route_topic_selection": {
            "node_id": "route_topic_selection",
            "node_name": "router_node",
            "node_config": {
                "choices": ["brief_approval_hitl", "topic_selection_hitl", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "brief_approval_hitl",
                        "input_path": "user_action",
                        "target_value": "complete"
                    },
                    {
                        "choice_id": "topic_selection_hitl",
                        "input_path": "user_action",
                        "target_value": "provide_feedback"
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "user_action",
                        "target_value": "cancel_workflow"
                    }
                ],
                "default_choice": "output_node"
            }
        },
        
        # 18. Brief Approval - HITL Node
        "brief_approval_hitl": {
            "node_id": "brief_approval_hitl",
            "node_name": "hitl_node__default",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "user_brief_action": {
                        "type": "enum",
                        "enum_values": ["complete", "provide_feedback", "cancel_workflow", "draft"],
                        "required": True,
                        "description": "User's decision on brief approval"
                    },
                    "revision_feedback": {
                        "type": "str",
                        "required": False,
                        "description": "Feedback for brief revision (required if revise_brief)"
                    },
                    "updated_content_brief": {
                        "type": "dict",
                        "required": True,
                        "description": "Updated content brief"
                    }
                }
            }
        },
        
        # 19. Route Brief Approval
        "route_brief_approval": {
            "node_id": "route_brief_approval",
            "node_name": "router_node",
            "node_config": {
                "choices": ["save_brief", "brief_approval_hitl", "output_node"],
                "allow_multiple": False,
                "choices_with_conditions": [
                    {
                        "choice_id": "save_brief",
                        "input_path": "user_brief_action",
                        "target_value": "complete"
                    },
                    {
                        "choice_id": "brief_approval_hitl",
                        "input_path": "user_brief_action",
                        "target_value": "provide_feedback"
                    },
                    {
                        "choice_id": "output_node",
                        "input_path": "user_brief_action",
                        "target_value": "cancel_workflow"
                    },
                    {
                        "choice_id": "brief_approval_hitl",
                        "input_path": "user_brief_action",
                        "target_value": "draft"
                    }
                ],
                "default_choice": "output_node"
            }
        },
        
        # 24. Save Brief - Store Customer Data
        "save_brief": {
            "node_id": "save_brief",
            "node_name": "store_customer_data",
            "node_config": {
                "global_versioning": {
                    "is_versioned": True,
                    "operation": "upsert_versioned"
                },
                "global_is_shared": False,
                "store_configs": [
                    {
                        "input_field_path": "final_content_brief",
                        "target_path": {
                            "filename_config": {
                                "input_namespace_field_pattern": BLOG_CONTENT_BRIEF_NAMESPACE_TEMPLATE,
                                "input_namespace_field": "company_name",
                                "input_docname_field_pattern": BLOG_CONTENT_BRIEF_DOCNAME,
                                "input_docname_field": "brief_uuid"
                            }
                        },
                        "extra_fields": [
                            {
                                "src_path": "user_brief_action",
                                "dst_path": "status"
                            },
                            {
                                "src_path": "brief_uuid",
                                "dst_path": "uuid"
                            }
                        ],
                        "versioning": {
                            "is_versioned": BLOG_CONTENT_BRIEF_IS_VERSIONED,
                            "operation": "upsert_versioned"
                        },
                    }
                ],
            }
        },
        
        # 25. Output Node
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {}
        }
    },
    
    "edges": [
        # Input -> State: Store initial values
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "user_input", "dst_field": "user_input"},
                {"src_field": "initial_status", "dst_field": "initial_status"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"},
                {"src_field": "topic_hitl_input", "dst_field": "topic_hitl_input"},
                {"src_field": "brief_hitl_input", "dst_field": "brief_hitl_input"}
            ]
        },
        
        # Topic Generation LLM -> HITL
        {
            "src_node_id": "input_node",
            "dst_node_id": "topic_selection_hitl",
            "mappings": [
                {"src_field": "topic_hitl_input", "dst_field": "topic_suggestions"}
            ]
        },

        
        # HITL -> Route Topic Selection
        {
            "src_node_id": "topic_selection_hitl",
            "dst_node_id": "route_topic_selection",
            "mappings": [
                {"src_field": "user_action", "dst_field": "user_action"}
            ]
        },
        
        # # --- Topic Selection Router Paths ---
        {
            "src_node_id": "route_topic_selection",
            "dst_node_id": "topic_selection_hitl",
        },

        {
            "src_node_id": "$graph_state",
            "dst_node_id": "topic_selection_hitl",
            "mappings": [
                {"src_field": "topic_hitl_input", "dst_field": "topic_suggestions"}
            ]
        },

        {
            "src_node_id": "route_topic_selection",
            "dst_node_id": "output_node",
            "description": "Route to output if workflow cancelled"
        },
        
        # Save as Draft After Brief Generation -> Brief Approval HITL
        { "src_node_id": "route_topic_selection", "dst_node_id": "brief_approval_hitl"},

        # ---- graph state -> brief approval hitl ----
        { "src_node_id": "$graph_state", "dst_node_id": "brief_approval_hitl", "mappings": [
            { "src_field": "brief_hitl_input", "dst_field": "content_brief"}
          ]
        },
        
        # Brief Approval HITL -> Route
        {
            "src_node_id": "brief_approval_hitl",
            "dst_node_id": "route_brief_approval",
            "mappings": [
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"}
            ]
        },
        
        # Brief Approval HITL -> State
        {
            "src_node_id": "brief_approval_hitl",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "revision_feedback", "dst_field": "current_revision_feedback"},
                {"src_field": "updated_content_brief", "dst_field": "current_content_brief"},
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"}            ]
        },
        
        # # --- Brief Approval Router Paths ---
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "save_brief",
            "description": "Route to save brief if approved"
        },
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "brief_approval_hitl",
            "description": "Route to check iteration limit if revision requested"
        },
        {
            "src_node_id": "route_brief_approval",
            "dst_node_id": "output_node",
            "description": "Route to output if workflow cancelled"
        },
        
        # # State -> Save Brief
        {
            "src_node_id": "$graph_state",
            "dst_node_id": "save_brief",
            "mappings": [
                {"src_field": "company_name", "dst_field": "company_name"},
                {"src_field": "current_content_brief", "dst_field": "final_content_brief"},
                {"src_field": "user_brief_action", "dst_field": "user_brief_action"},
                {"src_field": "brief_uuid", "dst_field": "brief_uuid"}            ]
        },
        
        # Save Brief -> Output
        {
            "src_node_id": "save_brief",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "paths_processed", "dst_field": "final_paths_processed"}
            ]
        }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                "current_topic_suggestions": "replace",
                "current_content_brief": "replace",
                "current_regeneration_feedback": "replace",
                "current_revision_feedback": "replace",
                "generation_metadata": "replace",
                "topic_generation_messages_history": "add_messages",
                "topic_feedback_analysis_messages_history": "add_messages",
                "brief_generation_messages_history": "add_messages",
                "brief_feedback_analysis_messages_history": "add_messages",
                "user_action": "replace",
                "user_brief_action": "replace"
            }
        }
    }
}


# --- Testing Code ---

async def validate_content_brief_workflow_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the content research & brief generation workflow outputs.
    
    Args:
        outputs: The dictionary of final outputs from the workflow run.
        
    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating content research & brief generation workflow outputs...")
    
    # Check for expected keys
    expected_keys = [
        'google_research_results', 
        'reddit_research_results', 
        'final_topic_suggestions',
        'selected_topic',
        'final_content_brief'
    ]
    
    for key in expected_keys:
        if key in outputs:
            logger.info(f"✓ Found expected key: {key}")
        else:
            logger.warning(f"⚠ Missing optional key: {key}")
    
    # Validate Google research results if present
    if 'google_research_results' in outputs:
        google_results = outputs['google_research_results']
        assert isinstance(google_results, dict), "Google research results should be a dict"
        assert 'research_queries' in google_results, "Google results missing research_queries"
        assert 'source_articles' in google_results, "Google results missing source_articles"
        assert 'people_also_asked' in google_results, "Google results missing people_also_asked"
        logger.info(f"✓ Google research found {len(google_results['source_articles'])} articles")
    
    # Validate Reddit research results if present
    if 'reddit_research_results' in outputs:
        reddit_results = outputs['reddit_research_results']
        assert isinstance(reddit_results, dict), "Reddit research results should be a dict"
        assert 'user_questions_summary' in reddit_results, "Reddit results missing user_questions_summary"
        logger.info(f"✓ Reddit research found {len(reddit_results['user_questions_summary'])} user questions")
    
    # Validate topic suggestions if present
    if 'final_topic_suggestions' in outputs:
        topic_suggestions = outputs['final_topic_suggestions']
        assert isinstance(topic_suggestions, dict), "Topic suggestions should be a dict"
        assert 'suggested_blog_topics' in topic_suggestions, "Topic suggestions missing suggested_blog_topics"
        topics = topic_suggestions['suggested_blog_topics']
        assert isinstance(topics, list), "Topics should be a list"
        assert len(topics) > 0, "Should have at least one topic suggestion"
        logger.info(f"✓ Generated {len(topics)} topic suggestions")
    
    # Validate selected topic if present
    if 'selected_topic' in outputs:
        selected_topic = outputs['selected_topic']
        assert isinstance(selected_topic, dict), "Selected topic should be a dict"
        if 'current_topic_suggestions' in selected_topic and 'suggested_blog_topics' in selected_topic['current_topic_suggestions']:
            topics = selected_topic['current_topic_suggestions']['suggested_blog_topics']
            assert isinstance(topics, list), "Selected topics should be a list"
            assert len(topics) == 1, "Should have exactly one selected topic"
            first_topic = topics[0]
            assert 'title' in first_topic, "Selected topic missing title"
            assert 'angle' in first_topic, "Selected topic missing angle"
            assert 'topic_id' in first_topic, "Selected topic missing topic_id"
            logger.info(f"✓ Selected topic: {first_topic['title']}")
    
    # Validate content brief if present
    if 'final_content_brief' in outputs:
        content_brief = outputs['final_content_brief']
        assert isinstance(content_brief, dict), "Content brief should be a dict"
        assert 'content_brief' in content_brief, "Content brief missing content_brief field"
        brief = content_brief['content_brief']
        
        # Check required brief fields
        required_brief_fields = [
            'title', 'target_audience', 'content_goal', 'key_takeaways',
            'content_structure', 'seo_keywords', 'brand_guidelines',
            'research_sources', 'call_to_action', 'estimated_word_count',
            'difficulty_level', 'writing_instructions'
        ]
        
        for field in required_brief_fields:
            assert field in brief, f"Content brief missing required field: {field}"
        
        logger.info(f"✓ Content brief generated with {len(brief['content_structure'])} sections")
        logger.info(f"✓ Estimated word count: {brief['estimated_word_count']}")
    
    # Check for brief document ID if brief was saved
    if 'brief_document_id' in outputs and outputs['brief_document_id'] is not None:
        brief_id = outputs['brief_document_id']
        if isinstance(brief_id, str) and len(brief_id) > 0:
            logger.info(f"✓ Brief saved with document ID: {brief_id}")
        else:
            logger.info("⚠ Brief document ID present but invalid format")
    
    logger.info("✓ Content research & brief generation workflow output validation passed.")
    return True


async def main_test_content_brief_workflow():
    """
    Test for Content Research & Brief Generation Workflow.
    
    This function sets up test data, executes the workflow, and validates the output.
    The workflow takes user input, conducts research, generates topic suggestions,
    and creates a comprehensive content brief with human-in-the-loop approval.
    """
    test_name = "Content Research & Brief Generation Workflow Test"
    print(f"--- Starting {test_name} ---")
    
    # Test parameters
    test_company_name = "Momentum"
    
    # # Create test company document data
    # company_data = {
    #     "name": "Momentum",
    #     "website_url": "https://www.momentum.io",
    #     "value_proposition": "AI-native Revenue Orchestration Platform that extracts, structures, and moves GTM data automatically. Momentum tracks what's said in every customer interaction and turns it into structured, usable data, updating CRM fields in real time for cleaner pipeline, better reporting, and smarter AI agents with context.",
    #     "company_offerings": [
    #         {
    #             "offering": "AI-powered Revenue Orchestration Platform",
    #             "use_case": [
    #                 "Automated CRM data entry and hygiene",
    #                 "Real-time deal tracking and forecasting",
    #                 "Customer conversation intelligence and insights",
    #                 "Sales process automation and optimization",
    #                 "Revenue pipeline visibility and reporting"
    #             ],
    #             "ideal_users": [
    #                 "Chief Revenue Officers",
    #                 "VP of Sales",
    #                 "Sales Operations Managers",
    #                 "VP of Customer Success",
    #                 "Revenue Operations Teams"
    #             ]
    #         },
    #         {
    #             "offering": "Conversation Intelligence and Analytics",
    #             "use_case": [
    #                 "Call transcription and sentiment analysis",
    #                 "Customer feedback extraction and categorization",
    #                 "Competitive intelligence gathering",
    #                 "Product feedback and feature request tracking",
    #                 "Risk signal identification and churn prevention"
    #             ],
    #             "ideal_users": [
    #                 "Sales Representatives",
    #                 "Customer Success Managers",
    #                 "Product Marketing Managers",
    #                 "Business Development Teams",
    #                 "Executive Leadership"
    #             ]
    #         },
    #         {
    #             "offering": "Automated GTM Data Workflows",
    #             "use_case": [
    #                 "Salesforce integration and data synchronization",
    #                 "Multi-platform data orchestration",
    #                 "Custom field mapping and data transformation",
    #                 "Workflow automation and trigger management",
    #                 "Data quality monitoring and alerts"
    #             ],
    #             "ideal_users": [
    #                 "Sales Operations Analysts",
    #                 "CRM Administrators",
    #                 "Revenue Operations Directors",
    #                 "IT and Systems Integration Teams",
    #                 "Data Analytics Teams"
    #             ]
    #         }
    #     ],
    #     "icps": [
    #         {
    #             "icp_name": "Enterprise SaaS Revenue Teams",
    #             "target_industry": "SaaS/Technology",
    #             "company_size": "Enterprise (1000+ employees)",
    #             "buyer_persona": "Chief Revenue Officer (CRO)",
    #             "pain_points": [
    #                 "Manual, repetitive Salesforce data entry",
    #                 "Poor CRM data hygiene and accuracy",
    #                 "Lack of visibility into deal progression and forecast risk",
    #                 "Difficulty extracting insights from customer conversations",
    #                 "Revenue team inefficiencies and administrative overhead"
    #             ]
    #         },
    #         {
    #             "icp_name": "Growth-Stage Sales Organizations",
    #             "target_industry": "B2B SaaS",
    #             "company_size": "Mid-market (200-1000 employees)",
    #             "buyer_persona": "VP of Sales/Sales Operations",
    #             "pain_points": [
    #                 "Inconsistent sales process execution",
    #                 "Manual deal room management and collaboration",
    #                 "Missing customer intelligence and buying signals",
    #                 "Time-consuming post-call administrative tasks",
    #                 "Lack of real-time coaching and performance insights"
    #             ]
    #         },
    #         {
    #             "icp_name": "Customer Success Teams",
    #             "target_industry": "Technology/SaaS",
    #             "company_size": "Mid-market to Enterprise (500+ employees)",
    #             "buyer_persona": "VP of Customer Success",
    #             "pain_points": [
    #                 "Inability to predict and prevent customer churn",
    #                 "Manual tracking of customer health and satisfaction",
    #                 "Difficulty identifying expansion opportunities",
    #                 "Lack of visibility into customer feedback and product insights",
    #                 "Inefficient handoff processes from sales to customer success"
    #             ]
    #         }
    #     ],
    #     "content_distribution_mix": {
    #         "awareness_percent": 30.0,
    #         "consideration_percent": 40.0,
    #         "purchase_percent": 20.0,
    #         "retention_percent": 10.0
    #     },
    #     "competitors": [
    #         {
    #             "website_url": "https://www.gong.io",
    #             "name": "Gong"
    #         },
    #         {
    #             "website_url": "https://www.outreach.io",
    #             "name": "Outreach"
    #         },
    #         {
    #             "website_url": "https://www.avoma.com",
    #             "name": "Avoma"
    #         }
    #     ],
    #     "goals": [
    #         "Establish thought leadership in revenue intelligence and AI-powered sales automation",
    #         "Educate target audience about the benefits of automated GTM data workflows",
    #         "Generate qualified leads through valuable content addressing CRM and sales operation challenges",
    #         "Build brand awareness among enterprise revenue teams and sales operations professionals",
    #         "Create content that drives organic traffic for high-intent keywords related to revenue orchestration and conversation intelligence"
    #     ]
    # }
    
    # # Test inputs
    test_inputs = {
        "company_name": test_company_name,
        "user_input": "I've been thinking about writing content around how AI is changing project management. I want to explore how small teams can leverage AI tools without losing the human touch in their workflows. Maybe something about the balance between automation and personal connection in remote teams?",
        "brief_uuid": "123e4567-e89b-12d3-a456-426614174000"
    }
    
    # # Setup test documents
    # setup_docs: List[SetupDocInfo] = [
    #     {
    #         'namespace': f"blog_company_profile_{test_company_name}",
    #         'docname': BLOG_COMPANY_DOCNAME,
    #         'initial_data': company_data,
    #         'is_shared': False,
    #         'is_versioned': BLOG_COMPANY_IS_VERSIONED,
    #         'initial_version': "default",
    #         'is_system_entity': False
    #     },
    #     {
    #         'namespace': f"blog_content_strategy_{test_company_name}",
    #         'docname': BLOG_CONTENT_STRATEGY_DOCNAME,
    #         'initial_data': {
    #             "name": test_company_name,
    #             "content_strategy": "This is a placeholder for the content strategy document. It will be populated with actual strategy details."
    #         },
    #         'is_shared': False,
    #         'is_versioned': BLOG_CONTENT_STRATEGY_IS_VERSIONED,
    #         'initial_version': "default",
    #         'is_system_entity': False
    #     }
    # ]
    
    # # Cleanup configuration
    # cleanup_docs: List[CleanupDocInfo] = [
    #     {
    #         'namespace': f"blog_company_profile_{test_company_name}",
    #         'docname': BLOG_COMPANY_DOCNAME,
    #         'is_shared': False,
    #         'is_versioned': BLOG_COMPANY_IS_VERSIONED,
    #         'is_system_entity': False
    #     },
    #     {
    #         'namespace': f"blog_content_strategy_{test_company_name}",
    #         'docname': BLOG_CONTENT_STRATEGY_DOCNAME,
    #         'is_shared': False,
    #         'is_versioned': BLOG_CONTENT_STRATEGY_IS_VERSIONED,
    #         'is_system_entity': False
    #     }
    # ]
    
    # Predefined HITL inputs - leaving empty to allow for interactive testing
    predefined_hitl_inputs = [
        {
            "user_action": "provide_feedback",
            "selected_topic_id": None,
            "revision_feedback": "Promising directions. Emphasize remote-team collaboration impacts and an exec framework for what to automate vs. where human leadership is essential."
        },
        {
            "user_action": "complete",
            "selected_topic_id": "topic_01",
            "revision_feedback": None
        },
        {
            "user_brief_action": "provide_feedback",
            "revision_feedback": "Please tighten the hook and add one concrete scenario. Keep the framework but make success metrics more specific.",
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework",
                    "target_audience": "Project managers at 50-500 employee tech companies",
                    "content_goal": "Clarify what to automate vs. what requires human leadership",
                    "key_takeaways": [
                        "Automate repetitive PM tasks",
                        "Preserve human judgment for priorities and stakeholder alignment"
                    ],
                    "content_structure": [
                        {"section": "Hook & Context", "word_count": 80, "description": "Execs struggle with where to apply AI; introduce 80/20."},
                        {"section": "80/20 Framework", "word_count": 200, "description": "Automate vs. Keep Human table with examples."},
                        {"section": "Remote Team Scenario", "word_count": 200, "description": "Concrete example with metrics."},
                        {"section": "Implementation Tips", "word_count": 180, "description": "Guardrails and checkpoints."},
                        {"section": "CTA", "word_count": 60, "description": "Invite engagement and next steps."}
                    ],
                    "seo_keywords": {"primary_keyword": "AI in project management", "secondary_keywords": ["human-in-the-loop", "remote teams"]},
                    "call_to_action": "Comment your top AI adoption challenge and get a readiness checklist.",
                    "estimated_word_count": 700,
                    "difficulty_level": "Intermediate",
                    "writing_instructions": ["Conversational yet authoritative", "Data-informed with practical examples"]
                }
            }
        },
        {
            "user_brief_action": "draft",
            "revision_feedback": None,
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework (Draft V2)",
                    "estimated_word_count": 750
                }
            }
        },
        {
            "user_brief_action": "provide_feedback",
            "revision_feedback": "Looks good—make the CTA more outcome-oriented and add a metric example (e.g., 20% faster status reporting).",
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework",
                    "call_to_action": "Download the AI readiness checklist and benchmark your current process.",
                    "writing_instructions": ["Add metric example in Remote Team Scenario"]
                }
            }
        },
        {
            "user_brief_action": "complete",
            "revision_feedback": None,
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework (Final)",
                    "estimated_word_count": 800
                }
            }
        }
    ]
    
    # VALID HUMAN INPUTS FOR MANUAL TESTING:
    # {"user_action": "accept_topic", "selected_topic_id": "topic_01"}
    # {"user_action": "regenerate_topics", "regeneration_feedback": "Please generate more technical topics"}
    # {"user_action": "complete", "updated_content_brief": {content_brief with user edits}}
    # {"user_action": "revise_brief", "revision_feedback": "Please add more practical examples", "updated_content_brief": {manually edited content_brief}}
    
    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        hitl_inputs=predefined_hitl_inputs,
        # setup_docs=setup_docs,
        # cleanup_docs=cleanup_docs,
        cleanup_docs_created_by_setup=False,
        validate_output_func=validate_content_brief_workflow_output,
        stream_intermediate_results=True,
        poll_interval_sec=3,
        timeout_sec=1800  # 30 minutes for research and generation
    )
    
    print(f"--- {test_name} Finished ---")
    if final_run_outputs:
        # Show research results
        if 'google_research_results' in final_run_outputs:
            google_results = final_run_outputs['google_research_results']
            print(f"Google Research: {len(google_results.get('source_articles', []))} articles found")
        
        if 'reddit_research_results' in final_run_outputs:
            reddit_results = final_run_outputs['reddit_research_results']
            print(f"Reddit Research: {len(reddit_results.get('user_questions_summary', []))} user questions")
        
        # Show topic suggestions
        if 'final_topic_suggestions' in final_run_outputs:
            topics = final_run_outputs['final_topic_suggestions'].get('suggested_blog_topics', [])
            print(f"Topics Generated: {len(topics)} suggestions")
        
        # Show selected topic
        if 'selected_topic' in final_run_outputs:
            selected = final_run_outputs['selected_topic']
            if 'current_topic_suggestions' in selected and 'suggested_blog_topics' in selected['current_topic_suggestions']:
                topics = selected['current_topic_suggestions']['suggested_blog_topics']
                if topics:
                    print(f"Selected Topic: {topics[0].get('title', 'N/A')}")
            else:
                print(f"Selected Topic: {selected.get('title', 'N/A')}")
        
        # Show brief info
        if 'final_content_brief' in final_run_outputs:
            brief = final_run_outputs['final_content_brief']['content_brief']
            print(f"Brief Generated: {brief.get('estimated_word_count', 'N/A')} words")
            print(f"Brief Title: {brief.get('title', 'N/A')}")
        
        # Show saved document
        if 'brief_document_id' in final_run_outputs:
            print(f"Brief Saved: Document ID {final_run_outputs['brief_document_id']}")


# Entry point
if __name__ == "__main__":
    print("="*80)
    print("Content Research & Brief Generation Workflow Test")
    print("="*80)
    
    try:
        asyncio.run(main_test_content_brief_workflow())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=. python kiwi_client/workflows_for_blog_teammate/wf_user_input_to_brief.py")