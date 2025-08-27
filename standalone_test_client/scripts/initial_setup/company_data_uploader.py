import asyncio
from uuid import UUID
from scripts.initial_setup.customer_data_uploader import SimpleDataUploader, DocumentConfig

"""
Company Data Uploader
- Edit the CONFIG and DATA sections below, then run this file to upload.
- The organization is determined by your authentication (see AuthenticatedClient setup).
- If uploading a non-system entity document and you want to act on behalf of a specific user,
  set USER_ID to that user's UUID. Leave it None for your own user.

Supported features:
- Versioned upsert (creates if missing, updates if present) and sets the version active
- Shared vs user-specific docs
- System entity docs (stored under system paths, not tied to a specific org user)
- Optional schema template attachment
"""

# === CONFIG (edit these) ===
NAMESPACE = "linkedin_executive_profile_namespace_hungweiwu"
DOCNAME = "linkedin_executive_profile_doc"
VERSION = None
IS_SHARED = False
IS_SYSTEM_ENTITY = False
SCHEMA_TEMPLATE_NAME = None  # e.g., "my_schema_template"
SCHEMA_TEMPLATE_VERSION = None  # e.g., "1.0.0"

# For non-system entities, optionally act on behalf of a specific user in your org
# Provide a valid UUID string or set to None
USER_ID = "400d6df9-6758-4f44-9ec6-83ebf551848c"

# === DATA (edit this payload) ===
EXECUTIVE_PROFILE_DATA = {
  "name": "Hung-WEI Wu",
  "title": "Founder & CEO",
  "company": "Momentic.ai",
  "industry_experience": "10+ years in software testing, DevTools, and AI/ML",
  "expertise_areas": [
    "AI-driven test automation",
    "Developer tools and platforms",
    "Enterprise QA strategy",
    "Product-led growth in B2B SaaS",
    "Go-to-market for technical products"
  ],
  "thought_leadership_focus": [
    "How AI is redefining software testing and QA",
    "From scripts to self-healing, adaptive testing",
    "Shortening enterprise sales cycles for DevTools",
    "Building category leadership in 'AI testing tools'",
    "Scaling developer-focused content engines"
  ],
  "linkedin_goals": [
    "Establish thought leadership in AI testing and DevTools",
    "Educate buyers on differences from Selenium/Cypress-era tools",
    "Grow mid-market and enterprise network across EMEA and North America",
    "Attract senior engineering, QA, and GTM talent",
    "Drive qualified demo pipeline and Series A visibility"
  ]
}


# EXECUTIVE_PROFILE_DATA = {
#   "company_name": "Momentic.ai",
#   "website_url": "http://momentic.ai/",
#   "positioning_headline": "Momentic.ai is an AI-powered testing automation platform that helps enterprises accelerate software release cycles by eliminating flaky tests, reducing test maintenance, and providing intelligent testing coverage far beyond traditional frameworks like Selenium or Cypress.",
#   "icps": {
#     "icp_name": "Enterprise Software Development & QA Teams",
#     "target_industry": "Technology, Financial Services, E-commerce, SaaS, and Telecommunications",
#     "company_size": "Mid-market to Enterprise (500+ employees)",
#     "buyer_persona": "VP of Engineering, Head of QA, DevOps Lead, CTO",
#     "pain_points": [
#       "Heavy time and costs lost to test maintenance and flaky automation scripts",
#       "Difficulty scaling test coverage without slowing down release cycles",
#       "Existing tools (e.g., Selenium, Cypress) are too manual and break easily",
#       "Pressure to accelerate software delivery while ensuring quality",
#       "Confusion in evaluating next-gen testing tools due to crowded market positioning"
#     ],
#   },
#   "goals": [
#       "Shorten release cycles by cutting testing time",
#       "Reduce manual intervention and maintenance effort in automated testing",
#       "Achieve higher quality and reliability in software before release",
#       "Adopt true AI-first testing solutions instead of legacy frameworks",
#       "Elevate QA and testing from cost center to strategic enabler of velocity"
#     ],
#   "competitors": [
#     {
#       "website_url": "https://www.mabl.com/",
#       "name": "Mabl"
#     },
#     {
#       "website_url": "https://www.testim.io/",
#       "name": "Testim"
#     },
#     {
#       "website_url": "https://www.selenium.dev/",
#       "name": "Selenium (legacy open-source)"
#     },
#     {
#       "website_url": "https://www.cypress.io/",
#       "name": "Cypress"
#     }
#   ]
# }


async def upload_company_data():
    uploader = SimpleDataUploader()

    config = DocumentConfig(
        namespace=NAMESPACE,
        docname=DOCNAME,
        is_shared=IS_SHARED,
        is_system_entity=IS_SYSTEM_ENTITY,
        version=VERSION,
        schema_template_name=SCHEMA_TEMPLATE_NAME,
        schema_template_version=SCHEMA_TEMPLATE_VERSION,
    )

    user_id_uuid = None
    if USER_ID:
        try:
            user_id_uuid = UUID(USER_ID)
        except Exception:
            print(f"⚠️  USER_ID is not a valid UUID string: {USER_ID}. Proceeding without on-behalf-of.")
            user_id_uuid = None

    print("📝 Uploading company data...")
    print(f"📍 Target: {config.namespace}/{config.docname}")
    print(f"🔖 Version: {config.version} | Shared: {config.is_shared} | System: {config.is_system_entity}")
    if config.schema_template_name and config.schema_template_version:
        print(f"📐 Schema: {config.schema_template_name} v{config.schema_template_version}")
    if user_id_uuid and not config.is_system_entity:
        print(f"👤 On behalf of user: {user_id_uuid}")

    try:
        response = await uploader.store_data_simple(
            config=config,
            data=EXECUTIVE_PROFILE_DATA,
            user_id=user_id_uuid,
        )

        if response:
            print("✅ SUCCESS: Company data uploaded!")
            print(f"🎯 Location: {config.namespace}/{config.docname}")
            print(f"📋 Operation: {response.operation_performed}")
        else:
            print("❌ FAILED: Upload did not return a success response.")
    except Exception as e:
        print(f"💥 ERROR during upload: {e}")
        raise


if __name__ == "__main__":
    print("🚀 Starting company data upload...")
    asyncio.run(upload_company_data())
    print("🏁 Upload process completed.") 