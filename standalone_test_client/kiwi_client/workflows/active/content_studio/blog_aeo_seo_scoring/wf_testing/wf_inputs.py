from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_testing.sandbox_setup_docs import (
    test_namespace,
    test_docname,
    test_is_shared,
)


test_name = "B2B Blog Content Scoring Workflow Test"
print(f"\n--- Starting {test_name} ---")

# Test scenario
test_scenario = {
    "name": "B2B Blog Content Analysis",
    "initial_inputs": {
        "namespace": test_namespace,
        "docname": test_docname,
        "is_shared": test_is_shared
    }
}
