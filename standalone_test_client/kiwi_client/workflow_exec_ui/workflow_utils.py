"""
Utility functions for discovering and gathering workflow information.

This module provides functions to:
1. Discover all workflow JSON schema files
2. Extract workflow metadata (category, name, content)
3. Fetch associated workflow files (LLM inputs, testing files)
4. Get sandbox identifiers
5. Combine all workflow data into structured format

Author: AI Assistant
Date: 2025-09-26
"""

import os
import glob
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import logging

# For variable editing functionality
import libcst as cst
import libcst.matchers as m

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class _UpdateAssign(cst.CSTTransformer):
    """
    CST Transformer for updating variable assignments in Python files.
    Handles both regular assignments (x = value) and annotated assignments (x: type = value).
    """
    
    def __init__(self, var_name: str, new_value_node: cst.BaseExpression):
        """
        Initialize the transformer.
        
        Args:
            var_name: Name of the variable to update
            new_value_node: CST expression node representing the new value
        """
        self.var_name = var_name
        self.new_value_node = new_value_node
        self.updated = False

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.BaseStatement:
        """Handle regular assignments: x = 1 or a = b = 1"""
        if any(m.matches(t.target, m.Name(self.var_name)) for t in original_node.targets):
            self.updated = True
            return updated_node.with_changes(value=self.new_value_node)
        return updated_node

    def leave_AnnAssign(self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign) -> cst.BaseStatement:
        """Handle annotated assignments: x: int = 1"""
        if m.matches(original_node.target, m.Name(self.var_name)) and original_node.value is not None:
            self.updated = True
            return updated_node.with_changes(value=self.new_value_node)
        return updated_node


def update_global_var(file_path: Union[str, Path], name: str, value: Any) -> bool:
    """
    Update a global variable in a Python file while preserving formatting and comments.
    
    Args:
        file_path: Path to the Python file to modify
        name: Variable name to update
        value: New value for the variable
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ImportError: If libcst is not available
        FileNotFoundError: If the file doesn't exist
    """

    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        # Read the current file content
        code = file_path.read_text(encoding="utf-8")
        
        # Build a CST expression from the Python value
        new_value_node = cst.parse_expression(repr(value))
        
        # Parse the module and apply the transformer
        mod = cst.parse_module(code)
        transformer = _UpdateAssign(name, new_value_node)
        new_mod = mod.visit(transformer)
        
        # If variable wasn't found, append it at the end
        if not transformer.updated:
            # Create a new assignment statement
            stmt = cst.parse_statement(f"{name} = {repr(value)}\n")
            new_mod = new_mod.with_changes(body=(*new_mod.body, stmt))
            logger.info(f"📝 APPENDING new variable '{name}' to {file_path}")
        else:
            logger.info(f"📝 UPDATING existing variable '{name}' in {file_path}")
        
        # Write the updated code back to file
        file_path.write_text(new_mod.code, encoding="utf-8")
        
        # Print the change clearly
        print(f"\n🔧 FILE EDIT: {file_path}")
        print(f"   Variable: {name}")
        print(f"   New Value: {repr(value)}")
        print(f"   Action: {'APPEND' if not transformer.updated else 'UPDATE'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating variable '{name}' in {file_path}: {e}")
        print(f"\n❌ FILE EDIT FAILED: {file_path}")
        print(f"   Variable: {name}")
        print(f"   Error: {e}")
        return False


def get_workflow_variable(workflow_info: Dict[str, Any], file_type: str, var_name: str) -> Any:
    """
    Get a specific variable value from a workflow's file.
    
    Args:
        workflow_info: Workflow information dictionary
        file_type: Type of file ('llm_inputs', 'testing_inputs', 'sandbox_setup', 'state_filter')
        var_name: Name of the variable to get
        
    Returns:
        Variable value or None if not found
    """
    try:
        if file_type == 'llm_inputs':
            module = workflow_info.get('llm_inputs')
        elif file_type == 'sandbox_identifiers':
            # This is handled separately since it's global
            module = workflow_info.get('sandbox_identifiers')
        else:
            # Handle testing files
            testing_files = workflow_info.get('testing_files', {})
            if file_type == 'testing_inputs':
                module = testing_files.get('wf_inputs')
            elif file_type == 'sandbox_setup':
                module = testing_files.get('sandbox_setup_docs')
            elif file_type == 'state_filter':
                module = testing_files.get('wf_state_filter_mapping')
            else:
                logger.error(f"Unknown file_type: {file_type}")
                return None
        
        if module and hasattr(module, var_name):
            return getattr(module, var_name)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting variable '{var_name}' from {file_type}: {e}")
        return None


def update_workflow_variable(workflow_info: Dict[str, Any], file_type: str, var_name: str, value: Any) -> bool:
    """
    Update a variable in a workflow's file.
    
    Args:
        workflow_info: Workflow information dictionary
        file_type: Type of file ('llm_inputs', 'testing_inputs', 'sandbox_setup', 'state_filter')
        var_name: Name of the variable to update
        value: New value for the variable
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        workflows_root = get_workflows_root_path()
        category = workflow_info['metadata']['category']
        workflow_name = workflow_info['metadata']['workflow_name']
        
        # Determine the file path based on file_type
        if file_type == 'llm_inputs':
            file_path = workflows_root / category / workflow_name / 'wf_llm_inputs.py'
        elif file_type == 'testing_inputs':
            file_path = workflows_root / category / workflow_name / 'wf_testing' / 'wf_inputs.py'
        elif file_type == 'sandbox_setup':
            file_path = workflows_root / category / workflow_name / 'wf_testing' / 'sandbox_setup_docs.py'
        elif file_type == 'state_filter':
            file_path = workflows_root / category / workflow_name / 'wf_testing' / 'wf_state_filter_mapping.py'
        else:
            logger.error(f"Unknown file_type: {file_type}")
            return False
        
        # Update the variable
        success = update_global_var(file_path, var_name, value)
        
        if success:
            # Reload the module to reflect changes in our data structure
            logger.info(f"Reloading module data for {category}/{workflow_name}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error updating workflow variable: {e}")
        return False


def update_sandbox_identifiers_variable(var_name: str, value: Any) -> bool:
    """
    Update a variable in the global sandbox_identifiers.py file.
    
    Args:
        var_name: Name of the variable to update
        value: New value for the variable
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        workflows_root = get_workflows_root_path()
        sandbox_file = workflows_root / 'sandbox_identifiers.py'
        
        return update_global_var(sandbox_file, var_name, value)
        
    except Exception as e:
        logger.error(f"Error updating sandbox identifiers variable: {e}")
        return False


def get_workflows_root_path() -> Path:
    """
    Get the root path for workflows relative to current file location.
    
    Current file: standalone_test_client/kiwi_client/workflow_exec_ui/workflow_utils.py
    Target: standalone_test_client/kiwi_client/workflows/active/
    
    Returns:
        Path: The absolute path to the workflows/active directory
    """
    # Get current file directory
    current_dir = Path(__file__).parent
    # Navigate back to workflows/active
    workflows_root = current_dir.parent / "workflows" / "active"
    
    if not workflows_root.exists():
        raise FileNotFoundError(f"Workflows directory not found: {workflows_root}")
    
    return workflows_root.resolve()


def discover_workflow_json_files() -> List[Dict[str, Any]]:
    """
    Discover all workflow JSON schema files matching pattern: *_json.py
    
    Returns:
        List[Dict]: List of dictionaries containing:
            - file_path: Absolute path to the JSON file
            - category: Workflow category (directory name)
            - workflow_name: Workflow name (directory name)
            - relative_path: Path relative to workflows/active
    """
    workflows_root = get_workflows_root_path()
    
    # Find all *_json.py files
    json_files = []
    pattern = "**/*_json.py"
    
    for file_path in workflows_root.glob(pattern):
        # Extract category and workflow name from path structure
        # Expected structure: workflows/active/<category>/<workflow_name>/*_json.py
        relative_path = file_path.relative_to(workflows_root)
        path_parts = relative_path.parts
        
        if len(path_parts) >= 3:  # category/workflow_name/file.py
            category = path_parts[0]
            workflow_name = path_parts[1]
            
            json_files.append({
                'file_path': file_path,
                'category': category,
                'workflow_name': workflow_name,
                'relative_path': str(relative_path),
                'filename': file_path.name
            })
    
    logger.info(f"Found {len(json_files)} workflow JSON files")
    return json_files


def load_python_module_content(file_path: Path) -> Optional[Any]:
    """
    Load content from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Module content or None if loading fails
    """
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
            
        spec = importlib.util.spec_from_file_location("module", file_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Could not load spec for: {file_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
        
    except Exception as e:
        logger.error(f"Error loading module {file_path}: {e}")
        return None


def get_workflow_json_content(workflow_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract the JSON schema content from a workflow JSON file.
    
    Args:
        workflow_info: Dictionary containing workflow file information
        
    Returns:
        Dictionary containing the workflow schema or None if extraction fails
    """
    try:
        file_path = workflow_info['file_path']
        module = load_python_module_content(file_path)
        
        if module is None:
            return None
        
        # Look for common function names that return workflow schema
        # Based on the pattern, these files typically have a main function that returns the schema
        schema_functions = ['main', 'get_workflow_schema', 'workflow_schema', 'get_graph_schema']
        
        for func_name in schema_functions:
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                if callable(func):
                    try:
                        schema = func()
                        if isinstance(schema, dict):
                            return schema
                    except Exception as e:
                        logger.warning(f"Error calling {func_name}() in {file_path}: {e}")
                        continue
        
        # If no function found, look for direct schema variables
        schema_vars = ['WORKFLOW_SCHEMA', 'GRAPH_SCHEMA', 'schema', 'workflow_schema']
        for var_name in schema_vars:
            if hasattr(module, var_name):
                schema = getattr(module, var_name)
                if isinstance(schema, dict):
                    return schema
        
        logger.warning(f"Could not extract schema from {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting JSON content from {workflow_info}: {e}")
        return None


def get_workflow_llm_inputs(workflow_info: Dict[str, Any]) -> Optional[Any]:
    """
    Get LLM inputs file (wf_llm_inputs.py) for a workflow.
    
    Args:
        workflow_info: Dictionary containing workflow information
        
    Returns:
        Module content or None if file not found
    """
    try:
        workflows_root = get_workflows_root_path()
        llm_inputs_path = workflows_root / workflow_info['category'] / workflow_info['workflow_name'] / 'wf_llm_inputs.py'
        
        return load_python_module_content(llm_inputs_path)
        
    except Exception as e:
        logger.error(f"Error loading LLM inputs for {workflow_info}: {e}")
        return None


def get_workflow_testing_files(workflow_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get workflow testing files from wf_testing directory.
    
    Args:
        workflow_info: Dictionary containing workflow information
        
    Returns:
        Dictionary containing testing file contents:
        - wf_inputs: Content of wf_inputs.py
        - sandbox_setup_docs: Content of sandbox_setup_docs.py  
        - wf_state_filter_mapping: Content of wf_state_filter_mapping.py
    """
    testing_files = {
        'wf_inputs': None,
        'sandbox_setup_docs': None,
        'wf_state_filter_mapping': None
    }
    
    try:
        workflows_root = get_workflows_root_path()
        testing_dir = workflows_root / workflow_info['category'] / workflow_info['workflow_name'] / 'wf_testing'
        
        if not testing_dir.exists():
            logger.warning(f"Testing directory not found: {testing_dir}")
            return testing_files
        
        # Load each testing file
        test_files = {
            'wf_inputs': 'wf_inputs.py',
            'sandbox_setup_docs': 'sandbox_setup_docs.py',
            'wf_state_filter_mapping': 'wf_state_filter_mapping.py'
        }
        
        for key, filename in test_files.items():
            file_path = testing_dir / filename
            testing_files[key] = load_python_module_content(file_path)
            
    except Exception as e:
        logger.error(f"Error loading testing files for {workflow_info}: {e}")
    
    return testing_files


def get_sandbox_identifiers() -> Optional[Any]:
    """
    Get the sandbox_identifiers.py file content.
    
    Returns:
        Module content or None if file not found
    """
    try:
        workflows_root = get_workflows_root_path()
        sandbox_file = workflows_root / 'sandbox_identifiers.py'
        
        return load_python_module_content(sandbox_file)
        
    except Exception as e:
        logger.error(f"Error loading sandbox identifiers: {e}")
        return None


def get_all_workflows_data() -> Dict[str, Any]:
    """
    Get comprehensive data for all workflows.
    
    Returns:
        Dictionary containing:
        - workflows: List of workflow data dictionaries
        - sandbox_identifiers: Sandbox identifiers module
        - summary: Summary statistics
    """
    logger.info("Starting comprehensive workflow data collection...")
    
    # Discover all workflows
    workflow_json_files = discover_workflow_json_files()
    
    # Get sandbox identifiers (shared across all workflows)
    sandbox_identifiers = get_sandbox_identifiers()
    
    # Process each workflow
    workflows_data = []
    
    for workflow_info in workflow_json_files:
        logger.info(f"Processing workflow: {workflow_info['category']}/{workflow_info['workflow_name']}")
        
        # Get JSON schema content
        json_content = get_workflow_json_content(workflow_info)
        
        # Get LLM inputs
        llm_inputs = get_workflow_llm_inputs(workflow_info)
        
        # Get testing files
        testing_files = get_workflow_testing_files(workflow_info)
        
        # Combine all workflow data
        workflow_data = {
            'metadata': workflow_info,
            'json_schema': json_content,
            'llm_inputs': llm_inputs,
            'testing_files': testing_files,
            'has_json_schema': json_content is not None,
            'has_llm_inputs': llm_inputs is not None,
            'has_testing_files': any(v is not None for v in testing_files.values())
        }
        
        workflows_data.append(workflow_data)
    
    # Create summary
    total_workflows = len(workflows_data)
    workflows_with_json = sum(1 for w in workflows_data if w['has_json_schema'])
    workflows_with_llm = sum(1 for w in workflows_data if w['has_llm_inputs'])
    workflows_with_testing = sum(1 for w in workflows_data if w['has_testing_files'])
    
    summary = {
        'total_workflows': total_workflows,
        'workflows_with_json_schema': workflows_with_json,
        'workflows_with_llm_inputs': workflows_with_llm,
        'workflows_with_testing_files': workflows_with_testing,
        'categories': list(set(w['metadata']['category'] for w in workflows_data))
    }
    
    result = {
        'workflows': workflows_data,
        'sandbox_identifiers': sandbox_identifiers,
        'summary': summary
    }
    
    logger.info(f"Data collection complete. Summary: {summary}")
    return result


def get_workflow_by_name(category: str, workflow_name: str) -> Optional[Dict[str, Any]]:
    """
    Get specific workflow data by category and name.
    
    Args:
        category: Workflow category
        workflow_name: Workflow name
        
    Returns:
        Workflow data dictionary or None if not found
    """
    all_data = get_all_workflows_data()
    
    for workflow in all_data['workflows']:
        if (workflow['metadata']['category'] == category and 
            workflow['metadata']['workflow_name'] == workflow_name):
            return workflow
    
    return None


def list_available_workflows() -> List[Tuple[str, str]]:
    """
    Get a simple list of available workflows.
    
    Returns:
        List of tuples: (category, workflow_name)
    """
    workflow_json_files = discover_workflow_json_files()
    return [(w['category'], w['workflow_name']) for w in workflow_json_files]


# Convenience functions for testing and variable management
def list_workflow_variables(workflow_info: Dict[str, Any], file_type: str) -> Dict[str, Any]:
    """
    List all variables from a specific workflow file.
    
    Args:
        workflow_info: Workflow information dictionary
        file_type: Type of file ('llm_inputs', 'testing_inputs', 'sandbox_setup', 'state_filter')
        
    Returns:
        Dictionary of variable names and values
    """
    try:
        if file_type == 'llm_inputs':
            module = workflow_info.get('llm_inputs')
        else:
            testing_files = workflow_info.get('testing_files', {})
            if file_type == 'testing_inputs':
                module = testing_files.get('wf_inputs')
            elif file_type == 'sandbox_setup':
                module = testing_files.get('sandbox_setup_docs')
            elif file_type == 'state_filter':
                module = testing_files.get('wf_state_filter_mapping')
            else:
                logger.error(f"Unknown file_type: {file_type}")
                return {}
        
        if module is None:
            return {}
        
        # Get all non-private attributes (those not starting with _)
        variables = {}
        for name in dir(module):
            if not name.startswith('_'):
                try:
                    value = getattr(module, name)
                    # Only include basic types and avoid functions/classes
                    if not callable(value):
                        variables[name] = value
                except:
                    pass
        
        return variables
        
    except Exception as e:
        logger.error(f"Error listing variables from {file_type}: {e}")
        return {}


def list_sandbox_variables() -> Dict[str, Any]:
    """
    List all variables from sandbox_identifiers.py.
    
    Returns:
        Dictionary of variable names and values
    """
    try:
        sandbox_module = get_sandbox_identifiers()
        if sandbox_module is None:
            return {}
        
        variables = {}
        for name in dir(sandbox_module):
            if not name.startswith('_'):
                try:
                    value = getattr(sandbox_module, name)
                    if not callable(value):
                        variables[name] = value
                except:
                    pass
        
        return variables
        
    except Exception as e:
        logger.error(f"Error listing sandbox variables: {e}")
        return {}


def demo_variable_editing():
    """
    Demonstrate variable editing functionality with examples.
    """
    print("\n🧪 VARIABLE EDITING DEMO")
    print("=" * 50)
    
    # Demo 1: Update sandbox identifiers
    print("\n1. Updating sandbox_identifiers.py:")
    current_vars = list_sandbox_variables()
    print(f"   Current variables: {list(current_vars.keys())}")
    
    if 'test_sandbox_company_name' in current_vars:
        old_value = current_vars['test_sandbox_company_name']
        new_value = f"{old_value}_updated"
        success = update_sandbox_identifiers_variable('test_sandbox_company_name', new_value)
        if success:
            print(f"   ✓ Updated test_sandbox_company_name: '{old_value}' → '{new_value}'")
        else:
            print(f"   ✗ Failed to update test_sandbox_company_name")
    
    # Demo 2: Update workflow variables
    print("\n2. Finding workflows with variables to update:")
    workflows_data = get_all_workflows_data()
    
    for workflow in workflows_data['workflows'][:2]:  # Demo with first 2 workflows
        category = workflow['metadata']['category']
        workflow_name = workflow['metadata']['workflow_name']
        print(f"\n   Workflow: {category}/{workflow_name}")
        
        # Check LLM inputs
        if workflow['has_llm_inputs']:
            llm_vars = list_workflow_variables(workflow, 'llm_inputs')
            print(f"     LLM Input variables: {list(llm_vars.keys())}")
            
            # Try to update a simple variable if it exists
            for var_name, var_value in llm_vars.items():
                if isinstance(var_value, str) and len(var_name) < 20:  # Simple string variable
                    print(f"     Attempting to demo edit of '{var_name}'...")
                    # Don't actually edit for demo, just show how it would work
                    print(f"     Would call: update_workflow_variable(workflow, 'llm_inputs', '{var_name}', 'new_value')")
                    break
        
        # Check testing inputs
        if workflow['has_testing_files']:
            testing_vars = list_workflow_variables(workflow, 'testing_inputs')
            if testing_vars:
                print(f"     Testing Input variables: {list(testing_vars.keys())}")


def print_workflow_summary():
    """Print a summary of all discovered workflows."""
    data = get_all_workflows_data()
    
    print("\n=== WORKFLOW DISCOVERY SUMMARY ===")
    print(f"Total workflows found: {data['summary']['total_workflows']}")
    print(f"Categories: {', '.join(data['summary']['categories'])}")
    print(f"Workflows with JSON schema: {data['summary']['workflows_with_json_schema']}")
    print(f"Workflows with LLM inputs: {data['summary']['workflows_with_llm_inputs']}")
    print(f"Workflows with testing files: {data['summary']['workflows_with_testing_files']}")
    
    print("\n=== INDIVIDUAL WORKFLOWS ===")
    for workflow in data['workflows']:
        meta = workflow['metadata']
        print(f"• {meta['category']}/{meta['workflow_name']}")
        print(f"  - JSON Schema: {'✓' if workflow['has_json_schema'] else '✗'}")
        print(f"  - LLM Inputs: {'✓' if workflow['has_llm_inputs'] else '✗'}")
        print(f"  - Testing Files: {'✓' if workflow['has_testing_files'] else '✗'}")
    
    print(f"\n=== SANDBOX IDENTIFIERS ===")
    sandbox = data['sandbox_identifiers']
    if sandbox:
        print("✓ Found sandbox_identifiers.py")
        # Try to show some attributes if available
        if hasattr(sandbox, 'test_sandbox_company_name'):
            print(f"  - Company: {sandbox.test_sandbox_company_name}")
        if hasattr(sandbox, 'test_brief_uuid'):
            print(f"  - Brief UUID: {sandbox.test_brief_uuid}")
    else:
        print("✗ sandbox_identifiers.py not found")


def example_usage():
    """
    Example usage of the workflow utilities and variable editing functionality.
    """
    print("\n📚 WORKFLOW UTILITIES USAGE EXAMPLES")
    print("=" * 60)
    
    # Example 1: Basic workflow discovery
    print("\n1. Discover all workflows:")
    workflows = list_available_workflows()
    print(f"   Found {len(workflows)} workflows:")
    for category, name in workflows[:3]:  # Show first 3
        print(f"     - {category}/{name}")
    if len(workflows) > 3:
        print(f"     ... and {len(workflows) - 3} more")
    
    # Example 2: Get specific workflow data
    print("\n2. Get specific workflow data:")
    if workflows:
        category, name = workflows[0]
        workflow_data = get_workflow_by_name(category, name)
        if workflow_data:
            print(f"   Retrieved data for: {category}/{name}")
            print(f"   Has JSON schema: {workflow_data['has_json_schema']}")
            print(f"   Has LLM inputs: {workflow_data['has_llm_inputs']}")
            print(f"   Has testing files: {workflow_data['has_testing_files']}")
    
    # Example 3: List variables from a workflow
    print("\n3. List variables from workflow files:")
    if workflows:
        category, name = workflows[0]
        workflow_data = get_workflow_by_name(category, name)
        if workflow_data:
            # Show LLM input variables
            if workflow_data['has_llm_inputs']:
                llm_vars = list_workflow_variables(workflow_data, 'llm_inputs')
                print(f"   LLM input variables in {category}/{name}:")
                for var_name, var_value in list(llm_vars.items())[:3]:  # Show first 3
                    print(f"     - {var_name}: {type(var_value).__name__} = {str(var_value)[:50]}...")
            
            # Show testing variables
            if workflow_data['has_testing_files']:
                test_vars = list_workflow_variables(workflow_data, 'testing_inputs')
                if test_vars:
                    print(f"   Testing input variables in {category}/{name}:")
                    for var_name, var_value in list(test_vars.items())[:3]:  # Show first 3
                        print(f"     - {var_name}: {type(var_value).__name__} = {str(var_value)[:50]}...")
    
    # Example 4: Sandbox variables
    print("\n4. Sandbox identifier variables:")
    sandbox_vars = list_sandbox_variables()
    for var_name, var_value in sandbox_vars.items():
        print(f"   - {var_name}: {repr(var_value)}")
    
    # Example 5: Variable editing (conceptual)
    print("\n5. Variable editing examples:")
    print("   # Update a sandbox identifier:")
    print("   update_sandbox_identifiers_variable('test_sandbox_company_name', 'new_company')")
    print("   ")
    print("   # Update a workflow variable:")
    print("   workflow_data = get_workflow_by_name('content_studio', 'blog_aeo_seo_scoring')")
    print("   update_workflow_variable(workflow_data, 'llm_inputs', 'some_variable', 'new_value')")
    print("   ")
    print("   # Get a specific variable:")
    print("   value = get_workflow_variable(workflow_data, 'llm_inputs', 'some_variable')")
    
    print(f"\n💡 For interactive variable editing demo, call: demo_variable_editing()")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run variable editing demo
        demo_variable_editing()
    elif len(sys.argv) > 1 and sys.argv[1] == "examples":
        # Show usage examples
        example_usage()
    else:
        # Default: show workflow summary
        print_workflow_summary()

