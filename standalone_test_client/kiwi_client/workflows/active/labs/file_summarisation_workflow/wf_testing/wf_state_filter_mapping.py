"""
State Mapping Configuration for File Summarisation Workflow State Dumps

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
- "structured_output.summary": None  -> includes summary as-is
- "structured_output.key_points": "summary_points"  -> includes key_points as "summary_points"
- "summary_content": None  -> includes summary_content from central state as-is
- None -> removes the field entirely from filtered output

If this mapping is empty or not provided, full unfiltered state will be dumped.
"""

# State filtering mapping for file summarisation workflow
# Customize this mapping to focus on the most relevant workflow state data
state_filter_mapping = {
    # Summary Name Generation LLM Node
    "generate_summary_name": {
        "structured_output": "summary_name_result",  # Rename for clarity
        "metadata.iteration_count": "name_iterations",
        "metadata.token_usage": "name_tokens_used"
    },
    
    # Main Summarization LLM Node - focus on summary content
    "conduct_summarization": {
        "llm_response": "summary_content",  # Rename for clarity
        "metadata.token_usage": "summary_tokens_used",
        "metadata.iteration_count": "summary_iterations"
    },
    
    # HITL Node - focus on user responses
    "summary_approval": {
        "user_action": None,  # Include user action as-is
        "revision_feedback": None,  # Include feedback as-is
        "load_additional_user_files": "user_additional_files"  # Rename for clarity
    },
    
    # Code Runner - focus on save configuration results
    "generate_save_config": {
        "code_output": "save_config_result",  # Rename for clarity
        "execution_time": "config_execution_time"
    },
    
    # Store/Save Nodes - focus on storage results
    "save_summary_draft": {
        "paths_processed": "draft_storage_paths"
    },
    "save_final_summary": {
        "paths_processed": "final_storage_paths" 
    },
    
    # Load Customer Data - focus on loaded file content
    "load_additional_user_files_node": {
        "loaded_files": "additional_context_files",
        "files_loaded": "context_files_count"
    },
    
    # Central State - focus on key workflow state
    "central_state": {
        "summary_context": None,  # Include as-is
        "asset_name": None,  # Include as-is
        "namespace": None,  # Include as-is
        "summary_content": "current_summary_content",  # Rename for clarity
        "generated_summary_name": "summary_name",  # Rename for clarity
        "user_action": "latest_user_action",  # Rename for clarity
        "revision_feedback": "latest_feedback",  # Rename for clarity
        "save_config": "document_save_config",  # Rename for clarity
        "generation_metadata": "llm_metadata",  # Rename for clarity
        "additional_user_files": "loaded_context_files"  # Rename for clarity
    }
}

# Alternative: Minimal mapping for debugging specific issues
# Uncomment and modify this section if you want to focus on specific aspects only
"""
minimal_state_filter_mapping = {
    "conduct_summarization": {
        "llm_response": "summary_content"
    },
    "summary_approval": {
        "user_action": None,
        "revision_feedback": None
    },
    "central_state": {
        "summary_content": "current_summary_content",
        "user_action": "latest_user_action"
    }
}
"""

# Alternative: Empty mapping (will result in full unfiltered state dumps)
# Use this when you need to see the complete workflow state
"""
state_filter_mapping = {}
"""
