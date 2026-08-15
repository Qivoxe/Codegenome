# Software Genome

## Definition

The Software Genome is a graph representation of a Python repository that captures:

- Modules
- Classes
- Functions
- Methods
- Imports
- Function calls
- Dependencies

## Graph Structure

### Nodes

- **Repository**: The root node representing the entire repository
- **Module**: A Python file/module
- **Class**: A class definition
- **Function**: A top-level function
- **Method**: A class method
- **Import**: An import statement

### Edges

- **CONTAINS**: Module contains class/function/method
- **CALLS**: Function calls another function
- **IMPORTS**: Module imports another module
- **DEPENDS_ON**: General dependency relationship

## Implementation

The Software Genome is implemented using NetworkX's `MultiDiGraph`:

```python
class GenomeGraph:
    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()
```

### Node Attributes

- `id`: Unique identifier (qualified name)
- `type`: Node type (module, class, function, method, import)
- `name`: Short name
- `qualified_name`: Full dotted name
- `file_path`: Source file location
- `lineno`: Start line number
- `end_lineno`: End line number

### Edge Attributes

- `source`: Source node ID
- `target`: Target node ID
- `type`: Edge type (calls, imports, contains, depends_on)
- `metadata`: Additional context

## Queries

The graph supports the following queries:

- `get_callers(node_id)` — Find functions that call this node
- `get_callees(node_id)` — Find functions called by this node
- `get_downstream_dependencies(node_id)` — BFS traversal following calls/imports
- `get_upstream_dependencies(node_id)` — Reverse BFS traversal
- `get_impact_paths(start, end)` — Find all simple paths between two nodes

## Circular Dependency Protection

All graph traversals use visited sets to prevent infinite loops in cyclic call graphs.

## Integration

The Software Genome is constructed by:

1. `SourceParser` extracts AST nodes from Python files
2. `GenomeGraph` builds the NetworkX graph
3. `ImpactEngine` queries the graph for propagation
