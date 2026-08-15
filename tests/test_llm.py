from __future__ import annotations

import pytest

from codegenome.llm import ExplanationInput, LLMExplainer


def test_llm_explainer_available_without_key() -> None:
    explainer = LLMExplainer()
    assert not explainer.is_available()


def test_llm_explainer_fallback() -> None:
    explainer = LLMExplainer()
    payload = ExplanationInput(
        changed_function="checkout.calculate_discount",
        impact_score=40,
        impact_level="MEDIUM",
        affected_components=["checkout", "order"],
        impact_paths=[["checkout.calculate_discount", "checkout.checkout", "order.create_order"]],
        direct_impact=["checkout.checkout"],
        transitive_impact=["order.create_order"],
    )
    output = explainer.explain(payload)
    assert output.summary
    assert output.why_risky
    assert len(output.recommended_tests) >= 1
    assert len(output.review_recommendations) >= 1
    assert "checkout.calculate_discount" in output.summary


def test_llm_explainer_empty_inputs() -> None:
    explainer = LLMExplainer()
    payload = ExplanationInput(
        changed_function="foo.bar",
        impact_score=0,
        impact_level="LOW",
        affected_components=[],
        impact_paths=[],
        direct_impact=[],
        transitive_impact=[],
    )
    output = explainer.explain(payload)
    assert output.summary
    assert output.why_risky


def test_llm_explainer_with_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEGENOME_LLM_API_KEY", "test-key")
    monkeypatch.setenv("CODEGENOME_LLM_BASE_URL", "http://localhost:9999")
    explainer = LLMExplainer()
    assert explainer.is_available()
    payload = ExplanationInput(
        changed_function="foo.bar",
        impact_score=50,
        impact_level="MEDIUM",
        affected_components=["foo"],
        impact_paths=[["foo.bar", "foo.baz"]],
        direct_impact=["foo.baz"],
        transitive_impact=[],
    )
    output = explainer.explain(payload)
    assert "foo.bar" in output.summary