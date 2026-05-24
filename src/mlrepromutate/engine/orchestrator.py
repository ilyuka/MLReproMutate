from collections.abc import Callable, Sequence
from pathlib import Path

from mlrepromutate.engine.evaluator import MutationEvaluator
from mlrepromutate.engine.runner import ExecutionResult
from mlrepromutate.models import (
    MutationCandidate,
    MutationResult,
)
from mlrepromutate.operators.base import MutationOperator

CandidateStartCallback = Callable[
    [int, int, MutationCandidate],
    None,
]

CandidateResultCallback = Callable[
    [int, int, MutationResult],
    None,
]

BaselinePassedCallback = Callable[[ExecutionResult], None]


class MutationOrchestrator:
    """Detect and evaluate mutations for a project."""

    def __init__(self, evaluator: MutationEvaluator) -> None:
        self.evaluator = evaluator

    def run(
        self,
        project_root: Path,
        operator: MutationOperator,
        *,
        candidates: Sequence[MutationCandidate] | None = None,
        on_baseline_passed: BaselinePassedCallback | None = None,
        on_candidate_start: CandidateStartCallback | None = None,
        on_candidate_result: CandidateResultCallback | None = None,
    ) -> list[MutationResult]:
        """Detect and evaluate selected mutation candidates."""

        if candidates is None:
            selected_candidates = list(operator.detect(project_root))
        else:
            selected_candidates = list(candidates)

        if not selected_candidates:
            return []

        baseline_result = self.evaluator.validate_baseline(project_root)

        if on_baseline_passed is not None:
            on_baseline_passed(baseline_result)

        results: list[MutationResult] = []
        total = len(selected_candidates)

        for index, candidate in enumerate(
            selected_candidates,
            start=1,
        ):
            if on_candidate_start is not None:
                on_candidate_start(
                    index,
                    total,
                    candidate,
                )

            result = self.evaluator.evaluate_mutation(
                project_root,
                operator,
                candidate,
            )
            results.append(result)

            if on_candidate_result is not None:
                on_candidate_result(
                    index,
                    total,
                    result,
                )

        return results
