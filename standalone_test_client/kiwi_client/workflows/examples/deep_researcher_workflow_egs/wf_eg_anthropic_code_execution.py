import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, ClassVar, Type
import json
from enum import Enum

# Using Pydantic for easier schema generation
from pydantic import BaseModel, Field

# Internal dependencies
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

# --- Workflow Configuration Constants ---

# LLM Configuration for Anthropic Code Execution
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-sonnet-4-20250514"  # Supports both code execution and web search
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 8192
LLM_REASONING_TOKENS_BUDGET = 6048

# Default prompts optimized for code execution tasks
DEFAULT_SYSTEM_PROMPT = """You are an expert data analyst and researcher with access to both web search and secure Python code execution capabilities.

Your task is to:
1. Research the given topic using web search when needed
2. Analyze data, perform calculations, and create visualizations using Python code
3. Provide comprehensive insights backed by data and analysis
4. Present results in a clear, structured format

When using code execution:
- Write clean, well-documented Python code
- Use appropriate libraries (pandas, numpy, matplotlib, etc.)
- Create visualizations when helpful
- Perform statistical analysis when relevant
- Show your work step-by-step

Use your tools strategically to provide the most valuable insights."""

DEFAULT_USER_PROMPT = """Analyze the growth trends of renewable energy adoption worldwide from 2020-2024. 

Please:
1. Research current statistics and trends
2. Create visualizations showing the data
3. Perform statistical analysis on the trends
4. Calculate growth rates and projections
5. Identify key factors driving adoption
6. Provide actionable insights

Focus on solar, wind, and electric vehicle adoption rates across major markets."""

### INPUTS ###

INPUT_FIELDS = {
    "system_prompt": {
        "type": "str", 
        "required": False, 
        "description": "System prompt for the analyst. If not provided, a default analytical prompt will be used."
    },
    "user_prompt": { 
        "type": "str", 
        "required": True, 
        "description": "The analysis request or research question to investigate."
    },
    "enable_reasoning": {
        "type": "bool",
        "required": False,
        "description": "Whether to enable reasoning mode for complex analysis. Default: True"
    }
}

##############

### EDGES CONFIG ###

field_mappings_from_input_to_llm = [
    { "src_field": "system_prompt", "dst_field": "system_prompt" },
    { "src_field": "user_prompt", "dst_field": "user_prompt" },
]

field_mappings_from_llm_to_output = [
    { "src_field": "current_messages", "dst_field": "current_messages"},
    { "src_field": "content", "dst_field": "content"},
    { "src_field": "text_content", "dst_field": "text_content"},
    { "src_field": "metadata", "dst_field": "metadata"},
    { "src_field": "tool_calls", "dst_field": "tool_calls"},
    { "src_field": "web_search_result", "dst_field": "web_search_result"},
]

#############

workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node ---
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": INPUT_FIELDS
            }
        },

        # --- 2. Anthropic Code Execution LLM Node ---
        "anthropic_analyst": {
            "node_id": "anthropic_analyst",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": LLM_PROVIDER, 
                        "model": LLM_MODEL
                    },
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS,
                    "reasoning_tokens_budget": LLM_REASONING_TOKENS_BUDGET,
                },
                "default_system_prompt": DEFAULT_SYSTEM_PROMPT,
                "tool_calling_config": {
                    "enable_tool_calling": True,
                    "parallel_tool_calls": True
                },
                "tools": [
                    # Web search tool (available on all Anthropic models)
                    {
                        "tool_name": "web_search",
                        "is_provider_inbuilt_tool": True,
                        "provider_inbuilt_user_config": {
                            "max_uses": 5,
                            "allowed_domains": ["wikipedia.org", "iea.org", "irena.org", "bloomberg.com"],
                            "user_location": {
                                "type": "approximate",
                                "city": "New York",
                                "region": "NY",
                                "country": "US"
                            }
                        }
                    },
                    # Code execution tool (available on Claude Opus 4, Sonnet 4, 3.7 Sonnet, 3.5 Haiku)
                    {
                        "tool_name": "code_execution",
                        "is_provider_inbuilt_tool": True,
                        "provider_inbuilt_user_config": None  # No configuration needed
                    }
                ]
            }
        },

        # --- 3. Output Node ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {},
        },
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # Input -> LLM: Pass inputs to the analyst
        { 
            "src_node_id": "input_node", 
            "dst_node_id": "anthropic_analyst", 
            "mappings": field_mappings_from_input_to_llm
        },
        
        # LLM -> Output: Pass all LLM outputs to the output node
        { 
            "src_node_id": "anthropic_analyst", 
            "dst_node_id": "output_node", 
            "mappings": field_mappings_from_llm_to_output
        },
    ],

    # --- Define Start and End ---
    "input_node_id": "input_node",
    "output_node_id": "output_node",
}

# --- Test Execution Logic ---
async def main_test_anthropic_code_execution_workflow():
    """
    Test for Anthropic Code Execution Workflow.
    
    This workflow demonstrates Anthropic's secure Python code execution capabilities
    combined with web search for comprehensive data analysis tasks.
    """
    test_name = "Anthropic Code Execution Workflow Test"
    print(f"--- Starting {test_name} ---")

    # Test inputs focused on data analysis tasks
    test_inputs = {
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": """Analyze the cryptocurrency market trends for Bitcoin and Ethereum over the past year.

Please:
1. Research current market data and recent trends
2. Create visualizations showing price movements
3. Calculate volatility metrics and correlation analysis
4. Perform statistical analysis on trading volumes
5. Generate insights about market patterns
6. Provide risk assessment and future outlook

Use both web search for current information and code execution for detailed analysis.""",
        "enable_reasoning": True
    }

    # No setup documents needed for this workflow
    setup_docs: List[SetupDocInfo] = []
    
    # No cleanup documents needed for this workflow
    cleanup_docs: List[CleanupDocInfo] = []

    # No predefined HITL inputs needed for this workflow
    predefined_hitl_inputs = []

    # Output validation function
    async def validate_code_execution_output(outputs) -> bool:
        """
        Validates the output from the Anthropic code execution workflow.
        
        Args:
            outputs: The workflow output dictionary to validate
            
        Returns:
            bool: True if validation passes, raises AssertionError otherwise
        """
        assert outputs is not None, "Validation Failed: Workflow returned no outputs."
        
        # Check that we have the expected LLM output fields
        expected_fields = ['current_messages', 'content', 'text_content', 'metadata']
        for field in expected_fields:
            assert field in outputs, f"Validation Failed: '{field}' missing from outputs."
        
        # Validate metadata structure
        metadata = outputs.get('metadata', {})
        assert 'model_name' in metadata, "Metadata missing 'model_name' field"
        assert 'token_usage' in metadata, "Metadata missing 'token_usage' field"
        assert 'latency' in metadata, "Metadata missing 'latency' field"
        
        # Validate that it's an Anthropic model
        model_name = metadata.get('model_name', '')
        assert 'claude' in model_name.lower(), f"Expected Claude model, got: {model_name}"
        
        # Validate token usage
        token_usage = metadata.get('token_usage', {})
        assert 'total_tokens' in token_usage, "Token usage missing 'total_tokens' field"
        assert token_usage['total_tokens'] > 0, "Total tokens should be greater than 0"
        
        # Check for reasoning tokens if reasoning was used
        if 'reasoning_tokens' in token_usage:
            print(f"✓ Reasoning tokens used: {token_usage['reasoning_tokens']}")
        
        # Validate content
        content = outputs.get('content')
        assert content is not None, "Content should not be None"
        assert len(str(content)) > 0, "Content should not be empty"
        
        # Validate text content
        text_content = outputs.get('text_content')
        if text_content:
            assert len(text_content) > 0, "Text content should not be empty if present"
        
        # Check if web search was used
        web_search_result = outputs.get('web_search_result')
        if web_search_result:
            print(f"✓ Web search was used - found search results")
            if 'citations' in web_search_result and web_search_result['citations']:
                print(f"✓ Citations found: {len(web_search_result['citations'])} sources")
        
        # Check if tools were called
        tool_calls = outputs.get('tool_calls')
        if tool_calls:
            print(f"✓ Tool calls made: {len(tool_calls)} calls")
            
            # Check for code execution tool calls
            code_execution_calls = [tc for tc in tool_calls if tc.get('tool_name') == 'code_execution']
            if code_execution_calls:
                print(f"✓ Code execution calls: {len(code_execution_calls)}")
            
            # Check for web search tool calls
            web_search_calls = [tc for tc in tool_calls if tc.get('tool_name') == 'web_search']
            if web_search_calls:
                print(f"✓ Web search calls: {len(web_search_calls)}")
        
        # Check tool call count in metadata
        tool_call_count = metadata.get('tool_call_count', 0)
        if tool_call_count > 0:
            print(f"✓ Tool calls in metadata: {tool_call_count}")
        
        # Check if the content suggests code execution was used
        content_str = str(content).lower()
        code_indicators = ['python', 'import', 'df', 'plt', 'pandas', 'numpy', 'matplotlib', 'calculation']
        code_usage_detected = any(indicator in content_str for indicator in code_indicators)
        if code_usage_detected:
            print(f"✓ Code execution usage detected in content")
        
        # Log success message
        print(f"✓ Anthropic code execution workflow validated successfully")
        print(f"✓ Model used: {metadata.get('model_name', 'unknown')}")
        print(f"✓ Total tokens: {token_usage.get('total_tokens', 0)}")
        print(f"✓ Latency: {metadata.get('latency', 0):.2f}s")
        print(f"✓ Content length: {len(str(content))} characters")
        
        return True

    # Execute the test
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        hitl_inputs=predefined_hitl_inputs,
        setup_docs=setup_docs,
        cleanup_docs_created_by_setup=False,
        cleanup_docs=cleanup_docs,
        validate_output_func=validate_code_execution_output,
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=1800  # 30 minutes timeout for complex analysis tasks
    )

    print(f"--- {test_name} Finished ---")
    
    if final_run_outputs:
        # Display key results
        metadata = final_run_outputs.get('metadata', {})
        content = final_run_outputs.get('content', '')
        
        print(f"\n=== ANALYSIS RESULTS ===")
        print(f"Model: {metadata.get('model_name', 'unknown')}")
        print(f"Total Tokens: {metadata.get('token_usage', {}).get('total_tokens', 0)}")
        
        # Show reasoning tokens if used
        reasoning_tokens = metadata.get('token_usage', {}).get('reasoning_tokens', 0)
        if reasoning_tokens > 0:
            print(f"Reasoning Tokens: {reasoning_tokens}")
        
        print(f"Tool Calls: {metadata.get('tool_call_count', 0)}")
        print(f"Latency: {metadata.get('latency', 0):.2f}s")
        
        # Show tool usage breakdown
        tool_calls = final_run_outputs.get('tool_calls', [])
        if tool_calls:
            print(f"\n=== TOOL USAGE BREAKDOWN ===")
            code_calls = sum(1 for tc in tool_calls if tc.get('tool_name') == 'code_execution')
            search_calls = sum(1 for tc in tool_calls if tc.get('tool_name') == 'web_search')
            print(f"Code Execution Calls: {code_calls}")
            print(f"Web Search Calls: {search_calls}")
        
        # Show web search results if available
        web_search_result = final_run_outputs.get('web_search_result')
        if web_search_result and web_search_result.get('citations'):
            print(f"\n=== SOURCES USED ===")
            for i, citation in enumerate(web_search_result['citations'][:3], 1):  # Show first 3 sources
                print(f"{i}. {citation.get('title', 'No title')}")
                print(f"   URL: {citation.get('url', 'No URL')}")
                if citation.get('snippet'):
                    print(f"   Snippet: {citation['snippet'][:100]}...")
                print()
        
        # Show a preview of the analysis content
        print(f"\n=== ANALYSIS PREVIEW ===")
        text_content = final_run_outputs.get('text_content', str(content))
        if text_content:
            # Show first 800 characters
            preview = text_content[:800]
            print(f"{preview}...")
            print(f"\n(Total content length: {len(text_content)} characters)")
        
        # Look for code execution indicators in content
        content_str = str(content).lower()
        code_indicators = ['python', 'import', 'df', 'plt', 'pandas', 'numpy', 'matplotlib']
        found_indicators = [indicator for indicator in code_indicators if indicator in content_str]
        if found_indicators:
            print(f"\n=== CODE EXECUTION DETECTED ===")
            print(f"Found indicators: {', '.join(found_indicators)}")
        
        print(f"\n=== END RESULTS ===")

# Alternative test with different focus
async def test_data_analysis_workflow():
    """
    Alternative test focusing on pure data analysis tasks.
    """
    test_name = "Anthropic Data Analysis Workflow Test"
    print(f"--- Starting {test_name} ---")

    # Test inputs focused on mathematical/statistical analysis
    test_inputs = {
        "system_prompt": """You are a skilled data scientist with expertise in statistical analysis and data visualization.
        
Your task is to perform comprehensive data analysis using Python code execution capabilities.
Focus on:
- Statistical analysis and hypothesis testing
- Data visualization with clear, informative charts
- Mathematical modeling and calculations
- Pattern recognition and trend analysis
- Clear interpretation of results

Write clean, well-documented code and explain your methodology.""",
        "user_prompt": """Analyze the relationship between global temperature anomalies and CO2 concentrations over the past 50 years.

Please:
1. Generate sample data representing historical temperature anomalies and CO2 levels
2. Create visualizations showing both time series
3. Calculate correlation coefficients and statistical significance
4. Perform regression analysis
5. Create scatter plots with trend lines
6. Generate predictive models for future trends
7. Provide comprehensive statistical interpretation

Focus on demonstrating code execution capabilities with real statistical analysis.""",
        "enable_reasoning": True
    }

    # Execute the test with the same validation function
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=test_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        hitl_inputs=[],
        setup_docs=[],
        cleanup_docs_created_by_setup=False,
        cleanup_docs=[],
        validate_output_func=lambda outputs: True,  # Simple validation
        stream_intermediate_results=True,
        poll_interval_sec=5,
        timeout_sec=1200  # 20 minutes timeout
    )

    print(f"--- {test_name} Finished ---")
    return final_run_outputs

if __name__ == "__main__":
    try:
        # Run the main test
        asyncio.run(main_test_anthropic_code_execution_workflow())
        
        # Optionally run the data analysis focused test
        # asyncio.run(test_data_analysis_workflow())
        
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"\nError running test: {e}")
        import traceback
        traceback.print_exc()
