# On-Demand External Research Workflow - Frontend Implementation Guide

## Workflow Purpose
This workflow conducts comprehensive external web research using advanced AI models. It automatically gathers information from the internet, creates detailed research reports with citations, and allows users to approve or request revisions.

## Input Node Requirements

When initiating the workflow, the frontend must provide the following data structure:

### Required Fields

1. **research_context** (string, required)
   - The research topic or context to investigate
   - Example: "Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024"

2. **asset_name** (string, required)
   - Asset name used for organizing and naming the research report
   - Example: "healthcare_ai_2024"

### Optional Fields

1. **namespace** (string, optional)
   - Custom namespace for saving the research report
   - Default: "external_research_reports_{item}" where {item} is replaced with asset_name
   - Example: "external_research_reports_healthcare_{item}"

2. **docname** (string, optional)
   - Custom document name for the research report
   - If not provided, the system generates a unique name automatically
   - Example: "ai_healthcare_impact_2024_research"

3. **is_shared** (boolean, optional)
   - Determines if the research report should be shared
   - Default: false

4. **load_additional_user_files** (list, optional)
   - List of additional documents to include as context for the research
   - Default: empty list []
   - Each item must contain:
     - **namespace**: The storage namespace of the file
     - **docname**: The document name
     - **is_shared**: Boolean indicating if the file is shared
   - Example:
     ```
     [
       {
         "namespace": "research_context_files_healthcare",
         "docname": "ai_diagnostic_trends_2024",
         "is_shared": false
       }
     ]
     ```

## HITL Node Output and Input Requirements

### What the User Sees (HITL Output)

When the workflow reaches the human-in-the-loop approval stage, the frontend displays:

1. **research_content**: The generated research document containing:
   - **report**: The full text of the research findings
   - **citations**: Web sources and references used in the research

### What Input the Frontend Must Collect (HITL Input)

The frontend must collect and send back the following structured data:

#### Required Fields

1. **user_action** (enum, required)
   - Must be one of: "approve", "request_revisions", "cancel"
   - Controls the workflow progression

#### Conditional Fields

2. **revision_feedback** (string, optional but required if user_action is "request_revisions")
   - Detailed feedback for improving the research
   - Example: "Please expand the section on regulatory challenges and add more specific examples of AI diagnostic tools"

#### Optional Fields

3. **load_additional_user_files** (list, optional)
   - Additional documents to consider during revision
   - Same structure as input node's load_additional_user_files
   - Default: empty list []
   - Example:
     ```
     [
       {
         "namespace": "research_context_files_healthcare",
         "docname": "fda_ai_medical_devices_2024",
         "is_shared": false
       }
     ]
     ```

## Output Structure

### Final Workflow Outputs

The workflow returns the following data structure:

1. **research_content** (object): The generated research document containing:
   - **report**: The full text of the research findings
   - **citations**: Web sources and references used in the research

2. **final_research_paths** (list): Information about where the research was saved
   - Each item is a list with 4 elements: `[namespace, docname, operation_string, operation_parameters_dict]`
   - **namespace** (string): The storage namespace of the saved document
   - **docname** (string): The document name of the saved document  
   - **operation_string** (string): Description of the operation performed (e.g., "upsert_versioned (created: True)")
   - **operation_parameters_dict** (object): Parameters used for the storage operation
   - Example: `[["external_research_reports_healthcare_healthcare_ai_2024", "ai_healthcare_impact_2024_research_abc123", "upsert_versioned (created: True)", {"org_id": "...", "is_shared": false, ...}]]`

## Node Input Structure Examples

### Input Node Expected Structure

```json
{
  "research_context": "Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.",
  "asset_name": "healthcare_ai_2024",
  "namespace": "external_research_reports_healthcare_{item}",
  "docname": "ai_healthcare_impact_2024_research",
  "is_shared": false,
  "load_additional_user_files": [
    {
      "namespace": "research_context_files_healthcare",
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
      "namespace": "research_context_files_healthcare",
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
    "input_field_path": "research_content",
    "target_path": {
      "filename_config": {
        "static_namespace": "external_research_reports_healthcare_healthcare_ai_2024",
        "static_docname": "ai_healthcare_impact_2024_research_abc123"
      }
    },
    "versioning": {
      "is_versioned": true,
      "operation": "upsert_versioned",
      "version": "latest_draft"
    },
    "is_shared": false
  },
  "research_content": {
    "report": "## AI Impact on Healthcare Diagnostics in 2024\n\n### Executive Summary\nArtificial intelligence has revolutionized healthcare diagnostics in 2024, with significant breakthroughs in medical imaging, diagnostic accuracy, and patient care optimization...",
    "citations": [
      {
        "title": "FDA Approves New AI Diagnostic Tools",
        "url": "https://example.com/fda-ai-approval",
        "domain": "fda.gov",
        "relevance_score": 0.95
      }
    ],
    "metadata": {
      "generated_at": "2024-01-15T10:30:00Z",
      "workflow_id": "external_research_workflow_v1",
      "iteration_count": 1,
      "sources_found": 15
    }
  }
}
```