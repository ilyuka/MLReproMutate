from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class MutationOutcome(StrEnum):
    """Possible outcomes of evaluating a mutation."""

    KILLED = "killed"
    SURVIVED = "survived"
    INVALID = "invalid"
    EQUIVALENT = "equivalent"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class MutationCandidate:
    """A possible reproducibility mutation detected in a project."""

    operator: str
    category: str
    target: Path
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MutationResult:
    """Result of evaluating a single mutation candidate."""

    candidate: MutationCandidate
    outcome: MutationOutcome
    duration_seconds: float | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)