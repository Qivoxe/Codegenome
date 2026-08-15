# Impact Engine

## Purpose

The Impact Engine determines what could break when a function changes by traversing the Software Genome graph.

## Algorithm

### Step 1: Identify Direct Callers

Using the graph, find all nodes that have a CALLS edge pointing to the changed function.

### Step 2: Transitive Propagation

Breadth-first search from direct callers to find all upstream dependencies:

```
queue = direct_callers
visited = set()
while queue:
    current = queue.pop(0)
    if current not in visited:
        visited.add(current)
        queue.extend(get_callers(current))
```

### Step 3: Compute Deterministic Score

The impact score (0-100) is computed using heuristics:

| Factor | Points |
|--------|--------|
| Has direct callers | +25 |
| Each transitive caller | +5 (max 25) |
| Multiple affected modules | +5 per module (max 20) |
| Dependency depth >= 3 | +5 per depth (max 20) |
| Centrality > 2 | +2 per point (max 10) |

### Step 4: Assign Risk Level

| Score | Level |
|-------|-------|
| 76-100 | CRITICAL |
| 51-75 | HIGH |
| 26-50 | MEDIUM |
| 0-25 | LOW |

### Step 5: Generate Explanation

The engine builds a human-readable explanation from:
- Direct caller count and names
- Transitive caller count and names
- Module spread
- Dependency chain depth
- Risk level

### Step 6: Compute Impact Paths

Using NetworkX's `all_simple_paths`, the engine finds paths from the changed function to affected components.

## Output

The `ImpactReport` includes:

- `changed_function`: The modified function
- `file_path`: Source file location
- `direct_impact`: Direct callers
- `transitive_impact`: All upstream callers
- `impact_score`: 0-100 deterministic score
- `impact_level`: LOW/MEDIUM/HIGH/CRITICAL
- `explanation`: Human-readable reasoning
- `affected_components`: Modules affected
- `impact_paths`: List of dependency chains
- `nodes`/`edges`: Graph data for visualization

## ML + LLM Extension

When enabled:

- `ml_risk`: XGBoost-predicted risk (0.0-1.0)
- `ml_risk_level`: ML-based risk level
- `llm_explanation`: Structured explanation from LLM or fallback template

## Deterministic Guarantee

The core engine is deterministic:
- Same input graph → same impact score
- Same changed function → same affected components
- Same paths → same ordering

ML and LLM are optional enhancements that do not affect the deterministic core.
