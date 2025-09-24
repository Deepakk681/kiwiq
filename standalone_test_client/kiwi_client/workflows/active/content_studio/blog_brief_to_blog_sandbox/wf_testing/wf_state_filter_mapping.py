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

# State filtering mapping for blog brief to blog workflow
# Customize this mapping to focus on the most relevant workflow state data
state_filter_mapping = {
    # Knowledge Enrichment LLM Node - focus on structured output and metadata
    "knowledge_enrichment_llm": {
        "structured_output": "knowledge_context",  # Rename for clarity
        "metadata.iteration_count": "iterations",  # Track iteration count
        "tool_calls": None  # Include tool calls as-is
    },
    
    # Content Generation LLM Node - focus on generated content
    "content_generation_llm": {
        "structured_output": "generated_content",  # Rename for clarity
        "metadata.token_usage": "tokens_used",  # Track token usage
        "metadata.iteration_count": "content_iterations"
    },
    
    # Feedback Analysis LLM Node - focus on analysis results
    "feedback_analysis_llm": {
        "structured_output": "feedback_analysis",  # Rename for clarity
        "metadata.token_usage": "analysis_tokens"
    },
    
    # HITL Node - focus on user responses
    "content_approval": {
        "user_action": None,  # Include user action as-is
        "revision_feedback": None,  # Include feedback as-is
        "updated_content_draft": "user_content_draft"  # Rename for clarity
    },
    
    # Tool Executor - focus on successful tool outputs
    "tool_executor": {
        "successful_calls": "successful_tool_calls",  # Rename for clarity
        "tool_outputs": None,  # Include all tool outputs
        "state_changes": "document_context_updates"  # Rename for clarity
    },
    
    # Store/Save Nodes - focus on storage results
    "store_draft": {
        "paths_processed": "draft_storage_paths"
    },
    "save_final_draft": {
        "paths_processed": "final_storage_paths" 
    },
    
    # Central State - focus on key workflow state
    "central_state": {
        "company_name": None,  # Include as-is
        "brief_docname": None,  # Include as-is  
        "post_uuid": None,  # Include as-is
        "blog_brief": None,  # Include loaded brief as-is
        "blog_content": "current_blog_content",  # Rename for clarity
        "knowledge_context": None,  # Include knowledge enrichment results
        "user_action": "latest_user_action",  # Rename for clarity
        "current_revision_feedback": "latest_feedback",  # Rename for clarity
        "generation_metadata": "llm_metadata",  # Rename for clarity
        "view_context": "document_context"  # Rename for clarity
    }
}

# Alternative: Minimal mapping for debugging specific issues
# Uncomment and modify this section if you want to focus on specific aspects only
"""
minimal_state_filter_mapping = {
    "content_generation_llm": {
        "structured_output": "generated_content"
    },
    "content_approval": {
        "user_action": None,
        "revision_feedback": None
    },
    "central_state": {
        "blog_content": "current_blog_content",
        "user_action": "latest_user_action"
    }
}
"""

# Alternative: Empty mapping (will result in full unfiltered state dumps)
# Use this when you need to see the complete workflow state
"""
state_filter_mapping = {}
"""
