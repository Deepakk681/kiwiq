# CLAUDE.md - AI Assistant Best Practices & Knowledge Base

## 🤖 Self-Maintenance Instructions
**IMPORTANT:** As an AI assistant working on this codebase, you should:
1. **Update this file** whenever you learn something new about the project
2. **Check this file first** when starting a new session for important context
3. **Add new sections** as needed to capture project-specific knowledge
4. **Document patterns** that work well or common pitfalls to avoid

---

## 📁 Project Overview
- **Project Type**: KiwiQ Standalone Client - Workflow Management System
- **Primary Language**: Python
- **Key Framework**: Workflow orchestration with HITL (Human-in-the-Loop) support
- **Testing**: Uses `poetry run python` for execution

---

## 🏗️ Project Structure

```
standalone_client/
├── kiwi_client/
│   ├── workflows/                 # Main workflows
│   │   ├── wf_*.py               # Individual workflow definitions
│   │   └── document_models/      # Document model definitions
│   ├── workflows_for_blog_teammate/  # Blog-specific workflows
│   │   ├── wf_*.py               # Blog workflow definitions
│   │   └── llm_inputs/           # LLM prompt templates
│   └── test_run_workflow_client.py  # Main testing utilities
├── scripts/                       # Utility scripts
├── pyproject.toml                # Poetry configuration
└── poetry.lock                   # Dependency lock file
```

---

## ⚡ Critical Workflow Rules

### Edge Mapping Restrictions
- **NEVER use dot notation in edge mappings** (e.g., `list_template_vars.0.entity_name`)
- **Problem**: Dot notation in edges doesn't work properly in the workflow system
- **Solution**: Use transform_data nodes to restructure data before passing to next nodes
- **Example**:
  ```python
  # ❌ WRONG - Don't do this in edges:
  {"src_field": "transformed_data.list_template_vars.0.entity_name", "dst_field": "entity_name"}
  
  # ✅ CORRECT - Map the entire field:
  {"src_field": "transformed_data", "dst_field": "input_data"}
  # Or restructure in the transform node itself
  ```

---

## 🔧 Common Commands & Patterns

### Running Workflows
```bash
# Run a workflow file directly
poetry run python kiwi_client/workflows/{workflow_file}.py

# Run with specific Python path
poetry run python -c "from kiwi_client.workflows.{module} import {function}; {function}()"
```

### Testing Workflows with HITL
- Workflows can have predefined HITL inputs in the main test function
- Look for `predefined_hitl_inputs` list in the workflow's main function
- Format: List of dictionaries with expected input fields

---

## 📝 Workflow Implementation Patterns

### Check Iteration Limit Pattern
When implementing iteration limits for HITL feedback loops:

1. **Add MAX_ITERATIONS constant** (typically set to 10)
```python
MAX_ITERATIONS = 10  # Maximum iterations for HITL feedback loops
```

2. **Add check_iteration_limit node**:
```python
"check_iteration_limit": {
    "node_id": "check_iteration_limit",
    "node_name": "if_else_condition",
    "node_config": {
        "tagged_conditions": [{
            "tag": "iteration_limit_check",
            "condition_groups": [{
                "logical_operator": "and",
                "conditions": [{
                    "field": "generation_metadata.iteration_count",
                    "operator": "less_than",
                    "value": MAX_ITERATIONS
                }]
            }],
            "group_logical_operator": "and"
        }],
        "branch_logic_operator": "and"
    }
}
```

3. **Add route_on_limit_check node** to handle routing based on limit
4. **Update routing nodes** to go through check_iteration_limit
5. **Add generation_metadata to state reducer**
6. **Update LLM nodes** to store metadata with iteration counts

### Node Numbering
- Don't focus on updating comment numbers when adding/modifying nodes
- The system doesn't rely on comment numbering for functionality

---

## ⚠️ Common Pitfalls & Solutions

### HITL Testing Issues
- **Problem**: Workflow hangs waiting for HITL input
- **Solution**: Add `predefined_hitl_inputs` in the main test function

### Document Already Exists Errors
- **Problem**: 409/500 errors when initializing documents
- **Solution**: Check if document exists first, handle gracefully

### Long Workflow Execution Times
- **Problem**: Workflows with multiple LLM calls can take 5-10+ minutes
- **Solution**: Be patient, use background execution, set appropriate timeouts

---

## 🧪 Testing Best Practices

1. **Always test with predefined HITL inputs** when possible
2. **Use poetry run python** for consistent environment
3. **Check workflow completion status** to verify implementations
4. **Monitor logs** for iteration count tracking

---

## 📊 Key Workflow Components

### Essential Nodes
- `input_node` - Entry point
- `output_node` - Exit point  
- `hitl_node__default` - Human interaction points
- `router_node` - Conditional routing
- `if_else_condition` - Conditional logic
- `llm` - LLM processing nodes

### State Management
- Use `$graph_state` for state persistence
- Define reducers for state fields (replace, add_messages, etc.)
- Track metadata like `generation_metadata` for iteration counting

---

## 🔍 Debugging Tips

1. **Check workflow validation**: Workflows validate schema before execution
2. **Monitor event streams**: Workflows emit events during execution
3. **Review HITL job IDs**: Each HITL pause has a unique job ID
4. **Examine state dumps**: Failed runs save state to data directory

---

## 📚 Recent Learnings

### 2025-08-07: Iteration Limit Implementation
- Successfully implemented `check_iteration_limit` across 4 workflows
- Pattern involves condition nodes, routing nodes, and metadata tracking
- Prevents infinite HITL loops by limiting to MAX_ITERATIONS (10)

### Workflow Execution
- Workflows require proper authentication (uses admin@example.com)
- API endpoint: https://api.prod.kiwiq.ai
- Workflows create temporary workflow instances during testing
- HITL inputs must match expected schema exactly

---

## 🚀 Future Improvements & TODOs

- [ ] Add automated testing for iteration limit functionality
- [ ] Create workflow templates for common patterns
- [ ] Document all HITL input schemas
- [ ] Add performance benchmarks for workflows

---

## 📖 Additional Resources

- Workflow documentation: Check individual workflow files for docstrings
- LLM inputs: See `llm_inputs/` directories for prompt templates
- Document models: Review `document_models/` for data structures

---

*Last Updated: 2025-08-07*
*Remember to update this file when you learn something new!*