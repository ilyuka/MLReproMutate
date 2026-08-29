from collections.abc import Sequence
from pathlib import Path
from typing import Any

from mlrepromutate.engine.environment import (
    VirtualEnvironmentResolver,
    normalize_distribution_name,
)
from mlrepromutate.engine.evaluator import (
    BaselineValidationError,
    MutationEvaluator,
)
from mlrepromutate.engine.runner import (
    ExecutionResult,
    ExperimentRunner,
)
from mlrepromutate.engine.sandbox import ProjectSandbox
from mlrepromutate.models import (
    MutationCandidate,
    MutationOutcome,
    MutationResult,
)
from mlrepromutate.operators.base import MutationOperator


class ResolvedDependencyEvaluator(MutationEvaluator):
    """Evaluate dependency mutations in freshly resolved environments."""

    def __init__(
        self,
        runner: ExperimentRunner,
        resolver: VirtualEnvironmentResolver,
        requirements_file: Path,
        *,
        sandbox_excludes: Sequence[Path] = (),
    ) -> None:
        super().__init__(
            runner,
            sandbox_excludes=sandbox_excludes,
        )

        self.resolver = resolver
        self.requirements_file = requirements_file
        self._baseline_versions: dict[str, str] | None = None
        self._baseline_resolution_metadata: dict[str, Any] | None = None

    def validate_baseline(
        self,
        project_root: Path,
    ) -> ExecutionResult:
        """Resolve and validate the unmodified dependency environment."""

        with ProjectSandbox(
            project_root,
            excludes=self.sandbox_excludes,
        ) as sandbox:
            resolution = self.resolver.resolve(
                sandbox,
                self.requirements_file,
            )
            self._baseline_resolution_metadata = {
                "return_code": resolution.return_code,
                "stdout": resolution.stdout,
                "stderr": resolution.stderr,
                "duration_seconds": resolution.duration_seconds,
                "timed_out": resolution.timed_out,
            }

            if resolution.timed_out:
                raise BaselineValidationError(
                    "Baseline dependency resolution timed out."
                )

            if (
                resolution.return_code != 0
                or resolution.python_executable is None
            ):
                raise BaselineValidationError(
                    "Baseline dependency resolution failed."
                )

            self._baseline_versions = (
                self.resolver.distribution_versions(
                    resolution.python_executable
                )
            )

            resolved_runner = self.runner.with_python_executable(
                resolution.python_executable
            )

            result = resolved_runner.run(
                sandbox,
                prefer_project_sources=True,
            )

        if result.timed_out:
            raise BaselineValidationError(
                "Baseline validation timed out."
            )

        if result.return_code != 0:
            raise BaselineValidationError(
                "Baseline validation failed after dependency resolution."
            )

        return result

    def run_metadata(self) -> dict[str, Any]:
        """Return resolved-environment provenance."""

        return {
            "baseline_resolution": self._baseline_resolution_metadata,
            "baseline_distributions": (
                dict(self._baseline_versions)
                if self._baseline_versions is not None
                else None
            ),
        }
    
    def evaluate_mutation(
        self,
        project_root: Path,
        operator: MutationOperator,
        candidate: MutationCandidate,
    ) -> MutationResult:
        """Resolve and evaluate one dependency mutation."""

        if self._baseline_versions is None:
            raise RuntimeError(
                "Resolved baseline must be validated before mutations."
            )

        package = candidate.metadata.get("package")

        if not isinstance(package, str):
            raise TypeError(
                "Dependency candidate must contain a package name."
            )

        normalized_package = normalize_distribution_name(package)
        baseline_version = self._baseline_versions.get(
            normalized_package
        )

        if baseline_version is None:
            return MutationResult(
                candidate=candidate,
                outcome=MutationOutcome.INVALID,
                reason=(
                    "Target dependency was not present in the "
                    "resolved baseline environment."
                ),
                metadata={
                    "dependency_mode": "resolved",
                    "baseline_resolved_version": None,
                    "mutant_resolved_version": None,
                },
            )

        with ProjectSandbox(
            project_root,
            excludes=self.sandbox_excludes,
        ) as sandbox:
            operator.apply(
                sandbox,
                candidate,
            )

            resolution = self.resolver.resolve(
                sandbox,
                self.requirements_file,
            )

            resolution_metadata = {
                "return_code": resolution.return_code,
                "stdout": resolution.stdout,
                "stderr": resolution.stderr,
                "duration_seconds": resolution.duration_seconds,
                "timed_out": resolution.timed_out,
            }

            if resolution.timed_out:
                return MutationResult(
                    candidate=candidate,
                    outcome=MutationOutcome.INVALID,
                    duration_seconds=resolution.duration_seconds,
                    reason=(
                        "Mutated dependency environment resolution "
                        "timed out."
                    ),
                    metadata={
                        "dependency_mode": "resolved",
                        "baseline_resolved_version": baseline_version,
                        "mutant_resolved_version": None,
                        "resolution": resolution_metadata,
                    },
                )

            if (
                resolution.return_code != 0
                or resolution.python_executable is None
            ):
                return MutationResult(
                    candidate=candidate,
                    outcome=MutationOutcome.INVALID,
                    duration_seconds=resolution.duration_seconds,
                    reason=(
                        "Mutated dependency environment could not "
                        "be resolved."
                    ),
                    metadata={
                        "dependency_mode": "resolved",
                        "baseline_resolved_version": baseline_version,
                        "mutant_resolved_version": None,
                        "resolution": resolution_metadata,
                    },
                )

            mutant_version = self.resolver.distribution_version(
                resolution.python_executable,
                package,
            )

            if mutant_version is None:
                return MutationResult(
                    candidate=candidate,
                    outcome=MutationOutcome.INVALID,
                    duration_seconds=resolution.duration_seconds,
                    reason=(
                        "Target dependency was not present in the "
                        "mutated resolved environment."
                    ),
                    metadata={
                        "dependency_mode": "resolved",
                        "baseline_resolved_version": baseline_version,
                        "mutant_resolved_version": None,
                        "resolution": resolution_metadata,
                    },
                )

            if mutant_version == baseline_version:
                return MutationResult(
                    candidate=candidate,
                    outcome=MutationOutcome.EQUIVALENT,
                    duration_seconds=resolution.duration_seconds,
                    reason=(
                        "The mutated dependency specification resolved "
                        "to the same installed version as the baseline."
                    ),
                    metadata={
                        "dependency_mode": "resolved",
                        "baseline_resolved_version": baseline_version,
                        "mutant_resolved_version": mutant_version,
                        "resolution": resolution_metadata,
                    },
                )

            resolved_runner = self.runner.with_python_executable(
                resolution.python_executable
            )

            validation = resolved_runner.run(
                sandbox,
                prefer_project_sources=True,
            )

        metadata = {
            "dependency_mode": "resolved",
            "baseline_resolved_version": baseline_version,
            "mutant_resolved_version": mutant_version,
            "resolution": resolution_metadata,
            "return_code": validation.return_code,
            "stdout": validation.stdout,
            "stderr": validation.stderr,
        }

        total_duration = (
            resolution.duration_seconds
            + validation.duration_seconds
        )

        if validation.timed_out:
            outcome = MutationOutcome.TIMEOUT
            reason = (
                "Validation timed out after resolving the "
                "mutated dependency environment."
            )
        elif validation.return_code == 0:
            outcome = MutationOutcome.SURVIVED
            reason = (
                "The dependency resolved to a different version and "
                "existing safeguards still completed successfully."
            )
        else:
            outcome = MutationOutcome.KILLED
            reason = (
                "The dependency resolved to a different version and "
                "existing safeguards failed."
            )

        return MutationResult(
            candidate=candidate,
            outcome=outcome,
            duration_seconds=total_duration,
            reason=reason,
            metadata=metadata,
        )