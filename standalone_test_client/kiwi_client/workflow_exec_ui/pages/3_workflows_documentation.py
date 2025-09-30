"""
Workflow Documentation Page

Displays workflow documentation from markdown files located in workflow directories.
"""

from typing import Optional

import streamlit as st

st.set_page_config(page_title="Workflow Documentation", page_icon="📚")

from kiwi_client.workflow_exec_ui.utils.workflow_utils import (
    get_workflow_documentation_content,
    get_workflow_documentation_path,
)


def _require_selection() -> bool:
    """
    Check if a workflow is selected and display appropriate message if not.
    
    Returns:
        bool: True if workflow is selected, False otherwise
    """
    if "selected_workflow" not in st.session_state or st.session_state.selected_workflow is None:
        st.info("⬅️ Please select a workflow from the **Workflows** page first.")
        return False
    return True


def main() -> None:
    """Main function to render the workflow documentation page."""
    st.title("📚 Workflow Documentation")
    
    if not _require_selection():
        return
    
    workflow = st.session_state.selected_workflow
    category = workflow['metadata']['category']
    workflow_name = workflow['metadata']['workflow_name']
    
    # Display current selection
    st.markdown(f"**Current Workflow:** `{category}/{workflow_name}`")
    st.divider()
    
    # Get documentation content
    doc_content = get_workflow_documentation_content(workflow)
    doc_path = get_workflow_documentation_path(workflow)
    
    if doc_content:
        # Show documentation file path
        if doc_path:
            st.caption(f"📄 Documentation file: `{doc_path.name}`")
        
        # Add refresh button
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🔄 Refresh", help="Reload documentation from file"):
                st.rerun()
        
        st.divider()
        
        # Render the markdown documentation
        st.markdown(doc_content)
        
    else:
        st.warning(f"📝 No documentation found for this workflow.")
        st.info(
            f"**Expected location:** `{category}/{workflow_name}/*_documentation.md`\n\n"
            "Documentation files should be named with the pattern `*_documentation.md` and placed "
            "in the workflow directory alongside the workflow schema file."
        )
        
        # Show example
        with st.expander("📖 Documentation File Naming Convention"):
            st.markdown("""
            Documentation files should follow this naming pattern:
            
            - `blog_brief_to_blog_documentation.md`
            - `linkedin_content_creation_documentation.md`
            - `on_demand_external_research_documentation.md`
            
            The file should be placed in the same directory as the workflow schema file.
            
            **Example structure:**
            ```
            workflows/active/
              ├── content_studio/
              │   └── blog_brief_to_blog_sandbox/
              │       ├── blog_brief_to_blog_documentation.md  ← Documentation
              │       ├── wf_blog_brief_to_blog_json.py       ← Workflow schema
              │       └── wf_llm_inputs.py
              └── labs/
                  └── on_demand_external_research/
                      ├── on_demand_external_research_documentation.md  ← Documentation
                      ├── wf_on_demand_external_research.py             ← Workflow schema
                      └── wf_llm_inputs.py
            ```
            """)


if __name__ == "__main__":
    main()

