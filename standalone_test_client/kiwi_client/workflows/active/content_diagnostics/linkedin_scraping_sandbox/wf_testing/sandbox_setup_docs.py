"""
LinkedIn Scraping Workflow - Sandbox Setup Documents

This workflow does not require any setup documents to be created before execution.
The workflow creates its own documents as output:
- LinkedIn scraped profile (raw and filtered)
- LinkedIn scraped posts (raw and filtered)

No prerequisite documents or test data need to be loaded.
"""

from typing import List, Dict, Any
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# No setup documents needed for this workflow
setup_docs = []

# Documents created by the workflow (for potential cleanup)
# Note: These are created by the workflow itself, not set up beforehand
cleanup_docs = []