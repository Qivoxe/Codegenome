from __future__ import annotations

from pathlib import Path

from codegenome.graph import GenomeGraph
from codegenome.impact import ImpactEngine
from codegenome.models import ImpactLevel, ImpactReport
from codegenome.parser import SourceParser
from codegenome.report import render_markdown

REPO_ROOT = Path(__file__).resolve().parent.parent / "sample_repo"


def test_parser_extracts_modules() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    assert len(parser.modules) == 7
    assert "checkout" in parser.modules
    assert "payment" in parser.modules
    assert "order" in parser.modules
    assert "invoice" in parser.modules
    assert "refund" in parser.modules
    assert "analytics" in parser.modules
    assert "notification" in parser.modules


def test_parser_extracts_functions() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    expected = {
        "checkout.calculate_discount",
        "checkout.apply_coupon",
        "checkout.checkout",
        "payment.process_payment",
        "payment.refund",
        "order.create_order",
        "order.cancel_order",
        "invoice.generate_invoice",
        "invoice.calculate_tax",
        "refund.process_refund",
        "refund.refund_status",
        "analytics.track_event",
        "analytics.get_dashboard_metrics",
        "notification.send_email",
        "notification.send_sms",
    }
    assert set(parser.functions.keys()) == expected


def test_parser_extracts_arguments() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    ctx = parser.functions["checkout.calculate_discount"]
    assert len(ctx.arguments) == 3
    arg_names = [a.name for a in ctx.arguments]
    assert "price" in arg_names
    assert "discount_rate" in arg_names
    assert "tax_rate" in arg_names


def test_parser_extracts_imports() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    assert any(node.qualified_name == "payment.process_payment" for node in parser.imports)
    assert any(node.qualified_name == "invoice.generate_invoice" for node in parser.imports)


def test_parser_builds_call_edges() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    call_edges = [e for e in parser.edges if e.type.value == "calls"]
    targets = {e.target for e in call_edges}
    assert "checkout.calculate_discount" in targets
    assert "checkout.checkout" in targets
    assert "payment.process_payment" in targets
    assert "analytics.track_event" in targets


def test_graph_builds_nodes_and_edges() -> None:
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
    assert graph.node_count() > 0
    assert graph.edge_count() > 0


def test_impact_direct_and_transitive() -> None:
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
    report = engine.compute_impact("checkout.calculate_discount")
    assert isinstance(report, ImpactReport)
    assert "checkout.checkout" in report.direct_impact
    assert "order.create_order" in report.transitive_impact
    assert report.impact_score > 0
    assert report.impact_level in (ImpactLevel.MEDIUM, ImpactLevel.HIGH)


def test_impact_report_markdown() -> None:
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
    report = engine.compute_impact("checkout.calculate_discount")
    md = render_markdown(report)
    assert "# CodeGenome Impact Report" in md
    assert "checkout.calculate_discount" in md
    assert "Impact Score:" in md


def test_graph_get_callers() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )

    callers = graph.get_callers("checkout.checkout")
    assert "order.create_order" in callers


def test_graph_get_callees() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )

    callees = graph.get_callees("checkout.checkout")
    assert "checkout.calculate_discount" in callees
    assert "invoice.generate_invoice" in callees


def test_graph_get_downstream_dependencies() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )

    downstream = graph.get_downstream_dependencies("checkout.checkout")
    assert "checkout.calculate_discount" in downstream
    assert "payment.process_payment" in downstream


def test_graph_get_upstream_dependencies() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )

    upstream = graph.get_upstream_dependencies("checkout.calculate_discount")
    assert "checkout.checkout" in upstream


def test_graph_get_impact_paths() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )

    paths = graph.get_impact_paths("checkout.checkout", "analytics.track_event")
    assert len(paths) > 0
    assert any("checkout.checkout" in p and "analytics.track_event" in p for p in paths)


def test_graph_circular_dependency_protection() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()

    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )

    callers = graph.get_callers("checkout.calculate_discount")
    visited = set()
    for caller in callers:
        assert caller not in visited
        visited.add(caller)
