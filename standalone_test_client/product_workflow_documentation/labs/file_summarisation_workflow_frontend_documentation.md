# File Summarisation Workflow - Frontend Implementation Guide

## Workflow Purpose
This workflow generates comprehensive document summaries with human review and feedback capabilities. It automatically processes documents, creates intelligent summaries, and allows users to approve or request revisions.

## Input Node Requirements

When initiating the workflow, the frontend must provide the following data structure:

### Required Fields

1. **summary_context** (string, required)
   - The context or purpose for the document summarization
   - Example: "Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024"

2. **asset_name** (string, required)
   - Asset name used for organizing and naming the summary
   - Example: "healthcare_ai_2024"

3. **load_additional_user_files** (list, required)
   - List of additional documents to include in the summarization
   - Each item must contain:
     - **namespace**: The storage namespace of the file
     - **docname**: The document name
     - **is_shared**: Boolean indicating if the file is shared
   - Example:
     ```
     [
       {
         "namespace": "summary_context_files_healthcare",
         "docname": "ai_diagnostic_trends_2024",
         "is_shared": false
       }
     ]
     ```

### Optional Fields

1. **namespace** (string, optional)
   - Custom namespace for saving the summary
   - Default: "document_summary_reports_{item}" where {item} is replaced with asset_name
   - Example: "document_summary_reports_healthcare_{item}"

2. **docname** (string, optional)
   - Custom document name for the summary
   - If not provided, the system generates a unique name automatically
   - Example: "ai_healthcare_impact_2024_summary"

3. **is_shared** (boolean, optional)
   - Determines if the summary should be shared
   - Default: false

## HITL Node Output and Input Requirements

### What the User Sees (HITL Output)

When the workflow reaches the human-in-the-loop approval stage, the frontend displays:

1. **summary_content**: The generated summary document containing:
   - **report**: The full text of the generated summary

### What Input the Frontend Must Collect (HITL Input)

The frontend must collect and send back the following structured data:

#### Required Fields

1. **user_action** (enum, required)
   - Must be one of: "approve", "request_revisions", "cancel"
   - Controls the workflow progression

#### Conditional Fields

2. **revision_feedback** (string, optional but required if user_action is "request_revisions")
   - Detailed feedback for improving the summary
   - Example: "Please expand the section on regulatory challenges and add more specific examples"

#### Optional Fields

3. **load_additional_user_files** (list, optional)
   - Additional documents to consider during revision
   - Same structure as input node's load_additional_user_files
   - Default: empty list []
   - Example:
     ```
     [
       {
         "namespace": "summary_context_files_healthcare",
         "docname": "fda_ai_medical_devices_2024",
         "is_shared": false
       }
     ]
     ```

## Output Structure

### Final Workflow Outputs

The workflow returns the following data structure:

1. **summary_content** (object): The generated summary document containing:
   - **report**: The full text of the generated summary

2. **final_summary_paths** (list): Information about where the summary was saved
   - Each item is a list with 4 elements: `[namespace, docname, operation_string, operation_parameters_dict]`
   - **namespace** (string): The storage namespace of the saved document
   - **docname** (string): The document name of the saved document  
   - **operation_string** (string): Description of the operation performed (e.g., "upsert_versioned (created: True)")
   - **operation_parameters_dict** (object): Parameters used for the storage operation
   - Example: `[["document_summary_reports_healthcare_healthcare_ai_2024", "ai_healthcare_impact_2024_summary_abc123", "upsert_versioned (created: True)", {"org_id": "...", "is_shared": false, ...}]]`

## Node Input Structure Examples

### Input Node Expected Structure

```json
{
  "summary_context": "Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.",
  "asset_name": "healthcare_ai_2024",
  "namespace": "document_summary_reports_healthcare_{item}",
  "docname": "ai_healthcare_impact_2024_summary",
  "is_shared": false,
  "load_additional_user_files": [
    {
      "namespace": "summary_context_files_healthcare",
      "docname": "ai_diagnostic_trends_2024",
      "is_shared": false
    }
  ]
}
```

### HITL Node Expected Input Structure

```json
{
  "user_action": "request_revisions",
  "revision_feedback": "Great start! Please expand the section on regulatory challenges and add more specific examples of AI diagnostic tools currently in use. Also, include more recent data from 2024 if available.",
  "load_additional_user_files": [
    {
      "namespace": "summary_context_files_healthcare",
      "docname": "fda_ai_medical_devices_2024",
      "is_shared": false
    }
  ]
}
```

### Store Customer Data Node Expected Input Structure

```json
{
  "save_config": {
    "input_field_path": "summary_content",
    "target_path": {
      "filename_config": {
        "static_namespace": "document_summary_reports_healthcare_healthcare_ai_2024",
        "static_docname": "ai_healthcare_impact_2024_summary_abc123"
      }
    },
    "versioning": {
      "is_versioned": true,
      "operation": "upsert_versioned",
      "version": "latest_draft"
    },
    "is_shared": false
  },
  "summary_content": {
    "report": "## AI Impact on Healthcare Diagnostics in 2024\n\n### Executive Summary\nArtificial intelligence has revolutionized healthcare diagnostics in 2024, with significant breakthroughs in medical imaging, diagnostic accuracy, and patient care optimization...",
    "metadata": {
      "generated_at": "2024-01-15T10:30:00Z",
      "workflow_id": "file_summarization_workflow_v1",
      "iteration_count": 1
    }
  }
}
```
