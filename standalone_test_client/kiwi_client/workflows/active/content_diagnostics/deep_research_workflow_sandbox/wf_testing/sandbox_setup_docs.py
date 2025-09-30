from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.workflows.active.sandbox_identifiers import test_sandbox_company_name as test_company_name
from kiwi_client.workflows.active.document_models.customer_docs import (
    BLOG_COMPANY_DOCNAME,
    BLOG_COMPANY_NAMESPACE_TEMPLATE,
    LINKEDIN_USER_PROFILE_DOCNAME,
    LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE,
    LINKEDIN_SCRAPED_PROFILE_DOCNAME,
    LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE
)

# Conditional test_inputs variable (will be set by the test runner)
try:
    test_inputs
except NameError:
    test_inputs = {"run_linkedin_exec": False}

COMPANY_DOCUMENT_DATA = {
"name": "otter.ai",
"website_url": "https://otter.ai",
"value_proposition": "AI meeting assistant that transcribes, summarizes, and automates follow-ups to boost team productivity across meetings, calls, and interviews",
"icp": {
"icp_name": "Marketing Director",
"target_industry": "Technology / B2B SaaS",
"company_size": "Mid to large enterprise",
"buyer_persona": "Senior marketing professional responsible for content strategy, team collaboration, and pipeline-driving meetings",
"pain_points": [
"Manual note-taking during meetings reduces focus and misses key details",
"Inconsistent documentation and poor knowledge transfer across teams",
"Difficulty turning meetings into actionable tasks and content assets",
"Limited visibility into meeting insights and follow-ups across stakeholders"
],
"goals": [
"Increase meeting productivity and reduce time spent on note-taking",
"Standardize meeting documentation and accelerate cross-functional alignment",
"Automatically generate action items and summaries to speed execution",
"Repurpose customer and internal meeting insights into content and enablement"
]
},
"competitors": [
{
"name": "Fireflies.ai",
"website_url": "https://fireflies.ai"
},
{
"name": "Fathom",
"website_url": "https://fathom.video"
},
{
"name": "Microsoft Copilot (Teams Premium)",
"website_url": "https://www.microsoft.com/microsoft-teams/premium"
}
]
}
    
    # LinkedIn profile data that will be loaded (if LinkedIn research is enabled)
LINKEDIN_PROFILE_DATA = {
"username": "samliang",
"full_name": "Sam Liang",
"headline": "Co-founder & CEO at Otter.ai | Stanford PhD | Ex-Google Maps Location Platform Lead",
"summary": "Founder-CEO focused on AI meeting assistants that transcribe, summarize, and activate knowledge from conversations. Previously led Google’s Maps Location Platform; founded Alohar Mobile (acquired). Stanford PhD in Electrical Engineering.",
"experience": [
{ "title": "CEO & Co-founder", "company": "Otter.ai", "duration": "2016 – Present" },
{ "title": "CEO & Co-founder", "company": "Alohar Mobile", "duration": "2010 – 2013 (acquired)" },
{ "title": "Lead, Maps Location Platform & API", "company": "Google", "duration": "2006 – 2010" }
],
"skills": ["Artificial Intelligence", "Speech Recognition", "NLP", "Distributed Systems", "Product-Led Growth", "Location Services"]
}
    
LINKEDIN_SCRAPED_DATA = {
"profile_url": "https://www.linkedin.com/in/samliang",
"full_name": "Sam Liang",
"headline": "Co-founder & CEO at Otter.ai | Stanford PhD | Ex-Google Maps Location Platform Lead",
"location": "Mountain View, California",
"about": "Founder-CEO building AI meeting assistants that transcribe, summarize, and activate knowledge from conversations. Previously led Google’s Map Location Platform; founder/CEO of Alohar Mobile (acquired). Stanford PhD in EE focused on large-scale distributed systems.",
"current_position": {
"title": "CEO & Co-founder",
"company": "Otter.ai",
"duration": "Feb 2016 – Present"
},
"past_positions": [
{
"title": "CEO & Co-founder",
"company": "Alohar Mobile",
"duration": "2010 – 2013 (acquired by AutoNavi/Alibaba)"
},
{
"title": "Lead, Google Map Location Platform & API",
"company": "Google",
"duration": "2006 – 2010"
},
{
"title": "Member",
"company": "Forbes Technology Council",
"duration": "Jun 2020 – Jun 2021"
}
],
"education": [
{
"school": "Stanford University",
"degree": "Ph.D., Electrical Engineering",
"years": ""
}
],
"skills": [
"Artificial Intelligence",
"Speech Recognition",
"NLP",
"Distributed Systems",
"Product-Led Growth",
"Location Services"
],
"notable_highlights": [
"Founded Otter.ai, scaling to tens of millions of users and billions of captured meeting minutes",
"Pioneered Google Maps ‘blue dot’ location services work",
"Built proprietary speech recognition and summarization stack at Otter.ai",
"Recognized in Top 50 CEOs to Watch"
],
"social_proof": [
"Regular media/features on AI meeting assistants and AI avatars for meetings",
"Interview appearances discussing Otter.ai’s AI agents and enterprise adoption"
],
"follower_count": 15000
}
    # Setup documents - create company and LinkedIn profile documents
setup_docs: List[SetupDocInfo] = [
        SetupDocInfo(
            docname=BLOG_COMPANY_DOCNAME,
            namespace=BLOG_COMPANY_NAMESPACE_TEMPLATE.format(item="otter"),
            initial_data=COMPANY_DOCUMENT_DATA,
            is_versioned=False,
            is_shared=False,
            is_system_entity=False
        )
    ]
    
    # Add LinkedIn documents if LinkedIn research is enabled
if test_inputs.get("run_linkedin_exec"):
        setup_docs.extend([
            SetupDocInfo(
                docname=LINKEDIN_USER_PROFILE_DOCNAME,
                namespace=LINKEDIN_USER_PROFILE_NAMESPACE_TEMPLATE.format(item="samliang"),
                initial_data=LINKEDIN_PROFILE_DATA,
                is_versioned=False,
                is_shared=False,
                is_system_entity=False
            ),
            SetupDocInfo(
                docname=LINKEDIN_SCRAPED_PROFILE_DOCNAME,
                namespace=LINKEDIN_SCRAPED_PROFILE_NAMESPACE_TEMPLATE.format(item="samliang"),
                initial_data=LINKEDIN_SCRAPED_DATA,
                is_versioned=False,
                is_shared=False,
                is_system_entity=False
            )
        ])
    
    # No cleanup documents needed
cleanup_docs: List[CleanupDocInfo] = []