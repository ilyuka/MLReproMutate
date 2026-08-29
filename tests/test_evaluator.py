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

def test_evaluator_in_place_restores_mutated_target(
    tmp_path: Path,
) -> None:
    from mlrepromutate.engine import ExecutionMode
    from mlrepromutate.operators.dependency import (
        RelaxRequirementsPinOperator,
    )

    project = tmp_path / "project"
    project.mkdir()

    requirements = project / "requirements.txt"
    requirements.write_text(
        "demo==1.0.0\n",
        encoding="utf-8",
    )

    validate = project / "validate.py"
    validate.write_text(
        "from pathlib import Path\n"
        "text = Path('requirements.txt').read_text()\n"
        "raise SystemExit(0 if 'demo>=1.0.0' in text else 1)\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt"),
    )
    candidate = operator.detect(project)[0]

    runner = ExperimentRunner(
        ["python", "validate.py"],
    )

    evaluator = MutationEvaluator(
        runner,
        execution_mode=ExecutionMode.IN_PLACE,
    )

    result = evaluator.evaluate_mutation(
        project,
        operator,
        candidate,
    )

    assert result.outcome.value == "survived"
    assert requirements.read_text(
        encoding="utf-8"
    ) == "demo==1.0.0\n"


def test_evaluator_in_place_restores_target_after_killed_mutation(
    tmp_path: Path,
) -> None:
    from mlrepromutate.engine import ExecutionMode
    from mlrepromutate.operators.dependency import (
        RelaxRequirementsPinOperator,
    )

    project = tmp_path / "project"
    project.mkdir()

    requirements = project / "requirements.txt"
    original = b"demo==1.0.0\n"
    requirements.write_bytes(original)

    validate = project / "validate.py"
    validate.write_text(
        "from pathlib import Path\n"
        "text = Path('requirements.txt').read_text()\n"
        "raise SystemExit(1 if 'demo>=1.0.0' in text else 0)\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt"),
    )
    candidate = operator.detect(project)[0]

    evaluator = MutationEvaluator(
        ExperimentRunner(["python", "validate.py"]),
        execution_mode=ExecutionMode.IN_PLACE,
    )

    result = evaluator.evaluate_mutation(
        project,
        operator,
        candidate,
    )

    assert result.outcome.value == "killed"
    assert requirements.read_bytes() == original


def test_evaluator_in_place_restores_target_after_timeout(
    tmp_path: Path,
) -> None:
    from mlrepromutate.engine import ExecutionMode
    from mlrepromutate.operators.dependency import (
        RelaxRequirementsPinOperator,
    )

    project = tmp_path / "project"
    project.mkdir()

    requirements = project / "requirements.txt"
    original = b"demo==1.0.0\n"
    requirements.write_bytes(original)

    validate = project / "validate.py"
    validate.write_text(
        "import time\n"
        "time.sleep(1)\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt"),
    )
    candidate = operator.detect(project)[0]

    evaluator = MutationEvaluator(
        ExperimentRunner(
            ["python", "validate.py"],
            timeout_seconds=0.05,
        ),
        execution_mode=ExecutionMode.IN_PLACE,
    )

    result = evaluator.evaluate_mutation(
        project,
        operator,
        candidate,
    )

    assert result.outcome.value == "timeout"
    assert requirements.read_bytes() == original


def test_sandbox_uses_mutated_src_tree_over_external_pythonpath(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mlrepromutate.operators.randomness import (
        ChangePythonRandomSeedOperator,
    )

    project = tmp_path / "project"
    package = project / "src" / "sample_project"
    package.mkdir(parents=True)

    (package / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )

    experiment = package / "experiment.py"
    experiment.write_text(
        "import random\n"
        "\n"
        "random.seed(42)\n"
        "VALUE = random.random()\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "from sample_project.experiment import VALUE\n"
        "\n"
        "EXPECTED = 0.6394267984578837\n"
        "raise SystemExit(0 if VALUE == EXPECTED else 1)\n",
        encoding="utf-8",
    )

    # Simulate an editable-installed src-layout project whose original
    # source tree is already visible to the validation interpreter.
    monkeypatch.setenv(
        "PYTHONPATH",
        str(project / "src"),
    )

    operator = ChangePythonRandomSeedOperator(
        python_file=Path("src/sample_project/experiment.py"),
    )
    candidate = operator.detect(project)[0]

    evaluator = MutationEvaluator(
        ExperimentRunner(
            [sys.executable, "validate.py"],
        ),
    )

    result = evaluator.evaluate(
        project,
        operator,
        candidate,
    )

    assert result.outcome is MutationOutcome.KILLED
