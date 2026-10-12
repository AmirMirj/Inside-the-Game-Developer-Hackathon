"""LLM client protocol: Azure OpenAI + deterministic mock swap-in."""

from __future__ import annotations

import json
from typing import Any, Protocol

from app.config import Settings, get_settings


class LlmClient(Protocol):
    provider_name: str

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]: ...


class MockLlmClient:
    """Offline explain client for demos/tests when Azure is not configured."""

    provider_name = "mock"

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        payload = json.loads(user)
        moment = payload["moment"]
        state = payload["state"]
        score = state.get("score", {})
        trigger = moment.get("trigger", "moment")
        clock = moment.get("match_clock", "?")
        team = payload.get("event", {}).get("team_id") or "a side"
        pressure = state.get("pressure", {})
        rhythm = state.get("rhythm", {})

        headlines = {
            "goal": f"Goal changes the story at {clock}",
            "shot": f"Chance created at {clock}",
            "pressure_spike": f"Pressure spike at {clock}",
            "turnover": f"Turnover shifts control at {clock}",
            "tackle_won": f"Tackle wins the ball at {clock}",
        }
        headline = headlines.get(trigger, f"Key moment at {clock}")

        why = (
            f"Score is {score.get('home', 0)}-{score.get('away', 0)}. "
            f"Recent pressure avg {pressure.get('recent_avg', 0)} "
            f"(swing {pressure.get('swing', 0)}), rhythm tempo "
            f"{rhythm.get('tempo', 'unknown')}. "
            f"This {trigger.replace('_', ' ')} matters because it changes who "
            f"controls the next phase for {team}."
        )
        body = (
            f"{moment.get('reason', 'A notable event occurred.')} "
            f"Context uses live match state, not the raw event alone."
        )
        return {
            "headline": headline,
            "body": body,
            "why_it_matters": why,
            "confidence": 0.72,
            "overlay_type": "moment_card",
            "duration_ms": 8000 if moment.get("priority") != "high" else 10000,
        }


class AzureOpenAIClient:
    """Thin Azure OpenAI chat client returning JSON object content."""

    provider_name = "azure_openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        try:
            from openai import AzureOpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Install openai package to use Azure explain provider: pip install openai"
            ) from exc

        if not self.settings.azure_openai_endpoint or not self.settings.azure_openai_api_key:
            raise RuntimeError("Azure OpenAI endpoint and API key are required")

        self._client = AzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
        )
        self._deployment = self.settings.azure_openai_deployment

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self._deployment,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


def build_llm_client(settings: Settings | None = None) -> LlmClient:
    cfg = settings or get_settings()
    provider = cfg.resolve_explain_provider()
    if provider == "azure":
        return AzureOpenAIClient(cfg)
    return MockLlmClient()
