"""
State filter mapping configuration for B2B Blog Content Scoring workflow testing.

This module defines how to filter and display state information during workflow execution.
Based on the workflow nodes: input_node, transform_document_config, load_document, 
construct_seo_analysis_prompt, seo_analysis_llm, output_node
"""

from typing import Dict, Any, List, Optional

# State filtering mapping for B2B Blog Content Scoring workflow
# Customize this mapping to focus on the most relevant workflow state data
state_filter_mapping = {
    # Input Node - focus on workflow inputs
    "input_node": {
        "namespace": None,  # Include as-is
        "docname": None,   # Include as-is  
        "is_shared": None  # Include as-is
    },
    
    # Transform Document Config - focus on transformation results
    "transform_document_config": {
        "transformed_data": "document_config",  # Rename for clarity
        "base_object": None  # Include base object configuration
    },
    
    # Load Document - focus on loaded blog content
    "load_document": {
        "blog_content.title": "blog_title",  # Extract title for quick view
        "blog_content.word_count": "blog_word_count",  # Extract word count
        "blog_content.author": "blog_author",  # Extract author
        "blog_content.content": "blog_content_preview",  # Will be truncated in display
        "blog_content": None  # Include full blog content as-is
    },
    
    # Construct SEO Analysis Prompt - focus on constructed prompts
    "construct_seo_analysis_prompt": {
        "seo_analysis_user_prompt": "analysis_prompt",  # Rename for clarity
        "prompt_metadata": "prompt_info"  # Include prompt construction metadata
    },
    
    # SEO Analysis LLM - focus on scoring results and metadata
    "seo_analysis_llm": {
        "structured_output.seo_score": "seo_score",  # Extract SEO score
        "structured_output.aeo_score": "aeo_score",  # Extract AEO score
        "structured_output.total_search_visibility_score": "total_score",  # Extract total score
        "structured_output.grade": "content_grade",  # Extract grade
        "structured_output.quick_wins": "quick_wins_list",  # Rename for clarity
        "structured_output": "scoring_results",  # Include full results
        "metadata.token_usage": "llm_tokens_used",  # Track token usage
        "metadata.reasoning_effort_class": "reasoning_effort"  # Track reasoning effort
    },
    
    # Output Node - focus on final outputs
    "output_node": {
        "seo_analysis_results": "final_scoring_results"  # Rename for clarity
    },
    
    # Central State - focus on key workflow state
    "central_state": {
        "namespace": None,  # Include as-is
        "docname": None,   # Include as-is
        "is_shared": None, # Include as-is
        "blog_content": "loaded_blog_content",  # Rename for clarity
        "seo_analysis_results": "current_scoring_results"  # Rename for clarity
    }
}

# Alternative: Minimal mapping for debugging specific scoring issues
# Uncomment and modify this section if you want to focus on scoring results only
"""
minimal_state_filter_mapping = {
    "seo_analysis_llm": {
        "structured_output.seo_score": "seo_score",
        "structured_output.aeo_score": "aeo_score", 
        "structured_output.grade": "grade"
    },
    "central_state": {
        "blog_content.title": "blog_title",
        "seo_analysis_results": "scoring_results"
    }
}
"""

# Alternative: Empty mapping (will result in full unfiltered state dumps)
# Use this when you need to see the complete workflow state
"""
state_filter_mapping = {}
"""

