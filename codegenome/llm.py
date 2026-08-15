from __future__ import annotations

import json
import os

from pydantic import BaseModel, Field


class ExplanationInput(BaseModel):
    changed_function: str
    impact_score: int
    impact_level: str
    affected_components: list[str]
    impact_paths: list[list[str]]
    direct_impact: list[str]
    transitive_impact: list[str]
    risk_factors: dict[str, float] = Field(default_factory=dict)
    relevant_code: str = ""


class ExplanationOutput(BaseModel):
    summary: str
    why_risky: str
    affected_components_explanation: str
    impact_paths_explanation: str
    recommended_tests: list[str]
    review_recommendations: list[str]


class LLMExplainer:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CODEGENOME_LLM_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("CODEGENOME_LLM_BASE_URL")
        self.model_name = os.getenv("OPENAI_MODEL") or os.getenv("CODEGENOME_LLM_MODEL", "gpt-4o-mini")
        self._available = bool(self.api_key)

    def is_available(self) -> bool:
        return self._available

    def explain(self, payload: ExplanationInput) -> ExplanationOutput:
        if not self._available:
            return self._fallback(payload)
        try:
            return self._call_llm(payload)
        except (OSError, ValueError, KeyError):
            return self._fallback(payload)

    def _call_llm(self, payload: ExplanationInput) -> ExplanationOutput:
        import urllib.request

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        prompt = self._build_prompt(payload)
        body = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return self._parse_response(text, payload)

    def _build_prompt(self, payload: ExplanationInput) -> str:
        return f"""
You are a software impact analyst. Explain the following code change impact.

Changed function: {payload.changed_function}
Impact score: {payload.impact_score}/100
Impact level: {payload.impact_level}
Affected components: {', '.join(payload.affected_components)}
Direct impact: {', '.join(payload.direct_impact)}
Transitive impact: {', '.join(payload.transitive_impact)}
Impact paths: {payload.impact_paths}

Relevant code snippet:
{payload.relevant_code}

Provide:
1. Summary
2. Why risky
3. Affected components explanation
4. Impact paths explanation
5. Recommended tests
6. Review recommendations

Return JSON with keys: summary, why_risky, affected_components_explanation, impact_paths_explanation, recommended_tests (list), review_recommendations (list).
"""

    def _parse_response(self, text: str, payload: ExplanationInput) -> ExplanationOutput:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(text[start:end])
                return ExplanationOutput(
                    summary=data.get("summary", ""),
                    why_risky=data.get("why_risky", ""),
                    affected_components_explanation=data.get("affected_components_explanation", ""),
                    impact_paths_explanation=data.get("impact_paths_explanation", ""),
                    recommended_tests=data.get("recommended_tests", []),
                    review_recommendations=data.get("review_recommendations", []),
                )
        except (json.JSONDecodeError, KeyError):
            pass
        return self._fallback(payload)

    def _fallback(self, payload: ExplanationInput) -> ExplanationOutput:
        summary = (
            f"Changing `{payload.changed_function}` has a {payload.impact_level.lower()} impact "
            f"with score {payload.impact_score}/100."
        )
        why_risky = (
            f"{payload.changed_function} affects {len(payload.affected_components)} component(s). "
            f"{len(payload.direct_impact)} direct caller(s) and {len(payload.transitive_impact)} transitive caller(s) depend on it."
        )
        affected = (
            f"Affected components: {', '.join(payload.affected_components)}."
            if payload.affected_components
            else "No affected components detected."
        )
        paths = (
            f"Impact paths: {'; '.join(' -> '.join(p) for p in payload.impact_paths[:3])}."
            if payload.impact_paths
            else "No impact paths found."
        )
        tests = [
            f"{payload.changed_function}_test",
        ]
        for comp in payload.affected_components[:3]:
            tests.append(f"{comp}_integration_test")
        reviews = [
            "Verify backward compatibility.",
            "Run integration tests for affected components.",
            "Check data contracts between affected modules.",
        ]
        return ExplanationOutput(
            summary=summary,
            why_risky=why_risky,
            affected_components_explanation=affected,
            impact_paths_explanation=paths,
            recommended_tests=tests,
            review_recommendations=reviews,
        )


__all__ = ["ExplanationInput", "ExplanationOutput", "LLMExplainer"]
