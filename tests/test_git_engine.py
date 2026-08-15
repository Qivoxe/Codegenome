from __future__ import annotations

from pathlib import Path

from codegenome.git_engine import GitEngine

REPO_ROOT = Path(__file__).resolve().parent.parent / "sample_repo"


def test_git_engine_initialization() -> None:
    engine = GitEngine(str(REPO_ROOT))
    assert engine.repo is not None


def test_git_engine_get_commit_info() -> None:
    engine = GitEngine(str(REPO_ROOT))
    commits = list(engine.repo.iter_commits("HEAD"))
    assert len(commits) >= 1
    info = engine.get_commit_info(commits[0].hexsha)
    assert info.commit_hash == commits[0].hexsha
    assert info.message


def test_git_engine_get_changed_files() -> None:
    engine = GitEngine(str(REPO_ROOT))
    commits = list(engine.repo.iter_commits("HEAD"))
    assert len(commits) >= 2
    files = engine.get_changed_files(commits[0].hexsha)
    assert len(files) >= 1
    assert any(f.file_path == "checkout.py" for f in files)


def test_git_engine_get_changed_lines() -> None:
    engine = GitEngine(str(REPO_ROOT))
    commits = list(engine.repo.iter_commits("HEAD"))
    assert len(commits) >= 2
    added, _deleted = engine.get_changed_lines(commits[0].hexsha, "checkout.py")
    assert len(added) > 0


def test_git_engine_get_changed_functions() -> None:
    engine = GitEngine(str(REPO_ROOT))
    commits = list(engine.repo.iter_commits("HEAD"))
    assert len(commits) >= 2
    funcs = engine.get_changed_functions(commits[0].hexsha, "checkout.py")
    assert len(funcs) >= 1
    names = [f.qualified_name for f in funcs]
    assert "checkout.calculate_discount" in names


def test_git_engine_modified_function_detection() -> None:
    engine = GitEngine(str(REPO_ROOT))
    commits = list(engine.repo.iter_commits("HEAD"))
    assert len(commits) >= 2
    for commit in commits:
        info = engine.get_commit_info(commit.hexsha)
        if "tax_rate" in info.message:
            funcs = engine.get_changed_functions(commit.hexsha, "checkout.py")
            assert any(f.qualified_name == "checkout.calculate_discount" for f in funcs)
            break
