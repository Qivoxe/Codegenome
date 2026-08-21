from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path

from codegenome.models import (
    EdgeType,
    FunctionArgument,
    GraphEdge,
    GraphNode,
    NodeType,
)


@dataclass
class FunctionContext:
    qualified_name: str
    lineno: int
    end_lineno: int | None
    arguments: list[FunctionArgument] = field(default_factory=list)
    calls: set[str] = field(default_factory=set)


class SourceParser:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.modules: dict[str, GraphNode] = {}
        self.classes: dict[str, GraphNode] = {}
        self.functions: dict[str, FunctionContext] = {}
        self.function_nodes: dict[str, GraphNode] = {}
        self.method_nodes: dict[str, GraphNode] = {}
        self.imports: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self._current_file: Path | None = None
        self._module_qualified_name: str = ""
        self._module_imports: dict[str, str] = {}
        self._current_class: str | None = None

    def parse_repo(self) -> None:
        for py_file in self._iter_python_files(self.repo_root):
            self._parse_file(py_file)

    def _iter_python_files(self, root: Path) -> list[Path]:
        files: list[Path] = []
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if fname.endswith(".py"):
                    files.append(Path(dirpath) / fname)
        return sorted(files)

    def _relative_module(self, file_path: Path) -> str:
        rel = file_path.relative_to(self.repo_root)
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else "__root__"

    def _parse_file(self, file_path: Path) -> None:
        self._current_file = file_path
        self._module_qualified_name = self._relative_module(file_path)
        self._module_imports = {}
        self._current_class = None
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError:
            return

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        module_node = GraphNode(
            id=self._module_qualified_name,
            type=NodeType.MODULE,
            name=self._module_qualified_name.split(".")[-1] or self._module_qualified_name,
            qualified_name=self._module_qualified_name,
            file_path=str(file_path.relative_to(self.repo_root)),
            lineno=1,
            end_lineno=len(source.splitlines()),
        )
        self.modules[self._module_qualified_name] = module_node

        visitor = _RepoVisitor(self)
        visitor.visit(tree)

        self.edges.extend(visitor.edges)

    def _register_class(self, name: str, qualname: str, lineno: int, end_lineno: int | None) -> None:
        node = GraphNode(
            id=qualname,
            type=NodeType.CLASS,
            name=name,
            qualified_name=qualname,
            file_path=str(self._current_file.relative_to(self.repo_root)) if self._current_file else "",
            lineno=lineno,
            end_lineno=end_lineno,
        )
        self.classes[qualname] = node

    def _register_function(self, ctx: FunctionContext, is_method: bool = False) -> None:
        node_type = NodeType.METHOD if is_method else NodeType.FUNCTION
        node = GraphNode(
            id=ctx.qualified_name,
            type=node_type,
            name=ctx.qualified_name.split(".")[-1],
            qualified_name=ctx.qualified_name,
            file_path=str(self._current_file.relative_to(self.repo_root)) if self._current_file else "",
            lineno=ctx.lineno,
            end_lineno=ctx.end_lineno,
            arguments=ctx.arguments,
        )
        if is_method:
            self.method_nodes[ctx.qualified_name] = node
        else:
            self.function_nodes[ctx.qualified_name] = node
        self.functions[ctx.qualified_name] = ctx

    def _register_import(self, module_name: str, alias: str | None, lineno: int) -> None:
        node = GraphNode(
            id=f"{self._module_qualified_name}::{module_name}::{lineno}",
            type=NodeType.IMPORT,
            name=alias or module_name,
            qualified_name=module_name,
            file_path=str(self._current_file.relative_to(self.repo_root)) if self._current_file else "",
            lineno=lineno,
        )
        self.imports.append(node)

    def _extract_arguments(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[FunctionArgument]:
        args: list[FunctionArgument] = []
        all_args = node.args.args + node.args.posonlyargs + node.args.kwonlyargs
        if node.args.vararg:
            all_args.append(node.args.vararg)
        if node.args.kwarg:
            all_args.append(node.args.kwarg)

        defaults = node.args.defaults + node.args.kw_defaults
        default_start = len(all_args) - len(defaults)

        for i, arg in enumerate(all_args):
            default_val = None
            if i >= default_start:
                d = defaults[i - default_start]
                if d is not None:
                    default_val = ast.unparse(d)
            args.append(
                FunctionArgument(
                    name=arg.arg,
                    kind=arg.arg,
                    default=default_val,
                )
            )
        return args


class _RepoVisitor(ast.NodeVisitor):
    def __init__(self, parser: SourceParser) -> None:
        self.parser = parser
        self.edges: list[GraphEdge] = []
        self._scope_stack: list[str] = []

    def _current_scope(self) -> str:
        return ".".join(self._scope_stack) if self._scope_stack else self.parser._module_qualified_name

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualname = f"{self._current_scope()}.{node.name}"
        self.parser._register_class(node.name, qualname, node.lineno, getattr(node, "end_lineno", None))
        self.edges.append(
            GraphEdge(
                source=self.parser._module_qualified_name,
                target=qualname,
                type=EdgeType.CONTAINS,
            )
        )
        previous_class = self.parser._current_class
        self.parser._current_class = qualname
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()
        self.parser._current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        scope = self._current_scope()
        qualname = f"{scope}.{node.name}"
        is_method = self.parser._current_class is not None and scope == self.parser._current_class
        args = self.parser._extract_arguments(node)
        ctx = FunctionContext(
            qualified_name=qualname,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", None),
            arguments=args,
        )
        self.parser._register_function(ctx, is_method=is_method)

        if scope != self.parser._module_qualified_name:
            self.edges.append(
                GraphEdge(
                    source=scope,
                    target=qualname,
                    type=EdgeType.CONTAINS,
                )
            )

        self._scope_stack.append(node.name)
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                self._record_call(child, qualname)
        self._scope_stack.pop()

    def _record_call(self, node: ast.Call, caller_qualname: str) -> None:
        func = node.func
        name_parts: list[str] = []

        if isinstance(func, ast.Name):
            name_parts = [func.id]
        elif isinstance(func, ast.Attribute):
            parts: list[str] = []
            cur: ast.expr = func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            name_parts = list(reversed(parts))
        elif isinstance(func, ast.Subscript):
            return

        if not name_parts:
            return

        callee = ".".join(name_parts)

        if len(name_parts) == 1:
            caller_module = caller_qualname.split(".")[0]
            local_fqn = f"{caller_module}.{name_parts[0]}"
            if local_fqn in self.parser.functions:
                callee = local_fqn
            elif name_parts[0] in self.parser._module_imports:
                callee = self.parser._module_imports[name_parts[0]]
        elif len(name_parts) == 2:
            if name_parts[0] == "self" and self.parser._current_class:
                method_fqn = f"{self.parser._current_class}.{name_parts[1]}"
                if method_fqn in self.parser.functions:
                    callee = method_fqn

        self.parser.functions[caller_qualname].calls.add(callee)
        self.edges.append(
            GraphEdge(
                source=caller_qualname,
                target=callee,
                type=EdgeType.CALLS,
            )
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.parser._register_import(alias.name, alias.asname, node.lineno)
            self.edges.append(
                GraphEdge(
                    source=self.parser._module_qualified_name,
                    target=alias.name,
                    type=EdgeType.IMPORTS,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.parser._register_import(full_name, alias.asname, node.lineno)
            local_name = alias.asname or alias.name
            self.parser._module_imports[local_name] = full_name
            self.edges.append(
                GraphEdge(
                    source=self.parser._module_qualified_name,
                    target=full_name,
                    type=EdgeType.IMPORTS,
                )
            )

    def generic_visit(self, node: ast.AST) -> None:
        super().generic_visit(node)


__all__ = ["SourceParser"]
