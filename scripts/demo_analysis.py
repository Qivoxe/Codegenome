from __future__ import annotations

from pathlib import Path

from codegenome import (
    GitEngine,
    GenomeGraph,
    ImpactEngine,
    ImpactReport,
    SourceParser,
    render_markdown,
)

REPO_ROOT = Path(__file__).resolve().parent.parent / "sample_repo"


def main() -> None:
    git_engine = GitEngine(str(REPO_ROOT))
    commits = list(git_engine.repo.iter_commits("HEAD"))
    if len(commits) < 2:
        print("Not enough commits to analyze.")
        return

    latest_commit = commits[0]
    print("=" * 60)
    print("CODEGENOME - REAL IMPACT ANALYSIS")
    print("=" * 60)
    print(f"Commit: {latest_commit.hexsha[:8]}")
    print(f"Message: {latest_commit.message.strip()}")
    print()

    changed_files = git_engine.get_changed_files(latest_commit.hexsha)
    if not changed_files:
        print("No changed files detected.")
        return

    print("Changed Files:")
    for cf in changed_files:
        print(f"  {cf.file_path} ({cf.change_type})")
    print()

    python_changes = [cf for cf in changed_files if cf.file_path.endswith(".py")]
    if not python_changes:
        print("No Python files changed.")
        return

    parser = SourceParser(REPO_ROOT)
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

    for cf in python_changes:
        changed_functions = git_engine.get_changed_functions(latest_commit.hexsha, cf.file_path)
        if not changed_functions:
            continue

        for changed_func in changed_functions:
            report = engine.compute_impact(changed_func.qualified_name)
            print("-" * 60)
            print(f"Changed Function: {report.changed_function}")
            print(f"File: {report.file_path}")
            print(f"Impact Score: {report.impact_score}/100")
            print(f"Impact Level: {report.impact_level.value}")
            print(f"Affected Components: {', '.join(report.affected_components)}")
            print()
            print("Impact Paths:")
            if report.impact_paths:
                for path in report.impact_paths[:5]:
                    print(f"  {' -> '.join(path)}")
            else:
                print("  No impact paths found.")
            print()
            print("Reasons:")
            print(f"  {report.explanation}")
            print()
            print("Markdown Report:")
            print(render_markdown(report))
            print()


if __name__ == "__main__":
    main()
