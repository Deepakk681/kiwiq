"""
Blog Content Analysis Workflow - Sandbox Setup Documents

This workflow doesn't require any pre-existing documents to be set up.
The workflow will:
1. Crawl and scrape blog content
2. Classify posts into funnel stages
3. Perform analysis
4. Store results

No setup documents needed as the workflow creates its own data.
"""

from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)

# No setup documents needed for this workflow
setup_docs = []

# Documents created by the workflow (for potential cleanup)
cleanup_docs = []