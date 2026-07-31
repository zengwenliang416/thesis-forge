from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AIRequest:
    task: str
    text: str


@dataclass(slots=True)
class AIResponse:
    text: str


class AIProvider(Protocol):
    def complete(self, request: AIRequest) -> AIResponse: ...
