# KiwiQ Workflow Service

This service implements a flexible workflow system for building and executing dynamic workflow graphs. The system supports various node types, including input/output nodes, HITL (Human-In-The-Loop) nodes, router nodes, and data processing nodes.

## Overview

The workflow service is designed around a graph-based workflow model where:

- **Nodes** represent processing units with defined inputs and outputs
- **Edges** connect nodes and define data flow between them
- **Schemas** validate data at each step of the workflow
- **Dynamic nodes** adapt their input/output schemas based on connections

The system supports:
- Dynamic branching with router nodes
- Human-in-the-loop interactions
- Data transformations between different schemas
- Joining data from multiple paths
- Input validation through schemas

## Architecture

The workflow service is built on several key components:

- **Node Registry**: Maintains all available node types with versioning
- **Graph Schema**: Defines the graph structure with nodes and edges
- **Graph Builder**: Validates and constructs executable graphs
- **Runtime Adapter**: Provides execution environment for workflows

## Running the Tests

The test suite demonstrates different types of workflow graphs:

1. **Simple Number Graph**: A basic linear workflow
2. **Router Graph**: Demonstrates conditional branching
3. **HITL Graph**: Shows human-in-the-loop interactions
4. **Complex Graph**: Combines multiple features into a comprehensive workflow

To run the tests:

```bash
python -m services.workflow_service.run_test_workflows
```

## Test Graphs

### Simple Number Graph
A basic workflow that generates a number and multiplies it.

```
Input → NumberGenerator → NumberMultiplier → Output
```

### Router Graph
Demonstrates conditional branching based on a numeric threshold.

```
Input → NumberGenerator → Router → [High Path | Low Path] → Output
```

### HITL Graph
Shows human-in-the-loop review of generated content.

```
Input → TextGenerator → HITL Review → TextProcessor → Output
```

### Complex Graph
Combines multiple features including routing, HITL, and joining data paths.

```
Input → NumberGenerator → Router →
    High Path: NumberMultiplier(5x) → DataTransform → HITL Review
    Low Path: NumberMultiplier(0.5x) → DataTransform
Both paths → JoinData → Output
```

## Implementation Details

The test implementation showcases:

1. **Node Types**:
   - Basic data processing nodes (generators, multipliers, processors)
   - Dynamic nodes (input, output, HITL, router)
   - Transformation nodes (data type conversion)
   - Join nodes (merging multiple paths)

2. **Schema Validation**:
   - Static schemas for regular nodes
   - Dynamic schemas for input/output/HITL nodes
   - Schema compatibility validation along edges

3. **Graph Construction**:
   - Node instantiation and configuration
   - Edge validation and data mapping
   - Runtime configuration for execution

4. **Execution**:
   - Graph state management
   - Node execution in correct order
   - Data flow between nodes
   - Handling of conditional branches 