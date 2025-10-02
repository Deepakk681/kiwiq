"""
Investor Lead Scoring Workflow

A comprehensive workflow for scoring and qualifying venture capital investors based on:
- Fund vitals (size, stage, check size, activity)
- Thesis alignment (portfolio composition, AI/B2B/MarTech focus)
- Partner value (authority, background, value-add)
- Geographic location
- Momentum signals (exits, follow-ons)

Total scoring framework: 315 points
Tiers: Dream (200+), Hot (150-199), Warm (100-149), Cool (70-99), Cold (<70)
"""

from kiwi_client.workflows.active.investor.investor_lead_scoring_sandbox.wf_investor_lead_scoring_json import (
    workflow_graph_schema
)

__all__ = ['workflow_graph_schema']

