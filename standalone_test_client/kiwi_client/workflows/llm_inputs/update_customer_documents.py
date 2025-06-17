from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


# System prompt for document update analysis
SYSTEM_PROMPT = """
You are an expert at analyzing user input and determining which documents and fields need to be updated.
Your task is to analyze the user's input and identify:
1. Which document(s) need to be updated (user_preferences_doc or content_strategy_doc)
2. Which specific fields within those documents need to be modified
3. The nature of the changes required, including current values and proposed updates
4. Any new fields that need to be added to the structure

For each field update, you must provide:
- The field name
- The proposed new value

Respond with a structured output that clearly identifies the document names and fields that need updates. Use this schema for your output:
Make sure you only suggest changes where it is necessary.
{schema}
"""

# User prompt template for document update analysis
USER_PROMPT = """
Analyze the following user input and determine which documents and fields need to be updated:

User Input: {user_input}

Available Documents and their Schemas:
1. User Preferences Schema for document name (user_preferences_doc):
{user_preferences_schema}

2. Content Strategy Schema for document name (content_strategy_doc):
{content_strategy_schema}

Based on the user's input, identify:
1. Which document needs to be updated (user_preferences_doc or content_strategy_doc) add this to document_name in output.
2. For each field:
   - Proposed value (this can be a description string as well)

Provide your analysis in a structured format that clearly identifies the document names and fields that need updates.
"""
# Field update detail schema for individual field updates
class FieldUpdateDetail(BaseModel):
    """Schema for individual field update details"""
    field_name: str = Field(
        description="Name of the field to update"
    )
    proposed_value: str = Field(
        description="Proposed value for the field"
    )


# Document update schema for a single document
class DocumentUpdate(BaseModel):
    """Schema for a single document update"""
    document_name: str = Field(
        description="Name of the document that needs to be updated"
    )
    update_details: List[FieldUpdateDetail] = Field(
        description="List of fields that need to be updated in this document"
    )


# Output schema for document update analysis
class DocumentUpdateSchema(BaseModel):
    """Schema for document update analysis output"""
    documents: List[DocumentUpdate] = Field(
        description="List of documents that need to be updated"
    )

DOCUMENT_UPDATE_SCHEMA = DocumentUpdateSchema.model_json_schema()

# System prompt for document content updates
DOCUMENT_UPDATE_SYSTEM_PROMPT = """
You are an expert at updating document content while maintaining exact structure and format.
Your task is to update the value of specified fields in the document while keeping ALL other fields and structure exactly the same.

IMPORTANT RULES:
1. DO NOT modify any fields that are not explicitly listed in fields_to_update
2. DO NOT change the structure, format, or organization of the document
3. DO NOT remove any fields
4. DO NOT modify field names or types of existing fields
5. Preserve all existing data in unchanged fields
6. Only update the exact fields specified in the update analysis
7. For new fields:
   - Add them to the appropriate location in the structure
   - Maintain the same format and style as existing fields
   - Ensure they follow the document's schema and conventions

The output must be the complete document with the specified fields updated and new fields added, maintaining the exact same structure as the input document.
"""

# User prompt template for document content updates
DOCUMENT_UPDATE_USER_PROMPT = """
Update the specified fields in the following document while keeping all other fields and structure exactly the same:

Document to be updated: {document}

Update Analysis:
{update_analysis}

IMPORTANT: 
1. Return the COMPLETE document with the specified fields updated
2. Keep ALL other fields and structure EXACTLY as they are
3. Do not modify any fields not listed in fields_to_update
4. Maintain the exact same document format and structure
5. For new fields:
   - Add them to the appropriate location in the structure
   - Maintain the same format and style as existing fields
   - Ensure they follow the document's schema and conventions

Provide the complete document with the specified fields updated and new fields added.
"""
