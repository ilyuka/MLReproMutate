from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class MutationOutcome(StrEnum):
    """Possible outcomes of evaluating a mutation.

    Attributes:
        KILLED: The validation workflow failed after mutation.
        SURVIVED: The validation workflow succeeded after mutation.
        INVALID: The mutation could not be evaluated as intended.
        EQUIVALENT: The mutation did not change the relevant property.
        TIMEOUT: Validation exceeded its configured time limit.
        ERROR: Evaluation failed for an unrelated infrastructure or framework
            reason.
    """

    KILLED = "killed"
    SURVIVED = "survived"
    INVALID = "invalid"
    EQUIVALENT = "equivalent"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class MutationCandidate:
    """A possible reproducibility mutation detected in a project.

    Attributes:
        operator: Unique name of the operator that detected the candidate.
        category: Reproducibility-threat category assigned by the operator.
        target: Path to the mutation target, relative to the project root.
        description: Human-readable description of the proposed mutation.
        metadata: Operator-specific data required to apply the mutation.
    """

    operator: str
    category: str
    target: Path
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MutationResult:
    """Result of evaluating a single mutation candidate.

    Attributes:
        candidate: Candidate that was evaluated.
        outcome: Classification produced by the evaluation.
        duration_seconds: Mutation-validation duration, when recorded.
        reason: Human-readable explanation of the outcome, when available.
        metadata: Evaluation-specific details such as command output.
    """

    candidate: MutationCandidate
    outcome: MutationOutcome
    duration_seconds: float | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
