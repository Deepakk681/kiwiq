import asyncio
from uuid import UUID
from scripts.initial_setup.customer_data_uploader import SimpleDataUploader, DocumentConfig

async def upload_momentum_company_data():
    """Upload Momentum company data to blog_company_doc location"""
    
    # Initialize uploader
    uploader = SimpleDataUploader()
    
    # Complete Momentum company data
    executive_profile_data = {
            "name": "Santiago Suarez",
            "title": "CEO & Founder",
            "company": "Momentum",
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
            "linkedin_goals": [
                "Build thought leadership in project management space",
                "Share insights on AI adoption",
                "Connect with other industry leaders",
                "Promote Momentum's vision"
            ]
        }
    
    # Configuration based on blog_company constants
    # From: BLOG_COMPANY_NAMESPACE_TEMPLATE = "blog_company_profile_{item}"
    # From: BLOG_COMPANY_DOCNAME = "blog_company_doc"
    config = DocumentConfig(
        namespace="linkedin_executive_profile_namespace_santiycr",  # Using template with company name
        docname="linkedin_executive_profile_doc",                    # From BLOG_COMPANY_DOCNAME
        is_shared=False,                               # From BLOG_COMPANY_IS_SHARED
        is_system_entity=False,                        # From BLOG_COMPANY_IS_SYSTEM_ENTITY
        version=None
    )
    
    # User details from original script
    user_id = UUID("f7f72f1b-2b04-45b9-a8f5-0d21a1004c4e")
    entity_username = "santiycr"
    
    print(f"📝 Uploading Momentum executive profile data...")
    print(f"📍 Target location: {config.namespace}/{config.docname}")
    print(f"👤 Entity: {entity_username}")
    
    try:
        # Upload the company data
        response = await uploader.store_data_simple(
            config=config,
            data=executive_profile_data,
            user_id=user_id        )
        
        if response:
            print("✅ SUCCESS: Momentum executive profile data uploaded successfully!")
            print(f"🎯 Stored at: {config.namespace}/{config.docname}")
            print(f"📋 Operation: {response.operation_performed}")
            print(f"🆔 Document ID available in response")
        else:
            print("❌ FAILED: Could not upload executive profile data")
            
    except Exception as e:
        print(f"💥 ERROR: {e}")
        raise


if __name__ == "__main__":
    print("🚀 Starting Momentum company data upload...")
    asyncio.run(upload_momentum_company_data())
    print("🏁 Upload process completed.") 