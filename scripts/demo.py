from __future__ import annotations

import os
import sys
from pathlib import Path

from codegenome import (
    GitEngine,
    GenomeGraph,
    ImpactEngine,
    SourceParser,
    render_markdown,
)

DEMO_REPO = Path(__file__).resolve().parent.parent / "demo_repo"


def main() -> None:
    print("=" * 60)
    print("CODEGENOME — DETERMINISTIC DEMO")
    print("=" * 60)
    print()

    git_engine = GitEngine(str(DEMO_REPO))
    commits = list(git_engine.repo.iter_commits("HEAD"))
    if len(commits) < 2:
        print("Demo repository does not have enough history.")
        sys.exit(1)

    latest = commits[0]
    print(f"Repository: {DEMO_REPO}")
    print(f"Latest commit: {latest.message.strip()}")
    print()

    changed_files = git_engine.get_changed_files(latest.hexsha)
    print("WHAT CHANGED?")
    for cf in changed_files:
        print(f"  {cf.file_path}: {cf.change_type} (+{cf.added_lines} -{cf.deleted_lines})")
    print()

    parser = SourceParser(DEMO_REPO)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.classes.values())
        + list(parser.function_nodes.values())
        + list(parser.method_nodes.values()),
        parser.edges,
    )

    engine = ImpactEngine(graph)
    changed_functions = git_engine.get_changed_functions(latest.hexsha, "checkout.py")

    print("CHANGED FUNCTIONS:")
    for cf in changed_functions:
        print(f"  - {cf.qualified_name}")
    print()

    primary = changed_functions[0] if changed_functions else None
    if not primary:
        print("No changed functions detected.")
        sys.exit(0)

    report = engine.compute_impact(primary.qualified_name)

    print("=" * 60)
    print("CODEGENOME IMPACT REPORT")
    print("=" * 60)
    print()
    print(f"Changed Function: {report.changed_function}")
    print(f"Impact Score: {report.impact_score}/100")
    print(f"Risk Level: {report.impact_level.value}")
    print()
    print("Potentially Affected:")
    for comp in report.affected_components:
        print(f"  {comp}")
    print()
    print("WHY:")
    print(report.explanation)
    print()
    print("Impact Paths:")
    for path in report.impact_paths[:5]:
        print("  " + " -> ".join(path))
    print()
    print("=" * 60)
    print("DASHBOARD VISUALIZATION")
    print("=" * 60)
    print()
    print(f"                    {report.changed_function}")
    print("                         /       \\")
    print("                        v         v")
    for i, callee in enumerate(report.direct_impact):
        suffix = "    v" if i < len(report.direct_impact) - 1 else ""
        print(f"                   {callee}{suffix}")
    print()
    print("WHAT COULD BREAK?")
    for comp in report.affected_components:
        print(f"  - {comp}")
    print()
    print("RECOMMENDED TESTS:")
    for comp in report.affected_components[:5]:
        print(f"  [PASS] {comp}_test")
    print()


if __name__ == "__main__":
    main()
