from collections.abc import Sequence
from pathlib import Path
from typing import Any

from mlrepromutate.engine.runner import ExecutionResult, ExperimentRunner
from mlrepromutate.engine.workspace import (
    ExecutionMode,
    MutationWorkspace,
    ProjectWorkspace,
)
from mlrepromutate.models import (
    MutationCandidate,
    MutationOutcome,
    MutationResult,
)
from mlrepromutate.operators.base import MutationOperator


class BaselineValidationError(RuntimeError):
    """The unmodified project failed or timed out during validation."""


class MutationEvaluator:
    """Evaluate mutation candidates against a project's safeguards.

    Args:
        runner: Runner for the project's validation command.
        execution_mode: Workspace isolation mode.
        sandbox_excludes: Project-relative paths omitted from sandbox copies.

    Attributes:
        runner: Runner used for baseline and mutation validation.
        execution_mode: Workspace isolation mode.
        sandbox_excludes: Normalized tuple of sandbox exclusions.
    """

    def __init__(
        self,
        runner: ExperimentRunner,
        execution_mode: ExecutionMode = ExecutionMode.SANDBOX,
        *,
        sandbox_excludes: Sequence[Path] = (),
    ) -> None:
        self.runner = runner
        self.execution_mode = execution_mode
        self.sandbox_excludes = tuple(sandbox_excludes)

    def validate_baseline(
        self,
        project_root: Path,
    ) -> ExecutionResult:
        """Validate the unmodified project once.

        Args:
            project_root: Root directory of the project to validate.

        Returns:
            Successful baseline execution result.

        Raises:
            BaselineValidationError: Baseline validation fails or times out.
            FileNotFoundError: ``project_root`` does not exist.
            NotADirectoryError: ``project_root`` is not a directory.
        """

        with ProjectWorkspace(
            project_root,
            self.execution_mode,
            excludes=self.sandbox_excludes,
        ) as workspace:
            result = self.runner.run(
                workspace,
                prefer_project_sources=(
                    self.execution_mode is ExecutionMode.SANDBOX
                ),
            )

        if result.timed_out:
            raise BaselineValidationError(
                "Baseline validation timed out."
            )

        if result.return_code != 0:
            raise BaselineValidationError(
                "Baseline validation failed before mutation."
            )

        return result

    def evaluate_mutation(
        self,
        project_root: Path,
        operator: MutationOperator,
        candidate: MutationCandidate,
    ) -> MutationResult:
        """Evaluate one mutation after a successful baseline.

        This method assumes baseline validation has already succeeded.

        Args:
            project_root: Root directory of the project to evaluate.
            operator: Operator that detected and applies the candidate.
            candidate: Candidate to apply and validate.

        Returns:
            Mutation result classified from the validation execution.
        """

        with MutationWorkspace(
            project_root,
            candidate,
            self.execution_mode,
            excludes=self.sandbox_excludes,
        ) as workspace:
            operator.apply(workspace, candidate)
            mutation_execution = self.runner.run(
                workspace,
                prefer_project_sources=(
                    self.execution_mode is ExecutionMode.SANDBOX
                ),
            )

        if mutation_execution.timed_out:
            outcome = MutationOutcome.TIMEOUT
            reason = "Validation timed out after applying the mutation."
        elif mutation_execution.return_code == 0:
            outcome = MutationOutcome.SURVIVED
            reason = (
                "Existing safeguards completed successfully and did not "
                "detect the mutation."
            )
        else:
            outcome = MutationOutcome.KILLED
            reason = (
                "Existing safeguards failed after applying the mutation."
            )

        return MutationResult(
            candidate=candidate,
            outcome=outcome,
            duration_seconds=mutation_execution.duration_seconds,
            reason=reason,
            metadata={
                "return_code": mutation_execution.return_code,
                "stdout": mutation_execution.stdout,
                "stderr": mutation_execution.stderr,
            },
        )

    def evaluate(
        self,
        project_root: Path,
        operator: MutationOperator,
        candidate: MutationCandidate,
    ) -> MutationResult:
        """Validate the baseline and evaluate one mutation.

        Args:
            project_root: Root directory of the project to evaluate.
            operator: Operator that detected and applies the candidate.
            candidate: Candidate to apply and validate.

        Returns:
            Mutation result produced after a successful baseline.

        Raises:
            BaselineValidationError: Baseline validation fails or times out.
        """

        self.validate_baseline(project_root)

        return self.evaluate_mutation(
            project_root,
            operator,
            candidate,
        )

    def run_metadata(self) -> dict[str, Any]:
        """Return evaluator-specific run provenance.

        Returns:
            Metadata to include in a run report.
        """

        return {}
