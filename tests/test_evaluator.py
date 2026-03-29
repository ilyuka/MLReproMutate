import sys
from pathlib import Path

import pytest

from mlrepromutate.engine import (
    BaselineValidationError,
    ExperimentRunner,
    MutationEvaluator,
)
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.dependency import RelaxRequirementsPinOperator


def create_project(tmp_path: Path, validation_script: str) -> Path:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        validation_script,
        encoding="utf-8",
    )

    return project


def test_mutation_survives_when_validation_still_passes(
    tmp_path: Path,
) -> None:
    project = create_project(
        tmp_path,
        "raise SystemExit(0)\n",
    )

    operator = RelaxRequirementsPinOperator()
    candidate = operator.detect(project)[0]

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(project, operator, candidate)

    assert result.outcome is MutationOutcome.SURVIVED
    assert result.metadata["return_code"] == 0


def test_mutation_is_killed_when_validation_detects_change(
    tmp_path: Path,
) -> None:
    project = create_project(
        tmp_path,
        (
            "from pathlib import Path\n"
            "\n"
            "content = Path('requirements.txt').read_text()\n"
            "raise SystemExit(0 if 'numpy==2.1.0' in content else 1)\n"
        ),
    )

    operator = RelaxRequirementsPinOperator()
    candidate = operator.detect(project)[0]

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(project, operator, candidate)

    assert result.outcome is MutationOutcome.KILLED
    assert result.metadata["return_code"] == 1


def test_baseline_failure_prevents_classification(
    tmp_path: Path,
) -> None:
    project = create_project(
        tmp_path,
        "raise SystemExit(2)\n",
    )

    operator = RelaxRequirementsPinOperator()
    candidate = operator.detect(project)[0]

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    evaluator = MutationEvaluator(runner)

    with pytest.raises(
        BaselineValidationError,
        match="Baseline validation failed",
    ):
        evaluator.evaluate(project, operator, candidate)


def test_mutation_timeout_is_reported(
    tmp_path: Path,
) -> None:
    project = create_project(
        tmp_path,
        (
            "from pathlib import Path\n"
            "import time\n"
            "\n"
            "content = Path('requirements.txt').read_text()\n"
            "if 'numpy>=' in content:\n"
            "    time.sleep(1)\n"
        ),
    )

    operator = RelaxRequirementsPinOperator()
    candidate = operator.detect(project)[0]

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
        timeout_seconds=0.05,
    )

    evaluator = MutationEvaluator(runner)

    result = evaluator.evaluate(project, operator, candidate)

    assert result.outcome is MutationOutcome.TIMEOUT
    assert result.metadata["return_code"] is None


def test_evaluation_does_not_modify_original_project(
    tmp_path: Path,
) -> None:
    project = create_project(
        tmp_path,
        "raise SystemExit(0)\n",
    )

    requirements = project / "requirements.txt"
    original_content = requirements.read_text(encoding="utf-8")

    operator = RelaxRequirementsPinOperator()
    candidate = operator.detect(project)[0]

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    evaluator = MutationEvaluator(runner)

    evaluator.evaluate(project, operator, candidate)

    assert requirements.read_text(encoding="utf-8") == original_content