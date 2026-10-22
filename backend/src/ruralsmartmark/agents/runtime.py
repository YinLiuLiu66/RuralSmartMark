from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from ..providers.llm import LLMProvider, get_llm_provider


@dataclass(slots=True)
class AgentRuntime:
    settings: Settings
    llm: LLMProvider
    artifact_dir: Path
    allow_mock_fallback: bool

    @property
    def provider_name(self) -> str:
        return self.llm.name


def build_runtime(
    settings: Settings | None = None,
    *,
    llm: LLMProvider | None = None,
    artifact_dir: Path | None = None,
    allow_mock_fallback: bool | None = None,
) -> AgentRuntime:
    settings = settings or get_settings()
    runtime = AgentRuntime(
        settings=settings,
        llm=llm or get_llm_provider(settings),
        artifact_dir=artifact_dir or settings.artifact_path,
        allow_mock_fallback=(
            settings.llm_fallback_to_mock if allow_mock_fallback is None else allow_mock_fallback
        ),
    )
    runtime.artifact_dir.mkdir(parents=True, exist_ok=True)
    return runtime


@lru_cache
def _cached_runtime() -> AgentRuntime:
    return build_runtime()


def get_runtime() -> AgentRuntime:
    return _cached_runtime()


RuntimeDep = Annotated[AgentRuntime, Depends(get_runtime)]
