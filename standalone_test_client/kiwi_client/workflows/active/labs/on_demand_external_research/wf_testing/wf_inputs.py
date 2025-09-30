from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test name for the workflow
test_name = "On-Demand External Research Workflow Test"

print(f"\n--- Starting {test_name} ---")

# Test scenario configuration
test_scenario = {
    "name": "AI Impact on Healthcare Research",
    "initial_inputs": {
        "research_context": "Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.",
        "asset_name": "healthcare_ai_2024",
        "namespace": f"external_research_reports_{test_sandbox_company_name}_{{item}}",  # Will replace {item} with asset_name
        # "docname": "ai_healthcare_impact_2024_research",  # Commented out to test auto-generation
        "is_shared": False,
        # Example of optional additional user files to load during research
        "load_additional_user_files": [
            {
                "namespace": f"research_context_files_{test_sandbox_company_name}",
                "docname": "ai_diagnostic_trends_2024",
                "is_shared": False
            }
        ]
    }
}

# Predefined HITL inputs for comprehensive testing
predefined_hitl_inputs = [
    # 1) Research approval: request revisions first
    {
        "user_action": "request_revisions",
        "revision_feedback": "Great start! Please expand the section on regulatory challenges and add more specific examples of AI diagnostic tools currently in use. Also, include more recent data from 2024 if available.",
        # Example of optional additional user files to load for feedback analysis
        "load_additional_user_files": [
            {
                "namespace": f"research_context_files_{test_sandbox_company_name}", 
                "docname": "fda_ai_medical_devices_2024",
                "is_shared": False
            }
        ]
    },
    
    # 2) Research approval: approve final version
    {
        "user_action": "approve",
        "revision_feedback": None,
    }
]
