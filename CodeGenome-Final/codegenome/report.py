from __future__ import annotations

from codegenome.models import ImpactReport


def render_markdown(report: ImpactReport) -> str:
    lines: list[str] = []
    lines.append("# CodeGenome Impact Report")
    lines.append("")
    lines.append(f"**Changed Function:** `{report.changed_function}`")
    lines.append(f"**File:** `{report.file_path}`")
    lines.append(f"**Impact Score:** `{report.impact_score}`/100")
    lines.append(f"**Impact Level:** `{report.impact_level.value}`")
    lines.append("")
    lines.append("## Explanation")
    lines.append("")
    lines.append(report.explanation)
    lines.append("")
    lines.append("## Direct Impact")
    lines.append("")
    if report.direct_impact:
        for func in report.direct_impact:
            lines.append(f"- `{func}`")
    else:
        lines.append("No direct callers found.")
    lines.append("")
    lines.append("## Transitive Impact")
    lines.append("")
    if report.transitive_impact:
        for func in report.transitive_impact:
            lines.append(f"- `{func}`")
    else:
        lines.append("No transitive callers found.")
    lines.append("")
    lines.append("## Affected Components")
    lines.append("")
    if report.affected_components:
        for comp in report.affected_components:
            lines.append(f"- `{comp}`")
    else:
        lines.append("No affected components found.")
    lines.append("")
    if report.impact_paths:
        lines.append("## Impact Paths")
        lines.append("")
        for path in report.impact_paths:
            lines.append(" -> ".join(f"`{p}`" for p in path))
        lines.append("")
    return "\n".join(lines)


__all__ = ["render_markdown"]
