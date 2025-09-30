"""
LinkedIn Scraping Workflow - LLM Inputs

This workflow does not use any LLM nodes.
It only performs data scraping, filtering, and storage operations.
Therefore, no LLM configurations, prompts, or schemas are required.

The workflow consists of:
1. Input node - Accepts LinkedIn entity URL and username
2. Scraping node - Scrapes profile and posts data
3. Filter node - Filters data to keep only relevant fields
4. Storage nodes - Stores raw and filtered data
5. Output node - Returns processing results
"""

# No LLM configurations needed for this workflow