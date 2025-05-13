import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel


# --- Test Execution Logic ---

# --- Inputs for the Post Creation Workflow ---
# These inputs match the 'input_node' dynamic_output_schema


import logging

# Configure logging
logging.basicConfig(level=logging.INFO) # Use INFO level for less verbose output
logger = logging.getLogger(__name__)

# Import the new helper function and necessary types
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
# CustomerDataTestClient is no longer directly needed in main, but keep for potential future use or reference
# from kiwi_client.customer_data_client import CustomerDataTestClient

# Removed the ensure_user_dna_exists function as setup is handled by run_workflow_test




import asyncio
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus
from kiwi_client.test_run_workflow_client import run_workflow_test

async def run_test(code_str: str):

    ns = {"__builtins__": __builtins__}
    exec(code_str, ns)

    var_list = ["test_name",
        "workflow_graph_schema",
        "workflow_inputs",
        "expected_final_status",
        "predefined_hitl_inputs",
        "setup_docs",
        "cleanup_docs",
        "validate_workflow_output",
        "stream_intermediate_results",
        "poll_interval_sec",
        "timeout_sec"
    ]
    for var in var_list:
        if var in ns:
            print(f"{var}: FOUND")
        else:
            print(f"{var} not found in namespace")

    # Get variables from ns with defaults if not found
    test_name = ns.get("test_name", "Content Workflow Test")
    workflow_graph_schema = ns.get("workflow_graph_schema", {})
    workflow_inputs = ns.get("workflow_inputs", {})
    
    # 
    predefined_hitl_inputs = ns.get("predefined_hitl_inputs", [])
    
    
    # OPTIONAL BUT RECOMMENDED
    setup_docs = ns.get("setup_docs", [])
    cleanup_docs = ns.get("cleanup_docs", [])
    
    # OPTIONAL
    expected_final_status = ns.get("expected_final_status", WorkflowRunStatus.COMPLETED)
    validate_workflow_output = ns.get("validate_workflow_output", None)
    stream_intermediate_results = ns.get("stream_intermediate_results", True)
    poll_interval_sec = ns.get("poll_interval_sec", 3)
    timeout_sec = ns.get("timeout_sec", 600)
    
    # Run the workflow test function
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=workflow_inputs,
        expected_final_status=expected_final_status,
        hitl_inputs=predefined_hitl_inputs,
        setup_docs=setup_docs,
        cleanup_docs=cleanup_docs,
        validate_output_func=validate_workflow_output,
        stream_intermediate_results=stream_intermediate_results,
        poll_interval_sec=poll_interval_sec,
        timeout_sec=timeout_sec
    )
    
    # # Display final results if available
    # if final_run_outputs and 'final_post_content' in final_run_outputs:
    #     post = final_run_outputs['final_post_content']
    #     print("\nGenerated LinkedIn Post:")
    #     print("-" * 50)
    #     print(post.get('post_text', 'No post text generated'))
    #     print("\nHashtags:")
    #     print(", ".join(post.get('hashtags', [])))
    #     print("-" * 50)
    
    return final_run_status_obj, final_run_outputs
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Workflow Test API", description="API to run workflow tests from code strings")


@app.get("/", response_class=HTMLResponse)
async def code_form():
    """
    Serves an HTML page with a form that allows submitting Python code to the run_workflow_test endpoint.
    """
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Workflow Test Code Form</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            #code-form {
                margin-top: 20px;
            }
            textarea {
                width: 100%;
                height: 500px;
                font-family: monospace;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-sizing: border-box;
                margin-bottom: 10px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            #result {
                margin-top: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f8f8;
                white-space: pre-wrap;
                display: none;
            }
            .spinner {
                display: none;
                margin-left: 10px;
                vertical-align: middle;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(0, 0, 0, 0.1);
                border-radius: 50%;
                border-top-color: #4CAF50;
                animation: spin 1s ease-in-out infinite;
            }
            @keyframes spin {
                to {
                    transform: rotate(360deg);
                }
            }
        </style>
    </head>
    <body>
        <h1>Workflow Test Code Form</h1>
        <p>Enter your Python code in the textarea below and click Submit to run the workflow test.</p>
        
        <form id="code-form">
            <textarea id="code-input" placeholder="Enter your Python code here..."></textarea>
            <button type="submit">Run Workflow Test <div id="spinner" class="spinner"></div></button>
        </form>
        
        <div id="result"></div>
        
        <script>
            document.getElementById('code-form').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const codeInput = document.getElementById('code-input').value;
                const resultDiv = document.getElementById('result');
                const spinner = document.getElementById('spinner');
                
                resultDiv.style.display = 'none';
                spinner.style.display = 'inline-block';
                
                try {
                    const response = await fetch('/run_workflow_test', {
                        method: 'POST',
                        body: codeInput,
                        headers: {
                            'Content-Type': 'text/plain'
                        }
                    });
                    
                    const result = await response.json();
                    
                    resultDiv.textContent = JSON.stringify(result, null, 2);
                    resultDiv.style.display = 'block';
                } catch (error) {
                    resultDiv.textContent = 'Error: ' + error.message;
                    resultDiv.style.display = 'block';
                } finally {
                    spinner.style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    """)


@app.post("/run_workflow_test")
async def api_run_workflow_test(request: Request):
    """
    POST endpoint to run a workflow test from a code string.
    Accepts the entire request body as a code string.
    
    Returns:
        JSON response with test results or error information.
    """
    try:
        # Get raw request body as string
        code_str = await request.body()
        code_str = code_str.decode("utf-8")
        
        # Run the test
        status_obj, outputs = await run_test(code_str)
        
        # Prepare response
        result = {
            "success": True,
            "status": str(status_obj.status) if status_obj else "Unknown",
            "outputs": outputs
        }
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.exception(f"Error running workflow test via API: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    # If this file is run directly, start the FastAPI development server
    uvicorn.run("test_string_exec:app", host="0.0.0.0", port=8005, reload=True)
    # # Run the async function
    # try:
    #     final_status, final_outputs = asyncio.run(run_test(CODE))
    #     # print(f"Workflow completed with status: {final_status.status if final_status else 'Unknown'}")
    # except Exception as e:
    #     print(f"Error running workflow test: {e}")

