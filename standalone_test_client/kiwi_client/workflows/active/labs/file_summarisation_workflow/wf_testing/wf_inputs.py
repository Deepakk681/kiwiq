from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name,
)

# Test name for the workflow
test_name = "File Summarisation Workflow Test"

print(f"\n--- Starting {test_name} ---")

# Test scenario configuration
test_scenario = {
    "name": "Enterprise SaaS Revenue Operations Guide Summary",
    "initial_inputs": {
        "summary_context": "Create an executive summary of the Enterprise SaaS Revenue Operations Best Practices guide. Focus on key strategic recommendations, implementation priorities, and measurable outcomes. The summary should be suitable for C-level executives and revenue operations leaders.",
        "asset_name": "revenue_ops_guide_2024",
        "namespace": f"document_summaries_{test_sandbox_company_name}_{{item}}",  # Will replace {item} with asset_name
        # "docname": "revenue_ops_best_practices_summary",  # Commented out to test auto-generation
        "is_shared": False,
        # Example of optional additional user files to load during summarization
        "load_additional_user_files": [
            {
                "namespace": f"documents_to_summarize_{test_sandbox_company_name}",
                "docname": "enterprise_saas_revenue_ops_guide",
                "is_shared": False
            },
            {
                "namespace": f"summary_context_files_{test_sandbox_company_name}",
                "docname": "revenue_ops_metrics_framework",
                "is_shared": False
            }
        ]
    }
}

# Predefined HITL inputs for comprehensive testing
predefined_hitl_inputs = [
    # 1) Summary approval: request revisions first
    {
        "user_action": "request_revisions",
        "revision_feedback": "Good comprehensive summary! Please add more specific implementation timelines and budget considerations. Also, include a section on common pitfalls and how to avoid them during revenue operations transformation.",
        # Example of optional additional user files to load for feedback analysis
        "load_additional_user_files": [
            {
                "namespace": f"summary_context_files_{test_sandbox_company_name}",
                "docname": "revenue_ops_metrics_framework", 
                "is_shared": False
            }
        ]
    },
    
    # 2) Summary approval: approve final version
    {
        "user_action": "approve",
        "revision_feedback": None,
    }
]
