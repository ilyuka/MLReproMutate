import sys
from pathlib import Path

from mlrepromutate.engine.evaluator import MutationEvaluator
from mlrepromutate.engine.runner import ExperimentRunner
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.data_split import (
    RemoveTrainTestSplitStratificationOperator,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "data-split"
)


def _candidate():
    operator = RemoveTrainTestSplitStratificationOperator(
        python_file=Path("experiment.py"),
    )

    candidates = operator.detect(FIXTURE_ROOT)

    assert len(candidates) == 1

    return operator, candidates[0]


def test_data_split_fixture_survives_unguarded_validation() -> None:
    operator, candidate = _candidate()

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


def test_data_split_fixture_is_killed_by_guarded_validation() -> None:
    operator, candidate = _candidate()

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
