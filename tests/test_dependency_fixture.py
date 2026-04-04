import sys
from pathlib import Path

from mlrepromutate.engine import ExperimentRunner, MutationEvaluator
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.dependency import RelaxRequirementsPinOperator

FIXTURE_ROOT = (
    Path(__file__).parent.parent / "examples" / "dependency-pin"
)


def test_dependency_mutation_survives_without_safeguard() -> None:
    operator = RelaxRequirementsPinOperator()
    candidates = operator.detect(FIXTURE_ROOT)

    assert len(candidates) == 1

    runner = ExperimentRunner(
        [sys.executable, "validate_unguarded.py"]
    )
    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(
        FIXTURE_ROOT,
        operator,
        candidates[0],
    )

    assert result.outcome is MutationOutcome.SURVIVED


def test_dependency_mutation_is_killed_with_safeguard() -> None:
    operator = RelaxRequirementsPinOperator()
    candidates = operator.detect(FIXTURE_ROOT)

    assert len(candidates) == 1

    runner = ExperimentRunner(
        [sys.executable, "validate_guarded.py"]
    )
    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(
        FIXTURE_ROOT,
        operator,
        candidates[0],
    )

    assert result.outcome is MutationOutcome.KILLED