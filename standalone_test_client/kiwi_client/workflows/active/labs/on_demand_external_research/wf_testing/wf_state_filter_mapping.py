"""
State Mapping Configuration for External Research Workflow State Dumps

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
- "research_content": None  -> includes research_content from central state as-is
- None -> removes the field entirely from filtered output

If this mapping is empty or not provided, full unfiltered state will be dumped.
"""

# State filtering mapping for external research workflow
# Customize this mapping to focus on the most relevant workflow state data
state_filter_mapping = {
    # Research Name Generation LLM Node
    "generate_research_name": {
        "structured_output": "research_name_result",  # Rename for clarity
        "metadata.iteration_count": "name_iterations",
        "metadata.token_usage": "name_tokens_used"
    },
    
    # Main Research LLM Node - focus on research content
    "conduct_research": {
        "llm_response": "research_content",  # Rename for clarity
        "metadata.token_usage": "research_tokens_used",
        "metadata.iteration_count": "research_iterations",
        "web_search_result": "search_citations"  # Include web search results
    },
    
    # HITL Node - focus on user responses
    "research_approval": {
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
    "save_research_draft": {
        "paths_processed": "draft_storage_paths"
    },
    "save_final_research": {
        "paths_processed": "final_storage_paths" 
    },
    
    # Load Customer Data - focus on loaded file content
    "load_additional_user_files_node": {
        "loaded_files": "additional_context_files",
        "files_loaded": "context_files_count"
    },
    
    # Central State - focus on key workflow state
    "central_state": {
        "research_context": None,  # Include as-is
        "asset_name": None,  # Include as-is
        "namespace": None,  # Include as-is
        "research_content": "current_research_content",  # Rename for clarity
        "generated_research_name": "research_name",  # Rename for clarity
        "user_action": "latest_user_action",  # Rename for clarity
        "revision_feedback": "latest_feedback",  # Rename for clarity
        "save_config": "document_save_config",  # Rename for clarity
        "generation_metadata": "llm_metadata",  # Rename for clarity
        "additional_user_files": "loaded_context_files",  # Rename for clarity
        "web_search_result": "search_results"  # Rename for clarity
    }
}

# Alternative: Minimal mapping for debugging specific issues
# Uncomment and modify this section if you want to focus on specific aspects only
"""
minimal_state_filter_mapping = {
    "conduct_research": {
        "llm_response": "research_content"
    },
    "research_approval": {
        "user_action": None,
        "revision_feedback": None
    },
    "central_state": {
        "research_content": "current_research_content",
        "user_action": "latest_user_action"
    }
}
"""

# Alternative: Empty mapping (will result in full unfiltered state dumps)
# Use this when you need to see the complete workflow state
"""
state_filter_mapping = {}
"""
