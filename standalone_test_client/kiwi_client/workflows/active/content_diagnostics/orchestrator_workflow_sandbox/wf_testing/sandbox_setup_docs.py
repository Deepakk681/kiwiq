"""
Orchestrator Workflow - Sandbox Setup Documents

This workflow orchestrates other content diagnostic workflows.
It may not require specific setup documents, but can be configured
as needed for testing different orchestration scenarios.
"""

from typing import List
from kiwi_client.test_run_workflow_client import (
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.workflows.active.sandbox_identifiers import test_sandbox_company_name as test_company_name

# No setup documents needed for orchestrator workflow by default
setup_docs = []

# No cleanup documents needed by default
cleanup_docs = []