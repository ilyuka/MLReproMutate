import sys
from pathlib import Path

from mlrepromutate.engine import (
    ExperimentRunner,
    MutationEvaluator,
    MutationOrchestrator,
)
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.dependency import RelaxRequirementsPinOperator


def test_orchestrator_detects_and_evaluates_candidates(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n"
        "pandas==2.2.3\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )
    evaluator = MutationEvaluator(runner)
    orchestrator = MutationOrchestrator(evaluator)
    operator = RelaxRequirementsPinOperator()

    results = orchestrator.run(project, operator)

    assert len(results) == 2
    assert all(
        result.outcome is MutationOutcome.SURVIVED
        for result in results
    )


def test_orchestrator_returns_empty_results_when_no_candidates(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy>=2.1.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )
    evaluator = MutationEvaluator(runner)
    orchestrator = MutationOrchestrator(evaluator)
    operator = RelaxRequirementsPinOperator()

    results = orchestrator.run(project, operator)

    assert results == []