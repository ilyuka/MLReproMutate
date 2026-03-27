from pathlib import Path

from mlrepromutate.engine.runner import ExperimentRunner
from mlrepromutate.engine.sandbox import ProjectSandbox
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

    def __init__(self, runner: ExperimentRunner) -> None:
        self.runner = runner

    def evaluate(
        self,
        project_root: Path,
        operator: MutationOperator,
        candidate: MutationCandidate,
    ) -> MutationResult:
        """Evaluate one mutation candidate."""

        baseline_result = self._run_baseline(project_root)

        if baseline_result.timed_out:
            raise BaselineValidationError(
                "Baseline validation timed out."
            )

        if baseline_result.return_code != 0:
            raise BaselineValidationError(
                "Baseline validation failed before mutation."
            )

        with ProjectSandbox(project_root) as sandbox:
            operator.apply(sandbox, candidate)

            mutation_execution = self.runner.run(sandbox)

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

    def _run_baseline(self, project_root: Path):
        with ProjectSandbox(project_root) as sandbox:
            return self.runner.run(sandbox)