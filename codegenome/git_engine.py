from __future__ import annotations

import git

from codegenome.models import ChangedFunction, GitChange, GitFileChange


class GitEngine:
    def __init__(self, repo_path: str) -> None:
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_changed_files(self, commit_hash: str) -> list[GitFileChange]:
        commit = self.repo.commit(commit_hash)
        if not commit.parents:
            return [
                GitFileChange(
                    file_path=str(item.path),  # type: ignore[union-attr]
                    change_type="added",
                    added_lines=item.size if item.size else 0,  # type: ignore[union-attr]
                )
                for item in commit.tree.traverse()
                if item.type == "blob"  # type: ignore[union-attr]
            ]
        parent = commit.parents[0]
        diffs = parent.diff(commit, create_patch=True)
        result: list[GitFileChange] = []
        for diff in diffs:
            change_type = "modified"
            if diff.new_file:
                change_type = "added"
            elif diff.deleted_file:
                change_type = "deleted"
            diff_text = diff.diff.decode("utf-8", errors="replace") if isinstance(diff.diff, bytes) else str(diff.diff or "")
            added = diff_text.count("\n+")
            deleted = diff_text.count("\n-")
            result.append(
                GitFileChange(
                    file_path=str(diff.b_path or diff.a_path or ""),
                    change_type=change_type,
                    added_lines=added,
                    deleted_lines=deleted,
                    modified_lines=max(0, added + deleted - max(added, deleted)),
                )
            )
        return result

    def get_changed_lines(self, commit_hash: str, file_path: str) -> tuple[set[int], set[int]]:
        commit = self.repo.commit(commit_hash)
        if not commit.parents:
            return set(), set()
        parent = commit.parents[0]
        diffs = parent.diff(commit, paths=[file_path], create_patch=True)
        added: set[int] = set()
        deleted: set[int] = set()
        for diff in diffs:
            if diff.diff is None:
                continue
            text = diff.diff.decode("utf-8", errors="replace") if isinstance(diff.diff, bytes) else str(diff.diff)
            old_line = 0
            new_line = 0
            for raw_line in text.splitlines():
                if raw_line.startswith("@@"):
                    parts = raw_line.split()
                    for part in parts:
                        if part.startswith("+"):
                            try:
                                new_line = int(part[1:].split(",", 1)[0])
                            except (ValueError, IndexError):
                                new_line = 0
                        elif part.startswith("-"):
                            try:
                                old_line = int(part[1:].split(",", 1)[0])
                            except (ValueError, IndexError):
                                old_line = 0
                elif raw_line.startswith("+") and not raw_line.startswith("+++"):
                    if new_line > 0:
                        added.add(new_line)
                    new_line += 1
                elif raw_line.startswith("-") and not raw_line.startswith("---"):
                    if old_line > 0:
                        deleted.add(old_line)
                    old_line += 1
                elif raw_line.startswith("\\"):
                    continue
                else:
                    if new_line > 0:
                        new_line += 1
                    if old_line > 0:
                        old_line += 1
        return added, deleted

    def get_changed_functions(self, commit_hash: str, file_path: str) -> list[ChangedFunction]:
        added, _ = self.get_changed_lines(commit_hash, file_path)
        if not added:
            return []
        try:
            content = self.repo.commit(commit_hash).tree[file_path].data_stream.read().decode("utf-8")
        except (OSError, SyntaxError):
            return []
        import ast
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        result: list[ChangedFunction] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", None)
                if end is None:
                    end = start
                if any(start <= line <= end for line in added):
                    module = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                    module = module.removesuffix(".__init__")
                    qualname = f"{module}.{node.name}"
                    result.append(
                        ChangedFunction(
                            qualified_name=qualname,
                            file_path=file_path,
                            lineno=start,
                            end_lineno=end,
                            change_type="modified" if end > start else "added",
                        )
                    )
        return result

    def get_commit_info(self, commit_hash: str) -> GitChange:
        commit = self.repo.commit(commit_hash)
        message = commit.message if isinstance(commit.message, str) else commit.message.decode("utf-8", errors="replace")
        author = commit.author.name if commit.author and commit.author.name else "unknown"
        return GitChange(
            commit_hash=commit.hexsha,
            message=message.strip(),
            author=author,
            timestamp=commit.committed_datetime.isoformat(),
            files=self.get_changed_files(commit_hash),
        )


__all__ = ["GitEngine"]
