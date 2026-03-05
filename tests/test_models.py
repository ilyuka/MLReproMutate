from pathlib import Path

from mlrepromutate.models import (
    MutationCandidate,
    MutationOutcome,
    MutationResult,
)


def test_mutation_outcome_values() -> None:
    assert MutationOutcome.KILLED == "killed"
    assert MutationOutcome.SURVIVED == "survived"
    assert MutationOutcome.INVALID == "invalid"
    assert MutationOutcome.EQUIVALENT == "equivalent"
    assert MutationOutcome.TIMEOUT == "timeout"
    assert MutationOutcome.ERROR == "error"


def test_mutation_candidate_creation() -> None:
    candidate = MutationCandidate(
        operator="remove_dependency_pin",
        category="dependency",
        target=Path("pyproject.toml"),
        description="Remove an exact dependency constraint.",
        metadata={"package": "scikit-learn"},
    )

    assert candidate.operator == "remove_dependency_pin"
    assert candidate.category == "dependency"
    assert candidate.target == Path("pyproject.toml")
    assert candidate.metadata["package"] == "scikit-learn"


def test_mutation_result_creation() -> None:
    candidate = MutationCandidate(
        operator="remove_dependency_pin",
        category="dependency",
        target=Path("pyproject.toml"),
        description="Remove an exact dependency constraint.",
    )

    result = MutationResult(
        candidate=candidate,
        outcome=MutationOutcome.SURVIVED,
        duration_seconds=1.25,
        reason="Existing safeguards did not detect the mutation.",
    )

    assert result.candidate == candidate
    assert result.outcome is MutationOutcome.SURVIVED
    assert result.duration_seconds == 1.25