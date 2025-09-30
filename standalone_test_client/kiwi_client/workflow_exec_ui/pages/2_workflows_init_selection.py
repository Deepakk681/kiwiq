"""
Workflows page: list discovered workflows and allow selection.
"""

from typing import Any, Dict, List, Tuple
from collections import defaultdict

import streamlit as st

st.set_page_config(page_title="Workflows", page_icon="🧩")

from kiwi_client.workflow_exec_ui.utils.workflow_utils import (
    list_available_workflows,
    get_workflow_by_name,
)


def _ensure_selection_defaults() -> None:
    """Initialize selection state variables if not present."""
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None
    if "selected_workflow_name" not in st.session_state:
        st.session_state.selected_workflow_name = None
    if "selected_workflow" not in st.session_state:
        st.session_state.selected_workflow = None


def _render_current_selection() -> None:
    """Display the currently selected workflow."""
    if st.session_state.selected_category and st.session_state.selected_workflow_name:
        st.markdown(
            f"**Selected:** `{st.session_state.selected_category}/{st.session_state.selected_workflow_name}`"
        )
    else:
        st.info("No workflow selected.")


def _sort_categories(categories: List[str]) -> List[str]:
    """
    Sort categories in priority order:
    1. content_studio
    2. labs
    3. content_diagnostics
    4. Any other categories (alphabetically)
    
    Args:
        categories: List of category names
        
    Returns:
        Sorted list of categories
    """
    priority_order = {
        'content_studio': 0,
        'labs': 1,
        'content_diagnostics': 2
    }
    
    def sort_key(category: str) -> Tuple[int, str]:
        # Return (priority, category_name) for sorting
        # Categories not in priority_order get priority 999 and are sorted alphabetically
        priority = priority_order.get(category, 999)
        return (priority, category)
    
    return sorted(categories, key=sort_key)


def _organize_workflows(workflows: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """
    Organize workflows by category with alphabetically sorted workflow names.
    
    Args:
        workflows: List of (category, workflow_name) tuples
        
    Returns:
        Dictionary mapping category to sorted list of workflow names
    """
    workflows_by_category = defaultdict(list)
    
    for category, workflow_name in workflows:
        workflows_by_category[category].append(workflow_name)
    
    # Sort workflow names alphabetically within each category
    for category in workflows_by_category:
        workflows_by_category[category].sort()
    
    return dict(workflows_by_category)


def main() -> None:
    """Main function to render the workflow selection page."""
    st.title("🧩 Workflows")
    _ensure_selection_defaults()
    _render_current_selection()

    st.divider()
    st.subheader("Available Workflows")

    workflows: List[Tuple[str, str]] = list_available_workflows()
    if not workflows:
        st.warning("No workflows found.")
        return

    # Organize workflows by category
    workflows_by_category = _organize_workflows(workflows)
    
    # Get sorted categories
    sorted_categories = _sort_categories(list(workflows_by_category.keys()))
    
    # Display workflows grouped by category
    for category in sorted_categories:
        workflow_names = workflows_by_category[category]
        
        # Category header
        st.markdown(f"### 📂 {category}")
        st.caption(f"{len(workflow_names)} workflow{'s' if len(workflow_names) != 1 else ''}")
        
        # Display workflows in this category
        for workflow_name in workflow_names:
            cols = st.columns([6, 2])
            cols[0].write(f"**{workflow_name}**")
            if cols[1].button("Select", key=f"select__{category}__{workflow_name}"):
                st.session_state.selected_category = category
                st.session_state.selected_workflow_name = workflow_name
                st.session_state.selected_workflow = get_workflow_by_name(category, workflow_name)
                st.success(f"✅ Selected: {category}/{workflow_name}")
                st.rerun()
        
        st.divider()


if __name__ == "__main__":
    main()


