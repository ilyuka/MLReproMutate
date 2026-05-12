import sys
from pathlib import Path

from mlrepromutate.engine.evaluator import MutationEvaluator
from mlrepromutate.engine.runner import ExperimentRunner
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.randomness import (
    ChangePythonRandomSeedOperator,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "random-seed"
)


def test_random_seed_fixture_survives_unguarded_validation() -> None:
    operator = ChangePythonRandomSeedOperator(
        python_file=Path("experiment.py"),
    )

    candidate = operator.detect(FIXTURE_ROOT)[0]

    runner = ExperimentRunner(
        [
            sys.executable,
            "validate_unguarded.py",
        ]
    )
    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(
        FIXTURE_ROOT,
        operator,
        candidate,
    )

    assert result.outcome is MutationOutcome.SURVIVED


def test_random_seed_fixture_is_killed_by_guarded_validation() -> None:
    operator = ChangePythonRandomSeedOperator(
        python_file=Path("experiment.py"),
    )

    candidate = operator.detect(FIXTURE_ROOT)[0]

    runner = ExperimentRunner(
        [
            sys.executable,
            "validate_guarded.py",
        ]
    )
    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(
        FIXTURE_ROOT,
        operator,
        candidate,
    )

    assert result.outcome is MutationOutcome.KILLED
