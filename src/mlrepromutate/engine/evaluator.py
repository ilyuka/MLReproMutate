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
    """Raised when the unmodified project does not pass validation."""


class MutationEvaluator:
    """Evaluate mutation candidates against project safeguards."""

    def __init__(
        self,
        runner: ExperimentRunner,
        execution_mode: ExecutionMode = ExecutionMode.SANDBOX,
    ) -> None:
        self.runner = runner
        self.execution_mode = execution_mode

    def validate_baseline(
        self,
        project_root: Path,
    ) -> ExecutionResult:
        """Validate the unmodified project once."""

        with ProjectWorkspace(
            project_root,
            self.execution_mode,
        ) as workspace:
            result = self.runner.run(workspace)

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
        """Evaluate one mutation after a successful baseline."""

        with MutationWorkspace(
            project_root,
            candidate,
            self.execution_mode,
        ) as workspace:
            operator.apply(workspace, candidate)
            mutation_execution = self.runner.run(workspace)

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
        """Validate the baseline and evaluate one mutation."""

        self.validate_baseline(project_root)

        return self.evaluate_mutation(
            project_root,
            operator,
            candidate,
        )

    def run_metadata(self) -> dict[str, Any]:
        """Return evaluator-specific run provenance."""

        return {}