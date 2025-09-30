"""
State Mapping Configuration for Workflow State Dumps

This mapping is used to filter workflow state dumps for better readability and reduced verbosity.
Only the specified nodes and central state paths will be included in filtered state dumps.

Mapping Structure:
{
    "node_id": {
        "path_within_node_output": None,  # Include field as-is
        "path_within_node_output": "renamed_key"  # Include field with new name
    },
    "central_state": {
        "path_within_central_state": None,  # Include field as-is
        "path_within_central_state": "renamed_key"  # Include field with new name
    }
}

Examples:
- "structured_output.title": None  -> includes title as-is
- "structured_output.main_content": "content"  -> includes main_content as "content"
- "blog_brief": None  -> includes blog_brief from central state as-is
- None -> removes the field entirely from filtered output

If this mapping is empty or not provided, full unfiltered state will be dumped.
"""

# State filtering mapping for blog user input to brief workflow
# Focuses on the key extract fields specified
state_filter_mapping = {
    # Google Research LLM Node
    "google_research_llm": {
        "structured_output": None  # Include structured output as-is
    },

    # Reddit Research LLM Node
    "reddit_research_llm": {
        "structured_output": None  # Include structured output as-is
    },

    # Topic Generation LLM Node
    "topic_generation_llm": {
        "structured_output": None  # Include structured output as-is
    },

    # Brief Generation LLM Node
    "brief_generation_llm": {
        "structured_output": None  # Include structured output as-is
    }
}

# Alternative: Empty mapping (will result in full unfiltered state dumps)
# Use this when you need to see the complete workflow state
"""
state_filter_mapping = {}
"""