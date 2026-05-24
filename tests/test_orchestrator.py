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

def test_orchestrator_runs_baseline_only_once(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n"
        "pandas==2.2.3\n"
        "scipy==1.14.0\n",
        encoding="utf-8",
    )

    counter_file = tmp_path / "counter.txt"
    counter_file.write_text("0", encoding="utf-8")

    validation_script = project / "validate.py"
    validation_script.write_text(
        (
            "from pathlib import Path\n"
            "\n"
            f"counter = Path({str(counter_file)!r})\n"
            "value = int(counter.read_text())\n"
            "counter.write_text(str(value + 1))\n"
            "raise SystemExit(0)\n"
        ),
        encoding="utf-8",
    )

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )
    evaluator = MutationEvaluator(runner)
    orchestrator = MutationOrchestrator(evaluator)
    operator = RelaxRequirementsPinOperator()

    results = orchestrator.run(project, operator)

    assert len(results) == 3

    # One baseline run + one run for each of the three mutants.
    assert counter_file.read_text(encoding="utf-8") == "4"

def test_orchestrator_can_evaluate_selected_candidates(
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

    candidates = operator.detect(project)

    results = orchestrator.run(
        project,
        operator,
        candidates=[candidates[1]],
    )

    assert len(results) == 1
    assert results[0].candidate == candidates[1]
    assert results[0].outcome is MutationOutcome.SURVIVED
