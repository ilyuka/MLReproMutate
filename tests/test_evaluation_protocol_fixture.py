import sys
from pathlib import Path

from mlrepromutate.engine.evaluator import MutationEvaluator
from mlrepromutate.engine.runner import ExperimentRunner
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.evaluation_protocol import (
    ChangeCrossValidationFoldCountOperator,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "evaluation-protocol"
)


def test_cv_fold_fixture_survives_unguarded_validation() -> None:
    operator = ChangeCrossValidationFoldCountOperator(
        python_file=Path("experiment.py"),
    )

    candidates = operator.detect(FIXTURE_ROOT)

    assert len(candidates) == 1

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
        candidates[0],
    )

    assert result.outcome is MutationOutcome.SURVIVED


def test_cv_fold_fixture_is_killed_by_guarded_validation() -> None:
    operator = ChangeCrossValidationFoldCountOperator(
        python_file=Path("experiment.py"),
    )

    candidates = operator.detect(FIXTURE_ROOT)

    assert len(candidates) == 1

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
        candidates[0],
    )

    assert result.outcome is MutationOutcome.KILLED
