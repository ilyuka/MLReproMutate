import sys
from pathlib import Path

from mlrepromutate.engine.environment import (
    EnvironmentResolutionResult,
)
from mlrepromutate.engine.resolved_dependency import (
    ResolvedDependencyEvaluator,
)
from mlrepromutate.engine.runner import ExperimentRunner
from mlrepromutate.models import MutationOutcome
from mlrepromutate.operators.dependency import (
    RelaxRequirementsPinOperator,
)


class FakeResolver:
    def __init__(
        self,
        *,
        mutant_version: str | None,
        mutant_return_code: int = 0,
        mutant_timed_out: bool = False,
    ) -> None:
        self.mutant_version = mutant_version
        self.mutant_return_code = mutant_return_code
        self.mutant_timed_out = mutant_timed_out
        self.calls = 0

    def resolve(
        self,
        project_root: Path,
        requirements_file: Path,
    ) -> EnvironmentResolutionResult:
        del project_root, requirements_file

        self.calls += 1

        if self.calls == 1:
            return EnvironmentResolutionResult(
                python_executable=Path(sys.executable),
                return_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.1,
                timed_out=False,
            )

        return EnvironmentResolutionResult(
            python_executable=Path(sys.executable),
            return_code=self.mutant_return_code,
            stdout="",
            stderr="",
            duration_seconds=0.1,
            timed_out=self.mutant_timed_out,
        )

    def distribution_versions(
        self,
        python_executable: Path,
    ) -> dict[str, str]:
        del python_executable

        return {
            "numpy": "2.1.0",
        }

    def distribution_version(
        self,
        python_executable: Path,
        distribution: str,
    ) -> str | None:
        del python_executable, distribution

        return self.mutant_version


def make_project(
    tmp_path: Path,
    *,
    validation_exit_code: int = 0,
) -> Path:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        f"raise SystemExit({validation_exit_code})\n",
        encoding="utf-8",
    )

    return project


def test_resolved_mutation_is_equivalent_when_version_does_not_change(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    resolver = FakeResolver(
        mutant_version="2.1.0",
    )

    evaluator = ResolvedDependencyEvaluator(
        runner,
        resolver,  # type: ignore[arg-type]
        Path("requirements.txt"),
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt")
    )

    candidate = operator.detect(project)[0]

    evaluator.validate_baseline(project)

    result = evaluator.evaluate_mutation(
        project,
        operator,
        candidate,
    )

    assert result.outcome is MutationOutcome.EQUIVALENT
    assert result.metadata["baseline_resolved_version"] == "2.1.0"
    assert result.metadata["mutant_resolved_version"] == "2.1.0"


def test_resolved_mutation_survives_when_version_changes_and_validation_passes(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    resolver = FakeResolver(
        mutant_version="2.2.0",
    )

    evaluator = ResolvedDependencyEvaluator(
        runner,
        resolver,  # type: ignore[arg-type]
        Path("requirements.txt"),
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt")
    )

    candidate = operator.detect(project)[0]

    evaluator.validate_baseline(project)

    result = evaluator.evaluate_mutation(
        project,
        operator,
        candidate,
    )

    assert result.outcome is MutationOutcome.SURVIVED
    assert result.metadata["baseline_resolved_version"] == "2.1.0"
    assert result.metadata["mutant_resolved_version"] == "2.2.0"


def test_resolved_mutation_is_invalid_when_resolution_fails(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    runner = ExperimentRunner(
        [sys.executable, "validate.py"],
    )

    resolver = FakeResolver(
        mutant_version=None,
        mutant_return_code=1,
    )

    evaluator = ResolvedDependencyEvaluator(
        runner,
        resolver,  # type: ignore[arg-type]
        Path("requirements.txt"),
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt")
    )

    candidate = operator.detect(project)[0]

    evaluator.validate_baseline(project)

    result = evaluator.evaluate_mutation(
        project,
        operator,
        candidate,
    )

    assert result.outcome is MutationOutcome.INVALID