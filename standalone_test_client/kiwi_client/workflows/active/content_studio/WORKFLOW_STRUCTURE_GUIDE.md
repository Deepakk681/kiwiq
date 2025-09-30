# Workflow Structure & Organization Guide

## Executive Summary
This document outlines the standardized structure for organizing workflow files in the KiwiQ content studio sandbox workflows. Each workflow follows a consistent pattern for file organization, making maintenance and updates systematic and predictable.

---

## 📁 Workflow File Structure

### Root Level Files

#### 1. **wf_*_json.py** (Workflow Graph Schema)
- **Purpose**: Defines the complete workflow structure with nodes and edges
- **Contains**:
  - Node definitions (input, output, LLM, HITL, routing, conditions)
  - Edge mappings between nodes
  - Dynamic schemas for inputs/outputs
- **Imports From**:
  - `wf_llm_inputs.py` (all LLM configurations)
  - `document_models.customer_docs` (document constants)
- **Key Changes Required**:
  - Remove inline LLM configurations (provider, model, temperature)
  - Import these configs from `wf_llm_inputs.py` instead

#### 2. **wf_llm_inputs.py** (LLM Configurations & Prompts)
- **Purpose**: Centralized location for all LLM-related configurations
- **Structure**:
  ```python
  # Top Section: Model Configurations
  - TEMPERATURE, MAX_TOKENS, MAX_LLM_ITERATIONS
  - TOOLCALL_LLM_PROVIDER, TOOLCALL_LLM_MODEL
  - DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL

  # Step-based Organization:
  # STEP 1: [Step Name]
  - Description of what happens
  - System prompt with variable explanations
  - User prompt template with variable explanations
  - Output schema for this step

  # STEP 2: [Next Step Name]
  - (Same structure as above)
  ```
- **Requirements**:
  - Group all prompts/schemas by workflow step
  - Include clear descriptions for each step
  - Document any variables used in prompts

#### 3. **[workflow_name]_documentation.md**
- **Purpose**: Detailed workflow documentation
- **Note**: Not required to be read/modified during standard updates

---

## 📂 wf_testing/ Folder Structure

### Core Testing Files

#### 1. **sandbox_setup_docs.py**
- **Purpose**: Creates required documents before workflow execution
- **Contains**:
  - Document creation logic for:
    - Input documents (e.g., blog brief, content calendar)
    - Company guidelines/documentation
    - System documents (e.g., SEO best practices)
- **Imports**:
  - Document constants from `document_models.customer_docs`
  - `test_sandbox_company_name` from `sandbox_identifiers.py`
- **Key Elements**:
  - `setup_docs` list - documents to create
  - `cleanup_docs` list - documents to remove after testing
  - Test data definitions for each document type

#### 2. **wf_inputs.py**
- **Purpose**: Initial inputs for workflow execution
- **Contains**:
  ```python
  test_scenario = {
      "name": "Scenario Name",
      "initial_inputs": {
          "company_name": test_sandbox_company_name,
          "brief_docname": test_brief_docname,
          "post_uuid": "unique_id",
          "load_additional_user_files": []  # Optional
      }
  }
  ```
- **Imports From**:
  - `sandbox_identifiers.py` (company name)
  - `sandbox_setup_docs.py` (test document names)

#### 3. **wf_runner.py**
- **Purpose**: Main workflow execution file
- **Key Functions**:
  - `main_test_[workflow_name]()` - Main test function
  - `validate_[workflow_name]_output()` - Output validation
- **Imports Required**:
  - `workflow_graph_schema` from main json file
  - `test_scenario` from `wf_inputs.py`
  - `setup_docs, cleanup_docs` from `sandbox_setup_docs.py`
- **Verification Needed**: Ensure all imports are correct

#### 4. **wf_run_hitl_inputs.py**
- **Purpose**: Predefined HITL (Human-in-the-Loop) responses for testing
- **Note**: Not critical for initial setup

#### 5. **wf_state_filter_mapping.py**
- **Purpose**: Configure state filtering for debugging
- **Note**: Not critical for initial setup

---

## 🔄 Standard Update Process

### When Updating a Workflow:

1. **In wf_*_json.py**:
   - [ ] Remove inline LLM configurations
   - [ ] Add imports from `wf_llm_inputs.py`
   - [ ] Verify all node references use imported configs

2. **In wf_llm_inputs.py**:
   - [ ] Move LLM configurations to top section
   - [ ] Organize prompts by workflow steps
   - [ ] Add step descriptions and variable documentation
   - [ ] Group related prompts and schemas together

3. **In wf_testing/sandbox_setup_docs.py**:
   - [ ] Verify document creation logic
   - [ ] Check imports from `sandbox_identifiers.py`
   - [ ] Ensure test data matches expected schemas

4. **In wf_testing/wf_inputs.py**:
   - [ ] Verify initial inputs structure
   - [ ] Check imports are correct
   - [ ] Ensure company name uses sandbox identifier

5. **In wf_testing/wf_runner.py**:
   - [ ] Verify all imports are present and correct
   - [ ] Check workflow name constant
   - [ ] Ensure validation logic matches expected outputs

---

## 📍 Key Import Locations

### Common Import Sources:
```python
# Sandbox identifier (shared across all workflows)
from kiwi_client.workflows.active.sandbox_identifiers import (
    test_sandbox_company_name  # Currently: "momentum"
)

# Document models
from kiwi_client.workflows.active.document_models.customer_docs import (
    # Import relevant document constants for your workflow
)

# From within workflow folder
from ..wf_llm_inputs import (
    # All LLM configurations and prompts
)

from ..wf_[workflow_name]_json import (
    workflow_graph_schema
)
```

---

## ✅ Validation Checklist

Before considering a workflow complete:

1. **Structure**:
   - [ ] All files follow naming conventions
   - [ ] LLM configs separated into `wf_llm_inputs.py`
   - [ ] Prompts organized by steps with descriptions

2. **Imports**:
   - [ ] Sandbox identifier imported correctly
   - [ ] Document models imported as needed
   - [ ] All cross-file imports verified

3. **Testing**:
   - [ ] Runner file has correct imports
   - [ ] Setup docs creates necessary documents
   - [ ] Initial inputs properly configured

4. **Documentation**:
   - [ ] Step descriptions clear in llm_inputs
   - [ ] Variable usage documented
   - [ ] Workflow purpose documented in main file

---

## 📝 Quick Reference

| File | Purpose | Key Changes |
|------|---------|-------------|
| `wf_*_json.py` | Workflow structure | Remove LLM configs, import from llm_inputs |
| `wf_llm_inputs.py` | LLM configs & prompts | Organize by steps with descriptions |
| `sandbox_setup_docs.py` | Document creation | Verify imports and test data |
| `wf_inputs.py` | Initial inputs | Use sandbox company name |
| `wf_runner.py` | Execute workflow | Verify all imports |

---

*Last Updated: 2025-09-29*
*This guide applies to all content studio sandbox workflows*